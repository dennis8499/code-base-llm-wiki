from __future__ import annotations

from pathlib import Path
import contextlib
import hashlib
import io
import json
import shutil
import subprocess
import sys
import tempfile
import unittest
from unittest import mock

from .test_export_notebooklm import load_canonical_exporter, write_fixture


def write_capability_pair(root: Path, *, sa_locator: str = "src/service.py:1") -> None:
    synthesis = root / "wiki/synthesis"
    (synthesis / "cap-customer-greeting-ba.md").write_text(
        """---
title: 客戶問候 BA
type: synthesis
summary: 依目前程式碼整理客戶問候功能。
standards_profile: codebase-business-analysis-v1
coverage_status: covered
capability_id: cap-customer-greeting
notebooklm_document: ba
notebooklm_group: business-greeting
notebooklm_role: business
notebooklm_terms: [客戶問候, customer, greeting]
sources: [src/service.py]
source_locators: ["src/service.py:1"]
derived_from: ["[[greeting-requirement]]", "[[cap-customer-greeting-sa]]"]
last_updated: 2026-09-07
tags: [synthesis, business-analysis, codebase-as-is, notebooklm]
status: active
---

# 客戶問候 BA

## 功能目的、角色與觸發

客戶提供名稱時觸發問候。

## 流程、規則、結果與例外

回傳 `hello` 與名稱；Codebase 未提供其他業務政策證據。

## 來源定位

- `src/service.py:1`

## 對應 SA

[[cap-customer-greeting-sa]]
""",
        encoding="utf-8",
    )
    (synthesis / "cap-customer-greeting-sa.md").write_text(
        f"""---
title: 客戶問候 SA
type: synthesis
summary: 依目前程式碼整理客戶問候系統行為。
standards_profile: codebase-system-analysis-v1
coverage_status: covered
capability_id: cap-customer-greeting
notebooklm_document: sa
notebooklm_group: business-greeting
notebooklm_role: analysis
notebooklm_terms: [客戶問候, greet, string]
sources: [src/service.py]
source_locators: ["{sa_locator}"]
derived_from: ["[[greeting-requirement]]", "[[cap-customer-greeting-ba]]"]
last_updated: 2026-09-07
tags: [synthesis, system-analysis, codebase-as-is, notebooklm]
status: active
---

# 客戶問候 SA

## 邊界、輸入輸出與狀態

`greet(name)` 接收 `str` 並回傳 `str`；Codebase 未提供持久狀態證據。

## 資料、介面與錯誤處理

目前介面是 Python function；Codebase 未提供錯誤處理政策證據。

## 來源定位

- `{sa_locator}`

## 對應 BA

[[cap-customer-greeting-ba]]
""",
        encoding="utf-8",
    )
    index = root / "wiki/index.md"
    index.write_text(
        index.read_text(encoding="utf-8").rstrip()
        + "\n[[cap-customer-greeting-ba]]\n[[cap-customer-greeting-sa]]\n",
        encoding="utf-8",
    )


def invoke(module, *arguments: str) -> tuple[int, dict]:
    stream = io.StringIO()
    with contextlib.redirect_stdout(stream):
        code = module.main([*arguments, "--format", "json"])
    return code, json.loads(stream.getvalue())


def mark_analysis_complete(root: Path, module) -> str:
    discovery_id = module.build_preflight(root, module.load_settings(root))["discovery_id"]
    ledger = root / "wiki/synthesis/codebase-functional-coverage.md"
    text = module.ANALYZED_DISCOVERY_PATTERN.sub(
        "", ledger.read_text(encoding="utf-8")
    ).rstrip()
    ledger.write_text(
        text + f"\n\nAnalyzed discovery ID: `{discovery_id}`\n",
        encoding="utf-8",
    )
    return discovery_id


def tree_hashes(root: Path) -> dict[str, str]:
    return {
        path.relative_to(root).as_posix(): hashlib.sha256(path.read_bytes()).hexdigest()
        for path in sorted(root.rglob("*"))
        if path.is_file()
    }


def unique_document_lines(document: str, other: str) -> set[str]:
    """Independent membership oracle for line-safe source splitting."""

    other_lines = {line.strip() for line in other.splitlines() if line.strip()}
    return {
        line.strip()
        for line in document.splitlines()
        if len(line.strip()) >= 24 and line.strip() not in other_lines
    }


