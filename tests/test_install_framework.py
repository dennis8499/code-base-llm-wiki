from __future__ import annotations

import contextlib
import datetime as dt
import importlib.util
import io
import json
import os
import subprocess
import sys
import tempfile
import unittest
from pathlib import Path
from unittest import mock


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
            self.assertEqual(payload["contract_version"], 3)
            self.assertEqual(payload["framework_version"], "0.2.0")
            self.assertEqual(payload["action"], "install")
            self.assertEqual(payload["surface"], "codex")
            self.assertEqual(payload["guard_mode"], "wiki-only")
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
            self.assertTrue(
                (
                    target
                    / ".agents"
                    / "skills"
                    / "codebase-wiki"
                    / "scripts"
                    / "export-notebooklm.py"
                ).exists()
            )
            self.assertTrue(
                (
                    target
                    / ".agents"
                    / "skills"
                    / "codebase-wiki"
                    / "scripts"
                    / "notebooklm_exporter.py"
                ).exists()
            )
            for template in (
                "business-process-template.md",
                "business-requirement-template.md",
                "business-rule-template.md",
                "functional-requirement-catalog-template.md",
                "business-process-catalog-template.md",
                "business-rule-catalog-template.md",
                "business-glossary-template.md",
                "business-knowledge-gaps-template.md",
                "codebase-functional-coverage-template.md",
            ):
                self.assertTrue(
                    (
                        target
                        / ".agents"
                        / "skills"
                        / "codebase-wiki"
                        / "assets"
                        / template
                    ).exists()
                )
            self.assertTrue(
                (
                    target
                    / ".agents"
                    / "skills"
                    / "codebase-wiki"
                    / "references"
                    / "notebooklm-export-workflow.md"
                ).exists()
            )
            self.assertEqual(
                (target / ".agents" / "skills" / "codebase-wiki" / "VERSION").read_text(
                    encoding="utf-8"
                ),
                "0.2.0\n",
            )
            self.assertTrue((target / ".codex" / "hooks.json").exists())
            self.assertTrue(
                (target / ".agents/skills/codebase-wiki/install-state.json").exists()
            )
            self.assertTrue((target / "wiki" / "index.md").exists())
            self.assertTrue((target / "wiki" / "processes").is_dir())
            self.assertTrue((target / "wiki" / "rules").is_dir())
            self.assertFalse((target / ".github").exists())
            self.assertFalse((target / ".codebase-wiki").exists())
            self.assertIn(
                'mode = "wiki-only"',
                (target / ".codex" / "config.toml").read_text(encoding="utf-8"),
            )

            repeat_plan = installer.plan_install(REPO_ROOT, target, "codex", "install")
            self.assertEqual(repeat_plan["changes"], [])
            self.assertEqual(repeat_plan["conflicts"], [])

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
            self.assertFalse((target / ".github" / "workflows" / "release.yml").exists())

    def test_conflicting_target_file_blocks_apply(self) -> None:
        installer = load_installer()
        with tempfile.TemporaryDirectory() as directory:
            target = Path(directory) / "target"
            target.mkdir()
            (target / "Codex.md").write_text("local guide\n", encoding="utf-8")

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
            self.assertIn("Codex.md", payload["conflicts"])
            self.assertFalse((target / ".agents").exists())

    def test_target_symlink_escape_blocks_apply_without_writing_outside(self) -> None:
        installer = load_installer()
        with tempfile.TemporaryDirectory() as directory:
            root = Path(directory)
            target = root / "target"
            outside = root / "outside"
            target.mkdir()
            outside.mkdir()
            protected = outside / "config.toml"
            protected.write_text("keep me\n", encoding="utf-8")
            link = target / ".codex"
            try:
                os.symlink(outside, link, target_is_directory=True)
            except (OSError, NotImplementedError) as exc:
                self.skipTest(f"symlink creation unavailable: {exc}")

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
            self.assertFalse(payload["applied"])
            self.assertTrue(any(path.startswith(".codex/") for path in payload["conflicts"]))
            self.assertEqual(protected.read_text(encoding="utf-8"), "keep me\n")

    def test_target_root_reparse_point_is_rejected_before_apply(self) -> None:
        installer = load_installer()
        with tempfile.TemporaryDirectory() as directory:
            root = Path(directory)
            target = root / "target"
            target.mkdir()

            def fake_reparse_point(path: Path) -> bool:
                return path == target

            with mock.patch.object(
                installer, "_is_reparse_point", side_effect=fake_reparse_point
            ):
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
            self.assertFalse(payload["applied"])
            self.assertTrue(payload["conflicts"])
            self.assertEqual(list(target.iterdir()), [])

    def test_framework_source_symlink_is_rejected(self) -> None:
        installer = load_installer()
        with tempfile.TemporaryDirectory() as directory:
            root = Path(directory)
            source = root / "source"
            target = root / "target"
            outside = root / "outside.md"
            (source / ".agents/skills/codebase-wiki").mkdir(parents=True)
            target.mkdir()
            outside.write_text("outside\n", encoding="utf-8")
            try:
                os.symlink(outside, source / ".agents/skills/codebase-wiki/SKILL.md")
            except (OSError, NotImplementedError) as exc:
                self.skipTest(f"symlink creation unavailable: {exc}")

            with self.assertRaisesRegex(OSError, "must not contain symlink"):
                installer.plan_install(source, target, "codex")

    def test_target_path_rejects_windows_drive_paths(self) -> None:
        installer = load_installer()
        with tempfile.TemporaryDirectory() as directory:
            target = Path(directory) / "target"
            target.mkdir()

            self.assertFalse(installer._target_path_is_safe(target, "C:/outside.txt"))
            self.assertFalse(installer._target_path_is_safe(target, r"C:\outside.txt"))
            self.assertFalse(installer._target_path_is_safe(target, r"..\outside.txt"))

    def test_target_directory_junction_is_rejected(self) -> None:
        installer = load_installer()
        with tempfile.TemporaryDirectory() as directory:
            root = Path(directory)
            target = root / "target"
            outside = root / "outside"
            target.mkdir()
            outside.mkdir()
            link = target / "linked"
            try:
                result = subprocess.run(
                    ["cmd", "/c", "mklink", "/J", str(link), str(outside)],
                    check=False,
                    capture_output=True,
                    text=True,
                    encoding="utf-8",
                    errors="replace",
                )
                if result.returncode != 0:
                    raise OSError(result.stderr or result.stdout or "unable to create directory junction")
            except (OSError, FileNotFoundError) as exc:
                self.skipTest(f"directory junction unavailable: {exc}")

            self.assertFalse(installer._target_path_is_safe(target, "linked/file.txt"))

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
            policy_path = target / "wiki/policy.md"
            policy_path.write_text("# Local policy\n", encoding="utf-8")
            policy_before = policy_path.read_bytes()

            plan = installer.plan_install(REPO_ROOT, target, "codex", "upgrade")
            installer.apply_install(REPO_ROOT, target, "codex", "upgrade")

            self.assertFalse(any(path.startswith("wiki/") for path in plan["files"]))
            self.assertFalse(any(path.startswith("wiki/") for path in plan["obsolete_paths"]))
            self.assertEqual(plan["conflicts"], [])
            self.assertEqual(index_path.read_bytes(), before)
            self.assertEqual(policy_path.read_bytes(), policy_before)

    def test_atomic_install_rolls_back_after_mid_commit_failure(self) -> None:
        installer = load_installer()
        with tempfile.TemporaryDirectory() as directory:
            target = Path(directory) / "target"
            target.mkdir()
            local = target / "AGENTS.md"
            local.write_text("# Local rules\n", encoding="utf-8")
            before = local.read_bytes()
            original_replace = installer.os.replace
            staged_moves = 0

            def fail_second_staged_move(source, destination):
                nonlocal staged_moves
                if "codebase-wiki-stage-" in str(source):
                    staged_moves += 1
                    if staged_moves == 2:
                        raise OSError("injected commit failure")
                return original_replace(source, destination)

            with mock.patch.object(
                installer.os, "replace", side_effect=fail_second_staged_move
            ):
                with self.assertRaisesRegex(OSError, "injected commit failure"):
                    installer.apply_install(REPO_ROOT, target, "codex", "install")

            self.assertEqual(local.read_bytes(), before)
            self.assertEqual(
                sorted(path.relative_to(target).as_posix() for path in target.rglob("*") if path.is_file()),
                ["AGENTS.md"],
            )

    def test_atomic_install_recovers_after_process_kill(self) -> None:
        installer = load_installer()
        with tempfile.TemporaryDirectory() as directory:
            target = Path(directory) / "target"
            target.mkdir()
            original = target / "a.txt"
            original.write_text("old\n", encoding="utf-8")
            installer_path = repr(str(INSTALLER_PATH))
            target_path = repr(str(target))
            child = f"""
import importlib.util
import os
from pathlib import Path

spec = importlib.util.spec_from_file_location("install_framework_child", {installer_path})
assert spec and spec.loader
module = importlib.util.module_from_spec(spec)
spec.loader.exec_module(module)
target = Path({target_path})
original_replace = module.os.replace

def crash_after_first_new_file(source, destination):
    result = original_replace(source, destination)
    if "codebase-wiki-stage-" in str(source) and Path(destination) == target / "a.txt":
        os._exit(91)
    return result

module.os.replace = crash_after_first_new_file
module._atomic_write(target, {{"a.txt": b"new\\n", "b.txt": b"second\\n"}})
"""
            result = subprocess.run(
                [sys.executable, "-c", child],
                check=False,
                capture_output=True,
                text=True,
                encoding="utf-8",
            )
            self.assertEqual(result.returncode, 91, result.stderr)
            self.assertTrue(installer._transaction_path(target).is_file())

            self.assertTrue(installer._recover_pending_transaction(target))
            self.assertEqual(original.read_text(encoding="utf-8"), "old\n")
            self.assertFalse((target / "b.txt").exists())
            self.assertFalse(installer._transaction_path(target).exists())
            self.assertEqual(list(target.parent.glob("codebase-wiki-stage-*")), [])
            self.assertEqual(list(target.parent.glob("codebase-wiki-backup-*")), [])

    def test_atomic_install_rejects_concurrent_writer(self) -> None:
        installer = load_installer()
        with tempfile.TemporaryDirectory() as directory:
            target = Path(directory) / "target"
            target.mkdir()
            installer_path = repr(str(INSTALLER_PATH))
            lock_path = repr(str(installer._transaction_lock_path(target)))
            child = f"""
import importlib.util
from pathlib import Path
import sys

spec = importlib.util.spec_from_file_location("install_framework_lock_child", {installer_path})
assert spec and spec.loader
module = importlib.util.module_from_spec(spec)
spec.loader.exec_module(module)
with module._TransactionLock(Path({lock_path})):
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
                self.assertFalse(payload["applied"])
                self.assertIn("transaction lock", payload["error"])
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

    def test_invalid_utf8_transaction_journal_fails_closed(self) -> None:
        installer = load_installer()
        with tempfile.TemporaryDirectory() as directory:
            target = Path(directory) / "target"
            target.mkdir()
            installer._transaction_path(target).write_bytes(b"\xff\xfe invalid utf-8")

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
            self.assertIn("unable to read installer transaction journal", payload["error"])

    def test_existing_agent_instructions_are_preserved_around_managed_block(self) -> None:
        installer = load_installer()
        with tempfile.TemporaryDirectory() as directory:
            target = Path(directory) / "target"
            target.mkdir()
            (target / "AGENTS.md").write_text(
                "# Local rules\n\nKeep this section.\n", encoding="utf-8"
            )

            plan = installer.apply_install(REPO_ROOT, target, "codex", "install")

            text = (target / "AGENTS.md").read_text(encoding="utf-8")
            self.assertIn("Keep this section.", text)
            self.assertIn(installer.MANAGED_BEGIN, text)
            self.assertIn(installer.MANAGED_END, text)
            self.assertNotIn("AGENTS.md", plan["conflicts"])

    def test_guard_mode_and_starter_date_are_explicit_and_reproducible(self) -> None:
        installer = load_installer()
        with tempfile.TemporaryDirectory() as directory:
            target = Path(directory) / "target"
            target.mkdir()
            installer.apply_install(
                REPO_ROOT,
                target,
                "codex",
                "install",
                guard_mode="coexist",
                install_date=dt.date(2030, 1, 2),
            )

            config = (target / ".codex/config.toml").read_text(encoding="utf-8")
            self.assertIn('mode = "coexist"', config)
            for relative in ("wiki/index.md", "wiki/log.md", "wiki/overview.md"):
                self.assertIn(
                    "last_updated: 2030-01-02",
                    (target / relative).read_text(encoding="utf-8"),
                )
            self.assertIn(
                "## [2030-01-02] init",
                (target / "wiki/log.md").read_text(encoding="utf-8"),
            )

    def test_manifest_distinguishes_user_only_and_two_sided_changes(self) -> None:
        installer = load_installer()
        with tempfile.TemporaryDirectory() as directory:
            root = Path(directory)
            source = root / "source"
            target = root / "target"
            (source / ".agents/skills/codebase-wiki/assets/wiki-starter").mkdir(
                parents=True
            )
            (source / ".codex").mkdir(parents=True)
            target.mkdir()
            (source / "AGENTS.md").write_text("wiki rules\n", encoding="utf-8")
            (source / "Codex.md").write_text("guide v1\n", encoding="utf-8")
            (source / "VERSION").write_text("0.1.0\n", encoding="utf-8")
            (source / ".agents/skills/codebase-wiki/SKILL.md").write_text(
                "skill v1\n", encoding="utf-8"
            )
            (source / ".codex/config.toml").write_text(
                '[wiki_guard]\nmode = "framework"\n', encoding="utf-8"
            )
            installer.apply_install(source, target, "codex", "install")

            codex = target / "Codex.md"
            codex.write_text("local guide\n", encoding="utf-8")
            user_only = installer.plan_install(source, target, "codex", "upgrade")
            self.assertIn("Codex.md", user_only["preserved"])
            self.assertNotIn("Codex.md", user_only["conflicts"])

            (source / "Codex.md").write_text("guide v2\n", encoding="utf-8")
            two_sided = installer.plan_install(source, target, "codex", "upgrade")
            self.assertIn("Codex.md", two_sided["conflicts"])

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
