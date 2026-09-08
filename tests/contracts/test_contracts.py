from __future__ import annotations

import json
import re
import shutil
import subprocess
import sys
import tempfile
import tomllib
import unittest
from pathlib import Path


REPO_ROOT = Path(__file__).parents[2]


class ContractTests(unittest.TestCase):
    def test_capability_manifest_declares_installer_contract_v6(self) -> None:
        manifest = json.loads(
            (REPO_ROOT / ".agents" / "skills" / "codebase-wiki" / "capabilities.json").read_text(
                encoding="utf-8"
            )
        )

        self.assertEqual(manifest["contract_version"], 6)
        self.assertEqual(manifest["guard_modes"]["default"], "wiki-only")
        self.assertEqual(manifest["guard_modes"]["installed"], ["wiki-only", "coexist"])
        self.assertEqual(manifest["surfaces"], ["copilot", "codex"])
        self.assertIn("query", manifest["intents"])
        self.assertFalse(manifest["intents"]["query"]["writes_by_default"])
        self.assertEqual(manifest["intents"]["query"]["authorization_policy"], "read_only")
        self.assertNotIn("guide", manifest["intents"])
        self.assertNotIn("delegation", manifest["intents"])
        self.assertEqual(
            manifest["intents"]["notebooklm_export"]["authorization_policy"],
            "preview_then_confirm",
        )
        self.assertEqual(
            manifest["intents"]["notebooklm_export"]["confirmation_stages"],
            ["discovery_plan"],
        )
        self.assertEqual(
            manifest["intents"]["notebooklm_export"]["audience"],
            "business-and-system-analyst",
        )
        self.assertEqual(len(manifest["intents"]), 11)
        self.assertEqual(len(manifest["intent_groups"]), 11)
        grouped = [
            operation
            for operations in manifest["intent_groups"].values()
            for operation in operations
        ]
        self.assertEqual(len(grouped), len(set(grouped)))
        self.assertEqual(set(grouped), set(manifest["intents"]))
        for operation in (
            "adr",
            "synthesis",
            "business_analysis",
            "system_analysis",
            "system_design",
        ):
            self.assertTrue(manifest["intents"][operation]["writes_by_default"])
            self.assertFalse(manifest["intents"][operation]["requires_confirmation"])
            self.assertEqual(
                manifest["intents"][operation]["authorization_policy"],
                "explicit_request",
            )
        for surface in manifest["entrypoints"].values():
            self.assertNotIn("guide", surface)
            self.assertNotIn("delegation", surface)
        self.assertEqual(set(manifest["cli"]), {"install", "upgrade"})
        self.assertIn("install-framework.py install", manifest["cli"]["install"])
        self.assertIn("install-framework.py upgrade", manifest["cli"]["upgrade"])

    def test_current_public_docs_declare_installer_contract_v6(self) -> None:
        expected_claims = {
            "README.md": "`contract_version: 6` 維持為獨立的",
            "docs/operations/releases/README.md": "`contract_version: 6` 則是獨立的",
            "wiki/guides/release-and-update.md": (
                "`contract_version: 6` 是 installer/capability contract"
            ),
            "wiki/modules/installer-and-upgrade.md": "JSON contract version 為 6",
        }

        for relative, expected in expected_claims.items():
            with self.subTest(path=relative):
                content = (REPO_ROOT / relative).read_text(encoding="utf-8")
                self.assertIn(expected, content)

    def test_ba_sa_sd_standard_aligned_document_contract(self) -> None:
        skill_root = REPO_ROOT / ".agents" / "skills" / "codebase-wiki"
        standards = (skill_root / "references/analysis-document-standards.md").read_text(
            encoding="utf-8"
        )
        for token in (
            "business-analysis-aligned-v1",
            "system-analysis-aligned-v1",
            "system-design-aligned-v1",
            "ISO/IEC/IEEE 29148:2018",
            "IIBA Business Analysis Standard v2.0",
            "ISO/IEC/IEEE 15288:2023",
            "ISO/IEC 25010:2023",
            "ISO/IEC/IEEE 42010:2022",
            "IEEE 1016-2009",
            "informative",
            "standard-aligned",
            "不代表 conformance",
        ):
            with self.subTest(resource="standards", token=token):
                self.assertIn(token, standards)

        documents = {
            "business-analysis": {
                "profile": "business-analysis-aligned-v1",
                "default": "wiki/synthesis/business-analysis.md",
                "ids": ("cap-*", "fr-*", "bp-*", "br-*", "AC-*"),
                "mermaid": ("業務流程", "現況／目標"),
                "role": "notebooklm_role: business",
                "sections": (
                    "## 文件控制",
                    "## 標準對照矩陣",
                    "## Coverage Map",
                    "## 業務脈絡、問題與機會",
                    "## 現況／目標狀態",
                    "## 利害關係人與 Needs",
                    "## 能力、需求與驗收",
                    "## 業務流程與規則",
                    "## Business Information 與詞彙",
                    "## 成功指標與驗收方法",
                    "## 變更影響與 Transition Needs",
                    "## BA → SA 追溯矩陣",
                    "## Gap Register",
                    "## 來源附錄",
                ),
            },
            "system-analysis": {
                "profile": "system-analysis-aligned-v1",
                "default": "wiki/synthesis/system-analysis.md",
                "ids": ("SR-{SCOPE}-NNN", "NFR-{SCOPE}-NNN", "IF-{SCOPE}-NNN"),
                "mermaid": ("系統脈絡", "主要情境"),
                "role": "notebooklm_role: traceability",
                "sections": (
                    "## 文件控制",
                    "## 標準對照矩陣",
                    "## Coverage Map",
                    "## Stakeholders、Actors 與 Needs",
                    "## 系統邊界與 Context",
                    "## Use Cases 與 Operational Scenarios",
                    "## Functional System Requirements",
                    "## External Interface Requirements",
                    "## Quality Requirements",
                    "## Conceptual Information Model and Flow",
                    "## Failure and Exceptional Behavior",
                    "## Verification and Validation Needs",
                    "## BA → SA 追溯矩陣",
                    "## Gap Register",
                    "## 來源附錄",
                ),
            },
            "system-design": {
                "profile": "system-design-aligned-v1",
                "default": "wiki/synthesis/system-design.md",
                "ids": ("DE-{SCOPE}-NNN", "VIEW-{SCOPE}-{SLUG}", "ADR"),
                "mermaid": ("元件", "runtime", "資料", "部署", "安全"),
                "role": "notebooklm_role: traceability",
                "sections": (
                    "## 文件控制",
                    "## 標準對照矩陣",
                    "## Coverage Map",
                    "## Stakeholders and Concerns",
                    "## Viewpoint and View Catalog",
                    "## Architecture and Design Decisions",
                    "## Component／Static View",
                    "## Runtime View",
                    "## Data View",
                    "## Interface Design",
                    "## Deployment and Operations View",
                    "## Security View",
                    "## Quality Strategy",
                    "## Cross-view Correspondences and Consistency",
                    "## SA → SD 追溯矩陣",
                    "## Risks、Technical Debt 與 Gap Register",
                    "## 來源附錄",
                ),
            },
        }
        for name, expected in documents.items():
            workflow = (skill_root / f"references/{name}-workflow.md").read_text(
                encoding="utf-8"
            )
            template = (skill_root / f"assets/{name}-template.md").read_text(
                encoding="utf-8"
            )
            prompt = (REPO_ROOT / f".github/prompts/{name}-doc.prompt.md").read_text(
                encoding="utf-8"
            )
            combined = "\n".join((workflow, template, prompt))
            for token in (
                expected["profile"],
                expected["default"],
                "coverage_status",
                "covered",
                "partial",
                "gap",
                "Gap",
                "codebase-wiki:managed:start",
                "codebase-wiki:user-notes:start",
                "notebooklm:local-only:start",
                *expected["ids"],
                *expected["mermaid"],
            ):
                with self.subTest(document=name, token=token):
                    self.assertIn(token, combined)
            self.assertIn(expected["role"], template)
            self.assertIn(f"{{kebab-scope}}-{name}.md", workflow)
            for section in expected["sections"]:
                with self.subTest(document=name, section=section):
                    self.assertIn(section, template)
            for marker in (
                "codebase-wiki:managed:start",
                "codebase-wiki:managed:end",
                "codebase-wiki:user-notes:start",
                "codebase-wiki:user-notes:end",
                "notebooklm:local-only:start",
                "notebooklm:local-only:end",
            ):
                with self.subTest(document=name, marker=marker):
                    self.assertEqual(template.count(marker), 1)

        sa_workflow = (skill_root / "references/system-analysis-workflow.md").read_text(
            encoding="utf-8"
        )
        for token in (
            "solution-neutral",
            "不得包含技術選型",
            "不得包含部署設計",
            "legacy",
            "原正文",
            "user-notes",
        ):
            self.assertIn(token, sa_workflow)

        intent_routing = (skill_root / "references/intent-routing.md").read_text(
            encoding="utf-8"
        )
        self.assertIn("BA文件", intent_routing)
        self.assertIn("只有裸稱 `BA`", intent_routing)
        self.assertIn("NotebookLM", intent_routing)
        self.assertIn("source pack", intent_routing)

    def test_framework_ba_sa_sd_documents_preserve_layering_and_traceability(self) -> None:
        synthesis_root = REPO_ROOT / "wiki" / "synthesis"
        ba = (synthesis_root / "business-analysis.md").read_text(encoding="utf-8")
        sa = (synthesis_root / "system-analysis.md").read_text(encoding="utf-8")
        sd = (synthesis_root / "system-design.md").read_text(encoding="utf-8")

        for text, profile, role in (
            (ba, "business-analysis-aligned-v1", "notebooklm_role: business"),
            (sa, "system-analysis-aligned-v1", "notebooklm_role: traceability"),
            (sd, "system-design-aligned-v1", "notebooklm_role: traceability"),
        ):
            with self.subTest(profile=profile):
                self.assertIn(f"standards_profile: {profile}", text)
                self.assertRegex(text, r"(?m)^coverage_status: (?:covered|partial|gap)$")
                self.assertIn(role, text)
                for marker in (
                    "codebase-wiki:managed:start",
                    "codebase-wiki:managed:end",
                    "codebase-wiki:user-notes:start",
                    "codebase-wiki:user-notes:end",
                    "notebooklm:local-only:start",
                    "notebooklm:local-only:end",
                ):
                    self.assertEqual(text.count(marker), 1)
                self.assertIn("gap-analysis-doc-", text)

        for upstream in (
            "fr-analysis-business-analysis-document",
            "fr-analysis-system-analysis-document",
            "fr-analysis-system-design-document",
        ):
            self.assertIn(upstream, ba)
            self.assertIn(upstream, sa)
        for requirement in ("SR-DOC-001", "NFR-DOC-001", "IF-DOC-001"):
            self.assertIn(requirement, sa)
            self.assertIn(requirement, sd)
        for design_id in ("DE-DOC-001", "VIEW-DOC-COMPONENT"):
            self.assertIn(design_id, sd)

        sa_managed = sa.split("<!-- codebase-wiki:user-notes:start -->", 1)[0]
        self.assertNotIn("## 架構與元件", sa_managed)
        self.assertNotIn("## 設定 / 部署 / 維運", sa_managed)
        self.assertIn("## Legacy SA snapshot — non-normative", sa)
        self.assertIn("## Component／Static View", sd)
        self.assertIn("## Deployment and Operations View", sd)

    def test_high_frequency_instruction_budgets(self) -> None:
        budgets = {
            "AGENTS.md": 100,
            ".agents/skills/codebase-wiki/SKILL.md": 140,
            ".github/copilot-instructions.md": 80,
            ".github/instructions/wiki-pages.instructions.md": 60,
        }
        for relative, maximum in budgets.items():
            with self.subTest(relative=relative):
                lines = (REPO_ROOT / relative).read_text(encoding="utf-8").splitlines()
                self.assertLessEqual(len(lines), maximum)

    def test_live_database_query_capability_is_removed(self) -> None:
        removed_reference = (
            REPO_ROOT
            / ".agents"
            / "skills"
            / "codebase-wiki"
            / "references"
            / "mssql-evidence-rules.md"
        )
        self.assertFalse(removed_reference.exists())

        active_surfaces = (
            ".agents/skills/codebase-wiki/SKILL.md",
            ".agents/skills/codebase-wiki/references/intent-routing.md",
            ".agents/skills/codebase-wiki/references/query-workflow.md",
            ".agents/skills/codebase-wiki/references/synthesis-workflow.md",
            ".agents/skills/codebase-wiki/references/business-analysis-workflow.md",
            ".agents/skills/codebase-wiki/references/system-analysis-workflow.md",
            ".agents/skills/codebase-wiki/references/system-design-workflow.md",
            ".github/prompts/query-wiki.prompt.md",
            ".github/prompts/business-analysis-doc.prompt.md",
            ".github/prompts/system-analysis-doc.prompt.md",
            ".github/prompts/system-design-doc.prompt.md",
            "AGENTS.md",
            "Codex.md",
            "README.md",
            "docs/product/architecture/README.md",
            "docs/operations/validation/README.md",
            "docs/product/workflows/README.md",
            "wiki/guides/framework-introduction.md",
            "wiki/synthesis/project-function-catalog.md",
            "wiki/synthesis/business-analysis.md",
            "wiki/synthesis/system-analysis.md",
            "wiki/synthesis/system-design.md",
        )
        enablement_tokens = (
            "mssql",
            "sql server live evidence",
            "sql query",
            "sql queries",
            "bounded read-only `select`",
            "db live evidence",
            "db evidence",
            "database evidence block",
            "database evidence is needed",
            "exposes sql server",
            "schema discovery",
            "metadata discovery",
        )
        for relative in active_surfaces:
            with self.subTest(surface=relative):
                text = (REPO_ROOT / relative).read_text(encoding="utf-8").lower()
                for token in enablement_tokens:
                    self.assertNotIn(token, text)

        boundaries = {
            ".agents/skills/codebase-wiki/references/query-workflow.md": (
                "must not connect to",
                "current database state",
            ),
        }
        for relative, required_tokens in boundaries.items():
            text = (REPO_ROOT / relative).read_text(encoding="utf-8").lower()
            for token in required_tokens:
                with self.subTest(surface=relative, token=token):
                    self.assertIn(token.lower(), text)

    def test_workflows_and_templates_have_single_authoritative_resources(self) -> None:
        reference_root = (
            REPO_ROOT / ".agents" / "skills" / "codebase-wiki" / "references"
        )
        for filename in (
            "ingest-workflow.md",
            "query-workflow.md",
            "follow-up-actions.md",
            "lint-checklist.md",
            "adr-workflow.md",
            "synthesis-workflow.md",
            "business-analysis-workflow.md",
            "system-analysis-workflow.md",
            "system-design-workflow.md",
            "code-archaeology-workflow.md",
            "notebooklm-export-workflow.md",
        ):
            with self.subTest(workflow=filename):
                text = (reference_root / filename).read_text(encoding="utf-8")
                self.assertRegex(text, r"Completion Criterion|完成條件")

        catalog = (reference_root / "page-types.md").read_text(encoding="utf-8")
        assets = re.findall(r"`assets/([a-z-]+-template\.md)`", catalog)
        self.assertEqual(len(assets), len(set(assets)))
        for filename in assets:
            with self.subTest(asset=filename):
                self.assertTrue(
                    (
                        REPO_ROOT
                        / ".agents"
                        / "skills"
                        / "codebase-wiki"
                        / "assets"
                        / filename
                    ).is_file()
                )
        self.assertFalse((reference_root / "guide-workflow.md").exists())
        self.assertFalse(
            (
                REPO_ROOT
                / ".agents"
                / "skills"
                / "codebase-wiki"
                / "assets"
                / "guide-template.md"
            ).exists()
        )
        self.assertRegex(catalog, r"(?im)^\|\s*`guide`.*(?:legacy|read-only|唯讀)")
        self.assertNotIn("`assets/guide-template.md`", catalog)

    def test_follow_up_action_contract_is_shared_by_both_surfaces(self) -> None:
        skill_root = REPO_ROOT / ".agents" / "skills" / "codebase-wiki"
        contract = (skill_root / "references" / "follow-up-actions.md").read_text(
            encoding="utf-8"
        )
        for token in (
            "save-synthesis",
            "reingest",
            "lint",
            "暫不處理",
            "Completion Criterion",
        ):
            self.assertIn(token, contract)
        self.assertNotIn("save-guide", contract)

        adapters = (
            REPO_ROOT / ".github" / "prompts" / "query-wiki.prompt.md",
            REPO_ROOT / ".github" / "prompts" / "lint-wiki.prompt.md",
            REPO_ROOT / "Codex.md",
        )
        for path in adapters:
            with self.subTest(adapter=path.relative_to(REPO_ROOT).as_posix()):
                text = path.read_text(encoding="utf-8")
                self.assertIn("follow-up-actions.md", text)

    def test_notebooklm_contract_requires_full_scan_and_preflight(self) -> None:
        skill_root = REPO_ROOT / ".agents" / "skills" / "codebase-wiki"
        workflow = (skill_root / "references" / "notebooklm-export-workflow.md").read_text(
            encoding="utf-8"
        )
        prompt = (REPO_ROOT / ".github" / "prompts" / "export-notebooklm.prompt.md").read_text(
            encoding="utf-8"
        )

        for text in (workflow, prompt):
            self.assertIn("--preflight", text)
            self.assertIn("notebooklm_group", text)
        self.assertIn("full safe project", workflow.lower())
        self.assertRegex(prompt, r"全專案|整個專案")
        self.assertIn("codebase-ba-sa-retrieval-v1", workflow)
        self.assertIn("codebase-ba-sa-v1", workflow)
        self.assertIn("business_source_paths", workflow)
        self.assertIn("analysis_include_tests", workflow)
        self.assertIn("codebase-functional-coverage.md", workflow)
        self.assertIn("notebooklm-enterprise-ba-sa-mask-v1", workflow)
        self.assertIn("500 MB", workflow)
        self.assertIn("discovery_id", workflow)
        self.assertIn("一次確認", prompt)
        self.assertNotIn("第二次確認", prompt)
        self.assertTrue((skill_root / "scripts" / "notebooklm_exporter.py").is_file())
        for template in (
            "business-process-template.md",
            "business-requirement-template.md",
            "business-rule-template.md",
            "functional-requirement-catalog-template.md",
            "business-process-catalog-template.md",
            "business-rule-catalog-template.md",
            "business-glossary-template.md",
            "business-knowledge-gaps-template.md",
            "codebase-functional-coverage-template.md",
            "notebooklm-ba-template.md",
            "notebooklm-sa-template.md",
        ):
            self.assertTrue((skill_root / "assets" / template).is_file())

    def test_validation_and_release_are_local_manual_workflows(self) -> None:
        workflow_root = REPO_ROOT / ".github" / "workflows"
        self.assertEqual(list(workflow_root.glob("*.yml")), [])
        self.assertEqual(list(workflow_root.glob("*.yaml")), [])

        validation = (REPO_ROOT / "docs" / "operations" / "validation" / "README.md").read_text(
            encoding="utf-8"
        )
        for token in (
            "python -m unittest discover -s tests -v",
            "parity-check.py",
            "validate-frontmatter.py wiki",
            "check-stale.py wiki .",
            "validate-log.py wiki/log.md --repo-root .",
            "rebuild-index.py wiki --check",
            "lint-wiki.py wiki --repo-root .",
        ):
            with self.subTest(document="validation", token=token):
                self.assertIn(token, validation)

        release = (REPO_ROOT / "docs" / "operations" / "releases" / "README.md").read_text(
            encoding="utf-8"
        )
        for token in (
            "python tools/release.py validate --tag",
            "python tools/release.py build --output dist",
            "gh release create",
            "dist/codebase-llm-wiki.zip",
            "dist/codebase-llm-wiki.tar.gz",
            "dist/update-manifest.json",
            "dist/SHA256SUMS",
        ):
            with self.subTest(document="release", token=token):
                self.assertIn(token, release)

    def test_system_analysis_prompt_preserves_source_schema_boundary(self) -> None:
        prompt = (
            REPO_ROOT / ".github" / "prompts" / "system-analysis-doc.prompt.md"
        ).read_text(encoding="utf-8")
        self.assertIn("raw source 路徑", prompt)
        self.assertIn("derived_from", prompt)
        self.assertIn("sources: []", prompt)
        self.assertNotIn("wiki/source 路徑", prompt)

    def test_copilot_prompts_bind_authoritative_workflows_and_completion_coupling(self) -> None:
        prompts = {
            "ingest-module.prompt.md": (
                "references/ingest-workflow.md",
                "等待確認",
                "index.md",
                "log.md",
            ),
            "ingest-batch.prompt.md": (
                "references/ingest-workflow.md",
                "Batch Ingest",
                "index.md",
                "log.md",
            ),
            "query-wiki.prompt.md": (
                "references/query-workflow.md",
                "references/follow-up-actions.md",
                "1–5",
                "零寫入",
            ),
            "lint-wiki.prompt.md": (
                "references/lint-checklist.md",
                "references/follow-up-actions.md",
                "先回報",
                "未經確認不得修復",
            ),
            "code-archaeology.prompt.md": (
                "references/code-archaeology-workflow.md",
                "git log",
                "語意 inbound",
                "wiki/index.md",
                "wiki/log.md",
            ),
            "new-adr.prompt.md": (
                "references/adr-workflow.md",
                "references/frontmatter-spec.md",
                "wiki/index.md",
                "wiki/log.md",
            ),
            "save-synthesis.prompt.md": (
                "references/synthesis-workflow.md",
                "references/frontmatter-spec.md",
                "wiki/index.md",
                "wiki/log.md",
            ),
            "business-analysis-doc.prompt.md": (
                "references/business-analysis-workflow.md",
                "assets/business-analysis-template.md",
                "wiki/index.md",
                "wiki/log.md",
            ),
            "system-analysis-doc.prompt.md": (
                "references/system-analysis-workflow.md",
                "assets/system-analysis-template.md",
                "wiki/index.md",
                "wiki/log.md",
            ),
            "system-design-doc.prompt.md": (
                "references/system-design-workflow.md",
                "assets/system-design-template.md",
                "wiki/index.md",
                "wiki/log.md",
            ),
            "export-notebooklm.prompt.md": (
                "references/notebooklm-export-workflow.md",
                "--preflight",
                "--apply",
                "等待使用者確認",
            ),
        }
        for filename, required_tokens in prompts.items():
            text = (REPO_ROOT / ".github" / "prompts" / filename).read_text(
                encoding="utf-8"
            )
            for token in required_tokens:
                with self.subTest(prompt=filename, token=token):
                    self.assertIn(token, text)

    def test_copilot_prompt_metadata_uses_builtin_agent(self) -> None:
        self.assertEqual(list((REPO_ROOT / ".github" / "agents").glob("*.agent.md")), [])
        for path in (REPO_ROOT / ".github" / "prompts").glob("*.prompt.md"):
            with self.subTest(prompt=path.name):
                text = path.read_text(encoding="utf-8")
                expected_name = path.name.removesuffix(".prompt.md")
                self.assertRegex(text, rf"(?m)^name:\s*[\"']?{re.escape(expected_name)}[\"']?\s*$")
                self.assertRegex(text, r"(?m)^description:\s*\S+")
                agent = re.search(r"(?m)^agent:\s*[\"']?([^\"'\s]+)", text)
                self.assertIsNotNone(agent)
                self.assertEqual(agent.group(1), "agent")
                self.assertRegex(
                    text,
                    r"(?m)^argument-hint:\s*(?:\"[^\"]+\"|'[^']+'|\S.*)$",
                )

    def test_entrypoint_coverage_matrix_includes_codex_recipes(self) -> None:
        manifest = json.loads(
            (REPO_ROOT / ".agents/skills/codebase-wiki/capabilities.json").read_text(
                encoding="utf-8"
            )
        )
        prompt_root = REPO_ROOT / ".github/prompts"
        mapped_prompts: set[str] = set()
        for operation, entry in manifest["entrypoints"]["copilot"].items():
            with self.subTest(operation=operation):
                for filename in entry:
                    mapped_prompts.add(filename)
                    self.assertTrue((prompt_root / filename).is_file())

        self.assertEqual(
            {
                path.name
                for path in prompt_root.glob("*.prompt.md")
            } - mapped_prompts,
            {"update-index.prompt.md"},
        )
        codex_recipe = (REPO_ROOT / "Codex.md").read_text(encoding="utf-8")
        for filename in mapped_prompts:
            with self.subTest(recipe=filename):
                self.assertIn(f"/{filename.removesuffix('.prompt.md')}", codex_recipe)
        self.assertIn("/update-index", codex_recipe)

        update_index = (prompt_root / "update-index.prompt.md").read_text(
            encoding="utf-8"
        )
        self.assertIn("rebuild-index.py", update_index)
        self.assertIn("wiki/log.md", update_index)

    def test_path_based_cli_scripts_expose_help(self) -> None:
        scripts = (
            "check-stale.py",
            "validate-frontmatter.py",
            "wiki-stats.py",
        )
        script_root = REPO_ROOT / ".agents/skills/codebase-wiki/scripts"
        for filename in scripts:
            with self.subTest(script=filename):
                result = subprocess.run(
                    [sys.executable, str(script_root / filename), "--help"],
                    check=False,
                    capture_output=True,
                    text=True,
                    encoding="utf-8",
                )
                self.assertEqual(result.returncode, 0, result.stderr)
                self.assertIn("usage:", result.stdout.lower())

    def test_framework_notebooklm_preflight_is_ready(self) -> None:
        script = (
            REPO_ROOT
            / ".agents/skills/codebase-wiki/scripts/export-notebooklm.py"
        )
        result = subprocess.run(
            [
                sys.executable,
                str(script),
                "--root",
                str(REPO_ROOT),
                "--preflight",
                "--format",
                "json",
            ],
            check=False,
            capture_output=True,
            text=True,
            encoding="utf-8",
        )
        self.assertEqual(result.returncode, 0, result.stderr)
        payload = json.loads(result.stdout)
        self.assertTrue(payload["ready_to_export"], payload)
        self.assertEqual(payload["scan_profile"], "framework")
        included = {item["path"] for item in payload["inventory"]["included"]}
        self.assertIn(
            ".agents/skills/codebase-wiki/scripts/notebooklm_exporter.py", included
        )
        self.assertIn(payload["coverage"]["status"], {"complete", "partial"})
        self.assertIn("uncovered_count", payload["coverage"])

    def test_codex_config_has_no_framework_agent_fanout(self) -> None:
        config = tomllib.loads(
            (REPO_ROOT / ".codex/config.toml").read_text(encoding="utf-8")
        )
        self.assertNotIn("agents", config)

    def test_repo_custom_agent_profiles_are_absent(self) -> None:
        for directory, pattern in (
            (REPO_ROOT / ".codex" / "agents", "*.toml"),
            (REPO_ROOT / ".github" / "agents", "*.agent.md"),
        ):
            with self.subTest(directory=directory.relative_to(REPO_ROOT).as_posix()):
                self.assertEqual(list(directory.glob(pattern)), [])

    def test_parity_allows_unrelated_platform_native_agents(self) -> None:
        with tempfile.TemporaryDirectory() as directory:
            target = Path(directory) / "repo"
            shutil.copytree(
                REPO_ROOT,
                target,
                ignore=shutil.ignore_patterns(".git", "__pycache__", "*.pyc"),
            )
            copilot_agent = target / ".github" / "agents" / "project-review.agent.md"
            codex_agent = target / ".codex" / "agents" / "project-review.toml"
            copilot_agent.parent.mkdir(parents=True, exist_ok=True)
            codex_agent.parent.mkdir(parents=True, exist_ok=True)
            copilot_agent.write_text(
                "---\nname: project-review\ndescription: Project-native reviewer\n"
                "tools: [read, search]\n---\nReview this project.\n",
                encoding="utf-8",
            )
            codex_agent.write_text(
                'sandbox_mode = "read-only"\n'
                'developer_instructions = "Review this project."\n',
                encoding="utf-8",
            )
            config_path = target / ".codex" / "config.toml"
            config = config_path.read_text(encoding="utf-8")
            if "[agents]" not in config:
                config += "\n[agents]\nmax_concurrent_threads_per_session = 2\n"
                config_path.write_text(config, encoding="utf-8")

            result = subprocess.run(
                [
                    sys.executable,
                    str(
                        target
                        / ".agents"
                        / "skills"
                        / "codebase-wiki"
                        / "scripts"
                        / "parity-check.py"
                    ),
                ],
                cwd=target,
                capture_output=True,
                text=True,
                encoding="utf-8",
                check=False,
            )

            self.assertEqual(result.returncode, 0, result.stdout + result.stderr)

    def test_removed_guide_creator_resources_are_absent(self) -> None:
        for relative in (
            ".agents/skills/codebase-wiki/references/guide-workflow.md",
            ".agents/skills/codebase-wiki/assets/guide-template.md",
            ".github/prompts/onboarding-guide.prompt.md",
            ".github/prompts/save-guide.prompt.md",
        ):
            with self.subTest(relative=relative):
                self.assertFalse((REPO_ROOT / relative).exists())

        exporter = (
            REPO_ROOT
            / ".agents"
            / "skills"
            / "codebase-wiki"
            / "scripts"
            / "notebooklm_exporter.py"
        ).read_text(encoding="utf-8")
        self.assertIn('if page_type == "guide":', exporter)
        self.assertIn('return "project-guides"', exporter)


if __name__ == "__main__":
    unittest.main()
