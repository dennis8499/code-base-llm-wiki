from __future__ import annotations

import sys
import unittest
from pathlib import Path


RUNTIME_ROOT = Path(__file__).parents[2] / ".codebase-wiki" / "runtime"
sys.path.insert(0, str(RUNTIME_ROOT))

from codebase_wiki_runtime.storage import IndexStore  # noqa: E402


class StorageTests(unittest.TestCase):
    def test_index_store_searches_wiki_and_preserves_cjk_terms(self) -> None:
        import tempfile

        with tempfile.TemporaryDirectory() as directory:
            store = IndexStore(Path(directory) / "index.sqlite3")
            store.initialize()
            store.replace_documents(
                [
                    {
                        "id": "wiki:auth",
                        "kind": "wiki_section",
                        "path": "wiki/auth.md",
                        "title": "登入流程",
                        "heading": "登入流程",
                        "body": "登入流程需要驗證 token",
                        "terms": "登入 驗證 token",
                        "line_start": 1,
                        "line_end": 4,
                    }
                ]
            )

            results = store.search("登入", limit=5)

            self.assertEqual([item["id"] for item in results], ["wiki:auth"])
            self.assertEqual(results[0]["path"], "wiki/auth.md")

    def test_index_store_uses_literal_queries_by_default(self) -> None:
        import tempfile

        with tempfile.TemporaryDirectory() as directory:
            store = IndexStore(Path(directory) / "index.sqlite3")
            store.initialize()
            store.replace_documents(
                [
                    {
                        "id": "wiki:literal",
                        "kind": "wiki_section",
                        "path": "wiki/literal.md",
                        "title": "FTS operators",
                        "heading": "FTS operators",
                        "body": "a OR b",
                        "terms": "a b",
                        "line_start": 1,
                        "line_end": 2,
                    }
                ]
            )

            self.assertEqual(store.search("a OR nonexistent", limit=5), [])

    def test_index_store_matches_cjk_phrases_as_bigrams(self) -> None:
        import tempfile

        with tempfile.TemporaryDirectory() as directory:
            store = IndexStore(Path(directory) / "index.sqlite3")
            store.initialize()
            store.replace_documents(
                [
                    {
                        "id": "wiki:cjk",
                        "kind": "wiki_section",
                        "path": "wiki/cjk.md",
                        "title": "流程",
                        "heading": "登入流程",
                        "body": "登入流程需要驗證",
                        "terms": "登入 入流 流程 驗證",
                    }
                ]
            )

            self.assertEqual([item["id"] for item in store.search("登入流程")], ["wiki:cjk"])
