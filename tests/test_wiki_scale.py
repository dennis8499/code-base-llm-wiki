from __future__ import annotations

import importlib.util
from pathlib import Path
import sys
import tempfile
import time
import unittest


REPO_ROOT = Path(__file__).parents[1]
LINT_PATH = REPO_ROOT / ".agents/skills/codebase-wiki/scripts/lint-wiki.py"


def load_lint():
    sys.path.insert(0, str(LINT_PATH.parent))
    spec = importlib.util.spec_from_file_location("wiki_scale_lint", LINT_PATH)
    assert spec and spec.loader
    module = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(module)
    return module


def page(title: str, page_type: str, body: str = "") -> str:
    return (
        "---\n"
        f"title: {title}\n"
        f"type: {page_type}\n"
        "sources: []\n"
        "last_updated: 2026-08-21\n"
        f"tags: [{page_type}]\n"
        "status: active\n"
        "---\n\n"
        f"# {title}\n\n{body}\n"
    )


class WikiScaleTests(unittest.TestCase):
    def test_lint_handles_a_200_page_wiki(self) -> None:
        lint = load_lint()
        with tempfile.TemporaryDirectory() as directory:
            root = Path(directory)
            wiki = root / "wiki"
            modules = wiki / "modules"
            modules.mkdir(parents=True)
            links = []
            for index in range(200):
                stem = f"module-{index:03d}"
                next_stem = f"module-{(index + 1) % 200:03d}"
                (modules / f"{stem}.md").write_text(
                    page(
                        f"Module {index:03d}",
                        "module",
                        f"Evidence-backed fixture. See [[{next_stem}]].",
                    ),
                    encoding="utf-8",
                )
                links.append(f"[[{stem}]]")
            (wiki / "index.md").write_text(
                page("Wiki Index", "index", "\n".join(links)),
                encoding="utf-8",
            )
            (wiki / "log.md").write_text(page("Wiki Log", "log"), encoding="utf-8")

            started = time.perf_counter()
            result = lint.lint_wiki(wiki, root)
            elapsed = time.perf_counter() - started

            self.assertEqual(result["summary"]["pages"], 202)
            self.assertEqual(result["summary"]["critical"], 0)
            self.assertEqual(result["summary"]["warning"], 0)
            self.assertLess(elapsed, 15.0, f"200-page lint took {elapsed:.2f}s")


if __name__ == "__main__":
    unittest.main()