def write_task_tracker_analysis(root: Path, module) -> None:
    """Install a reviewed current-state Wiki fixture after the one preview gate."""

    with tempfile.TemporaryDirectory() as directory:
        seed = Path(directory)
        write_fixture(seed)
        shutil.rmtree(root / "wiki")
        shutil.copytree(seed / "wiki", root / "wiki")

    replacements = {
        "src/service.py": "src/task_tracker/service.py",
        "cap-customer-greeting": "cap-task-tracking",
        "fr-customer-greeting": "fr-task-tracking",
        "bp-customer-greeting": "bp-task-tracking",
        "br-greeting-format": "br-task-title",
        "greeting-requirement": "task-tracking-requirement",
        "greeting-format": "task-title-rule",
        "[[greeting]]": "[[task-tracking]]",
        "business-greeting": "business-task-tracking",
        "Customer Greeting": "Task Tracking",
        "customer greeting": "task tracking",
        "The system returns a greeting for a named customer.": (
            "The system creates, completes, lists, and evaluates tasks."
        ),
        "The service returns a greeting.": (
            "The service manages tasks through TaskTrackerService."
        ),
        "Given a name, when greeting is requested, then hello and the name are returned.": (
            "Given a valid title, when a task is created, then an open TaskItem is returned."
        ),
        "greet(name)": "TaskTrackerService.create_task(title)",
        "`greet`": "`TaskTrackerService.create_task`",
    }
    for path in sorted((root / "wiki").rglob("*.md")):
        text = path.read_text(encoding="utf-8")
        text = module.ANALYZED_DISCOVERY_PATTERN.sub("", text)
        for old, new in replacements.items():
            text = text.replace(old, new)
        path.write_text(text, encoding="utf-8")

    renames = {
        "wiki/requirements/greeting-requirement.md": "wiki/requirements/task-tracking-requirement.md",
        "wiki/processes/greeting.md": "wiki/processes/task-tracking.md",
        "wiki/rules/greeting-format.md": "wiki/rules/task-title-rule.md",
        "wiki/synthesis/cap-customer-greeting-ba.md": "wiki/synthesis/cap-task-tracking-ba.md",
        "wiki/synthesis/cap-customer-greeting-sa.md": "wiki/synthesis/cap-task-tracking-sa.md",
    }
    for old, new in renames.items():
        (root / old).replace(root / new)

    ba = root / "wiki/synthesis/cap-task-tracking-ba.md"
    ba.write_text(
        ba.read_text(encoding="utf-8")
        + "\n## 程式碼優先的來源差異\n\n"
        + "README fixture 聲稱已完成任務可再次完成；"
        + "`TaskTrackerService.complete_task` 的目前程式碼會拒絕此操作，因此文件採程式碼行為。\n\n"
        + "核准角色與政策：Codebase 未提供證據。\n"
        + "\n<!-- codebase-wiki:user-notes:start -->\n"
        + "人工註記：保留 `TaskTrackerService.create_task`。\n"
        + "<!-- codebase-wiki:user-notes:end -->\n",
        encoding="utf-8",
    )

    pages, _, _ = module.collect_wiki_pages(root)
    settings = module.load_settings(root)
    scan = module.scan_project(root, settings, pages)
    ledger = root / "wiki/synthesis/codebase-functional-coverage.md"
    uncovered_rows = [
        f"| `{path}` | no-observable-behavior | |"
        for path in scan["uncovered_paths"]
    ]
    if uncovered_rows:
        ledger.write_text(
            ledger.read_text(encoding="utf-8").rstrip()
            + "\n"
            + "\n".join(uncovered_rows)
            + "\n",
            encoding="utf-8",
        )
    pages, _, _ = module.collect_wiki_pages(root)
    scan = module.scan_project(root, settings, pages)
    self_contained_hash, discovery_id = module._discovery_identity(root, settings, scan)
    assert self_contained_hash == discovery_id.removeprefix("sha256:")
    text = module.ANALYZED_DISCOVERY_PATTERN.sub(
        "", ledger.read_text(encoding="utf-8")
    ).rstrip()
    ledger.write_text(
        text + f"\n\nAnalyzed discovery ID: `{discovery_id}`\n", encoding="utf-8"
    )


