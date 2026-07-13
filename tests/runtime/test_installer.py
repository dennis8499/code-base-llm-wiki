from __future__ import annotations

import sys
import tempfile
import unittest
from pathlib import Path


RUNTIME_ROOT = Path(__file__).parents[2] / ".codebase-wiki" / "runtime"
sys.path.insert(0, str(RUNTIME_ROOT))

from codebase_wiki_runtime.installer import apply_install, plan_install  # noqa: E402


class InstallerTests(unittest.TestCase):
    def test_install_plan_reports_new_files_without_mutating_target(self) -> None:
        with tempfile.TemporaryDirectory() as directory:
            source = Path(directory) / "source"
            target = Path(directory) / "target"
            (source / ".agents" / "skills" / "codebase-wiki").mkdir(parents=True)
            (source / ".agents" / "skills" / "codebase-wiki" / "SKILL.md").write_text("skill", encoding="utf-8")
            target.mkdir()

            result = plan_install(source, target, "codex")

            self.assertEqual(result["conflicts"], [])
            self.assertIn(".agents/skills/codebase-wiki/SKILL.md", result["files"])
            self.assertFalse((target / ".agents").exists())

    def test_apply_install_copies_common_runtime_and_skill(self) -> None:
        source = Path(__file__).parents[2]
        with tempfile.TemporaryDirectory() as directory:
            target = Path(directory) / "target"
            target.mkdir()

            result = apply_install(source, target, "codex")

            self.assertFalse(result["conflicts"])
            self.assertTrue((target / ".agents" / "skills" / "codebase-wiki" / "SKILL.md").exists())
            self.assertTrue((target / ".codebase-wiki" / "runtime" / "scripts" / "codebase-wiki.py").exists())

            config = (target / ".codex" / "config.toml").read_text(encoding="utf-8")
            self.assertIn('mode = "target"', config)
            rerun = plan_install(source, target, "codex")
            self.assertEqual(rerun["conflicts"], [])
