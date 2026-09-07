from __future__ import annotations

from dataclasses import replace
from pathlib import Path
import tempfile
import json
import unittest
from unittest import mock

from test_export_notebooklm import load_canonical_exporter, write_fixture
from test_notebooklm_acceptance import (
    invoke,
    mark_analysis_complete,
    tree_hashes,
    unique_document_lines,
    write_capability_pair,
)


class NotebookLMContractTests(unittest.TestCase):
    def test_test_001_schema_v6_and_discovery_contract(self) -> None:
        module = load_canonical_exporter()
        self.assertEqual(module.EXPORT_SCHEMA_VERSION, 6)
        self.assertEqual(module.PREFLIGHT_SCHEMA_VERSION, 6)
        self.assertEqual(module.CONTENT_MODE, "ba_sa")
        self.assertEqual(module.KNOWLEDGE_CONTRACT, "codebase-ba-sa-v1")
        self.assertEqual(module.RETRIEVAL_CONTRACT, "codebase-ba-sa-retrieval-v1")

        with tempfile.TemporaryDirectory() as directory:
            root = Path(directory)
            write_fixture(root)
            feature = root / "features/payments.py"
            feature.parent.mkdir()
            feature.write_text(
                "def pay(invoice_id: str) -> bool:\n    return bool(invoice_id)\n",
                encoding="utf-8",
            )
            secret = root / "secrets/token.txt"
            secret.parent.mkdir()
            secret.write_text("never-read-this-secret", encoding="utf-8")
            original_read_bytes = Path.read_bytes

            def guarded_read_bytes(path: Path) -> bytes:
                if path == secret:
                    raise AssertionError("excluded bytes were opened")
                return original_read_bytes(path)

            with mock.patch.object(Path, "read_bytes", guarded_read_bytes):
                preflight = module.build_preflight(root, module.load_settings(root))
            self.assertRegex(preflight["discovery_id"], r"^sha256:[0-9a-f]{64}$")
            self.assertEqual(preflight["discovery_schema_version"], 1)
            preview = preflight["capability_preview"]
            self.assertIn(
                "cap-observed-features-payments",
                {item["capability_id"] for item in preview["capabilities"]},
            )
            self.assertIn("features/payments.py", preview["source_differences"]["uncovered"])
            self.assertTrue(any(item["path"] == "secrets" for item in preview["excluded_roots"]))

    def test_test_002_capability_pair_contract_and_locator_validation(self) -> None:
        module = load_canonical_exporter()
        with tempfile.TemporaryDirectory() as directory:
            root = Path(directory)
            write_fixture(root)
            write_capability_pair(root)
            pages, _, _ = module.collect_wiki_pages(root)
            scan = module.scan_project(root, module.load_settings(root), pages)

            self.assertTrue(hasattr(module, "capability_document_coverage"))
            coverage = module.capability_document_coverage(pages, root, scan)

            self.assertEqual(coverage["status"], "covered")
            pair = coverage["capabilities"][0]
            self.assertEqual(pair["documents"]["ba"]["profile"], "codebase-business-analysis-v1")
            self.assertEqual(pair["documents"]["sa"]["profile"], "codebase-system-analysis-v1")
            self.assertEqual(pair["documents"]["ba"]["group"], pair["documents"]["sa"]["group"])
            self.assertEqual(coverage["structural_issues"], [])

            ba = root / "wiki/synthesis/cap-customer-greeting-ba.md"
            duplicate = root / "wiki/synthesis/cap-customer-greeting-copy.md"
            duplicate.write_text(ba.read_text(encoding="utf-8"), encoding="utf-8")
            pages, _, _ = module.collect_wiki_pages(root)
            scan = module.scan_project(root, module.load_settings(root), pages)
            duplicate_coverage = module.capability_document_coverage(pages, root, scan)
            self.assertTrue(any("duplicate BA" in item for item in duplicate_coverage["structural_issues"]))
            duplicate.unlink()

            ba.write_text(
                ba.read_text(encoding="utf-8").replace(
                    "coverage_status: covered", "coverage_status: gap", 1
                ),
                encoding="utf-8",
            )
            pages, _, _ = module.collect_wiki_pages(root)
            scan = module.scan_project(root, module.load_settings(root), pages)
            gap_coverage = module.capability_document_coverage(pages, root, scan)
            self.assertIn("wiki/synthesis/cap-customer-greeting-ba.md", gap_coverage["analysis_gaps"])
            write_capability_pair(root)

            secret = root / "secrets/password.txt"
            secret.parent.mkdir()
            secret.write_text("excluded-sensitive-value", encoding="utf-8")
            ba = root / "wiki/synthesis/cap-customer-greeting-ba.md"
            ba.write_text(
                ba.read_text(encoding="utf-8")
                .replace("sources: [src/service.py]", "sources: [secrets/password.txt]", 1)
                .replace('source_locators: ["src/service.py:1"]', 'source_locators: ["secrets/password.txt:1"]', 1),
                encoding="utf-8",
            )
            pages, _, _ = module.collect_wiki_pages(root)
            scan = module.scan_project(root, module.load_settings(root), pages)
            original_read_text = Path.read_text

            def guarded_read_text(path: Path, *args, **kwargs) -> str:
                if path == secret:
                    raise AssertionError("excluded locator was opened")
                return original_read_text(path, *args, **kwargs)

            with mock.patch.object(Path, "read_text", guarded_read_text):
                unsafe = module.capability_document_coverage(pages, root, scan)
            self.assertTrue(unsafe["unsafe_source_issues"])

    def test_test_003_apply_parser_binds_discovery_and_readiness_ids(self) -> None:
        module = load_canonical_exporter()
        parser = module.build_parser()
        option_strings = {
            option for action in parser._actions for option in action.option_strings
        }
        self.assertIn("--discovery-id", option_strings)
        arguments = parser.parse_args(
            [
                "--apply",
                "--discovery-id",
                "sha256:" + "a" * 64,
                "--preflight-id",
                "sha256:" + "b" * 64,
            ]
        )
        self.assertEqual(arguments.discovery_id, "sha256:" + "a" * 64)
        self.assertEqual(arguments.preflight_id, "sha256:" + "b" * 64)

        with tempfile.TemporaryDirectory() as directory:
            root = Path(directory)
            write_fixture(root)
            write_capability_pair(root)
            mark_analysis_complete(root, module)
            preflight = module.build_preflight(root, module.load_settings(root))
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
            output = root / ".notebooklm"
            before = tree_hashes(output)
            source = root / "src/service.py"
            original_build_pack = module.build_pack

            def mutate_after_build(*args, **kwargs):
                result = original_build_pack(*args, **kwargs)
                source.write_text(
                    source.read_text(encoding="utf-8") + "# race\n", encoding="utf-8"
                )
                return result

            with mock.patch.object(module, "build_pack", side_effect=mutate_after_build):
                race_code, race = invoke(
                    module,
                    "--root",
                    str(root),
                    "--apply",
                    "--discovery-id",
                    preflight["discovery_id"],
                    "--preflight-id",
                    preflight["preflight_id"],
                )
            self.assertEqual(race_code, 2, race)
            self.assertEqual(tree_hashes(output), before)

    def test_test_004_ba_sa_document_materialization_contract(self) -> None:
        module = load_canonical_exporter()
        with tempfile.TemporaryDirectory() as directory:
            root = Path(directory)
            write_fixture(root)
            write_capability_pair(root)
            pages, _, _ = module.collect_wiki_pages(root)

            self.assertTrue(hasattr(module, "capability_document_units"))
            units = module.capability_document_units(pages)
            self.assertTrue(hasattr(module, "shared_business_context_units"))
            shared_units = module.shared_business_context_units(pages)

            self.assertEqual(
                [unit.logical_source_id for unit in units],
                ["cap-customer-greeting:ba", "cap-customer-greeting:sa"],
            )
            self.assertEqual(
                [unit.logical_source_id for unit in shared_units],
                ["shared-business-context"],
            )
            self.assertIn(
                "Greeting means the customer-facing salutation.",
                shared_units[0].content,
            )
            self.assertIn("Customer Greeting", shared_units[0].content)
            self.assertEqual({unit.kind for unit in units}, {"ba", "sa"})
            self.assertTrue(all(unit.content for unit in units))
            self.assertIn("greet(name)", next(unit.content for unit in units if unit.kind == "sa"))
            governance = module.governance_content()
            self.assertIn("租戶管理員待驗證", governance)
            self.assertIn("IAM", governance)
            self.assertIn("VPC Service Controls", governance)
            self.assertIn("CMEK", governance)
            self.assertIn("data location", governance)

            input_file = module.InputFile(
                path="wiki/synthesis/cap-example-ba.md",
                text="example",
                digest=module.sha256_bytes(b"example"),
            )
            ba_content = "\n".join(
                f"BA-UNIQUE-{index:03d} business observable result" for index in range(30)
            ) + "\n"
            sa_content = "\n".join(
                f"SA-UNIQUE-{index:03d} system observable behavior" for index in range(30)
            ) + "\n"
            document_units = [
                module.Unit(
                    logical_source_id="cap-example:ba",
                    kind="ba",
                    group="business-example",
                    title="BA",
                    inputs=(input_file,),
                    content=ba_content,
                ),
                module.Unit(
                    logical_source_id="cap-example:sa",
                    kind="sa",
                    group="business-example",
                    title="SA",
                    inputs=(input_file,),
                    content=sa_content,
                ),
            ]
            settings = replace(
                module.load_settings(root), max_source_bytes=100_000, max_source_words=35
            )
            split_sources, compacted = module.fit_capability_sources(
                document_units, settings, max_slots=100
            )
            self.assertFalse(compacted)
            documents = [
                (unit, f"documents/{unit.logical_source_id.replace(':', '-')}.md", "digest")
                for unit in document_units
            ]
            mapping = module._document_source_mapping(documents, split_sources, compacted)
            ba_lines = unique_document_lines(ba_content, sa_content)
            sa_lines = unique_document_lines(sa_content, ba_content)
            expected_ba = {
                filename
                for unit, filename, _ in split_sources
                if any(line in unit.content for line in ba_lines)
            }
            expected_sa = {
                filename
                for unit, filename, _ in split_sources
                if any(line in unit.content for line in sa_lines)
            }
            self.assertEqual(set(mapping["cap-example:ba"]), expected_ba)
            self.assertEqual(set(mapping["cap-example:sa"]), expected_sa)

            second_units = [
                replace(unit, logical_source_id=unit.logical_source_id.replace("cap-example", "cap-second"))
                for unit in document_units
            ]
            large_settings = replace(
                settings, max_source_bytes=10_000_000, max_source_words=500_000
            )
            compacted_sources, compacted = module.fit_capability_sources(
                [*document_units, *second_units], large_settings, max_slots=1
            )
            self.assertTrue(compacted)
            compacted_documents = [
                (unit, f"documents/{unit.logical_source_id.replace(':', '-')}.md", "digest")
                for unit in [*document_units, *second_units]
            ]
            compacted_mapping = module._document_source_mapping(
                compacted_documents, compacted_sources, compacted
            )
            self.assertEqual(len(compacted_sources), 1)
            self.assertTrue(all(paths == [compacted_sources[0][1]] for paths in compacted_mapping.values()))

    def test_test_005_capability_manifest_and_templates_are_schema_v6(self) -> None:
        repository = Path(__file__).resolve().parents[1]
        capability_path = repository / ".agents/skills/codebase-wiki/capabilities.json"
        capability = json.loads(capability_path.read_text(encoding="utf-8"))

        self.assertEqual(capability["contract_version"], 6)
        export = capability["intents"]["notebooklm_export"]
        self.assertEqual(export["confirmation_stages"], ["discovery_plan"])
        self.assertEqual(export["audience"], "business-and-system-analyst")
        self.assertEqual(export["knowledge_contract"], "codebase-ba-sa-v1")
        assets = repository / ".agents/skills/codebase-wiki/assets"
        self.assertTrue((assets / "notebooklm-ba-template.md").is_file())
        self.assertTrue((assets / "notebooklm-sa-template.md").is_file())
        config = (assets / "notebooklm.toml").read_text(encoding="utf-8")
        self.assertIn('content_mode = "ba_sa"', config)
        self.assertIn(
            'dlp_profile = "notebooklm-enterprise-ba-sa-mask-v1"', config
        )
        validation = (repository / "docs/validation/notebooklm-ba-uat.md").read_text(
            encoding="utf-8"
        )
        self.assertIn("Static Task Tracker journey", validation)
        self.assertIn("GitHub Copilot：runtime-unverified", validation)
        self.assertIn("OpenAI Codex：runtime-unverified", validation)
        self.assertIn("程式碼優先衝突核對", validation)
        self.assertIn("繁體中文與識別碼核對", validation)


if __name__ == "__main__":
    unittest.main()
