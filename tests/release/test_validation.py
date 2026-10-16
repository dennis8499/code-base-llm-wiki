"""Aggregate validation keeps standalone gate results without duplicate work."""
import importlib.util
import json
from pathlib import Path
import subprocess
import sys
import tempfile
import unittest
from unittest import mock

ROOT = Path(__file__).resolve().parents[2]
SCRIPTS = ROOT / ".agents/skills/codebase-wiki/scripts"
sys.path.insert(0, str(SCRIPTS))
spec = importlib.util.spec_from_file_location("release_validation_under_test", ROOT / "tools/validate_release.py")
validation = importlib.util.module_from_spec(spec)
spec.loader.exec_module(validation)


def page(title, kind, body="", sources="[]"):
    return (f"---\ntitle: {title}\ntype: {kind}\nsources: {sources}\nlast_updated: 2026-10-16\n"
            f"tags: [{kind}]\nstatus: active\n---\n\n# {title}\n\n{body}\n")


class ReleaseValidationTests(unittest.TestCase):
    def fixture(self, root):
        wiki = root / "wiki"
        wiki.mkdir()
        (wiki / "index.md").write_text(page("Index", "index", "[[overview]]"), encoding="utf-8")
        (wiki / "overview.md").write_text(page("Overview", "overview"), encoding="utf-8")
        (wiki / "log.md").write_text(page("Log", "log"), encoding="utf-8")
        return wiki

    def assert_standalone_codes(self, wiki, root):
        expected = {}
        commands = {"frontmatter": ["validate-frontmatter.py", str(wiki)],
                    "stale": ["check-stale.py", str(wiki), str(root)],
                    "log": ["validate-log.py", str(wiki / "log.md"), "--repo-root", str(root)],
                    "lint": ["lint-wiki.py", str(wiki), "--repo-root", str(root)]}
        for name, args in commands.items():
            result = subprocess.run([sys.executable, "-B", str(SCRIPTS / args[0]), *args[1:]],
                                    capture_output=True, text=True, encoding="utf-8")
            expected[name] = result.returncode
        actual = validation.wiki_checks(wiki, root)
        self.assertEqual({row["check"]: row["exit_code"] for row in actual}, expected)
        self.assertTrue(all(row["seconds"] >= 0 for row in actual))
        return actual

    def test_aggregate_matches_individual_success_warning_critical_and_missing_input(self):
        with tempfile.TemporaryDirectory() as temporary:
            root = Path(temporary)
            wiki = self.fixture(root)
            healthy = self.assert_standalone_codes(wiki, root)
            self.assertTrue(all(row["exit_code"] == 0 for row in healthy))
            modules = wiki / "modules"
            modules.mkdir()
            (root / "service.py").write_text("behavior\n", encoding="utf-8")
            (modules / "service.md").write_text(page("Service", "module", sources="[service.py, missing.py]"), encoding="utf-8")
            warning = self.assert_standalone_codes(wiki, root)
            self.assertEqual(next(row for row in warning if row["check"] == "stale")["exit_code"], 1)
            (modules / "service.md").write_text(page("Service", "invalid", sources="[missing.py]"), encoding="utf-8")
            critical = self.assert_standalone_codes(wiki, root)
            self.assertEqual(next(row for row in critical if row["check"] == "frontmatter")["exit_code"], 1)
            self.assertEqual(next(row for row in critical if row["check"] == "lint")["exit_code"], 2)
            self.assert_standalone_codes(root / "missing", root)

    def test_components_are_computed_once_and_reused_by_lint(self):
        with tempfile.TemporaryDirectory() as temporary:
            root = Path(temporary)
            wiki = self.fixture(root)
            # The aggregate computes each component once; lint must not call it again.
            original = importlib.util.module_from_spec
            calls = {"frontmatter": 0, "stale": 0, "log": 0}
            def instrument(spec):
                module = original(spec)
                loader = spec.loader
                execute = loader.exec_module
                def load(target):
                    execute(target)
                    attr = {"release_frontmatter": ("frontmatter", "validate_page"),
                            "release_stale": ("stale", "check_stale"),
                            "release_log": ("log", "validate_log")}.get(spec.name)
                    if attr:
                        key, method = attr
                        function = getattr(target, method)
                        def count(*args, **kwargs):
                            calls[key] += 1
                            return function(*args, **kwargs)
                        setattr(target, method, count)
                loader.exec_module = load
                return module
            with mock.patch.object(importlib.util, "module_from_spec", side_effect=instrument):
                report = validation.wiki_checks(wiki, root)
            self.assertTrue(all(row["exit_code"] == 0 for row in report))
            self.assertEqual(calls, {"frontmatter": 3, "stale": 1, "log": 1})

    def test_full_validation_keeps_running_after_a_gate_failure(self):
        result = subprocess.CompletedProcess([], 1, stdout="preserved diagnostic")
        with (mock.patch.object(validation.subprocess, "run", return_value=result) as run,
              mock.patch.object(validation, "wiki_checks", return_value=[])):
            report = validation.validate(ROOT, "v0.6.1")
        self.assertFalse(report["ok"])
        self.assertEqual(run.call_count, 6)
        self.assertTrue(all(row["output"] == "preserved diagnostic" for row in report["checks"]))


if __name__ == "__main__":
    unittest.main()
