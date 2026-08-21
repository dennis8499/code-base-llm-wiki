from __future__ import annotations

import importlib.util
from pathlib import Path
import sys
import unittest


REPO_ROOT = Path(__file__).parents[1]
HOOKS = REPO_ROOT / ".agents" / "skills" / "codebase-wiki" / "scripts" / "hooks"
CANONICAL_GUARD = HOOKS / "wiki-write-guard.py"
SESSION_HOOK = HOOKS / "wiki-session-init.py"
sys.path.insert(0, str(HOOKS))


def load_guard():
    spec = importlib.util.spec_from_file_location("wiki_write_guard_under_test", CANONICAL_GUARD)
    assert spec and spec.loader
    module = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(module)
    return module


class WriteGuardTests(unittest.TestCase):
    def test_platform_configs_use_canonical_hooks(self) -> None:
        codex = (REPO_ROOT / ".codex/hooks.json").read_text(encoding="utf-8")
        self.assertIn(".agents/skills/codebase-wiki/scripts/hooks/", codex.replace("\\", "/"))
        self.assertIn("--platform codex", codex)
        for path in (REPO_ROOT / ".github/hooks").glob("*.json"):
            text = path.read_text(encoding="utf-8")
            self.assertIn(".agents/skills/codebase-wiki/scripts/hooks/", text)
            self.assertIn("--platform copilot", text)

    def test_session_context_stays_within_budget(self) -> None:
        spec = importlib.util.spec_from_file_location("wiki_session_under_test", SESSION_HOOK)
        assert spec and spec.loader
        module = importlib.util.module_from_spec(spec)
        spec.loader.exec_module(module)
        message = module.build_message(REPO_ROOT)
        self.assertLessEqual(len(message.encode("utf-8")), 4 * 1024)
        self.assertLessEqual(len(message.splitlines()), 30)
        oversized = module.bounded_message(["中" * 5_000])
        self.assertLessEqual(len(oversized.encode("utf-8")), 4 * 1024)

    def test_framework_mode_allows_product_and_schema_paths(self) -> None:
        guard = load_guard()
        allowed = (
            "README.md",
            "docs/setup/README.md",
            "samples/task-tracker/README.md",
            "tests/test_write_guard.py",
            "tools/release.py",
            "VERSION",
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

    def test_wiki_only_alias_and_coexist_mode(self) -> None:
        guard = load_guard()
        self.assertTrue(guard.is_allowed_path("wiki/modules/orders.md", "wiki-only"))
        self.assertFalse(guard.is_allowed_path("src/orders/service.py", "wiki-only"))
        self.assertTrue(guard.is_allowed_path("src/orders/service.py", "coexist"))
        self.assertFalse(guard.is_allowed_path("../outside.py", "coexist"))

    def test_paths_outside_repository_are_denied(self) -> None:
        guard = load_guard()
        self.assertFalse(guard.is_allowed_path("../outside.md", "framework"))


if __name__ == "__main__":
    unittest.main()
