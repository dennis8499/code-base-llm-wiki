from __future__ import annotations

import hashlib
import importlib.util
import json
import os
from pathlib import Path
import shutil
import subprocess
import sys
import tempfile
import unittest


REPO_ROOT = Path(__file__).parents[1]
SAMPLE_ROOT = REPO_ROOT / "samples" / "task-tracker"
INSTALLER_PATH = (
    REPO_ROOT
    / ".agents"
    / "skills"
    / "codebase-wiki"
    / "scripts"
    / "install-framework.py"
)


def load_installer():
    spec = importlib.util.spec_from_file_location("sample_contract_installer", INSTALLER_PATH)
    assert spec and spec.loader
    module = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(module)
    return module


def source_hashes(root: Path) -> dict[str, str]:
    hashes: dict[str, str] = {}
    for relative_root in ("src", "config"):
        for path in sorted((root / relative_root).rglob("*")):
            if path.is_file():
                relative = path.relative_to(root).as_posix()
                hashes[relative] = hashlib.sha256(path.read_bytes()).hexdigest()
    return hashes


class SampleContractTests(unittest.TestCase):
    def test_sample_unit_tests_pass(self) -> None:
        result = subprocess.run(
            [sys.executable, "-m", "unittest", "discover", "-s", "tests", "-v"],
            cwd=SAMPLE_ROOT,
            check=False,
            capture_output=True,
            text=True,
        )
        self.assertEqual(result.returncode, 0, result.stdout + result.stderr)

    def test_both_surfaces_install_without_changing_raw_sample_sources(self) -> None:
        installer = load_installer()
        with tempfile.TemporaryDirectory() as temp_dir:
            temp_root = Path(temp_dir)
            for surface in ("copilot", "codex"):
                with self.subTest(surface=surface):
                    target = temp_root / surface
                    shutil.copytree(SAMPLE_ROOT, target)
                    before = source_hashes(target)

                    plan = installer.plan_install(REPO_ROOT, target, surface)
                    self.assertEqual(plan["conflicts"], [])
                    installer.apply_install(REPO_ROOT, target, surface)

                    self.assertEqual(source_hashes(target), before)
                    self.assertTrue((target / "wiki/index.md").is_file())
                    self.assertTrue((target / "wiki/log.md").is_file())
                    self.assertTrue((target / "wiki/overview.md").is_file())
                    self.assertEqual(
                        (
                            target
                            / ".agents"
                            / "skills"
                            / "codebase-wiki"
                            / "VERSION"
                        ).read_text(encoding="utf-8"),
                        "0.2.0\n",
                    )
                    self.assertIn(
                        "status: placeholder",
                        (target / "wiki/overview.md").read_text(encoding="utf-8"),
                    )
                    log_text = (target / "wiki/log.md").read_text(encoding="utf-8")
                    self.assertIn("Wiki skeleton installed", log_text)
                    self.assertNotIn("Repo 產品化", log_text)
                    self.assertFalse((target / "docs").exists())
                    self.assertFalse((target / "samples").exists())

                    for script, argument in (
                        ("validate-frontmatter.py", "wiki"),
                        ("check-stale.py", "wiki"),
                        ("validate-log.py", "wiki/log.md"),
                    ):
                        result = subprocess.run(
                            [
                                sys.executable,
                                str(
                                    target
                                    / ".agents"
                                    / "skills"
                                    / "codebase-wiki"
                                    / "scripts"
                                    / script
                                ),
                                argument,
                            ],
                            cwd=target,
                            check=False,
                            capture_output=True,
                            text=True,
                            encoding="utf-8",
                            errors="replace",
                        )
                        self.assertEqual(
                            result.returncode,
                            0,
                            f"{surface} {script}:\n{result.stdout}{result.stderr}",
                        )

                    exporter = (
                        target
                        / ".agents"
                        / "skills"
                        / "codebase-wiki"
                        / "scripts"
                        / "export-notebooklm.py"
                    )
                    preflight_result = subprocess.run(
                        [
                            sys.executable,
                            str(exporter),
                            "--root",
                            ".",
                            "--preflight",
                            "--format",
                            "json",
                        ],
                        cwd=target,
                        check=False,
                        capture_output=True,
                        text=True,
                        encoding="utf-8",
                        errors="replace",
                    )
                    self.assertEqual(
                        preflight_result.returncode,
                        0,
                        preflight_result.stdout + preflight_result.stderr,
                    )
                    preflight_payload = json.loads(preflight_result.stdout)
                    self.assertFalse(preflight_payload["ready_to_export"])
                    self.assertFalse((target / ".notebooklm").exists())

                    direct_result = subprocess.run(
                        [
                            sys.executable,
                            str(exporter),
                            "--root",
                            ".",
                            "--output",
                            ".notebooklm",
                            "--format",
                            "json",
                        ],
                        cwd=target,
                        check=False,
                        capture_output=True,
                        text=True,
                        encoding="utf-8",
                        errors="replace",
                    )
                    self.assertEqual(direct_result.returncode, 2)
                    self.assertIn("direct export is disabled", direct_result.stdout)

                    if surface == "codex":
                        self.assertTrue((target / ".codex/hooks.json").is_file())
                        self.assertFalse((target / ".github").exists())
                        config = (target / ".codex/config.toml").read_text(encoding="utf-8")
                        hooks_config = json.loads(
                            (target / ".codex/hooks.json").read_text(encoding="utf-8")
                        )
                    else:
                        self.assertTrue((target / ".github/copilot-instructions.md").is_file())
                        self.assertFalse((target / ".codex").exists())
                        config = (target / ".github/hooks/config.toml").read_text(
                            encoding="utf-8"
                        )
                    self.assertIn('mode = "wiki-only"', config)
                    self.assertNotIn('mode = "framework"', config)

                    if surface == "codex":
                        hook_payloads = {
                            "SessionStart": "{}",
                            "PreToolUse": json.dumps({"tool_name": "read", "tool_input": {}}),
                            "PostToolUse": json.dumps({"tool_name": "read", "tool_input": {}}),
                        }
                        for event_name, payload in hook_payloads.items():
                            handler = hooks_config["hooks"][event_name][0]["hooks"][0]
                            command = handler["command"]
                            command_windows = handler["commandWindows"]
                            self.assertNotIn("$(", command)
                            self.assertNotIn("git rev-parse", command)
                            self.assertNotIn("$(", command_windows)
                            self.assertNotIn("git rev-parse", command_windows)
                            self.assertNotIn('"', command_windows)
                            if os.name == "nt":
                                command = ["cmd.exe", "/d", "/s", "/c", command_windows]
                            else:
                                command = ["/bin/sh", "-lc", handler["command"]]
                            command_result = subprocess.run(
                                command,
                                cwd=target,
                                input=payload,
                                check=False,
                                capture_output=True,
                                text=True,
                                encoding="utf-8",
                                errors="replace",
                            )
                            self.assertEqual(
                                command_result.returncode,
                                0,
                                f"{surface} {event_name}:\n"
                                f"{command_result.stdout}{command_result.stderr}",
                            )

                    platform = "codex" if surface == "codex" else "copilot"
                    hook = (
                        target
                        / ".agents"
                        / "skills"
                        / "codebase-wiki"
                        / "scripts"
                        / "hooks"
                        / "wiki-session-init.py"
                    )
                    hook_result = subprocess.run(
                        [sys.executable, str(hook), "--platform", platform],
                        cwd=target,
                        input="{}",
                        check=False,
                        capture_output=True,
                        text=True,
                        encoding="utf-8",
                        errors="replace",
                    )
                    self.assertEqual(
                        hook_result.returncode,
                        0,
                        hook_result.stdout + hook_result.stderr,
                    )
                    context = json.loads(hook_result.stdout)["additionalContext"]
                    self.assertLessEqual(len(context.encode("utf-8")), 4 * 1024)
                    self.assertLessEqual(len(context.splitlines()), 30)
                    for hook_name in ("wiki-write-guard.py", "wiki-log-reminder.py"):
                        executable_hook = hook.with_name(hook_name)
                        executable_result = subprocess.run(
                            [
                                sys.executable,
                                str(executable_hook),
                                "--platform",
                                platform,
                            ],
                            cwd=target,
                            input=json.dumps({"tool_name": "read", "tool_input": {}}),
                            check=False,
                            capture_output=True,
                            text=True,
                            encoding="utf-8",
                            errors="replace",
                        )
                        self.assertEqual(
                            executable_result.returncode,
                            0,
                            executable_result.stdout + executable_result.stderr,
                        )
                        self.assertEqual(json.loads(executable_result.stdout), {})


if __name__ == "__main__":
    unittest.main()
