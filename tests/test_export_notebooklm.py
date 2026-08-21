from __future__ import annotations

import contextlib
import importlib.util
import io
import json
from pathlib import Path
import subprocess
import sys
import tempfile
import unittest


REPO_ROOT = Path(__file__).parents[1]
SCRIPT = REPO_ROOT / ".agents" / "skills" / "codebase-wiki" / "scripts" / "export-notebooklm.py"


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

    def run_preflight(self, module, root: Path) -> tuple[int, dict[str, object]]:
        stdout = io.StringIO()
        with contextlib.redirect_stdout(stdout):
            code = module.main(
                ["--root", str(root), "--preflight", "--format", "json"]
            )
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
            self.assertEqual(excluded[".agents/skills/codebase-wiki/SKILL.md"], "framework_adapter")
            self.assertEqual(excluded[".env"], "sensitive_filename")
            self.assertEqual(excluded["logo.bin"], "binary_or_unsupported_encoding")
            self.assertEqual(result["limits"]["enterprise_max_bytes"], 200_000_000)
            self.assertEqual(result["limits"]["max_bytes"], 180_000_000)
            self.assertTrue(result["ready_to_export"])
            self.assertRegex(result["preflight_id"], r"^sha256:[0-9a-f]{64}$")

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
