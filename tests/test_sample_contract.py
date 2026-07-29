from __future__ import annotations

import hashlib
import importlib.util
import json
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
                        "0.1.0\n",
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

                    for script in ("validate-frontmatter.py", "check-stale.py"):
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
                                "wiki",
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

                    if surface == "codex":
                        self.assertTrue((target / ".codex/hooks.json").is_file())
                        self.assertFalse((target / ".github").exists())
                        config = (target / ".codex/config.toml").read_text(encoding="utf-8")
                    else:
                        self.assertTrue((target / ".github/copilot-instructions.md").is_file())
                        self.assertFalse((target / ".codex").exists())
                        config = (target / ".github/hooks/config.toml").read_text(
                            encoding="utf-8"
                        )
                    self.assertIn('mode = "target"', config)
                    self.assertNotIn('mode = "framework"', config)

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
