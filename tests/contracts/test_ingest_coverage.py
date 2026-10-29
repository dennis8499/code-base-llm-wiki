from copy import deepcopy
from pathlib import Path
import subprocess
import sys
import tempfile
import unittest

SCRIPTS = Path(__file__).resolve().parents[2] / ".agents/skills/codebase-wiki/scripts"
sys.path.insert(0, str(SCRIPTS))
from ingest_coverage import inventory, validate


class IngestCoverageTests(unittest.TestCase):
    def setUp(self):
        self.temporary = tempfile.TemporaryDirectory()
        self.addCleanup(self.temporary.cleanup)
        self.root = Path(self.temporary.name).resolve()

    def write(self, path, content="source\n"):
        target = self.root / path
        target.parent.mkdir(parents=True, exist_ok=True)
        target.write_text(content, encoding="utf-8")

    def processed(self, ledger):
        result = deepcopy(ledger)
        for entry in result["files"]:
            entry.update(status="processed", pages=["wiki/modules/project.md"], reason="")
        return result

    def test_covers_sources_outside_src_ignored_untracked_and_nested_repos(self):
        subprocess.run(["git", "init", str(self.root)], check=True, capture_output=True)
        self.write(".gitignore", "ignored.py\n")
        for path in ("src/main.py", "config/app.toml", "schema/table.sql", "docs/rules.md", "tests/test_api.py",
                     ".github/workflows/ci.yml", "tools/task.ps1", "ignored.py", "nested/app.py"):
            self.write(path)
        subprocess.run(["git", "init", str(self.root / "nested")], check=True, capture_output=True)
        self.write("wiki/modules/project.md")
        self.write("exports/archive/project-r1.md")
        self.write("nested/exports/archive/project-r1.md")
        self.write("exports/real-source.py")
        ledger = inventory(self.root)
        paths = {e["path"] for e in ledger["files"]}
        self.assertTrue({"config/app.toml", "schema/table.sql", "ignored.py", "nested/app.py", "exports/real-source.py"} <= paths)
        self.assertIn("exports/archive/project-r1.md", paths)
        self.assertIn("nested/exports/archive/project-r1.md", paths)
        self.assertEqual("partial", validate(self.root, ledger)["status"])
        self.assertTrue(validate(self.root, self.processed(ledger))["ok"])

    def test_missing_duplicate_blocked_invalid_mapping_and_drift_are_partial(self):
        self.write("main.py")
        self.write("wiki/modules/project.md")
        ledger = self.processed(inventory(self.root))
        variants = []
        missing = deepcopy(ledger); missing["files"].pop(); variants.append(missing)
        duplicate = deepcopy(ledger); duplicate["files"].append(duplicate["files"][0]); variants.append(duplicate)
        blocked = deepcopy(ledger); blocked["files"][0]["status"] = "blocked"; variants.append(blocked)
        invalid = deepcopy(ledger); invalid["files"][0]["pages"] = ["wiki/../outside.md"]; variants.append(invalid)
        for variant in variants:
            self.assertFalse(validate(self.root, variant)["ok"])
        self.write("main.py", "changed\n")
        self.assertFalse(validate(self.root, ledger)["ok"])

    def test_writing_wiki_cache_and_export_outputs_does_not_invalidate_raw_snapshot(self):
        self.write("main.py")
        ledger = self.processed(inventory(self.root))
        self.write("wiki/modules/project.md")
        self.write("__pycache__/generated.pyc")
        self.assertTrue(validate(self.root, ledger)["ok"])
        self.write("exports/archive/project-r1.md")
        self.assertFalse(validate(self.root, ledger)["ok"])

    def test_notebooklm_test_filter_does_not_narrow_full_ingest(self):
        self.write("notebooklm.toml", "[notebooklm]\nanalysis_include_tests = false\n")
        self.write("tests/test_feature.py")
        ledger = inventory(self.root)
        self.assertIn("tests/test_feature.py", {entry["path"] for entry in ledger["files"]})
        self.assertTrue(ledger["analysis_include_tests"])

    def test_group_default_includes_unmapped_repos_and_detects_new_repo(self):
        for name in ("Alpha", "Beta"):
            (self.root / name).mkdir()
            subprocess.run(["git", "init", str(self.root / name)], check=True, capture_output=True)
            self.write(name + "/main.py")
        self.write("wiki/modules/project.md")
        ledger = self.processed(inventory(self.root, scope="group"))
        self.assertEqual(["Alpha", "Beta"], ledger["repositories"])
        self.assertTrue(validate(self.root, ledger, scope="group")["ok"])
        self.assertFalse(validate(self.root, ledger, scope="group", selected=["Alpha"])["ok"])
        selected = self.processed(inventory(self.root, scope="group", selected=["Alpha"]))
        self.assertTrue(validate(self.root, selected, scope="group", selected=["Alpha"])["ok"])
        (self.root / "Gamma").mkdir()
        subprocess.run(["git", "init", str(self.root / "Gamma")], check=True, capture_output=True)
        self.assertFalse(validate(self.root, ledger, scope="group")["ok"])


if __name__ == "__main__":
    unittest.main()
