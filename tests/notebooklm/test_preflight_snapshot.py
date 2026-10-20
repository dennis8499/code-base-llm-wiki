from __future__ import annotations

import contextlib
import io
import json
from pathlib import Path
import sys
import tempfile
import unittest
from unittest import mock

from .test_export_notebooklm import load_canonical_exporter, write_fixture


class PreflightSnapshotTests(unittest.TestCase):
    def test_preflight_shares_one_source_read_with_dlp_and_lint(self):
        module = load_canonical_exporter(); scanner = sys.modules["project_scanner"]
        with tempfile.TemporaryDirectory() as directory:
            root = Path(directory).resolve(); write_fixture(root)
            source = root / "src/service.py"
            original = Path.read_bytes
            def read_bytes(path):
                if path.resolve() == source:
                    raise AssertionError("source bytes were read again after the scanner snapshot")
                return original(path)
            with mock.patch.object(scanner, "read_source", wraps=scanner.read_source) as reads, \
                 mock.patch.object(Path, "read_bytes", read_bytes):
                result = module.build_preflight(root, module.load_settings(root))
            self.assertTrue(result["ready_to_export"], result["warnings"])
            self.assertEqual(sum(Path(call.args[0]).resolve() == source for call in reads.call_args_list), 1)

    def test_apply_checks_all_input_bytes_without_repeating_dlp_or_planning(self):
        module = load_canonical_exporter()
        with tempfile.TemporaryDirectory() as directory:
            root = Path(directory).resolve(); write_fixture(root)
            preview = module.build_preflight(root, module.load_settings(root))
            with mock.patch.object(module, "build_preflight", wraps=module.build_preflight) as builds, \
                 mock.patch.object(module, "plan_ba_sources", wraps=module.plan_ba_sources) as plans, \
                 contextlib.redirect_stdout(io.StringIO()):
                code = module.main(["--root", str(root), "--apply", "--discovery-id", preview["discovery_id"],
                                    "--preflight-id", preview["preflight_id"], "--format", "json"])
            self.assertEqual(code, 0)
            self.assertEqual(builds.call_count, 1)
            self.assertEqual(plans.call_count, 1)

    def test_mid_apply_source_wiki_and_configuration_changes_preserve_prior_output(self):
        module = load_canonical_exporter()
        for relative in ("src/service.py", "wiki/index.md", "notebooklm.toml"):
            with self.subTest(path=relative), tempfile.TemporaryDirectory() as directory:
                root = Path(directory).resolve(); write_fixture(root)
                preview = module.build_preflight(root, module.load_settings(root))
                arguments = ["--root", str(root), "--apply", "--discovery-id", preview["discovery_id"],
                             "--preflight-id", preview["preflight_id"], "--format", "json"]
                with contextlib.redirect_stdout(io.StringIO()):
                    self.assertEqual(module.main(arguments), 0)
                manifest_before = (root / ".notebooklm/manifest.json").read_bytes()
                original = module.build_pack
                def build(*args, **kwargs):
                    result = original(*args, **kwargs)
                    path = root / relative
                    path.write_bytes((path.read_bytes() if path.exists() else b"") + b"\n# changed during apply\n")
                    return result
                output = io.StringIO()
                with mock.patch.object(module, "build_pack", side_effect=build), contextlib.redirect_stdout(output):
                    code = module.main(arguments)
                self.assertEqual(code, 2, output.getvalue())
                self.assertIn("changed during apply", json.loads(output.getvalue())["error"])
                self.assertEqual((root / ".notebooklm/manifest.json").read_bytes(), manifest_before)


if __name__ == "__main__":
    unittest.main()
