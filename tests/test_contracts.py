from __future__ import annotations

import json
import re
import subprocess
import sys
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
        self.assertIn("Documentation is mandatory", workflow)
        self.assertIn("before evidence", workflow)
        self.assertTrue((skill_root / "scripts" / "notebooklm_exporter.py").is_file())
        self.assertTrue(
            (skill_root / "assets" / "project-function-catalog-template.md").is_file()
        )

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
