from __future__ import annotations

import contextlib
import importlib.util
import io
import json
import os
from pathlib import Path
import platform
import subprocess
import sys
import tempfile
import unittest
from unittest import mock


REPO_ROOT = Path(__file__).parents[2]
WRAPPER_PATH = REPO_ROOT / ".agents/skills/codebase-wiki/scripts/tgrep-search.py"


def load_wrapper():
    spec = importlib.util.spec_from_file_location("tgrep_search", WRAPPER_PATH)
    if spec is None or spec.loader is None:
        raise RuntimeError(f"Unable to load tgrep wrapper: {WRAPPER_PATH}")
    module = importlib.util.module_from_spec(spec)
    sys.modules[spec.name] = module
    spec.loader.exec_module(module)
    return module


def supported_windows_x64() -> bool:
    return os.name == "nt" and platform.machine().lower() in {"amd64", "x86_64", "x64"}


class TgrepWrapperTests(unittest.TestCase):
    def test_command_places_pattern_after_double_dash_and_uses_allowlist(self) -> None:
        wrapper = load_wrapper()
        args = type(
            "Args",
            (),
            {
                "no_index": True,
                "glob": ["*.py"],
                "type": ["py"],
                "list_files": False,
                "fixed": True,
                "ignore_case": True,
                "files_only": True,
                "count": False,
                "context": 2,
                "json": False,
                "pattern": "--no-index; Remove-Item -Recurse *",
            },
        )()
        bundle = wrapper.Bundle("1.0.5", Path("tgrep.exe"), "a" * 64, "https://example.invalid")

        command = wrapper.build_command(args, bundle, Path("."), "src")

        self.assertEqual(command[-3:], ["--", "--no-index; Remove-Item -Recurse *", "src"])
        self.assertIn("--no-index", command)
        self.assertIn("--fixed-strings", command)
        self.assertIn("--files-with-matches", command)
        self.assertNotIn("shell", command)

    def test_root_and_path_containment_reject_escape(self) -> None:
        wrapper = load_wrapper()
        with tempfile.TemporaryDirectory() as directory:
            root = Path(directory) / "repo"
            outside = Path(directory) / "outside"
            root.mkdir()
            outside.mkdir()
            (outside / "secret.txt").write_text("secret\n", encoding="utf-8")

            with self.assertRaisesRegex(wrapper.TgrepError, "escapes"):
                wrapper.resolve_search_path(root, Path("..") / "outside")

            link = root / "escape"
            try:
                os.symlink(outside, link, target_is_directory=True)
            except (OSError, NotImplementedError) as exc:
                self.skipTest(f"symlink creation unavailable: {exc}")
            with self.assertRaisesRegex(wrapper.TgrepError, "escapes"):
                wrapper.resolve_search_path(root, Path("escape"))

            root_link = Path(directory) / "repo-link"
            try:
                os.symlink(root, root_link, target_is_directory=True)
            except (OSError, NotImplementedError) as exc:
                self.skipTest(f"symlink creation unavailable: {exc}")
            with self.assertRaisesRegex(wrapper.TgrepError, "symlink or reparse"):
                wrapper.resolve_search_path(root_link, Path("."))

    @unittest.skipUnless(supported_windows_x64(), "bundled tgrep smoke test requires Windows x64")
    def test_bundle_hash_and_version_self_check(self) -> None:
        wrapper = load_wrapper()
        bundle = wrapper.validate_bundle(check_version=True)
        self.assertEqual(bundle.version, "1.0.5")
        self.assertEqual(
            bundle.sha256,
            "9b90e4446e2cbf05e1da086547501e35d7b32f0f6d5f687548cf270b07fbd9d7",
        )

    @unittest.skipUnless(supported_windows_x64(), "bundled tgrep metadata test requires Windows x64")
    def test_bundle_rejects_version_and_digest_mismatch(self) -> None:
        wrapper = load_wrapper()
        manifest = json.loads(wrapper.MANIFEST_PATH.read_text(encoding="utf-8"))
        manifest["version"] = "1.0.4"
        with mock.patch.object(wrapper, "_read_manifest", return_value=manifest):
            with self.assertRaises(wrapper.TgrepUnavailable):
                wrapper.validate_bundle()

        with mock.patch.object(wrapper, "_sha256", return_value="0" * 64):
            with self.assertRaisesRegex(wrapper.TgrepUnavailable, "SHA-256 mismatch"):
                wrapper.validate_bundle()

    @unittest.skipUnless(supported_windows_x64(), "bundled tgrep smoke test requires Windows x64")
    def test_cli_preserves_match_exit_code_and_does_not_create_index(self) -> None:
        with tempfile.TemporaryDirectory() as directory:
            root = Path(directory) / "repo"
            source = root / "src"
            source.mkdir(parents=True)
            (source / "sample.py").write_text("class PaymentService:\n    pass\n", encoding="utf-8")
            command = [
                sys.executable,
                str(WRAPPER_PATH),
                "--root",
                str(root),
                "--path",
                "src",
                "--no-index",
                "--fixed",
                "--files-only",
                "--pattern",
                "PaymentService",
            ]
            matched = subprocess.run(command, capture_output=True, text=True, check=False)
            self.assertEqual(matched.returncode, 0, matched.stderr)
            self.assertIn("sample.py", matched.stdout)
            self.assertFalse((root / ".tgrep").exists())

            unmatched = subprocess.run(
                [*command[:-1], "NotPresent"],
                capture_output=True,
                text=True,
                check=False,
            )
            self.assertEqual(unmatched.returncode, 1, unmatched.stderr)
            self.assertFalse((root / ".tgrep").exists())

    def test_unavailable_status_is_controlled(self) -> None:
        wrapper = load_wrapper()
        with mock.patch.object(wrapper, "_is_supported_host", return_value=False):
            with self.assertRaises(wrapper.TgrepUnavailable) as raised:
                wrapper.validate_bundle()
        self.assertEqual(raised.exception.exit_code, 3)

    def test_run_search_disables_shell_and_preserves_documented_codes(self) -> None:
        wrapper = load_wrapper()
        result = subprocess.CompletedProcess(["tgrep"], 1, b"", b"")
        with mock.patch.object(wrapper.subprocess, "run", return_value=result) as run:
            with contextlib.redirect_stdout(io.StringIO()), contextlib.redirect_stderr(io.StringIO()):
                code = wrapper.run_search(["tgrep", "--", "pattern", "."], Path("."))
        self.assertEqual(code, 1)
        self.assertFalse(run.call_args.kwargs["shell"])


if __name__ == "__main__":
    unittest.main()
