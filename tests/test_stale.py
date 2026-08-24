from __future__ import annotations

import importlib.util
import os
import subprocess
import sys
import tempfile
import unittest
from contextlib import redirect_stderr, redirect_stdout
import io
from unittest import mock
from pathlib import Path


SCRIPTS = Path(__file__).parents[1] / ".agents" / "skills" / "codebase-wiki" / "scripts"
sys.path.insert(0, str(SCRIPTS))

spec = importlib.util.spec_from_file_location("check_stale", SCRIPTS / "check-stale.py")
check_stale_module = importlib.util.module_from_spec(spec)
assert spec.loader is not None
spec.loader.exec_module(check_stale_module)
check_stale = check_stale_module.check_stale


class StaleTests(unittest.TestCase):
    def test_check_stale_cli_reports_success_warning_and_input_errors(self) -> None:
        script = str(SCRIPTS / "check-stale.py")
        with tempfile.TemporaryDirectory() as directory:
            root = Path(directory)
            wiki = root / "wiki"
            wiki.mkdir()

            success = subprocess.run(
                [sys.executable, script, str(wiki), str(root)],
                capture_output=True,
                text=True,
                encoding="utf-8",
                check=False,
            )
            self.assertEqual(success.returncode, 0)
            self.assertIn("OK: 0/0", success.stdout)

            source = root / "service.py"
            source.write_text("return 1\n", encoding="utf-8")
            (wiki / "service.md").write_text(
                "---\ntitle: Service\ntype: module\nsources:\n"
                "  - service.py\nsource_digest: sha256:"
                + "0" * 64
                + "\nlast_updated: 2026-07-01\ntags: [module]\n"
                "status: active\n---\n",
                encoding="utf-8",
            )
            warning = subprocess.run(
                [sys.executable, script, str(wiki), str(root)],
                capture_output=True,
                text=True,
                encoding="utf-8",
                check=False,
            )
            self.assertEqual(warning.returncode, 1)
            self.assertIn("WARNING", warning.stdout)
            self.assertIn("source_digest:", warning.stdout)

            missing = subprocess.run(
                [sys.executable, script, str(root / "missing"), str(root)],
                capture_output=True,
                text=True,
                encoding="utf-8",
                check=False,
            )
            self.assertEqual(missing.returncode, 1)
            self.assertIn("wiki directory not found", missing.stderr)

    def test_check_stale_cli_fails_closed_on_unsafe_tree_error(self) -> None:
        with tempfile.TemporaryDirectory() as directory:
            wiki = Path(directory) / "wiki"
            wiki.mkdir()
            output = io.StringIO()
            error = io.StringIO()
            with (
                mock.patch.object(
                    check_stale_module,
                    "validate_regular_tree",
                    side_effect=OSError("unsafe tree"),
                ),
                redirect_stdout(output),
                redirect_stderr(error),
            ):
                with self.assertRaises(SystemExit) as raised:
                    check_stale_module.main([str(wiki), str(Path(directory))])
            self.assertEqual(raised.exception.code, 2)
            self.assertIn("unsafe tree", error.getvalue())

    def test_directory_sources_use_filesystem_fallback_without_git(self) -> None:
        with tempfile.TemporaryDirectory() as directory:
            root = Path(directory)
            (root / "wiki").mkdir()
            (root / "src/nested").mkdir(parents=True)
            (root / "src/service.py").write_text("return 1\n", encoding="utf-8")
            (root / "src/nested/helper.py").write_text("return 2\n", encoding="utf-8")
            (root / "wiki/service.md").write_text(
                "---\ntitle: Service\ntype: module\nsources:\n  - src\n"
                "last_updated: 2026-07-01\ntags: [module]\nstatus: active\n---\n",
                encoding="utf-8",
            )

            result = check_stale(root / "wiki", root)

            self.assertEqual(result["critical"], [])
            self.assertEqual(result["warning"], [])
            self.assertRegex(
                check_stale_module.compute_source_digest(root, ["src"]),
                r"^sha256:[0-9a-f]{64}$",
            )

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

    def test_windows_drive_source_path_is_rejected(self) -> None:
        with tempfile.TemporaryDirectory() as directory:
            root = Path(directory)
            (root / "wiki").mkdir()
            (root / "wiki" / "unsafe.md").write_text(
                "---\ntitle: Unsafe\ntype: module\nsources:\n  - C:/outside.py\n"
                "last_updated: 2026-07-01\ntags: [module]\nstatus: active\n---\n",
                encoding="utf-8",
            )

            result = check_stale(root / "wiki", root)

            self.assertTrue(result["critical"])
            self.assertEqual(result["critical"][0]["invalid_sources"], ["C:/outside.py"])

    def test_windows_style_relative_source_path_is_resolved(self) -> None:
        with tempfile.TemporaryDirectory() as directory:
            root = Path(directory)
            (root / "wiki").mkdir()
            (root / "src").mkdir()
            (root / "src/service.py").write_text("return 1\n", encoding="utf-8")
            (root / "wiki/service.md").write_text(
                "---\ntitle: Service\ntype: module\nsources:\n"
                "  - src\\service.py\nlast_updated: 2026-07-01\n"
                "tags: [module]\nstatus: active\n---\n",
                encoding="utf-8",
            )

            result = check_stale(root / "wiki", root)

            self.assertEqual(result["critical"], [])
            self.assertEqual(result["warning"], [])
            self.assertEqual(
                check_stale_module.compute_source_digest(root, [r"src\service.py"]),
                check_stale_module.compute_source_digest(root, ["src/service.py"]),
            )

    def test_source_symlink_escape_is_rejected(self) -> None:
        with tempfile.TemporaryDirectory() as directory:
            root = Path(directory)
            (root / "wiki").mkdir()
            outside = root / "outside.py"
            outside.write_text("return 1\n", encoding="utf-8")
            link = root / "linked.py"
            try:
                os.symlink(outside, link)
            except (OSError, NotImplementedError) as exc:
                self.skipTest(f"symlink creation unavailable: {exc}")
            (root / "wiki" / "unsafe.md").write_text(
                "---\ntitle: Unsafe\ntype: module\nsources:\n  - linked.py\n"
                "last_updated: 2026-07-01\ntags: [module]\nstatus: active\n---\n",
                encoding="utf-8",
            )

            result = check_stale(root / "wiki", root)

            self.assertTrue(result["critical"])
            self.assertEqual(result["critical"][0]["invalid_sources"], ["linked.py"])

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
