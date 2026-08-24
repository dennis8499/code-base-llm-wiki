from __future__ import annotations

import contextlib
import importlib.util
import io
import json
import os
from pathlib import Path
import subprocess
import sys
import tempfile
import unittest
from unittest import mock


REPO_ROOT = Path(__file__).parents[1]
SCRIPT = REPO_ROOT / ".agents" / "skills" / "codebase-wiki" / "scripts" / "export-notebooklm.py"


def create_directory_reparse_point(link: Path, target: Path) -> None:
    try:
        os.symlink(target, link, target_is_directory=True)
        return
    except (OSError, NotImplementedError) as symlink_error:
        if os.name != "nt":
            raise symlink_error
    result = subprocess.run(
        ["cmd", "/c", "mklink", "/J", str(link), str(target)],
        check=False,
        capture_output=True,
        text=True,
        encoding="utf-8",
        errors="replace",
    )
    if result.returncode != 0:
        raise OSError(result.stderr or result.stdout or "unable to create directory junction")


def load_exporter():
    scripts = str(SCRIPT.parent)
    import sys

    if scripts not in sys.path:
        sys.path.insert(0, scripts)
    spec = importlib.util.spec_from_file_location("export_notebooklm_under_test", SCRIPT)
    assert spec and spec.loader
    module = importlib.util.module_from_spec(spec)
    sys.modules[spec.name] = module
    spec.loader.exec_module(module)
    return module


def write_fixture(root: Path) -> None:
    (root / "wiki").mkdir(parents=True)
    (root / "src").mkdir()
    (root / "wiki/index.md").write_text(
        """---
title: Wiki Index
type: index
sources: []
last_updated: 2026-08-17
tags: [index]
status: active
---

# Wiki Index

[[overview]]
[[project-function-catalog]]
[[system-architecture]]
[[system-analysis]]
""",
        encoding="utf-8",
    )
    (root / "wiki/overview.md").write_text(
        """---
title: Project Overview
type: overview
sources:
  - src/service.py
last_updated: 2026-08-17
tags: [overview]
status: active
---

# Project Overview

The service returns a greeting.
""",
        encoding="utf-8",
    )
    (root / "src/service.py").write_text(
        "def greet(name: str) -> str:\n    return f\"hello {name}\"\n",
        encoding="utf-8",
    )
    (root / "wiki/log.md").write_text(
        """---
title: Wiki Activity Log
type: log
sources: []
last_updated: 2026-08-17
tags: [log]
status: active
---

# Activity Log
""",
        encoding="utf-8",
    )
    required = {
        "synthesis/project-function-catalog.md": ("Function Catalog", "synthesis", "project"),
        "architecture/system-architecture.md": ("System Architecture", "architecture", "architecture"),
        "synthesis/system-analysis.md": ("System Analysis", "synthesis", "system-analysis"),
    }
    for relative, (title, page_type, group) in required.items():
        path = root / "wiki" / relative
        path.parent.mkdir(parents=True, exist_ok=True)
        path.write_text(
            "---\n"
            f"title: {title}\n"
            f"type: {page_type}\n"
            f"notebooklm_group: {group}\n"
            "sources: []\n"
            "derived_from: [\"[[overview]]\"]\n"
            "last_updated: 2026-08-17\n"
            f"tags: [{page_type}]\n"
            "status: active\n"
            "---\n\n"
            f"# {title}\n\n[[overview]]\n",
            encoding="utf-8",
        )


def add_index_links(root: Path, *stems: str) -> None:
    index = root / "wiki/index.md"
    index.write_text(
        index.read_text(encoding="utf-8").rstrip()
        + "\n"
        + "\n".join(f"[[{stem}]]" for stem in stems)
        + "\n",
        encoding="utf-8",
    )


