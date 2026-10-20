from __future__ import annotations

import os
import json
from pathlib import Path
import subprocess
import sys
import tempfile
import unittest
from unittest import mock

SCRIPTS = Path(__file__).parents[2] / ".agents/skills/codebase-wiki/scripts"
sys.path.insert(0, str(SCRIPTS))
import wiki_transaction as tx

ENTRY = b"## [2026-10-20] update | reviewed update\n\n- Affected pages: [[index]], [[a]]"


class WikiTransactionTests(unittest.TestCase):
    def setUp(self):
        temporary = tempfile.TemporaryDirectory(); self.addCleanup(temporary.cleanup)
        self.root = Path(temporary.name).resolve()
        (self.root / "wiki").mkdir()
        (self.root / "wiki/index.md").write_bytes(b"# Index\n[[a]]\n")
        (self.root / "wiki/a.md").write_bytes(b"# A\nUser notes stay here.\n")
        (self.root / "wiki/log.md").write_bytes(
            b"---\ntitle: Wiki Log\ntype: log\nsources: []\nlast_updated: 2026-10-19\ntags: [log]\nstatus: active\n---\n"
            b"<!-- codebase-wiki:log-contract-v1 -->\n\n## [2026-10-19] update | old\n- Affected pages: [[a]]\n")
        self.expected = tx.snapshot(self.root)
        self.writes = {"wiki/a.md": b"# A\nUser notes stay here.\nNew knowledge.\n", "wiki/index.md": b"# Index\n[[a]]\n"}

    def test_commit_preserves_log_body_and_notes_and_advances_snapshot(self):
        before = (self.root / "wiki/log.md").read_bytes().split(b"---\n", 2)[2]
        result = tx.commit(self.root, self.writes, self.expected, log_append=ENTRY)
        after = (self.root / "wiki/log.md").read_bytes()
        self.assertTrue(result["ok"])
        self.assertNotEqual(result["snapshot"], self.expected)
        self.assertTrue(after.split(b"---\n", 2)[2].startswith(before))
        self.assertIn(b"User notes stay here.", (self.root / "wiki/a.md").read_bytes())
        self.assertEqual(after.count(b"reviewed update"), 1)
        self.assertFalse((self.root / ".codebase-wiki-write.transaction.json").exists())

    def test_stale_whole_wiki_snapshot_preserves_concurrent_new_content(self):
        (self.root / "wiki/personal.md").write_bytes(b"new user note")
        before = tx.snapshot(self.root)
        with self.assertRaisesRegex(tx.WikiConflict, "after the preview"):
            tx.commit(self.root, self.writes, self.expected, log_append=ENTRY)
        self.assertEqual(tx.snapshot(self.root), before)

    def test_writer_lock_rejects_a_second_writer(self):
        with tx._Lock(self.root):
            with self.assertRaisesRegex(tx.WikiConflict, "another writer"):
                tx.commit(self.root, self.writes, self.expected, log_append=ENTRY)
        self.assertEqual(tx.snapshot(self.root), self.expected)

    def test_io_failure_rolls_back_pages_index_and_log(self):
        original = os.replace; failed = False
        def replace(source, destination):
            nonlocal failed
            if Path(destination) == self.root / "wiki/index.md" and not failed:
                failed = True
                raise OSError("simulated disk failure")
            return original(source, destination)
        with mock.patch.object(tx.os, "replace", replace):
            with self.assertRaisesRegex(OSError, "disk failure"):
                tx.commit(self.root, self.writes, self.expected, log_append=ENTRY)
        self.assertEqual(tx.snapshot(self.root), self.expected)

    def crash(self):
        code = """import sys,os
from pathlib import Path
sys.path.insert(0,sys.argv[1])
import wiki_transaction as tx
root=Path(sys.argv[2]); old=tx.snapshot(root); original=os.replace
def replace(source,destination):
    result=original(source,destination)
    if Path(destination)==root/'wiki/a.md': os._exit(77)
    return result
os.replace=replace
tx.commit(root,{'wiki/a.md':b'interrupted','wiki/index.md':b'index'},old,log_append=b'## [2026-10-20] update | interrupted\\n- Affected pages: [[a]]')
"""
        result = subprocess.run([sys.executable, "-B", "-c", code, str(SCRIPTS), str(self.root)], capture_output=True)
        self.assertEqual(result.returncode, 77, result.stderr)

    def test_crash_recovery_restores_before_retrying_same_preview(self):
        self.crash()
        result = tx.commit(self.root, self.writes, self.expected, log_append=ENTRY)
        self.assertTrue(result["ok"])
        self.assertEqual((self.root / "wiki/a.md").read_bytes(), self.writes["wiki/a.md"])
        self.assertNotIn(b"interrupted", (self.root / "wiki/log.md").read_bytes())

    def test_recovery_preserves_post_crash_user_edit_as_conflict(self):
        self.crash()
        (self.root / "wiki/a.md").write_bytes(b"user edit after crash")
        with self.assertRaisesRegex(tx.WikiConflict, "newer edit"):
            tx.commit(self.root, self.writes, self.expected, log_append=ENTRY)
        self.assertEqual((self.root / "wiki/a.md").read_bytes(), b"user edit after crash")

    def test_boundaries_log_rewrite_and_missing_index_are_rejected_before_writes(self):
        for writes in ({"src/a.py": b"source", "wiki/index.md": b"index"},
                       {"wiki/a.md": b"page"}, {"wiki/log.md": b"rewritten"},
                       {"wiki//a.md": b"duplicate", "wiki/index.md": b"index"}):
            with self.subTest(writes=list(writes)), self.assertRaises(tx.WikiConflict):
                tx.commit(self.root, writes, self.expected, log_append=ENTRY)
            self.assertEqual(tx.snapshot(self.root), self.expected)

    def test_cli_rejects_malformed_write_types_without_a_traceback(self):
        plan = self.root / "plan.json"
        plan.write_text(json.dumps({"schema": "codebase-wiki-write/v1", "snapshot": self.expected,
                                    "writes": {"wiki/a.md": 12}, "log_append": "invalid"}), encoding="utf-8")
        result = subprocess.run([sys.executable, "-X", "utf8", "-B", str(SCRIPTS / "wiki-write.py"),
                                 "apply", "--root", str(self.root), "--plan", str(plan)], capture_output=True, text=True)
        self.assertEqual(result.returncode, 2)
        self.assertFalse(json.loads(result.stderr)["ok"])
        self.assertNotIn("Traceback", result.stderr)
        self.assertEqual(tx.snapshot(self.root), self.expected)


if __name__ == "__main__":
    unittest.main()
