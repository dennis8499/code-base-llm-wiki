from __future__ import annotations

import importlib.util
from pathlib import Path
import re
import tempfile
import unittest
from urllib.parse import unquote


REPO_ROOT = Path(__file__).parents[1]
INSTALLER_PATH = (
    REPO_ROOT
    / ".agents"
    / "skills"
    / "codebase-wiki"
    / "scripts"
    / "install-framework.py"
)
LINK_PATTERN = re.compile(r"(?<!!)\[[^\]]+\]\(([^)]+)\)")


def load_installer():
    spec = importlib.util.spec_from_file_location("repository_format_installer", INSTALLER_PATH)
    assert spec and spec.loader
    module = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(module)
    return module


class RepositoryFormatTests(unittest.TestCase):
    def test_product_documentation_and_history_are_separated(self) -> None:
        required = (
            "docs/architecture/README.md",
            "docs/setup/README.md",
            "docs/workflows/README.md",
            "docs/validation/README.md",
            "docs/history/llm-wiki.md",
            "docs/history/original-prompt.txt",
            "samples/README.md",
            "samples/task-tracker/README.md",
        )
        for relative in required:
            with self.subTest(relative=relative):
                self.assertTrue((REPO_ROOT / relative).is_file())

        self.assertFalse((REPO_ROOT / "llm-wiki.md").exists())
        self.assertFalse((REPO_ROOT / "prompt.txt").exists())
        self.assertGreater((REPO_ROOT / "docs/history/llm-wiki.md").stat().st_size, 10_000)

    def test_local_markdown_links_resolve(self) -> None:
        documents = [
            REPO_ROOT / "README.md",
            REPO_ROOT / "Codex.md",
            *(REPO_ROOT / "docs").rglob("*.md"),
            *(REPO_ROOT / "samples").rglob("*.md"),
        ]
        failures: list[str] = []
        for document in documents:
            text = document.read_text(encoding="utf-8")
            for raw_target in LINK_PATTERN.findall(text):
                target = raw_target.strip().strip("<>")
                if not target or target.startswith("#") or "://" in target or target.startswith("mailto:"):
                    continue
                path_text = unquote(target.split("#", 1)[0])
                if not path_text:
                    continue
                resolved = (document.parent / path_text).resolve()
                if not resolved.exists():
                    failures.append(
                        f"{document.relative_to(REPO_ROOT).as_posix()} -> {target}"
                    )
        self.assertEqual(failures, [])

    def test_framework_only_docs_and_samples_are_not_installed(self) -> None:
        installer = load_installer()
        with tempfile.TemporaryDirectory() as temp_dir:
            target = Path(temp_dir)
            for surface in ("copilot", "codex"):
                with self.subTest(surface=surface):
                    plan = installer.plan_install(REPO_ROOT, target, surface)
                    self.assertFalse(
                        any(
                            path.startswith(("docs/", "samples/", "tests/"))
                            for path in plan["files"]
                        )
                    )
                    self.assertIn("wiki/index.md", plan["files"])
                    self.assertIn("wiki/log.md", plan["files"])
                    self.assertIn("wiki/overview.md", plan["files"])


if __name__ == "__main__":
    unittest.main()

