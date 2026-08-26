from __future__ import annotations

import json
import re
import subprocess
import sys
import tomllib
import unittest
from pathlib import Path


REPO_ROOT = Path(__file__).parents[1]


class ContractTests(unittest.TestCase):
    def test_capability_manifest_declares_installer_contract_v3(self) -> None:
        manifest = json.loads(
            (REPO_ROOT / ".agents" / "skills" / "codebase-wiki" / "capabilities.json").read_text(
                encoding="utf-8"
            )
        )

        self.assertEqual(manifest["contract_version"], 3)
        self.assertEqual(manifest["guard_modes"]["default"], "wiki-only")
        self.assertEqual(manifest["guard_modes"]["installed"], ["wiki-only", "coexist"])
        self.assertEqual(manifest["surfaces"], ["copilot", "codex"])
        self.assertIn("query", manifest["intents"])
        self.assertFalse(manifest["intents"]["query"]["writes_by_default"])
        self.assertEqual(manifest["intents"]["query"]["authorization_policy"], "read_only")
        self.assertEqual(manifest["intents"]["delegation"]["authorization_policy"], "explicit_delegation")
        self.assertEqual(
            manifest["intents"]["notebooklm_export"]["authorization_policy"],
            "preview_then_confirm",
        )
        self.assertEqual(
            manifest["intents"]["notebooklm_export"]["confirmation_stages"],
            ["discovery_plan", "readiness_apply"],
        )
        self.assertEqual(
            manifest["intents"]["notebooklm_export"]["audience"],
            "business-analyst",
        )
        self.assertEqual(len(manifest["intents"]), 11)
        self.assertEqual(len(manifest["intent_groups"]), 10)
        grouped = [
            operation
            for operations in manifest["intent_groups"].values()
            for operation in operations
        ]
        self.assertEqual(len(grouped), len(set(grouped)))
        self.assertEqual(set(grouped), set(manifest["intents"]))
        for operation in ("adr", "guide", "synthesis", "system_analysis"):
            self.assertTrue(manifest["intents"][operation]["writes_by_default"])
            self.assertFalse(manifest["intents"][operation]["requires_confirmation"])
            self.assertEqual(
                manifest["intents"][operation]["authorization_policy"],
                "explicit_request",
            )
        self.assertFalse(manifest["intents"]["delegation"]["requires_confirmation"])
        self.assertEqual(set(manifest["cli"]), {"install", "upgrade"})
        self.assertIn("install-framework.py install", manifest["cli"]["install"])
        self.assertIn("install-framework.py upgrade", manifest["cli"]["upgrade"])

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
            "guide-workflow.md",
            "synthesis-workflow.md",
            "system-analysis-workflow.md",
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

    def test_follow_up_action_contract_is_shared_by_both_surfaces(self) -> None:
        skill_root = REPO_ROOT / ".agents" / "skills" / "codebase-wiki"
        contract = (skill_root / "references" / "follow-up-actions.md").read_text(
            encoding="utf-8"
        )
        for token in (
            "save-synthesis",
            "save-guide",
            "reingest",
            "lint",
            "暫不處理",
            "Completion Criterion",
        ):
            self.assertIn(token, contract)

        adapters = (
            REPO_ROOT / ".github" / "prompts" / "query-wiki.prompt.md",
            REPO_ROOT / ".github" / "prompts" / "lint-wiki.prompt.md",
            REPO_ROOT / ".github" / "agents" / "wiki-query.agent.md",
            REPO_ROOT / ".github" / "agents" / "wiki-lint.agent.md",
            REPO_ROOT / ".codex" / "agents" / "wiki-query.toml",
            REPO_ROOT / ".codex" / "agents" / "wiki-lint.toml",
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
        self.assertIn("business-only-ba-v2", workflow)
        self.assertIn("business-functional-requirements-v2", workflow)
        self.assertIn("business_source_paths", workflow)
        self.assertIn("analysis_include_tests", workflow)
        self.assertIn("codebase-functional-coverage.md", workflow)
        self.assertIn("notebooklm-enterprise-ba-mask-v1", workflow)
        self.assertIn("500 MB", workflow)
        self.assertIn("second readiness preflight", workflow)
        self.assertIn("第二次確認", prompt)
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
        ):
            self.assertTrue((skill_root / "assets" / template).is_file())

    def test_ci_and_release_workflows_bind_runtime_and_release_gates(self) -> None:
        ci = (REPO_ROOT / ".github/workflows/ci.yml").read_text(encoding="utf-8")
        self.assertRegex(ci, r"os:\s+ubuntu-latest\s+python:\s+\"3\.11\"")
        self.assertRegex(ci, r"os:\s+ubuntu-latest\s+python:\s+\"3\.14\"")
        self.assertRegex(ci, r"os:\s+windows-latest\s+python:\s+\"3\.11\"")
        for token in (
            "python -m unittest discover -s tests -v",
            "parity-check.py",
            "validate-frontmatter.py wiki",
            "check-stale.py wiki .",
            "validate-log.py wiki/log.md --repo-root .",
            "rebuild-index.py wiki --check",
            "lint-wiki.py wiki --repo-root .",
        ):
            with self.subTest(workflow="ci", token=token):
                self.assertIn(token, ci)

        release = (REPO_ROOT / ".github/workflows/release.yml").read_text(encoding="utf-8")
        self.assertIn('python-version: "3.11"', release)
        for token in (
            "python tools/release.py validate --tag",
            "python tools/release.py build --output dist",
            "gh release create",
        ):
            with self.subTest(workflow="release", token=token):
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
                "1-5",
                "不寫檔",
            ),
            "lint-wiki.prompt.md": (
                "references/lint-checklist.md",
                "references/follow-up-actions.md",
                "先回報 findings",
                "確認後",
            ),
            "code-archaeology.prompt.md": (
                "references/code-archaeology-workflow.md",
                "git log",
                "wiki/index.md",
                "wiki/log.md",
            ),
            "new-adr.prompt.md": (
                "references/adr-workflow.md",
                "references/frontmatter-spec.md",
                "wiki/index.md",
                "wiki/log.md",
            ),
            "onboarding-guide.prompt.md": (
                "references/guide-workflow.md",
                "assets/guide-template.md",
                "wiki/index.md",
                "wiki/log.md",
            ),
            "save-guide.prompt.md": (
                "references/guide-workflow.md",
                "wiki/index.md",
                "wiki/log.md",
                "derived_from",
            ),
            "save-synthesis.prompt.md": (
                "references/synthesis-workflow.md",
                "references/frontmatter-spec.md",
                "wiki/index.md",
                "wiki/log.md",
            ),
            "system-analysis-doc.prompt.md": (
                "references/system-analysis-workflow.md",
                "assets/system-analysis-template.md",
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

    def test_codex_config_and_read_only_agents_use_current_contract(self) -> None:
        config = tomllib.loads(
            (REPO_ROOT / ".codex/config.toml").read_text(encoding="utf-8")
        )
        agents = config["agents"]
        self.assertEqual(agents["max_concurrent_threads_per_session"], 6)
        self.assertNotIn("max_threads", agents)
        for name in ("wiki-query", "wiki-lint", "wiki-archaeologist"):
            agent = tomllib.loads(
                (REPO_ROOT / ".codex/agents" / f"{name}.toml").read_text(encoding="utf-8")
            )
            self.assertEqual(agent["sandbox_mode"], "read-only")

    def test_copilot_read_only_agents_restrict_direct_mutation_and_handoff(self) -> None:
        expected = {
            "wiki-query.agent.md": {"read", "search"},
            "wiki-lint.agent.md": {"execute", "read", "search"},
            "wiki-archaeologist.agent.md": {"execute", "read", "search"},
        }
        for filename, tools in expected.items():
            with self.subTest(agent=filename):
                text = (REPO_ROOT / ".github" / "agents" / filename).read_text(
                    encoding="utf-8"
                )
                match = re.search(r"(?m)^tools:\s*\[([^]]*)\]\s*$", text)
                self.assertIsNotNone(match)
                actual = {
                    item.strip().strip("\"'")
                    for item in match.group(1).split(",")
                    if item.strip()
                }
                self.assertEqual(actual, tools)
                self.assertNotIn("edit", actual)
                self.assertNotIn("agent", actual)

    def test_agents_are_explicit_delegation_only_and_compact(self) -> None:
        for directory, pattern in (
            (REPO_ROOT / ".codex" / "agents", "*.toml"),
            (REPO_ROOT / ".github" / "agents", "*.agent.md"),
        ):
            for path in directory.glob(pattern):
                with self.subTest(agent=path.name):
                    text = path.read_text(encoding="utf-8")
                    self.assertIn("Explicit delegation only.", text)
                    self.assertLessEqual(len(text.splitlines()), 40)


if __name__ == "__main__":
    unittest.main()
