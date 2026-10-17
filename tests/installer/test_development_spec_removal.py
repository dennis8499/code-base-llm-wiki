from __future__ import annotations

import hashlib
import importlib.util
import json
from pathlib import Path
import subprocess
import sys
import tempfile
import unittest
from unittest import mock
import zipfile

ROOT = Path(__file__).resolve().parents[2]
INSTALLER = ROOT / ".agents/skills/codebase-wiki/scripts/install-framework.py"
FIXTURE = ROOT / "tests/fixtures/development-spec-legacy.zip"


def load_installer():
    spec = importlib.util.spec_from_file_location("retirement_installer", INSTALLER)
    module = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(module)
    return module


def snapshot(root):
    return {path.relative_to(root).as_posix(): path.read_bytes()
            for path in root.rglob("*") if path.is_file()}


class DevelopmentSpecRemovalTests(unittest.TestCase):
    def setUp(self):
        self.temp = tempfile.TemporaryDirectory()
        self.addCleanup(self.temp.cleanup)
        self.target = Path(self.temp.name) / "target"
        self.target.mkdir()
        self.installer = load_installer()

    def legacy(self, surface="copilot"):
        self.installer.apply_install(ROOT, self.target, surface)
        state_path = self.target / self.installer.INSTALL_STATE_PATH
        state = json.loads(state_path.read_text(encoding="utf-8"))
        with zipfile.ZipFile(FIXTURE) as archive:
            for name in archive.namelist():
                if name.startswith(".github/") and surface == "codex":
                    continue
                path = self.target / name
                path.parent.mkdir(parents=True, exist_ok=True)
                data = archive.read(name)
                path.write_bytes(data)
                state["files"][name] = {"kind": "file", "sha256": hashlib.sha256(data).hexdigest()}
        state_path.write_text(json.dumps(state), encoding="utf-8")
        personal = self.target / "wiki/synthesis/personal-development-spec.md"
        personal.parent.mkdir(parents=True, exist_ok=True)
        personal.write_text("# Personal specification\n", encoding="utf-8")
        return state

    def test_both_surfaces_remove_only_owned_retired_files_and_upgrade_is_idempotent(self):
        for surface in ("codex", "copilot"):
            with self.subTest(surface=surface), tempfile.TemporaryDirectory() as directory:
                self.target = Path(directory)
                state = self.legacy(surface)
                before = snapshot(self.target)
                plan = self.installer.plan_install(ROOT, self.target, surface, "upgrade")
                self.assertEqual(before, snapshot(self.target))
                self.assertFalse(plan["conflicts"])
                retired = set(state["files"]) & self.installer.RETIRED_DEVELOPMENT_SPEC_PATHS
                self.assertTrue(retired <= set(plan["changes"]))
                self.installer.apply_install(ROOT, self.target, surface, "upgrade")
                self.assertTrue(all(not (self.target / name).exists() for name in retired))
                self.assertEqual(before["wiki/synthesis/personal-development-spec.md"], (self.target / "wiki/synthesis/personal-development-spec.md").read_bytes())
                self.assertEqual([], self.installer.plan_install(ROOT, self.target, surface, "upgrade")["changes"])

    def test_modified_and_unowned_retired_files_block_without_mutation(self):
        state = self.legacy()
        relative = ".github/prompts/development-spec.prompt.md"
        path = self.target / relative
        for unowned in (False, True):
            with self.subTest(unowned=unowned):
                if unowned:
                    del state["files"][relative]
                    (self.target / self.installer.INSTALL_STATE_PATH).write_text(json.dumps(state), encoding="utf-8")
                else:
                    path.write_text("# Locally modified prompt\n", encoding="utf-8")
                before = snapshot(self.target)
                self.assertIn(relative, self.installer.plan_install(ROOT, self.target, "copilot", "upgrade")["conflicts"])
                with self.assertRaises(FileExistsError):
                    self.installer.apply_install(ROOT, self.target, "copilot", "upgrade")
                self.assertEqual(before, snapshot(self.target))

    def test_failure_after_deletions_restores_all_original_bytes(self):
        self.legacy()
        before = snapshot(self.target)
        real = self.installer._write_transaction

        def fail_commit(path, payload):
            if payload["phase"] == "committed":
                raise OSError("injected commit failure")
            return real(path, payload)

        with mock.patch.object(self.installer, "_write_transaction", fail_commit):
            with self.assertRaises(OSError):
                self.installer.apply_install(ROOT, self.target, "copilot", "upgrade")
        self.assertEqual(before, snapshot(self.target))

    def test_crash_during_retirement_recovers_before_retry(self):
        self.legacy()
        before = snapshot(self.target)
        script = """
import importlib.util, os, sys
from pathlib import Path
spec = importlib.util.spec_from_file_location('crash_installer', sys.argv[1])
module = importlib.util.module_from_spec(spec); spec.loader.exec_module(module)
real = module.os.replace
def replace(source, destination):
    real(source, destination)
    if Path(source).name == 'development_spec.py':
        os._exit(77)
module.os.replace = replace
module.apply_install(Path(sys.argv[2]), Path(sys.argv[3]), 'copilot', 'upgrade')
"""
        result = subprocess.run([sys.executable, "-X", "utf8", "-B", "-c", script,
                                 str(INSTALLER), str(ROOT), str(self.target)], capture_output=True)
        self.assertEqual(77, result.returncode, result.stderr)
        self.installer._recover_pending_transaction(self.target)
        self.assertEqual(before, snapshot(self.target))
        self.installer.apply_install(ROOT, self.target, "copilot", "upgrade")


if __name__ == "__main__":
    unittest.main()
