from __future__ import annotations

import contextlib
import importlib.util
import io
import json
from pathlib import Path
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


class NotebookLMExporterTests(unittest.TestCase):
    def run_export(self, module, root: Path, output: Path) -> tuple[int, dict[str, object]]:
        stdout = io.StringIO()
        relative_output = output.relative_to(root).as_posix()
        with contextlib.redirect_stdout(stdout):
            code = module.main(
                ["--root", str(root), "--output", relative_output, "--format", "json"]
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
            self.assertEqual(first["source_count"], 4)
            self.assertEqual(len(first["actions"]["added"]), 4)
            self.assertTrue((output / "manifest.json").is_file())
            self.assertTrue((output / "sources/project-map.md").is_file())

            second_code, second = self.run_export(module, root, output)
            self.assertEqual(second_code, 0)
            self.assertEqual(len(second["actions"]["added"]), 0)
            self.assertEqual(len(second["actions"]["changed"]), 0)
            self.assertEqual(len(second["actions"]["deleted"]), 0)
            self.assertEqual(len(second["actions"]["unchanged"]), 4)

            (root / "src/service.py").write_text(
                "def greet(name: str) -> str:\n    return f\"welcome {name}\"\n",
                encoding="utf-8",
            )
            changed_code, changed = self.run_export(module, root, output)
            self.assertEqual(changed_code, 0)
            self.assertEqual(
                [item["logical_source_id"] for item in changed["actions"]["changed"]],
                ["evidence:src"],
            )
            self.assertEqual(len(changed["actions"]["unchanged"]), 3)

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
            added_code, added = self.run_export(module, root, output)
            self.assertEqual(added_code, 0)
            added_ids = {item["logical_source_id"] for item in added["actions"]["added"]}
            changed_ids = {item["logical_source_id"] for item in added["actions"]["changed"]}
            self.assertIn("wiki:wiki/guides/usage.md", added_ids)
            self.assertIn("project-map", changed_ids)

            new_page.unlink()
            deleted_code, deleted = self.run_export(module, root, output)
            self.assertEqual(deleted_code, 0)
            deleted_ids = {item["logical_source_id"] for item in deleted["actions"]["deleted"]}
            self.assertIn("wiki:wiki/guides/usage.md", deleted_ids)
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
            self.assertIn("source pack needs", failed["error"])
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


if __name__ == "__main__":
    unittest.main()
