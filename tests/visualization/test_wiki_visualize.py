from __future__ import annotations

import argparse
import hashlib
import importlib.util
import json
import shutil
import subprocess
import sys
import tempfile
from pathlib import Path
from unittest import mock
import unittest


REPO_ROOT = Path(__file__).parents[2]
SCRIPT_DIR = REPO_ROOT / ".agents/skills/codebase-wiki/scripts"
SCRIPT_PATH = SCRIPT_DIR / "wiki-visualize.py"
sys.path.insert(0, str(SCRIPT_DIR))

spec = importlib.util.spec_from_file_location("wiki_visualize", SCRIPT_PATH)
if spec is None or spec.loader is None:
    raise RuntimeError(f"Unable to load visualization workflow: {SCRIPT_PATH}")
visualize = importlib.util.module_from_spec(spec)
spec.loader.exec_module(visualize)
REAL_RUN_BOUNDED = visualize.run_bounded


def digest(data: bytes) -> str:
    return hashlib.sha256(data).hexdigest()


class WikiVisualizeTests(unittest.TestCase):
    def setUp(self) -> None:
        self.tmp = Path(tempfile.mkdtemp(prefix="wiki-visualize-tests-", dir=REPO_ROOT))
        self.addCleanup(self._cleanup_tmp)
        self.root = self.tmp / "repo"
        (self.root / "wiki").mkdir(parents=True)
        (self.root / "src").mkdir()
        (self.root / "wiki/overview.md").write_text(
            "---\ntitle: Overview\ntype: overview\nsources: []\nlast_updated: 2026-10-30\n"
            "tags: [overview]\nstatus: active\n---\n\n# Overview\n",
            encoding="utf-8",
        )
        (self.root / "wiki/index.md").write_text(
            "---\ntitle: Wiki Index\ntype: index\nsources: []\nlast_updated: 2026-10-30\n"
            "tags: [index]\nstatus: active\n---\n\n# Index\n",
            encoding="utf-8",
        )
        (self.root / "wiki/log.md").write_text(
            "---\ntitle: Wiki Activity Log\ntype: log\nsources: []\nlast_updated: 2026-10-30\n"
            "tags: [log]\nstatus: active\n---\n\n# Activity Log\n",
            encoding="utf-8",
        )
        self.source = self.root / "src/evidence.md"
        self.source.write_text("The fixture contains a root node.\n", encoding="utf-8")
        self.prepared = None

    def _cleanup_tmp(self) -> None:
        target = self.tmp.resolve()
        self.assertTrue(target.is_relative_to(REPO_ROOT.resolve()))
        if target.exists():
            shutil.rmtree(target)

    def prepare(self, slug: str = "fixture-tree") -> dict:
        args = argparse.Namespace(
            root=self.root,
            type="tree",
            slug=slug,
            title="Fixture Tree",
            wiki_page=["wiki/overview.md"],
            source=["src/evidence.md"],
            illustrative=False,
        )
        with mock.patch.object(visualize.tempfile, "gettempdir", return_value=str(self.tmp)):
            self.prepared = visualize.prepare(args)
        return self.prepared

    def fill_candidate(self, prepared: dict) -> None:
        candidate_path = Path(prepared["candidate"])
        candidate = json.loads(candidate_path.read_text(encoding="utf-8"))
        candidate["nodes"] = [{"id": "root", "label": "Root"}]
        candidate_path.write_text(json.dumps(candidate, ensure_ascii=False, indent=2), encoding="utf-8")
        source_hash = digest(self.source.read_bytes())
        mapping = {
            "schema": "codebase-wiki-visualization-evidence/v1",
            "claims": [
                {
                    "element_id": "nodes:root",
                    "evidence": [{"path": "src/evidence.md", "sha256": source_hash}],
                }
            ],
            "gaps": [],
        }
        Path(prepared["evidence_map"]).write_text(
            json.dumps(mapping, ensure_ascii=False, indent=2), encoding="utf-8"
        )

    def fake_archify(self, command, **kwargs):
        if len(command) == 2 and command[1] == "--version":
            return subprocess.CompletedProcess(command, 0, "v24.0.0\n", "")
        if any("rebuild-index.py" in str(value) for value in command):
            return REAL_RUN_BOUNDED(command, **kwargs)
        self.assertIn("finalize", command)
        candidate_path = Path(command[4])
        output_path = Path(command[5])
        candidate_bytes = candidate_path.read_bytes()
        output_bytes = b"<!doctype html><html><body>validated test diagram</body></html>\n"
        output_path.write_bytes(output_bytes)
        stages = {
            "validate": {"status": "not-run", "execution": "embedded-in-deliver"},
            "deliver": {"status": "pass", "durationMs": 1},
            "check": {"status": "pass", "durationMs": 1},
            "browser-check": {"status": "pass", "durationMs": 1},
        }
        receipt = {
            "ok": True,
            "status": "pass",
            "specification": {"sha256": digest(candidate_bytes)},
            "artifact": {"sha256": digest(output_bytes)},
            "stages": stages,
        }
        output_path.with_name(output_path.stem + ".finalize.json").write_text(
            json.dumps(receipt), encoding="utf-8"
        )
        output_path.with_name(output_path.stem + ".delivery.json").write_text(
            '{"command":"deliver","ok":true}\n', encoding="utf-8"
        )
        output_path.with_name(output_path.stem + ".browser-check.json").write_text(
            '{"command":"browser-check","ok":true}\n', encoding="utf-8"
        )
        return subprocess.CompletedProcess(
            command, 0,
            json.dumps({"ok": True, "status": "pass"}).encode("utf-8"),
            b"",
        )

    def fail_archify(self, command, **kwargs):
        if len(command) == 2 and command[1] == "--version":
            return subprocess.CompletedProcess(command, 0, "v24.0.0\n", "")
        return subprocess.CompletedProcess(
            command, 1,
            b'{"ok":false,"status":"failed","failedStage":"browser-check"}',
            b"browser unavailable",
        )

    def publish(self, prepared: dict) -> dict:
        args = argparse.Namespace(root=self.root, plan=Path(prepared["plan"]))
        with (
            mock.patch.object(visualize.tempfile, "gettempdir", return_value=str(self.tmp)),
            mock.patch.object(visualize, "run_bounded", side_effect=self.fake_archify),
        ):
            return visualize.publish(args)

    def test_bundle_verifies_and_prepare_captures_evidence_without_wiki_writes(self) -> None:
        bundle = visualize.verify_bundle()
        self.assertEqual(bundle["version"], "3.2.0")
        before = visualize.wiki_snapshot(self.root)
        prepared = self.prepare()
        self.addCleanup(
            shutil.rmtree,
            Path(json.loads(Path(prepared["plan"]).read_text(encoding="utf-8"))["workdir"]),
        )
        self.assertEqual(visualize.wiki_snapshot(self.root), before)
        candidate = json.loads(Path(prepared["candidate"]).read_text(encoding="utf-8"))
        self.assertEqual(candidate["meta"]["locale"], "zh-TW")
        self.assertEqual(candidate["meta"]["quality_profile"], "showcase")
        self.assertEqual(candidate["meta"]["animation"], "none")
        self.assertIn("src/evidence.md", [item["path"] for item in prepared["evidence"]])

    def test_publish_is_one_snapshot_checked_transaction_and_verify_detects_changes(self) -> None:
        prepared = self.prepare()
        workdir = Path(json.loads(Path(prepared["plan"]).read_text(encoding="utf-8"))["workdir"])
        self.addCleanup(shutil.rmtree, workdir)
        self.fill_candidate(prepared)
        overview_before = (self.root / "wiki/overview.md").read_bytes()
        published = self.publish(prepared)
        self.assertTrue(published["ok"])
        self.assertEqual(set(published["gates"]), {"validate", "deliver", "check", "browser-check"})
        self.assertEqual(published["wiki_files"].count("wiki/log.md"), 1)
        self.assertTrue((self.root / published["artifact"]).is_file())
        self.assertTrue((self.root / published["companion"]).is_file())
        self.assertEqual((self.root / "wiki/overview.md").read_bytes(), overview_before)
        self.assertEqual(
            visualize.verify_run(argparse.Namespace(root=self.root, run=published["artifact"].removesuffix("/diagram.html"), bundle=False))["evidence_fresh"],
            True,
        )
        artifact = self.root / published["artifact"]
        artifact.write_bytes(artifact.read_bytes() + b"tamper")
        with self.assertRaisesRegex(visualize.VisualizeError, "hash or size mismatch"):
            visualize.verify_run(argparse.Namespace(root=self.root, run=published["artifact"].removesuffix("/diagram.html"), bundle=False))

    def test_source_drift_blocks_publish_before_any_wiki_write(self) -> None:
        prepared = self.prepare()
        workdir = Path(json.loads(Path(prepared["plan"]).read_text(encoding="utf-8"))["workdir"])
        self.addCleanup(shutil.rmtree, workdir)
        self.fill_candidate(prepared)
        before = visualize.wiki_snapshot(self.root)
        self.source.write_text("changed after prepare\n", encoding="utf-8")
        with self.assertRaisesRegex(visualize.VisualizeError, "evidence changed after prepare"):
            self.publish(prepared)
        self.assertEqual(visualize.wiki_snapshot(self.root), before)

    def test_invalid_candidate_json_fails_without_wiki_writes(self) -> None:
        prepared = self.prepare()
        workdir = Path(json.loads(Path(prepared["plan"]).read_text(encoding="utf-8"))["workdir"])
        self.addCleanup(shutil.rmtree, workdir)
        Path(prepared["candidate"]).write_text("{broken", encoding="utf-8")
        before = visualize.wiki_snapshot(self.root)
        with self.assertRaisesRegex(visualize.VisualizeError, "not valid UTF-8 JSON"):
            self.publish(prepared)
        self.assertEqual(visualize.wiki_snapshot(self.root), before)

    def test_failed_browser_validation_leaves_wiki_unchanged(self) -> None:
        prepared = self.prepare()
        workdir = Path(json.loads(Path(prepared["plan"]).read_text(encoding="utf-8"))["workdir"])
        self.addCleanup(shutil.rmtree, workdir)
        self.fill_candidate(prepared)
        before = visualize.wiki_snapshot(self.root)
        args = argparse.Namespace(root=self.root, plan=Path(prepared["plan"]))
        with (
            mock.patch.object(visualize.tempfile, "gettempdir", return_value=str(self.tmp)),
            mock.patch.object(visualize, "run_bounded", side_effect=self.fail_archify),
            self.assertRaisesRegex(visualize.VisualizeError, "finalize failed at browser-check"),
        ):
            visualize.publish(args)
        self.assertEqual(visualize.wiki_snapshot(self.root), before)

    def test_second_run_preserves_human_notes_and_previous_artifact(self) -> None:
        first_prepared = self.prepare()
        first_workdir = Path(json.loads(Path(first_prepared["plan"]).read_text(encoding="utf-8"))["workdir"])
        self.addCleanup(shutil.rmtree, first_workdir)
        self.fill_candidate(first_prepared)
        first = self.publish(first_prepared)
        companion = self.root / first["companion"]
        content = companion.read_text(encoding="utf-8")
        content = content.replace(
            "<!-- Add or edit human notes in this block; future runs preserve it. -->",
            "Human note: keep this annotation.",
        )
        companion.write_text(content, encoding="utf-8")

        second_prepared = self.prepare()
        second_workdir = Path(json.loads(Path(second_prepared["plan"]).read_text(encoding="utf-8"))["workdir"])
        self.addCleanup(shutil.rmtree, second_workdir)
        self.fill_candidate(second_prepared)
        second = self.publish(second_prepared)
        updated = companion.read_text(encoding="utf-8")
        self.assertIn("Human note: keep this annotation.", updated)
        self.assertIn(first["run_id"], updated)
        self.assertTrue((self.root / first["artifact"]).is_file())
        self.assertTrue((self.root / second["artifact"]).is_file())

    def test_wiki_snapshot_conflict_preserves_concurrent_edit(self) -> None:
        prepared = self.prepare()
        workdir = Path(json.loads(Path(prepared["plan"]).read_text(encoding="utf-8"))["workdir"])
        self.addCleanup(shutil.rmtree, workdir)
        self.fill_candidate(prepared)
        parent = self.root / "wiki/overview.md"
        parent.write_text(parent.read_text(encoding="utf-8") + "\nConcurrent human edit.\n", encoding="utf-8")
        with self.assertRaisesRegex(visualize.VisualizeError, "Wiki snapshot changed"):
            self.publish(prepared)
        self.assertIn("Concurrent human edit", parent.read_text(encoding="utf-8"))
        self.assertFalse((self.root / "wiki/visualizations").exists())


if __name__ == "__main__":
    unittest.main()
