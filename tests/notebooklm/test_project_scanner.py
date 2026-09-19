from __future__ import annotations

import contextlib
import io
import json
from pathlib import Path
import os
import sys
from types import SimpleNamespace
import tempfile
import unittest
from unittest import mock

from .test_export_notebooklm import load_canonical_exporter


class ProjectScannerTests(unittest.TestCase):
    def settings(self, profile: str = "target") -> SimpleNamespace:
        return SimpleNamespace(
            scan_profile=profile,
            output_directory=".notebooklm",
            analysis_include_tests=True,
            business_source_paths=(),
            exclude_paths=(),
        )

    def test_full_root_inventory_includes_project_owned_automation_and_nested_sources(self) -> None:
        module = load_canonical_exporter()
        with tempfile.TemporaryDirectory() as directory:
            root = Path(directory)
            (root / "src").mkdir()
            (root / "src/api.py").write_text("@app.get('/items')\ndef list_items():\n    return []\n", encoding="utf-8")
            (root / ".github/workflows").mkdir(parents=True)
            (root / ".github/workflows/ci.yml").write_text("name: ci\n", encoding="utf-8")
            (root / "infra").mkdir()
            (root / "infra/main.tf").write_text("resource \"x\" \"y\" {}\n", encoding="utf-8")
            (root / "tools").mkdir()
            (root / "tools/check.py").write_text("print('check')\n", encoding="utf-8")
            (root / "bin").mkdir()
            (root / "bin/run.sh").write_text("#!/bin/sh\n", encoding="utf-8")
            (root / "nested/.git").mkdir(parents=True)
            (root / "nested/.git/config").write_text("metadata\n", encoding="utf-8")
            (root / "nested/src").mkdir(parents=True)
            (root / "nested/src/job.py").write_text("def job():\n    return True\n", encoding="utf-8")
            (root / "ignored.py").write_text("VALUE = 1\n", encoding="utf-8")
            (root / ".gitignore").write_text("ignored.py\n", encoding="utf-8")
            (root / ".env").write_text("TOKEN=secret\n", encoding="utf-8")
            (root / "node_modules/pkg").mkdir(parents=True)
            (root / "node_modules/pkg/index.js").write_text("module.exports = {};\n", encoding="utf-8")

            scan = module.shared_scan_project(root, self.settings())
            included = {item["path"]: item["category"] for item in scan["included"]}
            excluded = {item["path"]: item["reason"] for item in scan["excluded"]}

            self.assertIn("src/api.py", included)
            self.assertEqual(included[".github/workflows/ci.yml"], "ci_cd")
            self.assertEqual(included["infra/main.tf"], "iac")
            self.assertEqual(included["tools/check.py"], "engineering_tooling")
            self.assertEqual(included["bin/run.sh"], "engineering_tooling")
            self.assertIn("nested/src/job.py", included)
            self.assertIn("ignored.py", included)
            self.assertEqual(excluded[".env"], "sensitive_filename")
            self.assertTrue(any(item["path"] == "nested/.git" for item in scan["excluded_roots"]))
            self.assertTrue(any(item["path"] == "node_modules" for item in scan["excluded_roots"]))
            self.assertTrue(scan["entrypoint_candidates"])
            self.assertRegex(scan["snapshot_id"], r"^sha256:[0-9a-f]{64}$")

    def test_target_profile_only_excludes_framework_adapter_subtrees(self) -> None:
        module = load_canonical_exporter()
        with tempfile.TemporaryDirectory() as directory:
            root = Path(directory)
            (root / ".agents/skills/codebase-wiki").mkdir(parents=True)
            (root / ".agents/skills/codebase-wiki/SKILL.md").write_text("framework\n", encoding="utf-8")
            (root / ".github/prompts").mkdir(parents=True)
            (root / ".github/prompts/a.prompt.md").write_text("framework adapter\n", encoding="utf-8")
            (root / ".github/instructions").mkdir(parents=True)
            (root / ".github/instructions/wiki-pages.instructions.md").write_text(
                "framework adapter\n", encoding="utf-8"
            )
            (root / ".github/copilot-instructions.md").write_text(
                "framework adapter\n", encoding="utf-8"
            )
            (root / ".github/workflows").mkdir(parents=True)
            (root / ".github/workflows/ci.yml").write_text("name: ci\n", encoding="utf-8")

            target = module.shared_scan_project(root, self.settings("target"))
            target_paths = {item["path"] for item in target["included"]}
            target_roots = {item["path"]: item["reason"] for item in target["excluded_roots"]}
            self.assertNotIn(".agents/skills/codebase-wiki/SKILL.md", target_paths)
            self.assertNotIn(".github/prompts/a.prompt.md", target_paths)
            self.assertNotIn(".github/instructions/wiki-pages.instructions.md", target_paths)
            self.assertNotIn(".github/copilot-instructions.md", target_paths)
            self.assertIn(".github/workflows/ci.yml", target_paths)
            self.assertEqual(target_roots[".agents/skills/codebase-wiki"], "framework_adapter")
            self.assertEqual(target_roots[".github/prompts"], "framework_adapter")
            self.assertEqual(target_roots[".github/instructions"], "framework_adapter")
            self.assertEqual(
                {item["path"]: item["reason"] for item in target["excluded"]}[".github/copilot-instructions.md"],
                "framework_adapter",
            )

            framework = module.shared_scan_project(root, self.settings("framework"))
            framework_paths = {item["path"] for item in framework["included"]}
            self.assertIn(".agents/skills/codebase-wiki/SKILL.md", framework_paths)
            self.assertIn(".github/prompts/a.prompt.md", framework_paths)
            self.assertIn(".github/instructions/wiki-pages.instructions.md", framework_paths)
            self.assertIn(".github/copilot-instructions.md", framework_paths)

    def test_exporter_evidence_expansion_reuses_framework_boundary(self) -> None:
        module = load_canonical_exporter()
        with tempfile.TemporaryDirectory() as directory:
            root = Path(directory)
            instructions = root / ".github/instructions/wiki-pages.instructions.md"
            instructions.parent.mkdir(parents=True)
            instructions.write_text("framework adapter\n", encoding="utf-8")

            target_settings = module.load_settings(root)
            skipped: list[dict[str, str]] = []
            self.assertEqual(
                module.expand_path(".github/instructions", root, target_settings, skipped),
                [],
            )
            self.assertIn(
                {"path": ".github/instructions", "reason": "framework_adapter"},
                skipped,
            )

            (root / "notebooklm.toml").write_text(
                "[notebooklm]\nscan_profile = \"framework\"\n",
                encoding="utf-8",
            )
            framework_settings = module.load_settings(root)
            self.assertEqual(
                [item.path for item in module.expand_path(
                    ".github/instructions", root, framework_settings, []
                )],
                [".github/instructions/wiki-pages.instructions.md"],
            )

    def test_exporter_and_standalone_scanner_share_the_same_scope(self) -> None:
        module = load_canonical_exporter()
        scanner = sys.modules["project_scanner"]
        with tempfile.TemporaryDirectory() as directory:
            root = Path(directory)
            (root / "src").mkdir()
            (root / "src/service.py").write_text(
                "def service():\n    return 1\n", encoding="utf-8"
            )
            (root / "tests").mkdir()
            (root / "tests/test_service.py").write_text(
                "def test_service():\n    assert True\n", encoding="utf-8"
            )
            (root / "business").mkdir()
            (root / "business/brief.md").write_text("business\n", encoding="utf-8")
            (root / "private").mkdir()
            (root / "private/notes.md").write_text("private\n", encoding="utf-8")
            (root / ".github/instructions").mkdir(parents=True)
            (root / ".github/instructions/guide.md").write_text(
                "framework adapter\n", encoding="utf-8"
            )
            (root / "notebooklm.toml").write_text(
                "[notebooklm]\n"
                "scan_profile = \"target\"\n"
                "output_directory = \".export\"\n"
                "analysis_include_tests = false\n"
                "business_source_paths = [\"business\"]\n"
                "exclude_paths = [\"private\"]\n"
                "extra_paths = []\n",
                encoding="utf-8",
            )

            exporter_settings = module.load_settings(root)
            standalone_settings = scanner.cli_settings(root, "target")
            exporter_scan = module.shared_scan_project(root, exporter_settings, ())
            standalone_scan = scanner.scan_project(root, standalone_settings, ())

            def scope(scan: dict[str, object]) -> dict[str, object]:
                return {
                    "included": [
                        (item["path"], item["category"])
                        for item in scan["included"]  # type: ignore[index]
                    ],
                    "excluded": [
                        (item["path"], item["reason"])
                        for item in scan["excluded"]  # type: ignore[index]
                    ],
                    "excluded_roots": [
                        (item["path"], item["reason"])
                        for item in scan["excluded_roots"]  # type: ignore[index]
                    ],
                    "skipped": scan["skipped"],
                    "snapshot_id": scan["snapshot_id"],
                }

            self.assertEqual(scope(exporter_scan), scope(standalone_scan))

    def test_business_source_override_does_not_duplicate_test_exclusion(self) -> None:
        module = load_canonical_exporter()
        with tempfile.TemporaryDirectory() as directory:
            root = Path(directory)
            source = root / "docs/note_test.md"
            source.parent.mkdir(parents=True)
            source.write_text("business evidence\n", encoding="utf-8")
            settings = self.settings()
            settings.analysis_include_tests = False
            settings.business_source_paths = ("docs/note_test.md",)

            scan = module.shared_scan_project(root, settings, ())

            included = {
                item["path"]: item["category"] for item in scan["included"]
            }
            self.assertEqual(included["docs/note_test.md"], "business_documentation")
            self.assertNotIn(
                "docs/note_test.md", {item["path"] for item in scan["excluded"]}
            )

    def test_v2_coverage_requires_exact_file_rows(self) -> None:
        module = load_canonical_exporter()
        with tempfile.TemporaryDirectory() as directory:
            root = Path(directory)
            (root / "src").mkdir()
            (root / "src/a.py").write_text("def a():\n    return 1\n", encoding="utf-8")
            ledger = SimpleNamespace(
                path="wiki/synthesis/codebase-functional-coverage.md",
                text=(
                    "coverage_schema_version: 2\n"
                    "| Path or prefix | Disposition | Functional requirements |\n"
                    "| --- | --- | --- |\n"
                    "| `src/` | functional-evidence | [[req-a]] |\n"
                ),
            )
            scan = module.shared_scan_project(root, self.settings(), [ledger])
            self.assertIn("src/a.py", scan["uncovered_paths"])
            self.assertTrue(scan["coverage_ledger_issues"])

    def test_links_are_reported_as_boundaries_without_following_targets(self) -> None:
        module = load_canonical_exporter()
        with tempfile.TemporaryDirectory() as directory:
            root = Path(directory)
            outside = root.parent / (root.name + "-outside.py")
            outside.write_text("SECRET = 'outside'\n", encoding="utf-8")
            link = root / "linked.py"
            try:
                os.symlink(outside, link)
            except (OSError, NotImplementedError):
                self.skipTest("symlinks are unavailable in this environment")
            scan = module.shared_scan_project(root, self.settings())
            self.assertNotIn("linked.py", {item["path"] for item in scan["included"]})
            self.assertIn("linked.py", {item["path"] for item in scan["excluded"]})
            self.assertIn(
                {"path": "linked.py", "reason": "link_boundary"},
                scan["skipped"],
            )

    def test_reparse_regular_file_is_reported_without_reading_target(self) -> None:
        module = load_canonical_exporter()
        scanner = sys.modules["project_scanner"]
        with tempfile.TemporaryDirectory() as directory:
            root = Path(directory)
            linked = (root / "linked.py").absolute()
            linked.write_text("SECRET = 'outside'\n", encoding="utf-8")

            def is_reparse(path: Path) -> bool:
                return Path(path).absolute() == linked

            with mock.patch.object(scanner, "_is_reparse_point", side_effect=is_reparse):
                scan = module.shared_scan_project(root, self.settings())

            self.assertNotIn("linked.py", {item["path"] for item in scan["included"]})
            self.assertIn(
                {"path": "linked.py", "reason": "link_boundary"},
                scan["excluded"],
            )
            self.assertIn(
                {"path": "linked.py", "reason": "link_boundary"},
                scan["skipped"],
            )

    def test_standalone_cli_rejects_linked_config_before_reading(self) -> None:
        load_canonical_exporter()
        scanner = sys.modules["project_scanner"]
        with tempfile.TemporaryDirectory() as directory:
            root = Path(directory)
            (root / "src").mkdir()
            (root / "src/service.py").write_text("def service():\n    return 1\n", encoding="utf-8")
            config = (root / "notebooklm.toml").absolute()
            config.write_text('exclude_paths = ["src"]\n', encoding="utf-8")

            def is_reparse(path: Path) -> bool:
                return Path(path).absolute() == config

            stdout = io.StringIO()
            with mock.patch.object(scanner, "_is_reparse_point", side_effect=is_reparse):
                with contextlib.redirect_stdout(stdout):
                    code = scanner.main(["--root", str(root), "--format", "json"])

            payload = json.loads(stdout.getvalue())
            self.assertEqual(code, 2)
            self.assertFalse(payload["ok"])
            self.assertIn("config file must not be a symlink or reparse point", payload["error"])

    def test_standalone_cli_uses_defaults_when_config_is_missing(self) -> None:
        load_canonical_exporter()
        scanner = sys.modules["project_scanner"]
        with tempfile.TemporaryDirectory() as directory:
            root = Path(directory)
            (root / "src").mkdir()
            (root / "src/service.py").write_text("def service():\n    return 1\n", encoding="utf-8")

            settings = scanner.cli_settings(root, "target")

            self.assertEqual(settings.exclude_paths, ())
            self.assertEqual(settings.business_source_paths, ())

    def test_standalone_cli_fails_closed_for_invalid_scan_configuration(self) -> None:
        load_canonical_exporter()
        scanner = sys.modules["project_scanner"]
        invalid_configs = (
            "[notebooklm\n",
            "[notebooklm]\nanalysis_include_tests = \"false\"\n",
            "[notebooklm]\nexclude_paths = [\"../outside\"]\n",
        )
        for config_text in invalid_configs:
            with self.subTest(config_text=config_text):
                with tempfile.TemporaryDirectory() as directory:
                    root = Path(directory)
                    (root / "src").mkdir()
                    (root / "src/service.py").write_text(
                        "def service():\n    return 1\n", encoding="utf-8"
                    )
                    (root / "notebooklm.toml").write_text(
                        config_text, encoding="utf-8"
                    )
                    stdout = io.StringIO()
                    with contextlib.redirect_stdout(stdout):
                        code = scanner.main(
                            ["--root", str(root), "--format", "json"]
                        )
                    payload = json.loads(stdout.getvalue())
                    self.assertEqual(code, 2)
                    self.assertFalse(payload["ok"])
                    self.assertIn("error", payload)

    def test_business_source_path_cannot_escape_explicit_root(self) -> None:
        module = load_canonical_exporter()
        with tempfile.TemporaryDirectory() as directory:
            root = Path(directory) / "project"
            root.mkdir()
            outside = root.parent / "outside.py"
            outside.write_text("OUTSIDE = True\n", encoding="utf-8")
            settings = self.settings()
            settings.business_source_paths = ("../outside.py",)

            scan = module.shared_scan_project(root, settings)

            self.assertNotIn("../outside.py", {item["path"] for item in scan["included"]})
            self.assertIn(
                {"path": "../outside.py", "reason": "path_escape"},
                scan["skipped"],
            )


if __name__ == "__main__":
    unittest.main()
