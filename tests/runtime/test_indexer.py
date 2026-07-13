from __future__ import annotations

import json
import sys
import tempfile
import unittest
from pathlib import Path


RUNTIME_ROOT = Path(__file__).parents[2] / ".codebase-wiki" / "runtime"
sys.path.insert(0, str(RUNTIME_ROOT))

from codebase_wiki_runtime.indexer import build_index  # noqa: E402
from codebase_wiki_runtime.storage import IndexStore  # noqa: E402


class IndexerTests(unittest.TestCase):
    def test_build_index_indexes_wiki_and_source_structure(self) -> None:
        with tempfile.TemporaryDirectory() as directory:
            root = Path(directory)
            (root / "wiki").mkdir()
            (root / "wiki" / "auth.md").write_text(
                "# Auth\n\n## 登入流程\n\n驗證 token。\n", encoding="utf-8"
            )
            (root / "users.py").write_text("class User:\n    def login(self):\n        pass\n", encoding="utf-8")

            result = build_index(root, root / "index.sqlite3")
            rows = IndexStore(root / "index.sqlite3").search("登入")
            symbols = IndexStore(root / "index.sqlite3").search("login")

            self.assertTrue(result["documents"] >= 3)
            self.assertTrue(any(item["kind"] == "wiki_section" for item in rows))
            self.assertTrue(any(item["kind"] == "symbol" for item in symbols))
            self.assertEqual(result["diagnostics"], [])
