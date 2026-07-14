from __future__ import annotations

import contextlib
import io
import json
import subprocess
import sys
import tempfile
import unittest
from pathlib import Path


RUNTIME_ROOT = Path(__file__).parents[2] / ".codebase-wiki" / "runtime"
sys.path.insert(0, str(RUNTIME_ROOT))

from codebase_wiki_runtime.cli import _index_stale, main  # noqa: E402


class CliTests(unittest.TestCase):
    def test_setup_and_index_update_make_search_available(self) -> None:
        with tempfile.TemporaryDirectory() as directory:
            root = Path(directory)
            (root / "wiki").mkdir()
            (root / "wiki" / "auth.md").write_text("# Auth\n\n## 登入流程\n驗證 token\n", encoding="utf-8")
            output = io.StringIO()
            with contextlib.chdir(root), contextlib.redirect_stdout(output):
                self.assertEqual(main(["setup", "--no-install", "--format", "json"]), 0)
                self.assertEqual(main(["index", "update", "--format", "json"]), 0)
                self.assertEqual(main(["search", "登入", "--format", "json"]), 0)

            payloads = [json.loads(line) for line in output.getvalue().splitlines()]
            self.assertTrue(payloads[-1]["results"])
            self.assertTrue(all(item["kind"] == "wiki_section" for item in payloads[-1]["results"]))

    def test_doctor_json_reports_fts5(self) -> None:
        with tempfile.TemporaryDirectory() as directory, contextlib.chdir(directory):
            output = io.StringIO()
            with contextlib.redirect_stdout(output):
                self.assertEqual(main(["doctor", "--format", "json"]), 0)

            payload = json.loads(output.getvalue())
            self.assertEqual(payload["contract_version"], 1)
            self.assertTrue(payload["capabilities"]["fts5"])

    def test_doctor_text_reports_tree_sitter(self) -> None:
        with tempfile.TemporaryDirectory() as directory, contextlib.chdir(directory):
            output = io.StringIO()
            with contextlib.redirect_stdout(output):
                self.assertEqual(main(["doctor", "--format", "text"]), 0)

            self.assertIn("FTS5: yes", output.getvalue())
            self.assertIn("Tree-sitter: yes", output.getvalue())

    def test_search_json_is_read_only_when_index_is_missing(self) -> None:
        with tempfile.TemporaryDirectory() as directory, contextlib.chdir(directory):
            output = io.StringIO()
            with contextlib.redirect_stdout(output):
                self.assertEqual(main(["search", "hello", "--format", "json"]), 4)

            payload = json.loads(output.getvalue())
            self.assertFalse(payload["ok"])
            self.assertEqual(payload["error"]["code"], "index_missing")

    def test_source_changes_mark_existing_index_stale(self) -> None:
        with tempfile.TemporaryDirectory() as directory:
            root = Path(directory)
            (root / "service.py").write_text("return 1\n", encoding="utf-8")
            subprocess.run(["git", "init", "-q"], cwd=root, check=True)
            subprocess.run(["git", "add", "."], cwd=root, check=True)
            subprocess.run(
                ["git", "-c", "user.email=wiki@example.com", "-c", "user.name=Wiki", "commit", "-qm", "initial"],
                cwd=root,
                check=True,
            )
            self.assertFalse(_index_stale(root))
            (root / "service.py").write_text("return 2\n", encoding="utf-8")
            self.assertTrue(_index_stale(root))

    def test_non_indexed_document_changes_do_not_mark_existing_index_stale(self) -> None:
        with tempfile.TemporaryDirectory() as directory:
            root = Path(directory)
            (root / "README.md").write_text("initial\n", encoding="utf-8")
            (root / "service.py").write_text("return 1\n", encoding="utf-8")
            subprocess.run(["git", "init", "-q"], cwd=root, check=True)
            subprocess.run(["git", "add", "."], cwd=root, check=True)
            subprocess.run(
                ["git", "-c", "user.email=wiki@example.com", "-c", "user.name=Wiki", "commit", "-qm", "initial"],
                cwd=root,
                check=True,
            )
            (root / "README.md").write_text("formatting-only change\n", encoding="utf-8")
            self.assertFalse(_index_stale(root))

    def test_renamed_indexed_source_marks_existing_index_stale(self) -> None:
        with tempfile.TemporaryDirectory() as directory:
            root = Path(directory)
            (root / "service.py").write_text("return 1\n", encoding="utf-8")
            subprocess.run(["git", "init", "-q"], cwd=root, check=True)
            subprocess.run(["git", "add", "."], cwd=root, check=True)
            subprocess.run(
                ["git", "-c", "user.email=wiki@example.com", "-c", "user.name=Wiki", "commit", "-qm", "initial"],
                cwd=root,
                check=True,
            )
            subprocess.run(["git", "mv", "service.py", "service.txt"], cwd=root, check=True)
            self.assertTrue(_index_stale(root))
