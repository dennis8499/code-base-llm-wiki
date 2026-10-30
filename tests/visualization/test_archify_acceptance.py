from __future__ import annotations

import json
import os
from pathlib import Path
import importlib.util
import sys
import tempfile
import unittest

REPO_ROOT = Path(__file__).parents[2]
SCRIPT_DIR = REPO_ROOT / ".agents/skills/codebase-wiki/scripts"
sys.path.insert(0, str(SCRIPT_DIR))
from bounded_process import run_bounded

spec = importlib.util.spec_from_file_location(
    "wiki_visualize_acceptance", SCRIPT_DIR / "wiki-visualize.py"
)
if spec is None or spec.loader is None:
    raise RuntimeError("unable to load wiki-visualize.py")
wiki_visualize = importlib.util.module_from_spec(spec)
spec.loader.exec_module(wiki_visualize)


EXAMPLES = REPO_ROOT / ".agents/skills/codebase-wiki/vendor/archify/examples"
FIXTURES = (
    ("architecture", "brand-aware-delivery.architecture.json"),
    ("workflow", "holiday-planning.workflow.json"),
    ("sequence", "async-job-roundtrip.sequence.json"),
    ("dataflow", "event-stream.dataflow.json"),
    ("lifecycle", "agent-run.lifecycle.json"),
    ("erd", "orders.erd.json"),
    ("class", "payment-processors.class.json"),
    ("tree", "archify-repository.tree.json"),
    ("timeline", "archify-dev-activity.timeline.json"),
    ("waterfall", "checkout-request.waterfall.json"),
)
REQUIRED_GATES = {"validate", "deliver", "check", "browser-check"}


@unittest.skipUnless(
    os.environ.get("CODEBASE_WIKI_ARCHIFY_ACCEPTANCE") == "1",
    "set CODEBASE_WIKI_ARCHIFY_ACCEPTANCE=1 to run all ten browser-backed fixtures",
)
class ArchifyAcceptanceTests(unittest.TestCase):
    def test_all_diagram_types_finalize_and_pass_browser_check(self) -> None:
        bundle = wiki_visualize.validate_bundle()
        self.assertEqual(bundle["version"], "3.2.0")
        node = os.environ.get("NODE") or __import__("shutil").which("node")
        self.assertIsNotNone(node, "Node.js is required for Archify acceptance")
        env = os.environ.copy()
        env["ARCHIFY_UPDATE_CHECK_DISABLED"] = "1"

        with tempfile.TemporaryDirectory(prefix="archify-ten-types-") as directory:
            work = Path(directory)
            for diagram_type, filename in FIXTURES:
                with self.subTest(diagram_type=diagram_type):
                    source = json.loads((EXAMPLES / filename).read_text(encoding="utf-8"))
                    self.assertEqual(source.get("diagram_type"), diagram_type)
                    self.assertIsInstance(source.get("meta"), dict)
                    source["meta"].update(
                        locale="zh-TW",
                        quality_profile="showcase",
                        animation="none",
                        output="diagram.html",
                    )
                    # Let showcase delivery size the canvas around each
                    # fixture's content instead of inheriting upstream demo
                    # dimensions that may clip at the target viewport.
                    source["meta"].pop("viewBox", None)
                    case = work / diagram_type
                    case.mkdir()
                    candidate = case / "candidate.json"
                    output = case / "diagram.html"
                    candidate.write_text(
                        json.dumps(source, ensure_ascii=False, indent=2) + "\n",
                        encoding="utf-8",
                    )
                    result = run_bounded(
                        [
                            node,
                            str(wiki_visualize.VENDOR_ROOT / "bin/archify.mjs"),
                            "finalize",
                            diagram_type,
                            str(candidate),
                            str(output),
                            "--quality",
                            "showcase",
                            "--json",
                        ],
                        cwd=case,
                        env=env,
                        timeout=180,
                        max_output_bytes=8 * 1024 * 1024,
                        text=False,
                    )
                    self.assertEqual(
                        result.returncode,
                        0,
                        result.stdout.decode("utf-8", errors="replace")
                        + result.stderr.decode("utf-8", errors="replace"),
                    )
                    receipt = json.loads(
                        (case / "diagram.finalize.json").read_text(encoding="utf-8")
                    )
                    self.assertIs(receipt.get("ok"), True)
                    self.assertEqual(receipt.get("status"), "pass")
                    self.assertTrue(REQUIRED_GATES <= set(receipt.get("stages", {})))
                    for gate in REQUIRED_GATES:
                        self.assertEqual(receipt["stages"][gate]["status"], "pass", gate)
                    self.assertTrue(output.is_file())
                    self.assertGreater(output.stat().st_size, 0)


if __name__ == "__main__":
    unittest.main()
