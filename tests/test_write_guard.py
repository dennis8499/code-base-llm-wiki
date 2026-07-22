from __future__ import annotations

import importlib.util
from pathlib import Path
import unittest


REPO_ROOT = Path(__file__).parents[1]
CODEX_GUARD = REPO_ROOT / ".codex" / "hooks" / "scripts" / "wiki-write-guard.py"
COPILOT_GUARD = REPO_ROOT / ".github" / "hooks" / "scripts" / "wiki-write-guard.py"


def load_guard():
    spec = importlib.util.spec_from_file_location("wiki_write_guard_under_test", CODEX_GUARD)
    assert spec and spec.loader
    module = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(module)
    return module


class WriteGuardTests(unittest.TestCase):
    def test_copilot_and_codex_guard_scripts_are_mirrored(self) -> None:
        self.assertEqual(CODEX_GUARD.read_bytes(), COPILOT_GUARD.read_bytes())

    def test_framework_mode_allows_product_and_schema_paths(self) -> None:
        guard = load_guard()
        allowed = (
            "README.md",
            "docs/setup/README.md",
            "samples/task-tracker/README.md",
            "tests/test_write_guard.py",
            "wiki/index.md",
            ".agents/skills/codebase-wiki/SKILL.md",
            ".codex/config.toml",
            ".github/copilot-instructions.md",
        )
        for path in allowed:
            with self.subTest(path=path):
                self.assertTrue(guard.is_allowed_path(path, "framework"))

    def test_target_mode_only_allows_wiki(self) -> None:
        guard = load_guard()
        self.assertTrue(guard.is_allowed_path("wiki/modules/orders.md", "target"))
        for path in (
            "README.md",
            "docs/setup/README.md",
            "samples/task-tracker/README.md",
            "tests/test_write_guard.py",
            ".github/copilot-instructions.md",
            "src/orders/service.py",
        ):
            with self.subTest(path=path):
                self.assertFalse(guard.is_allowed_path(path, "target"))

    def test_paths_outside_repository_are_denied(self) -> None:
        guard = load_guard()
        self.assertFalse(guard.is_allowed_path("../outside.md", "framework"))


if __name__ == "__main__":
    unittest.main()