class NotebookLMExporterTests(unittest.TestCase):
    def test_compatibility_wrapper_matches_canonical_cli(self) -> None:
        canonical = SCRIPT.with_name("notebooklm_exporter.py")
        wrapper_result = subprocess.run(
            [sys.executable, str(SCRIPT), "--help"],
            check=False,
            capture_output=True,
            text=True,
            encoding="utf-8",
        )
        canonical_result = subprocess.run(
            [sys.executable, str(canonical), "--help"],
            check=False,
            capture_output=True,
            text=True,
            encoding="utf-8",
        )
        self.assertEqual(wrapper_result.returncode, canonical_result.returncode)
        self.assertEqual(wrapper_result.stdout, canonical_result.stdout)

    def run_export(self, module, root: Path, output: Path) -> tuple[int, dict[str, object]]:
        preflight_code, preflight = self.run_preflight(module, root)
        if preflight_code != 0:
            return preflight_code, preflight
        stdout = io.StringIO()
        relative_output = output.relative_to(root).as_posix()
        with contextlib.redirect_stdout(stdout):
            code = module.main(
                [
                    "--root",
                    str(root),
                    "--apply",
                    "--preflight-id",
                    str(preflight["preflight_id"]),
                    "--output",
                    relative_output,
                    "--format",
                    "json",
                ]
            )
        return code, json.loads(stdout.getvalue())

    def run_preflight(
        self, module, root: Path, output: Path | None = None
    ) -> tuple[int, dict[str, object]]:
        arguments = ["--root", str(root), "--preflight", "--format", "json"]
        if output is not None:
            arguments[2:2] = ["--output", output.relative_to(root).as_posix()]
        stdout = io.StringIO()
        with contextlib.redirect_stdout(stdout):
            code = module.main(arguments)
        return code, json.loads(stdout.getvalue())

    def test_first_and_second_runs_produce_incremental_actions(self) -> None:
        module = load_exporter()
        with tempfile.TemporaryDirectory() as directory:
            root = Path(directory)
            write_fixture(root)
            output = root / ".notebooklm"

            first_code, first = self.run_export(module, root, output)
            self.assertEqual(first_code, 0)
            self.assertEqual(first["source_count"], 5)
            self.assertEqual(len(first["actions"]["added"]), 5)
            self.assertTrue((output / "manifest.json").is_file())
            self.assertTrue((output / "sources/project-map.md").is_file())

            second_code, second = self.run_export(module, root, output)
            self.assertEqual(second_code, 0)
            self.assertEqual(len(second["actions"]["added"]), 0)
            self.assertEqual(len(second["actions"]["changed"]), 0)
            self.assertEqual(len(second["actions"]["deleted"]), 0)
            self.assertEqual(len(second["actions"]["unchanged"]), 5)

            (root / "src/service.py").write_text(
                "def greet(name: str) -> str:\n    return f\"welcome {name}\"\n",
                encoding="utf-8",
            )
            changed_code, changed = self.run_export(module, root, output)
            self.assertEqual(changed_code, 0)
            self.assertEqual(
                [item["logical_source_id"] for item in changed["actions"]["changed"]],
                ["evidence:project"],
            )
            self.assertEqual(len(changed["actions"]["unchanged"]), 4)

    def test_add_and_delete_page_updates_project_map_and_source_plan(self) -> None:
        module = load_exporter()
        with tempfile.TemporaryDirectory() as directory:
            root = Path(directory)
            write_fixture(root)
            output = root / ".notebooklm"
            self.run_export(module, root, output)

            new_page = root / "wiki/guides/usage.md"
            new_page.parent.mkdir()
            new_page.write_text(
                """---
title: Usage
type: guide
sources: []
last_updated: 2026-08-17
tags: [guide]
status: active
---

# Usage

Call the service.
""",
                encoding="utf-8",
            )
            add_index_links(root, "usage")
            added_code, added = self.run_export(module, root, output)
            self.assertEqual(added_code, 0)
            added_ids = {item["logical_source_id"] for item in added["actions"]["added"]}
            changed_ids = {item["logical_source_id"] for item in added["actions"]["changed"]}
            self.assertIn("docs:project-guides", added_ids)
            self.assertIn("project-map", changed_ids)

            new_page.unlink()
            index = root / "wiki/index.md"
            index.write_text(
                index.read_text(encoding="utf-8").replace("[[usage]]\n", ""),
                encoding="utf-8",
            )
            deleted_code, deleted = self.run_export(module, root, output)
            self.assertEqual(deleted_code, 0)
            deleted_ids = {item["logical_source_id"] for item in deleted["actions"]["deleted"]}
            self.assertIn("docs:project-guides", deleted_ids)
            self.assertIn(
                "project-map",
                {item["logical_source_id"] for item in deleted["actions"]["changed"]},
            )

    def test_sensitive_and_generated_inputs_are_reported_and_not_exported(self) -> None:
        module = load_exporter()
        with tempfile.TemporaryDirectory() as directory:
            root = Path(directory)
            write_fixture(root)
            (root / ".env").write_text("TOKEN=do-not-export\n", encoding="utf-8")
            (root / ".github").mkdir()
            (root / ".github/private.md").write_text("internal\n", encoding="utf-8")
            overview = root / "wiki/overview.md"
            overview.write_text(
                overview.read_text(encoding="utf-8").replace(
                    "  - src/service.py\n", "  - src/service.py\n  - .env\n  - .github/\n"
                ),
                encoding="utf-8",
            )
            output = root / ".notebooklm"
            code, result = self.run_export(module, root, output)
            self.assertEqual(code, 0)
            skipped = {(item["path"], item["reason"]) for item in result["manifest"]["skipped"]}
            self.assertIn((".env", "sensitive_filename"), skipped)
            self.assertTrue(any(path == ".github/private.md" for path, _ in skipped))
            exported_text = "\n".join(
                path.read_text(encoding="utf-8")
                for path in (output / "sources").glob("*.md")
            )
            self.assertNotIn("do-not-export", exported_text)

    def test_sensitive_filter_ignores_repository_parent_directories(self) -> None:
        module = load_exporter()
        with tempfile.TemporaryDirectory() as directory:
            root = Path(directory) / "secrets" / "project"
            root.mkdir(parents=True)
            write_fixture(root)

            code, result = self.run_preflight(module, root)

            self.assertEqual(code, 0)
            included = {
                item["path"]: item["category"]
                for item in result["inventory"]["included"]
            }
            self.assertEqual(included["src/service.py"], "runtime_source")

    def test_limits_fail_before_replacing_existing_pack(self) -> None:
        module = load_exporter()
        with tempfile.TemporaryDirectory() as directory:
            root = Path(directory)
            write_fixture(root)
            output = root / ".notebooklm"
            first_code, _ = self.run_export(module, root, output)
            self.assertEqual(first_code, 0)
            before = (output / "manifest.json").read_bytes()
            (root / "notebooklm.toml").write_text(
                "source_limit = 2\nreserved_source_slots = 1\n",
                encoding="utf-8",
            )
            failed_code, failed = self.run_export(module, root, output)
            self.assertEqual(failed_code, 2)
            self.assertIn("source slot", failed["error"])
            self.assertEqual((output / "manifest.json").read_bytes(), before)

    def test_source_parts_stay_within_configured_limits(self) -> None:
        module = load_exporter()
        with tempfile.TemporaryDirectory() as directory:
            root = Path(directory)
            write_fixture(root)
            (root / "notebooklm.toml").write_text(
                "max_source_bytes = 220\nmax_source_words = 100\nsource_limit = 50\n",
                encoding="utf-8",
            )
            output = root / ".notebooklm"
            code, result = self.run_export(module, root, output)
            self.assertEqual(code, 0)
            self.assertGreater(result["source_count"], 4)
            manifest = json.loads((output / "manifest.json").read_text(encoding="utf-8"))
            for source in manifest["sources"]:
                self.assertLessEqual(source["byte_count"], 220)
                self.assertLessEqual(source["estimated_words"], 100)
            self.assertTrue(any("#part-" in item["logical_source_id"] for item in manifest["sources"]))

    def test_unsplittable_utf8_character_fails_before_output_commit(self) -> None:
        module = load_exporter()
        with tempfile.TemporaryDirectory() as directory:
            root = Path(directory)
            write_fixture(root)
            (root / "notebooklm.toml").write_text(
                "max_source_bytes = 1\nmax_source_words = 10\n",
                encoding="utf-8",
            )
            output = root / ".notebooklm"

            code, result = self.run_export(module, root, output)

            self.assertEqual(code, 2)
            self.assertIn("unable to split", result["error"])
            self.assertFalse(output.exists())

    def test_invalid_parent_source_is_rejected_without_output(self) -> None:
        module = load_exporter()
        with tempfile.TemporaryDirectory() as directory:
            root = Path(directory)
            write_fixture(root)
            overview = root / "wiki/overview.md"
            overview.write_text(
                overview.read_text(encoding="utf-8").replace(
                    "  - src/service.py", "  - ../outside.md"
                ),
                encoding="utf-8",
            )
            output = root / ".notebooklm"
            code, result = self.run_export(module, root, output)
            self.assertEqual(code, 2)
            self.assertIn("repo-relative", result["error"])
            self.assertFalse(output.exists())

    def test_explicit_missing_config_is_rejected(self) -> None:
        module = load_exporter()
        with tempfile.TemporaryDirectory() as directory:
            root = Path(directory)
            write_fixture(root)
            stdout = io.StringIO()
            with contextlib.redirect_stdout(stdout):
                code = module.main(
                    [
                        "--root",
                        str(root),
                        "--config",
                        "missing.toml",
                        "--preflight",
                        "--format",
                        "json",
                    ]
                )

            self.assertEqual(code, 2)
            self.assertIn("config path does not exist", json.loads(stdout.getvalue())["error"])

    def test_invalid_utf8_config_is_rejected_without_traceback(self) -> None:
        module = load_exporter()
        with tempfile.TemporaryDirectory() as directory:
            root = Path(directory)
            write_fixture(root)
            config = root / "invalid.toml"
            config.write_bytes(b"\xff\xfe invalid utf-8")
            stdout = io.StringIO()
            with contextlib.redirect_stdout(stdout):
                code = module.main(
                    [
                        "--root",
                        str(root),
                        "--config",
                        str(config),
                        "--preflight",
                        "--format",
                        "json",
                    ]
                )

            self.assertEqual(code, 2)
            self.assertIn("unable to read config", json.loads(stdout.getvalue())["error"])

    def test_invalid_utf8_previous_manifest_is_rejected_without_traceback(self) -> None:
        module = load_exporter()
        with tempfile.TemporaryDirectory() as directory:
            root = Path(directory)
            write_fixture(root)
            output = root / ".notebooklm"
            output.mkdir()
            (output / "manifest.json").write_bytes(b"\xff\xfe invalid utf-8")

            code, result = self.run_export(module, root, output)

            self.assertEqual(code, 2)
            self.assertIn("unable to read previous manifest", result["error"])

    def test_invalid_utf8_transaction_journal_is_rejected_without_traceback(self) -> None:
        load_exporter()
        module = sys.modules["notebooklm_exporter"]
        with tempfile.TemporaryDirectory() as directory:
            output = Path(directory) / "pack"
            output.mkdir()
            module._output_transaction_path(output).write_bytes(b"\xff\xfe invalid utf-8")

            with self.assertRaisesRegex(
                module.ExportError, "unable to read NotebookLM transaction journal"
            ):
                module._recover_pending_output(output)

    def test_explicit_config_outside_repository_is_rejected_before_reading(self) -> None:
        module = load_exporter()
        with tempfile.TemporaryDirectory() as directory:
            base = Path(directory)
            root = base / "repo"
            root.mkdir()
            write_fixture(root)
            outside = base / "outside.toml"
            outside.write_text("this is not valid TOML =\n", encoding="utf-8")
            stdout = io.StringIO()
            with contextlib.redirect_stdout(stdout):
                code = module.main(
                    [
                        "--root",
                        str(root),
                        "--config",
                        str(outside),
                        "--preflight",
                        "--format",
                        "json",
                    ]
                )

            self.assertEqual(code, 2)
            self.assertIn(
                "config path must stay inside the repository",
                json.loads(stdout.getvalue())["error"],
            )

    def test_output_directory_must_be_a_child_directory(self) -> None:
        module = load_exporter()
        with tempfile.TemporaryDirectory() as directory:
            root = Path(directory)
            write_fixture(root)
            (root / "notebooklm.toml").write_text(
                'output_directory = "."\n', encoding="utf-8"
            )
            stdout = io.StringIO()
            with contextlib.redirect_stdout(stdout):
                code = module.main(
                    ["--root", str(root), "--preflight", "--format", "json"]
                )

            self.assertEqual(code, 2)
            self.assertIn(
                "output_directory must be a child directory",
                json.loads(stdout.getvalue())["error"],
            )

    def test_output_root_symlink_is_rejected_before_export(self) -> None:
        module = load_exporter()
        with tempfile.TemporaryDirectory() as directory:
            root = Path(directory)
            write_fixture(root)
            real_output = root / "real-pack"
            real_output.mkdir()
            link = root / "pack"
            try:
                create_directory_reparse_point(link, real_output)
            except (OSError, NotImplementedError) as exc:
                self.skipTest(f"symlink creation is unavailable: {exc}")

            code, result = self.run_preflight(module, root, link)

            self.assertEqual(code, 2)
            self.assertIn("must not contain symlink", result["error"])
            self.assertFalse((real_output / "manifest.json").exists())

    def test_output_tree_junction_is_rejected_before_copy(self) -> None:
        load_exporter()
        canonical = sys.modules["notebooklm_exporter"]
        with tempfile.TemporaryDirectory() as directory:
            root = Path(directory)
            output = root / "pack"
            outside = root / "outside"
            output.mkdir()
            outside.mkdir()
            try:
                create_directory_reparse_point(output / "linked", outside)
            except (OSError, NotImplementedError) as exc:
                self.skipTest(f"directory reparse point unavailable: {exc}")

            with self.assertRaisesRegex(canonical.ExportError, "reparse point"):
                canonical.commit_output(output, {"manifest.json": b"{}\n"}, None)

    def test_output_override_is_bound_to_preflight_identity(self) -> None:
        module = load_exporter()
        with tempfile.TemporaryDirectory() as directory:
            root = Path(directory)
            write_fixture(root)
            alternate = root / "alternate-pack"
            default_code, default = self.run_preflight(module, root)
            alternate_code, alternate_preflight = self.run_preflight(
                module, root, alternate
            )
            self.assertEqual(default_code, 0)
            self.assertEqual(alternate_code, 0)
            self.assertNotEqual(
                default["preflight_id"], alternate_preflight["preflight_id"]
            )

            stdout = io.StringIO()
            with contextlib.redirect_stdout(stdout):
                code = module.main(
                    [
                        "--root",
                        str(root),
                        "--output",
                        "alternate-pack",
                        "--apply",
                        "--preflight-id",
                        str(default["preflight_id"]),
                        "--format",
                        "json",
                    ]
                )

            self.assertEqual(code, 2)
            self.assertIn("preflight_id", json.loads(stdout.getvalue())["error"])
            self.assertFalse(alternate.exists())

    def test_preflight_scans_selected_project_evidence_without_writing(self) -> None:
        module = load_exporter()
        with tempfile.TemporaryDirectory() as directory:
            root = Path(directory)
            write_fixture(root)
            (root / "docs").mkdir()
            (root / "docs/usage.md").write_text("# Usage\n", encoding="utf-8")
            (root / "config").mkdir()
            (root / "config/runtime.toml").write_text("port = 8080\n", encoding="utf-8")
            (root / "migrations").mkdir()
            (root / "migrations/001.sql").write_text("create table item(id int);\n", encoding="utf-8")
            (root / "tests").mkdir()
            (root / "tests/test_service.py").write_text("assert True\n", encoding="utf-8")
            (root / ".github/workflows").mkdir(parents=True)
            (root / ".github/workflows/ci.yml").write_text("name: ci\n", encoding="utf-8")
            (root / "infra").mkdir()
            (root / "infra/main.tf").write_text("resource {}\n", encoding="utf-8")
            (root / "tools").mkdir()
            (root / "tools/build.py").write_text("print('build')\n", encoding="utf-8")
            (root / "secrets").mkdir()
            (root / "secrets/runtime.toml").write_text(
                "token = 'do-not-export'\n", encoding="utf-8"
            )
            (root / ".codex-hook-logs").mkdir()
            (root / ".codex-hook-logs/audit.jsonl").write_text(
                "generated audit state\n", encoding="utf-8"
            )
            (root / ".github-hook-logs").mkdir()
            (root / ".github-hook-logs/audit.jsonl").write_text(
                "generated audit state\n", encoding="utf-8"
            )
            (root / ".agents/skills/codebase-wiki").mkdir(parents=True)
            (root / ".agents/skills/codebase-wiki/SKILL.md").write_text("framework\n", encoding="utf-8")
            (root / ".env").write_text("TOKEN=hidden\n", encoding="utf-8")
            (root / "logo.bin").write_bytes(b"\x00\x01")

            code, result = self.run_preflight(module, root)

            self.assertEqual(code, 0)
            self.assertEqual(result["mode"], "preflight")
            self.assertFalse((root / ".notebooklm").exists())
            included = {item["path"]: item["category"] for item in result["inventory"]["included"]}
            self.assertEqual(included["src/service.py"], "runtime_source")
            self.assertEqual(included["config/runtime.toml"], "runtime_config")
            self.assertEqual(included["migrations/001.sql"], "data_schema")
            self.assertEqual(included["docs/usage.md"], "documentation")
            excluded = {item["path"]: item["reason"] for item in result["inventory"]["excluded"]}
            self.assertEqual(excluded["tests/test_service.py"], "scan_scope_tests")
            self.assertEqual(excluded[".github/workflows/ci.yml"], "scan_scope_ci_or_iac")
            self.assertEqual(excluded["infra/main.tf"], "scan_scope_ci_or_iac")
            self.assertEqual(excluded["tools/build.py"], "scan_scope_dev_tooling")
            self.assertEqual(excluded[".codex-hook-logs/audit.jsonl"], "binary_or_generated")
            self.assertEqual(excluded[".github-hook-logs/audit.jsonl"], "binary_or_generated")
            self.assertEqual(excluded[".agents/skills/codebase-wiki/SKILL.md"], "framework_adapter")
            self.assertEqual(excluded[".env"], "sensitive_filename")
            self.assertEqual(excluded["secrets/runtime.toml"], "sensitive_filename")
            self.assertEqual(excluded["logo.bin"], "binary_or_unsupported_encoding")
            self.assertEqual(result["limits"]["enterprise_max_bytes"], 200_000_000)
            self.assertEqual(result["limits"]["max_bytes"], 180_000_000)
            self.assertTrue(result["ready_to_export"])
            self.assertEqual(result["coverage"]["status"], "partial")
            self.assertGreater(result["coverage"]["uncovered_count"], 0)
            self.assertTrue(
                any("未被 Wiki sources 覆蓋" in warning for warning in result["warnings"])
            )
            self.assertRegex(result["preflight_id"], r"^sha256:[0-9a-f]{64}$")

    def test_preflight_rejects_symlinked_files_that_escape_repository(self) -> None:
        module = load_exporter()
        with tempfile.TemporaryDirectory() as directory:
            base = Path(directory)
            root = base / "repo"
            outside = base / "outside.md"
            write_fixture(root)
            outside.write_text("outside\n", encoding="utf-8")
            link = root / "src/linked.md"
            try:
                os.symlink(outside, link)
            except (OSError, NotImplementedError) as exc:
                self.skipTest(f"symlink creation is unavailable: {exc}")

            code, result = self.run_preflight(module, root)

            self.assertEqual(code, 0)
            excluded = {
                item["path"]: item["reason"] for item in result["inventory"]["excluded"]
            }
            self.assertEqual(excluded["src/linked.md"], "path_escape")
            self.assertNotIn("src/linked.md", {item["path"] for item in result["inventory"]["included"]})

    def test_preflight_rejects_unsafe_wiki_tree_before_reading(self) -> None:
        module = load_exporter()
        with tempfile.TemporaryDirectory() as directory:
            base = Path(directory)
            root = base / "repo"
            outside = base / "outside"
            write_fixture(root)
            outside.mkdir()
            (outside / "rogue.md").write_bytes(b"\xff\xfe external content")
            link = root / "wiki/linked"
            try:
                create_directory_reparse_point(link, outside)
            except (OSError, NotImplementedError) as exc:
                self.skipTest(f"directory reparse point unavailable: {exc}")

            code, result = self.run_preflight(module, root)

            self.assertEqual(code, 2)
            self.assertIn("Wiki directory is unsafe to read", result["error"])
            self.assertIn("symlink or reparse point", result["error"])
            self.assertNotIn("unable to read Wiki page", result["error"])

    def test_preflight_rejects_reparse_root_before_resolving(self) -> None:
        load_exporter()
        module = sys.modules["notebooklm_exporter"]
        with tempfile.TemporaryDirectory() as directory:
            base = Path(directory)
            actual = base / "repo"
            write_fixture(actual)
            linked = base / "repo-link"
            try:
                create_directory_reparse_point(linked, actual)
            except (OSError, NotImplementedError) as exc:
                self.skipTest(f"directory reparse point unavailable: {exc}")

            with self.assertRaisesRegex(module.ExportError, "root must not be a symlink or reparse point"):
                module.collect_wiki_pages(linked)
            code, result = self.run_preflight(module, linked)
            self.assertEqual(code, 2)
            self.assertIn("root must not be a symlink or reparse point", result["error"])

    def test_direct_export_is_rejected_and_changed_input_invalidates_preflight(self) -> None:
        module = load_exporter()
        with tempfile.TemporaryDirectory() as directory:
            root = Path(directory)
            write_fixture(root)
            stdout = io.StringIO()
            with contextlib.redirect_stdout(stdout):
                direct_code = module.main(
                    ["--root", str(root), "--output", ".notebooklm", "--format", "json"]
                )
            self.assertEqual(direct_code, 2)
            self.assertIn("direct export is disabled", json.loads(stdout.getvalue())["error"])

            preflight_code, preflight = self.run_preflight(module, root)
            self.assertEqual(preflight_code, 0)
            (root / "src/service.py").write_text("VALUE = 2\n", encoding="utf-8")
            stdout = io.StringIO()
            with contextlib.redirect_stdout(stdout):
                apply_code = module.main(
                    [
                        "--root",
                        str(root),
                        "--apply",
                        "--preflight-id",
                        str(preflight["preflight_id"]),
                        "--format",
                        "json",
                    ]
                )
            self.assertEqual(apply_code, 2)
            self.assertIn("no longer matches", json.loads(stdout.getvalue())["error"])
            self.assertFalse((root / ".notebooklm").exists())

    def test_missing_mandatory_document_keeps_preflight_not_ready(self) -> None:
        module = load_exporter()
        with tempfile.TemporaryDirectory() as directory:
            root = Path(directory)
            write_fixture(root)
            (root / "wiki/synthesis/system-analysis.md").unlink()
            index = root / "wiki/index.md"
            index.write_text(
                index.read_text(encoding="utf-8").replace("[[system-analysis]]\n", ""),
                encoding="utf-8",
            )

            code, result = self.run_preflight(module, root)

            self.assertEqual(code, 0)
            self.assertFalse(result["ready_to_export"])
            self.assertEqual(
                result["inventory"]["required_documents"][
                    "wiki/synthesis/system-analysis.md"
                ],
                "missing",
            )

    def test_framework_scan_profile_includes_framework_adapters(self) -> None:
        module = load_exporter()
        with tempfile.TemporaryDirectory() as directory:
            root = Path(directory)
            write_fixture(root)
            (root / ".agents/skills/codebase-wiki").mkdir(parents=True)
            (root / ".agents/skills/codebase-wiki/SKILL.md").write_text(
                "framework\n", encoding="utf-8"
            )
            (root / "notebooklm.toml").write_text(
                'scan_profile = "framework"\n', encoding="utf-8"
            )

            code, result = self.run_preflight(module, root)

            self.assertEqual(code, 0)
            included = {item["path"] for item in result["inventory"]["included"]}
            self.assertIn(".agents/skills/codebase-wiki/SKILL.md", included)

    def test_documents_are_kept_when_evidence_exceeds_source_budget(self) -> None:
        module = load_exporter()
        with tempfile.TemporaryDirectory() as directory:
            root = Path(directory)
            write_fixture(root)
            guide = root / "wiki/guides/usage.md"
            guide.parent.mkdir()
            guide.write_text(
                """---
title: Usage
type: guide
notebooklm_group: project-guides
sources: []
last_updated: 2026-08-20
tags: [guide]
status: active
---

# Usage
""",
                encoding="utf-8",
            )
            add_index_links(root, "usage")
            (root / "notebooklm.toml").write_text("source_limit = 5\n", encoding="utf-8")
            output = root / ".notebooklm"

            code, result = self.run_export(module, root, output)

            self.assertEqual(code, 0)
            self.assertEqual(result["source_count"], 5)
            self.assertEqual(result["manifest"]["omitted_evidence"], [
                {"path": "src/service.py", "reason": "source_budget"}
            ])
            self.assertTrue(all(item["kind"] != "evidence" for item in result["manifest"]["sources"]))
            self.assertIn(
                "因額度未匯出的證據",
                (output / "upload-plan.md").read_text(encoding="utf-8"),
            )

    def test_enterprise_byte_limit_is_200_mb(self) -> None:
        module = load_exporter()
        with tempfile.TemporaryDirectory() as directory:
            root = Path(directory)
            write_fixture(root)
            (root / "notebooklm.toml").write_text(
                "max_source_bytes = 200000001\n",
                encoding="utf-8",
            )
            output = root / ".notebooklm"

            code, result = self.run_export(module, root, output)

            self.assertEqual(code, 2)
            self.assertIn("200000000", result["error"])
            self.assertFalse(output.exists())

    def test_schema_v1_manifest_is_migrated_to_v2(self) -> None:
        module = load_exporter()
        with tempfile.TemporaryDirectory() as directory:
            root = Path(directory)
            write_fixture(root)
            output = root / ".notebooklm"
            first_code, _ = self.run_export(module, root, output)
            self.assertEqual(first_code, 0)
            manifest_path = output / "manifest.json"
            previous = json.loads(manifest_path.read_text(encoding="utf-8"))
            previous["schema_version"] = 1
            manifest_path.write_text(json.dumps(previous), encoding="utf-8")

            code, result = self.run_export(module, root, output)

            self.assertEqual(code, 0)
            self.assertEqual(result["manifest"]["schema_version"], 2)
            self.assertEqual(len(result["actions"]["unchanged"]), 5)

    def test_previous_manifest_path_traversal_is_rejected_without_deletion(self) -> None:
        module = load_exporter()
        with tempfile.TemporaryDirectory() as directory:
            root = Path(directory)
            write_fixture(root)
            output = root / ".notebooklm"
            first_code, _ = self.run_export(module, root, output)
            self.assertEqual(first_code, 0)

            victim = root / "victim.txt"
            victim.write_text("must survive\n", encoding="utf-8")
            manifest_path = output / "manifest.json"
            previous = json.loads(manifest_path.read_text(encoding="utf-8"))
            previous["sources"][0]["file"] = "../victim.txt"
            manifest_path.write_text(json.dumps(previous), encoding="utf-8")

            code, result = self.run_export(module, root, output)

            self.assertEqual(code, 2)
            self.assertIn("output directory", result["error"])
            self.assertTrue(victim.is_file())
            self.assertEqual(victim.read_text(encoding="utf-8"), "must survive\n")

    def test_commit_output_rejects_path_traversal_without_writing_outside(self) -> None:
        load_exporter()
        canonical = sys.modules["notebooklm_exporter"]
        with tempfile.TemporaryDirectory() as directory:
            root = Path(directory)
            output = root / "pack"
            victim = root / "victim.txt"

            with self.assertRaisesRegex(canonical.ExportError, "inside the output directory"):
                canonical.commit_output(output, {"../victim.txt": b"must not write\n"}, None)

            self.assertFalse(victim.exists())
            self.assertFalse(output.exists())

    def test_commit_output_rejects_symlinked_output_tree(self) -> None:
        load_exporter()
        canonical = sys.modules["notebooklm_exporter"]
        with tempfile.TemporaryDirectory() as directory:
            root = Path(directory)
            output = root / "pack"
            outside = root / "outside"
            outside.mkdir()
            (outside / "private.txt").write_text("private\n", encoding="utf-8")
            output.mkdir()
            try:
                os.symlink(outside / "private.txt", output / "managed.md")
            except (OSError, NotImplementedError) as exc:
                self.skipTest(f"symlink creation is unavailable: {exc}")

            with self.assertRaisesRegex(canonical.ExportError, "must not contain symlink"):
                canonical.commit_output(output, {"manifest.json": b"{}\n"}, None)

            self.assertTrue((outside / "private.txt").is_file())
            self.assertTrue((output / "managed.md").is_symlink())

    def test_commit_output_restores_previous_pack_after_replacement_failure(self) -> None:
        load_exporter()
        canonical = sys.modules["notebooklm_exporter"]
        with tempfile.TemporaryDirectory() as directory:
            root = Path(directory)
            output = root / "pack"
            output.mkdir()
            (output / "manifest.json").write_text('{"version": 1}\n', encoding="utf-8")
            (output / "old.md").write_text("old source\n", encoding="utf-8")
            original_replace = canonical.os.replace
            injected = False

            def fail_stage_replacement(source, destination):
                nonlocal injected
                if not injected and ".staging-" in str(source) and destination == output:
                    injected = True
                    raise OSError("injected output replacement failure")
                return original_replace(source, destination)

            with mock.patch.object(
                canonical.os, "replace", side_effect=fail_stage_replacement
            ):
                with self.assertRaisesRegex(
                    canonical.ExportError, "unable to commit NotebookLM output"
                ):
                    canonical.commit_output(
                        output,
                        {
                            "manifest.json": b'{"version": 2}\n',
                            "new.md": b"new source\n",
                        },
                        {"sources": [{"file": "old.md"}]},
                    )

            self.assertTrue(injected)
            self.assertEqual(
                (output / "manifest.json").read_text(encoding="utf-8"),
                '{"version": 1}\n',
            )
            self.assertEqual(
                (output / "old.md").read_text(encoding="utf-8"), "old source\n"
            )
            self.assertFalse((output / "new.md").exists())
            self.assertEqual(list(root.glob("pack.staging-*")), [])
            self.assertEqual(list(root.glob("pack.backup-*")), [])

    def test_commit_output_recovers_after_process_kill(self) -> None:
        load_exporter()
        canonical = sys.modules["notebooklm_exporter"]
        canonical_path = SCRIPT.with_name("notebooklm_exporter.py")
        with tempfile.TemporaryDirectory() as directory:
            root = Path(directory)
            output = root / "pack"
            output.mkdir()
            (output / "manifest.json").write_text('{"version": 1}\n', encoding="utf-8")
            (output / "old.md").write_text("old source\n", encoding="utf-8")
            canonical_path_literal = repr(str(canonical_path))
            output_path_literal = repr(str(output))
            child = f"""
import importlib.util
import os
from pathlib import Path
import sys

spec = importlib.util.spec_from_file_location("notebooklm_exporter_child", {canonical_path_literal})
assert spec and spec.loader
module = importlib.util.module_from_spec(spec)
sys.modules[spec.name] = module
spec.loader.exec_module(module)
output = Path({output_path_literal})
original_replace = module.os.replace

def crash_after_new_pack_is_visible(source, destination):
    result = original_replace(source, destination)
    if ".staging-" in str(source) and Path(destination) == output:
        os._exit(92)
    return result

module.os.replace = crash_after_new_pack_is_visible
module.commit_output(
    output,
    {{"manifest.json": bytes('{{"version": 2}}\\n', "utf-8"), "new.md": b"new source\\n"}},
    {{"sources": [{{"file": "old.md"}}]}},
)
"""
            result = subprocess.run(
                [sys.executable, "-c", child],
                check=False,
                capture_output=True,
            )
            child_stderr = result.stderr.decode("utf-8", errors="replace")
            self.assertEqual(result.returncode, 92, child_stderr)
            self.assertTrue(canonical._output_transaction_path(output).is_file())

            self.assertTrue(canonical._recover_pending_output(output))
            self.assertEqual(
                (output / "manifest.json").read_text(encoding="utf-8"),
                '{"version": 1}\n',
            )
            self.assertEqual(
                (output / "old.md").read_text(encoding="utf-8"), "old source\n"
            )
            self.assertFalse((output / "new.md").exists())
            self.assertFalse(canonical._output_transaction_path(output).exists())
            self.assertEqual(list(root.glob("pack.staging-*")), [])
            self.assertEqual(list(root.glob("pack.backup-*")), [])

    def test_commit_output_rejects_concurrent_writer(self) -> None:
        load_exporter()
        canonical = sys.modules["notebooklm_exporter"]
        canonical_path = SCRIPT.with_name("notebooklm_exporter.py")
        with tempfile.TemporaryDirectory() as directory:
            root = Path(directory)
            output = root / "pack"
            canonical_path_literal = repr(str(canonical_path))
            lock_path_literal = repr(str(canonical._output_transaction_lock_path(output)))
            child = f"""
import importlib.util
from pathlib import Path
import sys

spec = importlib.util.spec_from_file_location("notebooklm_exporter_lock_child", {canonical_path_literal})
assert spec and spec.loader
module = importlib.util.module_from_spec(spec)
sys.modules[spec.name] = module
spec.loader.exec_module(module)
with module._OutputTransactionLock(Path({lock_path_literal})):
    print("ready", flush=True)
    sys.stdin.buffer.read()
"""
            process = subprocess.Popen(
                [sys.executable, "-c", child],
                stdin=subprocess.PIPE,
                stdout=subprocess.PIPE,
                stderr=subprocess.PIPE,
                text=True,
                encoding="utf-8",
            )
            try:
                self.assertEqual(process.stdout.readline().strip(), "ready")
                with self.assertRaises(canonical.ExportError):
                    canonical.commit_output(
                        output, {"manifest.json": b"{}\n"}, None
                    )
            finally:
                if process.stdin is not None:
                    process.stdin.close()
                process.wait(timeout=10)
                stderr = process.stderr.read() if process.stderr is not None else ""
                if process.stdout is not None:
                    process.stdout.close()
                if process.stderr is not None:
                    process.stderr.close()
                self.assertEqual(process.returncode, 0, stderr)

    def test_output_transaction_journal_is_excluded_from_inventory(self) -> None:
        load_exporter()
        module = sys.modules["notebooklm_exporter"]
        with tempfile.TemporaryDirectory() as directory:
            root = Path(directory)
            write_fixture(root)
            settings = module.load_settings(root)
            journal = root / ".notebooklm.notebooklm-transaction.json"
            lock = root / ".notebooklm.notebooklm-transaction.lock"
            stage = root / "pack.staging-crashed"
            backup = root / "pack.backup-crashed"
            journal_temp = root / ".pack.notebooklm-transaction.json.tmp-crashed"
            journal.write_text('{"phase": "active"}\n', encoding="utf-8")
            lock.write_bytes(b"\0")
            stage.mkdir()
            backup.mkdir()
            journal_temp.write_text("partial\n", encoding="utf-8")
            try:
                self.assertEqual(
                    module.exclusion_reason(journal, root, settings),
                    "binary_or_generated",
                )
                self.assertEqual(
                    module.exclusion_reason(lock, root, settings),
                    "binary_or_generated",
                )
                self.assertEqual(
                    module.exclusion_reason(stage / "source.md", root, settings),
                    "binary_or_generated",
                )
                self.assertEqual(
                    module.exclusion_reason(backup / "source.md", root, settings),
                    "binary_or_generated",
                )
                self.assertEqual(
                    module.exclusion_reason(journal_temp, root, settings),
                    "binary_or_generated",
                )
            finally:
                journal.unlink()
                lock.unlink()
                journal_temp.unlink()
                stage.rmdir()
                backup.rmdir()

    def test_functional_pages_share_stable_document_group(self) -> None:
        module = load_exporter()
        with tempfile.TemporaryDirectory() as directory:
            root = Path(directory)
            write_fixture(root)
            modules = root / "wiki/modules"
            entities = root / "wiki/entities"
            modules.mkdir()
            entities.mkdir()
            module_page = modules / "orders.md"
            module_page.write_text(
                """---
title: Orders
type: module
notebooklm_group: function-orders
sources: []
last_updated: 2026-08-20
tags: [orders]
status: active
---

# Orders
""",
                encoding="utf-8",
            )
            (entities / "order-service.md").write_text(
                """---
title: Order Service
type: entity
entity_type: service
parent_module: orders
notebooklm_group: function-orders
sources: []
last_updated: 2026-08-20
tags: [orders]
status: active
---

# Order Service
""",
                encoding="utf-8",
            )
            add_index_links(root, "orders", "order-service")
            output = root / ".notebooklm"
            first_code, first = self.run_export(module, root, output)
            self.assertEqual(first_code, 0)
            ids = [item["logical_source_id"] for item in first["manifest"]["sources"]]
            self.assertEqual(ids.count("docs:function-orders"), 1)
            grouped = next(
                item for item in first["manifest"]["sources"]
                if item["logical_source_id"] == "docs:function-orders"
            )
            self.assertEqual(
                {item["path"] for item in grouped["inputs"]},
                {"wiki/modules/orders.md", "wiki/entities/order-service.md"},
            )

            module_page.write_text(
                module_page.read_text(encoding="utf-8") + "\nUpdated responsibility.\n",
                encoding="utf-8",
            )
            changed_code, changed = self.run_export(module, root, output)
            self.assertEqual(changed_code, 0)
            self.assertIn(
                "docs:function-orders",
                {item["logical_source_id"] for item in changed["actions"]["changed"]},
            )

    def test_preflight_and_apply_handle_500_wiki_pages(self) -> None:
        module = load_exporter()
        with tempfile.TemporaryDirectory() as directory:
            root = Path(directory)
            write_fixture(root)
            modules = root / "wiki/modules"
            modules.mkdir(parents=True)
            stems = [f"scale-{index:03d}" for index in range(500)]
            for index, stem in enumerate(stems):
                next_stem = stems[(index + 1) % len(stems)]
                (modules / f"{stem}.md").write_text(
                    "---\n"
                    f"title: Scale {index:03d}\n"
                    "type: module\n"
                    "sources: []\n"
                    "last_updated: 2026-08-17\n"
                    "tags: [module]\n"
                    "status: active\n"
                    "---\n\n"
                    f"# Scale {index:03d}\n\n[[{next_stem}]]\n",
                    encoding="utf-8",
                )
            add_index_links(root, *stems)
            output = root / ".notebooklm"

            preflight_code, preflight = self.run_preflight(module, root, output)
            self.assertEqual(preflight_code, 0)
            self.assertTrue(preflight["ready_to_export"])
            self.assertEqual(preflight["required_document_issues"], [])
            self.assertEqual(preflight["wiki_pages"], 505)

            export_code, exported = self.run_export(module, root, output)
            self.assertEqual(export_code, 0)
            self.assertEqual(exported["manifest"]["schema_version"], 2)
            self.assertLessEqual(exported["manifest"]["source_count"], 300)
            self.assertTrue((output / "manifest.json").is_file())

    def test_invalid_notebooklm_group_is_rejected(self) -> None:
        module = load_exporter()
        with tempfile.TemporaryDirectory() as directory:
            root = Path(directory)
            write_fixture(root)
            page = root / "wiki/modules/orders.md"
            page.parent.mkdir()
            page.write_text(
                """---
title: Orders
type: module
notebooklm_group: Function Orders
sources: []
last_updated: 2026-08-20
tags: [orders]
status: active
---

# Orders
""",
                encoding="utf-8",
            )
            add_index_links(root, "orders")
            output = root / ".notebooklm"

            code, result = self.run_preflight(module, root)

            self.assertEqual(code, 0)
            self.assertFalse(result["ready_to_export"])
            self.assertTrue(
                any(
                    "notebooklm_group" in item["message"]
                    for item in result["lint"]["findings"]
                )
            )
            self.assertFalse(output.exists())


if __name__ == "__main__":
    unittest.main()
