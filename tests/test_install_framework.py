from __future__ import annotations

import contextlib
import importlib.util
import io
import json
import subprocess
import sys
import tempfile
import unittest
from pathlib import Path


REPO_ROOT = Path(__file__).parents[1]
INSTALLER_PATH = REPO_ROOT / ".agents" / "skills" / "codebase-wiki" / "scripts" / "install-framework.py"


def load_installer():
    spec = importlib.util.spec_from_file_location("install_framework", INSTALLER_PATH)
    if spec is None or spec.loader is None:
        raise RuntimeError(f"Unable to load installer: {INSTALLER_PATH}")
    module = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(module)
    return module


class FrameworkInstallerTests(unittest.TestCase):
    def run_main(self, module, arguments: list[str]) -> tuple[int, dict[str, object]]:
        output = io.StringIO()
        with contextlib.redirect_stdout(output):
            exit_code = module.main(arguments)
        return exit_code, json.loads(output.getvalue())

    def test_install_dry_run_reports_contract_without_mutating_target(self) -> None:
        installer = load_installer()
        with tempfile.TemporaryDirectory() as directory:
            target = Path(directory) / "target"
            target.mkdir()

            exit_code, payload = self.run_main(
                installer,
                ["install", "--target", str(target), "--surface", "codex", "--format", "json"],
            )

            self.assertEqual(exit_code, 0)
            self.assertEqual(payload["contract_version"], 2)
            self.assertEqual(payload["action"], "install")
            self.assertEqual(payload["surface"], "codex")
            self.assertTrue(payload["ok"])
            self.assertFalse(payload["applied"])
            self.assertEqual(payload["obsolete_paths"], [])
            self.assertEqual(list(target.iterdir()), [])

    def test_apply_copies_codex_surface_in_target_mode_without_runtime(self) -> None:
        installer = load_installer()
        with tempfile.TemporaryDirectory() as directory:
            target = Path(directory) / "target"
            target.mkdir()

            exit_code, payload = self.run_main(
                installer,
                [
                    "install",
                    "--target",
                    str(target),
                    "--surface",
                    "codex",
                    "--apply",
                    "--format",
                    "json",
                ],
            )

            self.assertEqual(exit_code, 0)
            self.assertTrue(payload["applied"])
            self.assertTrue((target / "AGENTS.md").exists())
            self.assertTrue((target / "Codex.md").exists())
            self.assertTrue((target / ".agents" / "skills" / "codebase-wiki" / "SKILL.md").exists())
            self.assertTrue((target / ".codex" / "hooks.json").exists())
            self.assertTrue((target / "wiki" / "index.md").exists())
            self.assertFalse((target / ".github").exists())
            self.assertFalse((target / ".codebase-wiki").exists())
            self.assertIn(
                'mode = "target"',
                (target / ".codex" / "config.toml").read_text(encoding="utf-8"),
            )

            rerun_code, rerun_payload = self.run_main(
                installer,
                [
                    "install",
                    "--target",
                    str(target),
                    "--surface",
                    "codex",
                    "--apply",
                    "--format",
                    "json",
                ],
            )
            self.assertEqual(rerun_code, 0)
            self.assertEqual(rerun_payload["conflicts"], [])
            self.assertTrue(rerun_payload["applied"])

    def test_copilot_surface_excludes_codex_files(self) -> None:
        installer = load_installer()
        with tempfile.TemporaryDirectory() as directory:
            target = Path(directory) / "target"
            target.mkdir()

            exit_code, payload = self.run_main(
                installer,
                [
                    "install",
                    "--target",
                    str(target),
                    "--surface",
                    "copilot",
                    "--apply",
                    "--format",
                    "json",
                ],
            )

            self.assertEqual(exit_code, 0)
            self.assertTrue(payload["applied"])
            self.assertTrue((target / ".github" / "copilot-instructions.md").exists())
            self.assertTrue((target / ".agents" / "skills" / "codebase-wiki" / "SKILL.md").exists())
            self.assertFalse((target / ".codex").exists())
            self.assertFalse((target / "Codex.md").exists())

    def test_conflicting_target_file_blocks_apply(self) -> None:
        installer = load_installer()
        with tempfile.TemporaryDirectory() as directory:
            target = Path(directory) / "target"
            target.mkdir()
            (target / "AGENTS.md").write_text("local instructions\n", encoding="utf-8")

            exit_code, payload = self.run_main(
                installer,
                [
                    "install",
                    "--target",
                    str(target),
                    "--surface",
                    "codex",
                    "--apply",
                    "--format",
                    "json",
                ],
            )

            self.assertEqual(exit_code, 2)
            self.assertFalse(payload["ok"])
            self.assertFalse(payload["applied"])
            self.assertIn("AGENTS.md", payload["conflicts"])
            self.assertFalse((target / ".agents").exists())

    def test_upgrade_reports_legacy_runtime_without_deleting_it(self) -> None:
        installer = load_installer()
        with tempfile.TemporaryDirectory() as directory:
            target = Path(directory) / "target"
            legacy = target / ".codebase-wiki" / "custom.txt"
            legacy.parent.mkdir(parents=True)
            legacy.write_text("keep me\n", encoding="utf-8")

            exit_code, payload = self.run_main(
                installer,
                [
                    "upgrade",
                    "--target",
                    str(target),
                    "--surface",
                    "codex",
                    "--apply",
                    "--format",
                    "json",
                ],
            )

            self.assertEqual(exit_code, 0)
            self.assertEqual(payload["obsolete_paths"], [".codebase-wiki/"])
            self.assertTrue(legacy.exists())
            self.assertEqual(legacy.read_text(encoding="utf-8"), "keep me\n")

    def test_installer_excludes_unrelated_local_skills(self) -> None:
        installer = load_installer()
        with tempfile.TemporaryDirectory() as directory:
            root = Path(directory)
            source = root / "source"
            target = root / "target"
            (source / ".agents/skills/codebase-wiki").mkdir(parents=True)
            (source / ".agents/skills/unrelated").mkdir(parents=True)
            (source / ".codex").mkdir()
            target.mkdir()
            (source / "AGENTS.md").write_text("rules\n", encoding="utf-8")
            (source / "Codex.md").write_text("guide\n", encoding="utf-8")
            (source / ".agents/skills/codebase-wiki/SKILL.md").write_text(
                "shared\n", encoding="utf-8"
            )
            (source / ".agents/skills/unrelated/SKILL.md").write_text(
                "private\n", encoding="utf-8"
            )
            (source / ".codex/config.toml").write_text(
                '[wiki_guard]\nmode = "framework"\n', encoding="utf-8"
            )

            plan = installer.plan_install(source, target, "codex")

            self.assertIn(".agents/skills/codebase-wiki/SKILL.md", plan["files"])
            self.assertNotIn(".agents/skills/unrelated/SKILL.md", plan["files"])

    def test_upgrade_preserves_modified_target_wiki(self) -> None:
        installer = load_installer()
        with tempfile.TemporaryDirectory() as directory:
            target = Path(directory) / "target"
            target.mkdir()
            installer.apply_install(REPO_ROOT, target, "codex", "install")
            index_path = target / "wiki/index.md"
            index_path.write_text(
                index_path.read_text(encoding="utf-8") + "\nlocal knowledge\n",
                encoding="utf-8",
            )
            before = index_path.read_bytes()

            plan = installer.plan_install(REPO_ROOT, target, "codex", "upgrade")
            installer.apply_install(REPO_ROOT, target, "codex", "upgrade")

            self.assertFalse(any(path.startswith("wiki/") for path in plan["files"]))
            self.assertEqual(plan["conflicts"], [])
            self.assertEqual(index_path.read_bytes(), before)

    def test_script_resolves_framework_root_outside_repo_working_directory(self) -> None:
        with tempfile.TemporaryDirectory() as directory:
            root = Path(directory)
            target = root / "target"
            target.mkdir()

            result = subprocess.run(
                [
                    sys.executable,
                    str(INSTALLER_PATH),
                    "install",
                    "--target",
                    str(target),
                    "--surface",
                    "codex",
                    "--format",
                    "json",
                ],
                cwd=root,
                capture_output=True,
                text=True,
                check=False,
            )

            self.assertEqual(result.returncode, 0, result.stderr)
            payload = json.loads(result.stdout)
            self.assertIn("AGENTS.md", payload["files"])
            self.assertEqual(list(target.iterdir()), [])


if __name__ == "__main__":
    unittest.main()