class NotebookLMAcceptanceTests(unittest.TestCase):
    def test_bdd_001_full_preview_uses_a_raw_source_discovery_identity(self) -> None:
        module = load_canonical_exporter()
        with tempfile.TemporaryDirectory() as directory:
            root = Path(directory)
            write_fixture(root)
            feature = root / "features/payments.py"
            feature.parent.mkdir()
            feature.write_text("def pay(invoice_id: str) -> bool:\n    return bool(invoice_id)\n", encoding="utf-8")
            sensitive = root / "secrets/password.txt"
            sensitive.parent.mkdir()
            sensitive.write_text("EXCLUDED-SECRET-BYTES", encoding="utf-8")
            raw_before = feature.read_bytes()
            original_read_bytes = Path.read_bytes

            def guarded_read_bytes(path: Path) -> bytes:
                if path == sensitive:
                    raise AssertionError("excluded source content was opened")
                return original_read_bytes(path)

            with mock.patch.object(Path, "read_bytes", guarded_read_bytes):
                first = module.build_preflight(root, module.load_settings(root))

            self.assertIn("discovery_id", first)
            self.assertIn("capability_preview", first)
            self.assertIn("features/payments.py", first["capability_preview"]["pending_analysis"])
            candidate = next(
                item
                for item in first["capability_preview"]["capabilities"]
                if item["capability_id"] == "cap-observed-features-payments"
            )
            self.assertEqual(candidate["discovery_status"], "pending-analysis")
            self.assertEqual(candidate["observed_sources"], ["features/payments.py"])
            self.assertEqual(candidate["document_coverage"], {"ba": "missing", "sa": "missing"})
            self.assertEqual(
                first["capability_preview"]["evidence_gaps"],
                first["capability_coverage"]["evidence_gaps"],
            )
            self.assertIn(
                "features/payments.py",
                first["capability_preview"]["source_differences"]["uncovered"],
            )
            self.assertTrue(
                any(
                    item["path"] == "secrets" and item["reason"] == "sensitive_filename"
                    for item in first["capability_preview"]["excluded_roots"]
                )
            )
            self.assertEqual(feature.read_bytes(), raw_before)
            self.assertEqual(sensitive.read_bytes(), b"EXCLUDED-SECRET-BYTES")

            overview = root / "wiki/overview.md"
            overview.write_text(overview.read_text(encoding="utf-8") + "\nWiki-only rebuild.\n", encoding="utf-8")
            wiki_changed = module.build_preflight(root, module.load_settings(root))
            self.assertEqual(first["discovery_id"], wiki_changed["discovery_id"])

            feature.write_text(feature.read_text(encoding="utf-8") + "# raw drift\n", encoding="utf-8")
            raw_changed = module.build_preflight(root, module.load_settings(root))
            self.assertNotEqual(first["discovery_id"], raw_changed["discovery_id"])

    def test_bdd_002_requires_one_traceable_ba_sa_pair_per_capability(self) -> None:
        module = load_canonical_exporter()
        with tempfile.TemporaryDirectory() as directory:
            root = Path(directory)
            write_fixture(root)
            write_capability_pair(root)

            complete = module.build_preflight(root, module.load_settings(root))

            self.assertIn("capability_coverage", complete)
            self.assertEqual(complete["capability_coverage"]["status"], "covered")
            self.assertEqual(
                complete["capability_coverage"]["capabilities"][0]["capability_id"],
                "cap-customer-greeting",
            )
            self.assertEqual(complete["capability_coverage"]["structural_issues"], [])

            source_ba = root / "wiki/synthesis/cap-customer-greeting-ba.md"
            duplicate_ba = root / "wiki/synthesis/cap-customer-greeting-ba-copy.md"
            duplicate_ba.write_text(source_ba.read_text(encoding="utf-8"), encoding="utf-8")
            duplicate = module.build_preflight(root, module.load_settings(root))
            self.assertFalse(duplicate["ready_to_export"])
            self.assertTrue(
                any("duplicate BA" in issue for issue in duplicate["capability_coverage"]["structural_issues"])
            )
            duplicate_ba.unlink()

            source_ba.write_text(
                source_ba.read_text(encoding="utf-8").replace(
                    "coverage_status: covered", "coverage_status: gap", 1
                ),
                encoding="utf-8",
            )
            processing_gap = module.build_preflight(root, module.load_settings(root))
            self.assertFalse(processing_gap["ready_to_export"])
            self.assertIn(
                "wiki/synthesis/cap-customer-greeting-ba.md",
                processing_gap["capability_coverage"]["analysis_gaps"],
            )
            write_capability_pair(root)

            source_ba = root / "wiki/synthesis/cap-customer-greeting-ba.md"
            source_ba.write_text(
                source_ba.read_text(encoding="utf-8")
                .replace("sources: [src/service.py]", "sources: []", 1)
                .replace('source_locators: ["src/service.py:1"]', "source_locators: []", 1)
                .replace(
                    "客戶提供名稱時觸發問候。",
                    "Codebase 未提供證據。",
                    1,
                ),
                encoding="utf-8",
            )
            documented_gap = module.build_preflight(root, module.load_settings(root))
            self.assertEqual(documented_gap["capability_coverage"]["status"], "partial")
            self.assertEqual(documented_gap["capability_coverage"]["analysis_gaps"], [])
            self.assertIn(
                "wiki/synthesis/cap-customer-greeting-ba.md",
                documented_gap["capability_coverage"]["evidence_gaps"],
            )
            write_capability_pair(root)

            (root / "wiki/synthesis/cap-customer-greeting-sa.md").unlink()
            missing = module.build_preflight(root, module.load_settings(root))
            self.assertFalse(missing["ready_to_export"])
            self.assertTrue(
                any("missing SA" in issue for issue in missing["capability_coverage"]["structural_issues"])
            )

            write_capability_pair(root, sa_locator="src/service.py:99")
            bad_locator = module.build_preflight(root, module.load_settings(root))
            self.assertFalse(bad_locator["ready_to_export"])
            self.assertTrue(
                any("invalid source locator" in issue for issue in bad_locator["capability_coverage"]["structural_issues"])
            )

            write_capability_pair(root)
            ba = root / "wiki/synthesis/cap-customer-greeting-ba.md"
            ba.write_text(
                ba.read_text(encoding="utf-8").replace(
                    "sources: [src/service.py]\n",
                    "sources: [src/service.py]\nsource_digest: sha256:"
                    + ("0" * 64)
                    + "\n",
                    1,
                ),
                encoding="utf-8",
            )
            self.assertIn("source_digest: sha256:" + ("0" * 64), ba.read_text(encoding="utf-8"))
            stale = module.build_preflight(root, module.load_settings(root))
            self.assertFalse(stale["ready_to_export"], stale["lint"])
            self.assertEqual(stale["capability_coverage"]["status"], "gap")
            self.assertIn(
                "wiki/synthesis/cap-customer-greeting-ba.md",
                stale["capability_coverage"]["stale_documents"],
            )

            write_capability_pair(root)
            sensitive = root / "secrets/password.txt"
            sensitive.parent.mkdir()
            sensitive.write_text("never-open-this-value", encoding="utf-8")
            ba = root / "wiki/synthesis/cap-customer-greeting-ba.md"
            ba.write_text(
                ba.read_text(encoding="utf-8")
                .replace("sources: [src/service.py]", "sources: [secrets/password.txt]", 1)
                .replace(
                    'source_locators: ["src/service.py:1"]',
                    'source_locators: ["secrets/password.txt:1"]',
                    1,
                ),
                encoding="utf-8",
            )
            original_read_bytes = Path.read_bytes
            original_read_text = Path.read_text

            def guarded_read_bytes(path: Path) -> bytes:
                if path == sensitive:
                    raise AssertionError("excluded locator bytes were opened")
                return original_read_bytes(path)

            def guarded_read_text(path: Path, *args, **kwargs) -> str:
                if path == sensitive:
                    raise AssertionError("excluded locator text was opened")
                return original_read_text(path, *args, **kwargs)

            with mock.patch.object(Path, "read_bytes", guarded_read_bytes), mock.patch.object(
                Path, "read_text", guarded_read_text
            ):
                unsafe = module.build_preflight(root, module.load_settings(root))
            self.assertFalse(unsafe["ready_to_export"])
            self.assertTrue(
                any(
                    "safe included inventory" in issue
                    for issue in unsafe["capability_coverage"]["unsafe_source_issues"]
                )
            )

    def test_bdd_003_apply_requires_the_confirmed_discovery_identity(self) -> None:
        module = load_canonical_exporter()
        with tempfile.TemporaryDirectory() as directory:
            root = Path(directory)
            write_fixture(root)
            write_capability_pair(root)
            mark_analysis_complete(root, module)
            preflight = module.build_preflight(root, module.load_settings(root))
            self.assertTrue(preflight["ready_to_export"])

            code, result = invoke(
                module,
                "--root",
                str(root),
                "--apply",
                "--preflight-id",
                preflight["preflight_id"],
            )

            self.assertEqual(code, 2)
            self.assertIn("--discovery-id", result["error"])
            self.assertFalse((root / ".notebooklm").exists())

            applied_code, applied = invoke(
                module,
                "--root",
                str(root),
                "--apply",
                "--discovery-id",
                preflight["discovery_id"],
                "--preflight-id",
                preflight["preflight_id"],
            )
            self.assertEqual(applied_code, 0, applied)
            manifest = root / ".notebooklm/manifest.json"

            ba = root / "wiki/synthesis/cap-customer-greeting-ba.md"
            ba.write_text(ba.read_text(encoding="utf-8") + "\n重新整理 Wiki 敘述。\n", encoding="utf-8")
            wiki_rebuilt = module.build_preflight(root, module.load_settings(root))
            self.assertEqual(preflight["discovery_id"], wiki_rebuilt["discovery_id"])
            self.assertNotEqual(preflight["preflight_id"], wiki_rebuilt["preflight_id"])
            rebuilt_code, rebuilt = invoke(
                module,
                "--root",
                str(root),
                "--apply",
                "--discovery-id",
                preflight["discovery_id"],
                "--preflight-id",
                wiki_rebuilt["preflight_id"],
            )
            self.assertEqual(rebuilt_code, 0, rebuilt)
            previous_manifest = manifest.read_bytes()

            source = root / "src/service.py"
            source.write_text(source.read_text(encoding="utf-8") + "# raw drift\n", encoding="utf-8")
            drift_code, drift = invoke(
                module,
                "--root",
                str(root),
                "--apply",
                "--discovery-id",
                preflight["discovery_id"],
                "--preflight-id",
                wiki_rebuilt["preflight_id"],
            )
            self.assertEqual(drift_code, 2)
            self.assertIn("discovery_id no longer matches", drift["error"])
            self.assertEqual(manifest.read_bytes(), previous_manifest)

            source.write_bytes(source.read_bytes().replace(b"# raw drift\n", b""))
            mark_analysis_complete(root, module)
            stable = module.build_preflight(root, module.load_settings(root))
            self.assertTrue(
                stable["ready_to_export"],
                json.dumps(
                    {
                        "warnings": stable["warnings"],
                        "coverage": stable["coverage"],
                        "capability": stable["capability_coverage"],
                        "pack_plan": stable["pack_plan"],
                    },
                    ensure_ascii=False,
                ),
            )
            prior_tree = tree_hashes(root / ".notebooklm")
            original_build_pack = module.build_pack

            def raw_interpass(*args, **kwargs):
                pack = original_build_pack(*args, **kwargs)
                source.write_text(
                    source.read_text(encoding="utf-8") + "# inter-pass raw drift\n",
                    encoding="utf-8",
                )
                return pack

            with mock.patch.object(module, "build_pack", side_effect=raw_interpass):
                race_code, race = invoke(
                    module,
                    "--root",
                    str(root),
                    "--apply",
                    "--discovery-id",
                    stable["discovery_id"],
                    "--preflight-id",
                    stable["preflight_id"],
                )
            self.assertEqual(race_code, 2, race)
            self.assertIn("changed during apply", race["error"])
            self.assertEqual(tree_hashes(root / ".notebooklm"), prior_tree)
            source.write_bytes(source.read_bytes().replace(b"# inter-pass raw drift\n", b""))

            config = root / "notebooklm.toml"
            config.write_text('content_mode = "ba_sa"\n', encoding="utf-8")
            mark_analysis_complete(root, module)
            config_preflight = module.build_preflight(root, module.load_settings(root))
            baseline_code, baseline = invoke(
                module,
                "--root",
                str(root),
                "--apply",
                "--discovery-id",
                config_preflight["discovery_id"],
                "--preflight-id",
                config_preflight["preflight_id"],
            )
            self.assertEqual(baseline_code, 0, baseline)
            prior_tree = tree_hashes(root / ".notebooklm")

            def config_interpass(*args, **kwargs):
                pack = original_build_pack(*args, **kwargs)
                config.write_text(
                    'content_mode = "ba_sa"\nreserved_source_slots = 1\n',
                    encoding="utf-8",
                )
                return pack

            with mock.patch.object(module, "build_pack", side_effect=config_interpass):
                race_code, race = invoke(
                    module,
                    "--root",
                    str(root),
                    "--apply",
                    "--discovery-id",
                    config_preflight["discovery_id"],
                    "--preflight-id",
                    config_preflight["preflight_id"],
                )
            self.assertEqual(race_code, 2, race)
            self.assertIn("configuration changed during apply", race["error"])
            self.assertEqual(tree_hashes(root / ".notebooklm"), prior_tree)
            config.write_text('content_mode = "ba_sa"\n', encoding="utf-8")

            sa = root / "wiki/synthesis/cap-customer-greeting-sa.md"

            def wiki_interpass(*args, **kwargs):
                pack = original_build_pack(*args, **kwargs)
                sa.write_text(
                    sa.read_text(encoding="utf-8") + "\n競態中的 Wiki 變更。\n",
                    encoding="utf-8",
                )
                return pack

            with mock.patch.object(module, "build_pack", side_effect=wiki_interpass):
                race_code, race = invoke(
                    module,
                    "--root",
                    str(root),
                    "--apply",
                    "--discovery-id",
                    config_preflight["discovery_id"],
                    "--preflight-id",
                    config_preflight["preflight_id"],
                )
            self.assertEqual(race_code, 2, race)
            self.assertIn("changed during apply", race["error"])
            self.assertEqual(tree_hashes(root / ".notebooklm"), prior_tree)

    def test_bdd_004_pack_contains_masked_ba_sa_documents_and_complete_mapping(self) -> None:
        module = load_canonical_exporter()
        with tempfile.TemporaryDirectory() as directory:
            root = Path(directory)
            write_fixture(root)
            write_capability_pair(root)
            ba = root / "wiki/synthesis/cap-customer-greeting-ba.md"
            ba.write_text(
                ba.read_text(encoding="utf-8")
                + "\n<!-- codebase-wiki:user-notes:start -->\n"
                + "人工註記：呼叫 `greet`；\"password\": \"p@ssword123!\"；"
                + "DB_PASSWORD=env-secret-456\n"
                + "\n".join(
                    f"BA-ONLY-EVIDENCE-{index:03d}：客戶問候業務流程第 {index} 項可觀察結果。"
                    for index in range(24)
                )
                + "\n"
                + "<!-- codebase-wiki:user-notes:end -->\n",
                encoding="utf-8",
            )
            sa = root / "wiki/synthesis/cap-customer-greeting-sa.md"
            sa.write_text(
                sa.read_text(encoding="utf-8")
                + "\n"
                + "\n".join(
                    f"SA-ONLY-EVIDENCE-{index:03d}：`greet` 系統介面第 {index} 項目前行為。"
                    for index in range(24)
                )
                + "\n",
                encoding="utf-8",
            )
            decoy = root / "wiki/synthesis/target-system-design.md"
            decoy.write_text(
                "---\ntitle: Target design\ntype: synthesis\n"
                "notebooklm_group: target-design\nnotebooklm_role: traceability\nsources: []\n"
                "last_updated: 2026-09-07\ntags: [system-design]\nstatus: active\n"
                "---\n\n# Target design\nSHOULD-NOT-BE-UPLOADED\n",
                encoding="utf-8",
            )
            for filename, profile, role, sentinel in (
                ("standalone-business-analysis.md", "babok-business-analysis-v1", "business", "STANDALONE-BA-DECOY"),
                ("standalone-system-analysis.md", "iso29148-system-analysis-v1", "analysis", "STANDALONE-SA-DECOY"),
            ):
                (root / "wiki/synthesis" / filename).write_text(
                    "---\ntitle: Standalone analysis\ntype: synthesis\n"
                    f"standards_profile: {profile}\nnotebooklm_group: standalone\n"
                    f"notebooklm_role: {role}\nnotebooklm_terms: [standalone, analysis]\nsources: []\n"
                    "last_updated: 2026-09-07\ntags: [synthesis]\nstatus: active\n"
                    f"---\n\n# Standalone analysis\n{sentinel}\n",
                    encoding="utf-8",
                )
            index = root / "wiki/index.md"
            index.write_text(
                index.read_text(encoding="utf-8")
                + "\n[[target-system-design]]\n[[standalone-business-analysis]]\n"
                + "[[standalone-system-analysis]]\n",
                encoding="utf-8",
            )
            output = root / ".notebooklm"
            output.mkdir()
            (output / "keep.me").write_text("preserve", encoding="utf-8")
            (output / "manifest.json").write_text(
                json.dumps(
                    {
                        "schema_version": 5,
                        "retrieval": {"contract": "business-only-ba-v2"},
                        "sources": [],
                    }
                ),
                encoding="utf-8",
            )

            (root / "notebooklm.toml").write_text(
                'content_mode = "ba_sa"\nmax_source_bytes = 900\nmax_source_words = 450000\n',
                encoding="utf-8",
            )

            mark_analysis_complete(root, module)
            preflight = module.build_preflight(root, module.load_settings(root))
            self.assertTrue(
                preflight["ready_to_export"],
                json.dumps(
                    {
                        "warnings": preflight["warnings"],
                        "pack_plan": preflight["pack_plan"],
                        "lint": preflight["lint"],
                        "capability": preflight["capability_coverage"],
                        "coverage": preflight["coverage"],
                    },
                    ensure_ascii=False,
                ),
            )
            code, result = invoke(
                module,
                "--root",
                str(root),
                "--apply",
                "--discovery-id",
                preflight["discovery_id"],
                "--preflight-id",
                preflight["preflight_id"],
            )

            self.assertEqual(code, 0, result)
            manifest = json.loads((output / "manifest.json").read_text(encoding="utf-8"))
            self.assertEqual(manifest["schema_version"], 6)
            self.assertTrue(manifest["migration"]["requires_full_rebuild"])
            self.assertEqual(
                {item["role"] for item in manifest["documents"]}, {"ba", "sa"}
            )
            self.assertEqual(
                {item["file"] for item in manifest["documents"]},
                {
                    "documents/cap-customer-greeting-ba.md",
                    "documents/cap-customer-greeting-sa.md",
                },
            )
            mapping = manifest["document_source_mapping"]
            self.assertEqual(set(mapping), {"cap-customer-greeting:ba", "cap-customer-greeting:sa"})
            self.assertTrue(all(mapping[key] for key in mapping))
            self.assertTrue(all(path.startswith("sources/") for paths in mapping.values() for path in paths))
            self.assertGreater(
                len(
                    [
                        item
                        for item in manifest["sources"]
                        if item["logical_source_id"].startswith("capability:cap-customer-greeting")
                    ]
                ),
                2,
            )
            document_text = "\n".join(
                path.read_text(encoding="utf-8")
                for path in sorted((output / "documents").glob("*.md"))
            )
            source_text = "\n".join(
                path.read_text(encoding="utf-8")
                for path in sorted((output / "sources").glob("*.md"))
            )
            self.assertIn(
                "Greeting means the customer-facing salutation.",
                source_text,
            )
            self.assertIn("Customer Greeting", source_text)
            self.assertIn("人工註記", document_text)
            self.assertIn("greet", document_text)
            self.assertIn("[MASKED:PASSWORD]", document_text)
            self.assertNotIn("p@ssword123!", document_text + source_text)
            self.assertNotIn("env-secret-456", document_text + source_text)
            self.assertNotIn("SHOULD-NOT-BE-UPLOADED", source_text)
            self.assertNotIn("STANDALONE-BA-DECOY", source_text)
            self.assertNotIn("STANDALONE-SA-DECOY", source_text)

            document_by_id = {
                item["logical_document_id"]: (output / item["file"]).read_text(encoding="utf-8")
                for item in manifest["documents"]
            }
            ba_lines = unique_document_lines(
                document_by_id["cap-customer-greeting:ba"],
                document_by_id["cap-customer-greeting:sa"],
            )
            sa_lines = unique_document_lines(
                document_by_id["cap-customer-greeting:sa"],
                document_by_id["cap-customer-greeting:ba"],
            )
            capability_files = {
                item["file"]
                for item in manifest["sources"]
                if item["logical_source_id"].startswith("capability:")
            }
            expected_ba = {
                relative
                for relative in capability_files
                if any(
                    line in (output / relative).read_text(encoding="utf-8")
                    for line in ba_lines
                )
            }
            expected_sa = {
                relative
                for relative in capability_files
                if any(
                    line in (output / relative).read_text(encoding="utf-8")
                    for line in sa_lines
                )
            }
            self.assertEqual(set(mapping["cap-customer-greeting:ba"]), expected_ba)
            self.assertEqual(set(mapping["cap-customer-greeting:sa"]), expected_sa)
            query_text = "".join(
                (output / item["file"]).read_text(encoding="utf-8")
                for item in manifest["sources"]
                if item["logical_source_id"] == "query-index"
                or item["logical_source_id"].startswith("query-index#part-")
            )
            self.assertIn("BA", query_text)
            self.assertIn("SA", query_text)
            self.assertEqual((output / "keep.me").read_text(encoding="utf-8"), "preserve")
            governance = (output / "governance.md").read_text(encoding="utf-8")
            self.assertIn("本機已檢查", governance)
            self.assertIn("租戶管理員待驗證", governance)
            self.assertIn("Sensitive Data Protection", governance)
            self.assertIn("Model Armor", governance)
            self.assertIn("300", governance)
            self.assertIn("500,000", governance)

            old_tree = tree_hashes(output)
            (root / "notebooklm.toml").write_text(
                'content_mode = "ba_sa"\nsource_limit = 2\n', encoding="utf-8"
            )
            new_discovery = mark_analysis_complete(root, module)
            limited = module.build_preflight(root, module.load_settings(root))
            self.assertEqual(limited["discovery_id"], new_discovery)
            self.assertFalse(limited["ready_to_export"])
            limited_code, limited_result = invoke(
                module,
                "--root",
                str(root),
                "--apply",
                "--discovery-id",
                limited["discovery_id"],
                "--preflight-id",
                limited["preflight_id"],
            )
            self.assertEqual(limited_code, 2)
            self.assertIn("not ready", limited_result["error"])
            self.assertEqual(tree_hashes(output), old_tree)

    def test_bdd_005_installed_surfaces_share_one_confirmation_ba_sa_workflow(self) -> None:
        repository = Path(__file__).resolve().parents[2]
        installer = (
            repository
            / ".agents/skills/codebase-wiki/scripts/install-framework.py"
        )
        with tempfile.TemporaryDirectory() as directory:
            temp = Path(directory)
            for surface in ("codex", "copilot"):
                target = temp / surface
                shutil.copytree(repository / "samples/task-tracker", target)
                sample_readme = target / "README.md"
                sample_readme.write_text(
                    sample_readme.read_text(encoding="utf-8")
                    + "\nFixture conflict: a completed task can be completed again.\n",
                    encoding="utf-8",
                )
                raw_paths = [
                    path.relative_to(target).as_posix()
                    for path in sorted(target.rglob("*"))
                    if path.is_file()
                ]
                raw_before = {
                    relative: hashlib.sha256((target / relative).read_bytes()).hexdigest()
                    for relative in raw_paths
                }
                result = subprocess.run(
                    [
                        sys.executable,
                        "-X",
                        "utf8",
                        str(installer),
                        "install",
                        "--target",
                        str(target),
                        "--surface",
                        surface,
                        "--apply",
                        "--format",
                        "json",
                    ],
                    cwd=repository,
                    capture_output=True,
                    text=True,
                    encoding="utf-8",
                    check=False,
                )
                self.assertEqual(result.returncode, 0, result.stderr or result.stdout)
                payload = json.loads(result.stdout)
                self.assertEqual(payload["contract_version"], 6)
                skill = target / ".agents/skills/codebase-wiki"
                installed_capability = json.loads(
                    (skill / "capabilities.json").read_text(encoding="utf-8")
                )
                self.assertEqual(
                    installed_capability["intents"]["notebooklm_export"]["confirmation_stages"],
                    ["discovery_plan"],
                )
                workflow = (skill / "references/notebooklm-export-workflow.md").read_text(
                    encoding="utf-8"
                )
                self.assertIn("一次確認", workflow)
                self.assertIn("--discovery-id", workflow)
                self.assertIn("--preflight-id", workflow)
                self.assertIn("documents/", workflow)
                self.assertIn("governance.md", workflow)
                for name, profile, role in (
                    ("notebooklm-ba-template.md", "codebase-business-analysis-v1", "ba"),
                    ("notebooklm-sa-template.md", "codebase-system-analysis-v1", "sa"),
                ):
                    template = (skill / "assets" / name).read_text(encoding="utf-8")
                    self.assertIn(profile, template)
                    self.assertIn(f"notebooklm_document: {role}", template)
                    self.assertIn("source_locators:", template)
                    self.assertIn("Codebase 未提供證據", template)
                    self.assertIn("codebase-wiki:user-notes:start", template)
                coverage_template = (
                    skill / "assets/codebase-functional-coverage-template.md"
                ).read_text(encoding="utf-8")
                self.assertIn("Analyzed discovery ID:", coverage_template)
                if surface == "copilot":
                    prompt = (
                        target / ".github/prompts/export-notebooklm.prompt.md"
                    ).read_text(encoding="utf-8")
                    self.assertIn("一次確認", prompt)
                    self.assertNotIn("第二次確認", prompt)
                else:
                    recipe = (target / "Codex.md").read_text(encoding="utf-8")
                    self.assertIn("NotebookLM", recipe)
                    self.assertIn("BA／SA", recipe)

                exporter = skill / "scripts/export-notebooklm.py"
                preview_process = subprocess.run(
                    [
                        sys.executable,
                        "-X",
                        "utf8",
                        str(exporter),
                        "--root",
                        str(target),
                        "--preflight",
                        "--format",
                        "json",
                    ],
                    cwd=target,
                    capture_output=True,
                    text=True,
                    encoding="utf-8",
                    check=False,
                )
                self.assertEqual(
                    preview_process.returncode,
                    0,
                    preview_process.stderr or preview_process.stdout,
                )
                preview = json.loads(preview_process.stdout)
                self.assertFalse(preview["ready_to_export"])
                self.assertIn(
                    "src/task_tracker/service.py",
                    preview["capability_preview"]["pending_analysis"],
                )
                self.assertIn(
                    "cap-observed-src-task-tracker-service",
                    {
                        item["capability_id"]
                        for item in preview["capability_preview"]["capabilities"]
                    },
                )

                confirmations = [preview["discovery_id"]]
                write_task_tracker_analysis(target, module=load_canonical_exporter())
                ready_process = subprocess.run(
                    [
                        sys.executable,
                        "-X",
                        "utf8",
                        str(exporter),
                        "--root",
                        str(target),
                        "--preflight",
                        "--format",
                        "json",
                    ],
                    cwd=target,
                    capture_output=True,
                    text=True,
                    encoding="utf-8",
                    check=False,
                )
                self.assertEqual(
                    ready_process.returncode,
                    0,
                    ready_process.stderr or ready_process.stdout,
                )
                ready = json.loads(ready_process.stdout)
                self.assertTrue(ready["ready_to_export"], ready["warnings"])
                self.assertEqual(ready["discovery_id"], confirmations[0])
                apply_process = subprocess.run(
                    [
                        sys.executable,
                        "-X",
                        "utf8",
                        str(exporter),
                        "--root",
                        str(target),
                        "--apply",
                        "--discovery-id",
                        confirmations[0],
                        "--preflight-id",
                        ready["preflight_id"],
                        "--format",
                        "json",
                    ],
                    cwd=target,
                    capture_output=True,
                    text=True,
                    encoding="utf-8",
                    check=False,
                )
                self.assertEqual(
                    apply_process.returncode,
                    0,
                    apply_process.stderr or apply_process.stdout,
                )
                self.assertEqual(len(confirmations), 1)
                manifest = json.loads(
                    (target / ".notebooklm/manifest.json").read_text(encoding="utf-8")
                )
                self.assertEqual(
                    {item["logical_document_id"] for item in manifest["documents"]},
                    {"cap-task-tracking:ba", "cap-task-tracking:sa"},
                )
                self.assertIn(
                    "人工註記",
                    (target / ".notebooklm/documents/cap-task-tracking-ba.md").read_text(
                        encoding="utf-8"
                    ),
                )
                exported_ba = (
                    target / ".notebooklm/documents/cap-task-tracking-ba.md"
                ).read_text(encoding="utf-8")
                self.assertIn("程式碼優先的來源差異", exported_ba)
                self.assertIn("TaskTrackerService.complete_task", exported_ba)
                self.assertIn("Codebase 未提供證據", exported_ba)
                self.assertEqual(
                    {
                        relative: hashlib.sha256((target / relative).read_bytes()).hexdigest()
                        for relative in raw_paths
                    },
                    raw_before,
                )


if __name__ == "__main__":
    unittest.main()
