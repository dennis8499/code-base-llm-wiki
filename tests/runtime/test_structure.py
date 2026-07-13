from __future__ import annotations

import sys
import tempfile
import unittest
from pathlib import Path


RUNTIME_ROOT = Path(__file__).parents[2] / ".codebase-wiki" / "runtime"
sys.path.insert(0, str(RUNTIME_ROOT))

from codebase_wiki_runtime.structure import extract_source_documents  # noqa: E402


class StructureTests(unittest.TestCase):
    def test_tree_sitter_extracts_python_symbols(self) -> None:
        with tempfile.TemporaryDirectory() as directory:
            source = Path(directory) / "sample.py"
            source.write_text(
                "class User:\n    def login(self):\n        return True\n",
                encoding="utf-8",
            )

            documents, diagnostics = extract_source_documents(source, "python")

            self.assertEqual(diagnostics, [])
            self.assertGreaterEqual({item["name"] for item in documents}, {"User", "login"})
            self.assertTrue(all(item["parse_quality"] == "tree_sitter" for item in documents))

    def test_tree_sitter_supports_the_four_language_families(self) -> None:
        samples = {
            "javascript": ("sample.js", "class User {}\nfunction login() {}\n"),
            "jsx": ("sample.jsx", "function App() { return <div /> }\n"),
            "typescript": ("sample.ts", "interface User {}\nfunction login() {}\n"),
            "tsx": ("sample.tsx", "interface User {}\nfunction App() { return <div /> }\n"),
            "csharp": ("sample.cs", "public class User { public void Login() {} }\n"),
        }
        with tempfile.TemporaryDirectory() as directory:
            for language, (filename, text) in samples.items():
                source = Path(directory) / filename
                source.write_text(text, encoding="utf-8")
                documents, diagnostics = extract_source_documents(source, language)
                self.assertTrue(documents, language)
                self.assertEqual(diagnostics, [], language)
