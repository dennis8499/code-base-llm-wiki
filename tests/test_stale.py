from __future__ import annotations

import importlib.util
import subprocess
import sys
import tempfile
import unittest
from pathlib import Path


SCRIPTS = Path(__file__).parents[1] / ".agents" / "skills" / "codebase-wiki" / "scripts"
sys.path.insert(0, str(SCRIPTS))

spec = importlib.util.spec_from_file_location("check_stale", SCRIPTS / "check-stale.py")
check_stale_module = importlib.util.module_from_spec(spec)
assert spec.loader is not None
spec.loader.exec_module(check_stale_module)
check_stale = check_stale_module.check_stale


class StaleTests(unittest.TestCase):
    def test_dirty_source_is_reported_as_stale(self) -> None:
        with tempfile.TemporaryDirectory() as directory:
            root = Path(directory)
            (root / "wiki").mkdir()
            (root / "service.py").write_text("return 1\n", encoding="utf-8")
            (root / "wiki" / "service.md").write_text(
                "---\ntitle: Service\ntype: module\nsources:\n  - service.py\n"
                "last_updated: 2026-07-01\ntags: [module]\nstatus: active\n---\n",
                encoding="utf-8",
            )
            subprocess.run(["git", "init", "-q"], cwd=root, check=True)
            subprocess.run(["git", "add", "."], cwd=root, check=True)
            subprocess.run(
                ["git", "-c", "user.email=wiki@example.com", "-c", "user.name=Wiki", "commit", "-qm", "initial"],
                cwd=root,
                check=True,
            )
            (root / "service.py").write_text("return 2\n", encoding="utf-8")

            result = check_stale(root / "wiki", root)

            self.assertTrue(result["warning"])
            self.assertEqual(result["warning"][0]["stale"], ["service.py"])

    def test_parent_source_path_is_rejected(self) -> None:
        with tempfile.TemporaryDirectory() as directory:
            root = Path(directory)
            (root / "wiki").mkdir()
            (root / "wiki" / "unsafe.md").write_text(
                "---\ntitle: Unsafe\ntype: module\nsources:\n  - ../outside.py\n"
                "last_updated: 2026-07-01\ntags: [module]\nstatus: active\n---\n",
                encoding="utf-8",
            )

            result = check_stale(root / "wiki", root)

            self.assertTrue(result["critical"])
            self.assertEqual(result["critical"][0]["invalid_sources"], ["../outside.py"])

    def test_source_digest_detects_same_day_change_and_exact_revert(self) -> None:
        with tempfile.TemporaryDirectory() as directory:
            root = Path(directory)
            (root / "wiki").mkdir()
            source = root / "service.py"
            source.write_text("return 1\n", encoding="utf-8")
            digest = check_stale_module.compute_source_digest(root, ["service.py"])
            page = root / "wiki/service.md"
            page.write_text(
                "---\ntitle: Service\ntype: module\nsources:\n  - service.py\n"
                f"source_digest: {digest}\n"
                "last_updated: 2026-07-01\ntags: [module]\nstatus: active\n---\n",
                encoding="utf-8",
            )

            self.assertFalse(check_stale(root / "wiki", root)["warning"])
            source.write_text("return 2\n", encoding="utf-8")
            changed = check_stale(root / "wiki", root)
            self.assertIn("digest_mismatch", changed["warning"][0])

            source.write_text("return 1\n", encoding="utf-8")
            self.assertFalse(check_stale(root / "wiki", root)["warning"])


if __name__ == "__main__":
    unittest.main()
