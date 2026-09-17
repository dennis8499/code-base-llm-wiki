from __future__ import annotations

import json
import unittest
from pathlib import Path


REPO_ROOT = Path(__file__).parents[2]
SKILL_ROOT = REPO_ROOT / ".agents" / "skills" / "codebase-wiki"
FIXTURE_ROOT = REPO_ROOT / "tests" / "fixtures" / "code-audit"


class CodeAuditContractTests(unittest.TestCase):
    def test_audit_is_a_persisting_static_intent_outside_tgrep(self) -> None:
        manifest = json.loads((SKILL_ROOT / "capabilities.json").read_text(encoding="utf-8"))
        audit = manifest["intents"]["code_audit"]
        self.assertEqual(
            audit,
            {
                "writes_by_default": True,
                "requires_confirmation": False,
                "authorization_policy": "explicit_request",
                "checks": [
                    "transaction_consistency",
                    "configuration_reference_consistency",
                    "logic_state_consistency",
                    "change_regression",
                ],
                "finding_classes": ["BUG", "RISK", "BIZ"],
                "history": {
                    "mode": "current_first_targeted",
                    "commands": ["git log", "git show", "git blame"],
                    "read_only": True,
                },
                "report_validator": ".agents/skills/codebase-wiki/scripts/validate-code-audit.py",
            },
        )
        self.assertEqual(manifest["intent_groups"]["code_audit"], ["code_audit"])
        self.assertEqual(
            manifest["entrypoints"]["copilot"]["code_audit"],
            ["code-audit.prompt.md"],
        )
        self.assertEqual(
            manifest["integrations"]["source_discovery"]["operations"],
            ["ingest", "archaeology"],
        )

        workflow = (SKILL_ROOT / "references" / "code-audit-workflow.md").read_text(
            encoding="utf-8"
        )
        normalized_workflow = " ".join(workflow.split())
        for required in (
            "Do not run the target application",
            "checked",
            "partial",
            "not checked",
            "Confirmed defect (`BUG-*`)",
            "Technical risk (`RISK-*`)",
            "Business question (`BIZ-*`)",
            "upstream validation and downstream constraints",
            "Transactions and side effects",
            "Configuration references",
            "Logic and state contracts",
            "Change completeness",
            "git show --format=fuller --stat --patch",
            "complete body",
            "uncommitted changes",
            "preserve its original record",
            "separate Archaeology report",
            "Preserve the prior ID",
            "user-notes markers",
            "synthesis` entry",
        ):
            with self.subTest(required=required):
                self.assertIn(required, normalized_workflow)
        self.assertIn("只回報", workflow)
        self.assertIn("Do not use the optional tgrep wrapper", workflow)

    def test_prompt_and_template_define_the_shared_output_contract(self) -> None:
        prompt = (REPO_ROOT / ".github" / "prompts" / "code-audit.prompt.md").read_text(
            encoding="utf-8"
        )
        self.assertIn("code-audit-workflow.md", prompt)
        self.assertIn("code-audit-template.md", prompt)
        self.assertIn("保持 Wiki、index、log 零寫入", prompt)
        for required in (
            "git log --follow",
            "git show --format=fuller --stat --patch",
            "transaction／connection",
            "設定檔／鍵引用",
            "RISK-*",
            "validate-code-audit.py",
        ):
            with self.subTest(prompt_token=required):
                self.assertIn(required, prompt)

        template = (SKILL_ROOT / "assets" / "code-audit-template.md").read_text(
            encoding="utf-8"
        )
        for required in (
            "## 入口覆蓋",
            "## 靜態交叉檢查",
            "## Git 歷史與變更線索",
            "## 確定缺陷",
            "## 技術風險",
            "## 待確認業務疑點",
            "## 未完成工作與驗證建議",
            "證據確定度",
            "已核對防護／反證",
            "關聯欄位連結",
            "影響程度",
            "source_digest: \"sha256:",
            "歷史索引限制",
            "<!-- codebase-wiki:managed:start -->",
            "<!-- codebase-wiki:user-notes:start -->",
            "notebooklm_role: exclude",
            "BUG-001",
            "RISK-001",
            "BIZ-001",
        ):
            with self.subTest(required=required):
                self.assertIn(required, template)

    def test_fixture_covers_shared_root_cause_policy_gap_guard_and_dynamic_entry(self) -> None:
        expected = (FIXTURE_ROOT / "expected-findings.md").read_text(encoding="utf-8")
        normalized_expected = " ".join(expected.split())
        for required in (
            "2 confirmed defects",
            "BUG-001",
            "BUG-002",
            "explicitly forbids cancellation while an unpaid invoice exists",
            "BIZ-001",
            "validates positive quantity before calling the service",
            "Partial coverage",
        ):
            with self.subTest(required=required):
                self.assertIn(required, normalized_expected)

        source_paths = (
            "src/api/orders.py",
            "src/cli/orders.py",
            "src/services/orders.py",
            "src/data/orders.py",
            "src/api/accounts.py",
            "src/services/accounts.py",
            "src/api/checkout.py",
            "src/api/returns.py",
            "src/services/returns.py",
            "src/plugins/loader.py",
            "docs/business-rules.md",
        )
        for relative in source_paths:
            with self.subTest(source=relative):
                self.assertTrue((FIXTURE_ROOT / relative).is_file())

        summary = (FIXTURE_ROOT / "src" / "services" / "orders.py").read_text(
            encoding="utf-8"
        )
        self.assertIn("order.total / order.line_count", summary)
        api = (FIXTURE_ROOT / "src" / "api" / "checkout.py").read_text(
            encoding="utf-8"
        )
        self.assertIn("if quantity <= 0:", api)
        dynamic_loader = (FIXTURE_ROOT / "src" / "plugins" / "loader.py").read_text(
            encoding="utf-8"
        )
        self.assertIn("importlib.import_module(module_name)", dynamic_loader)

    def test_history_fixture_covers_transaction_configuration_and_contract_regressions(self) -> None:
        history = FIXTURE_ROOT / "history"
        expected = (history / "expected-findings.md").read_text(encoding="utf-8")
        normalized = " ".join(expected.split())
        for required in (
            "BUG-*",
            "config/payment.yml",
            "post-commit notification rule",
            "full commit SHA",
            "complete body",
            "current source",
            "rename",
            "follow-up",
            "dirty worktree",
            "history is incomplete",
            "valid transaction contrast",
            "fallback",
            "swallows a ledger exception",
            "idempotency rules",
            "missing framework evidence",
            "shared root cause",
            "continue finding IDs",
            "preserve the user-notes block",
            "classification changes",
        ):
            with self.subTest(required=required):
                self.assertIn(required, normalized)
        for relative in (
            "README.md",
            "expected-findings.md",
            "config/payment.yml",
            "docs/payment-rules.md",
            "src/config_loader.py",
            "src/payments.py",
            "src/refund_cli.py",
            "src/refunds.py",
            "src/legacy_settlement.py",
            "src/transaction_cases.py",
            "src/framework_managed.py",
            "src/config_fallback.py",
            "src/state_cases.py",
            "src/unknown_boundary.py",
            "deploy/payment.env.example",
        ):
            with self.subTest(source=relative):
                self.assertTrue((history / relative).is_file())
        self.assertIn("with db.transaction()", (history / "src/payments.py").read_text(encoding="utf-8"))
        self.assertIn("CONFIG_PATH", (history / "src/config_loader.py").read_text(encoding="utf-8"))
        self.assertIn("reason: str", (history / "src/refunds.py").read_text(encoding="utf-8"))
        legacy = (history / "src/legacy_settlement.py").read_text(encoding="utf-8")
        self.assertLess(legacy.index("db.transaction"), legacy.index("notifier.send"))
        transaction_cases = (history / "src/transaction_cases.py").read_text(encoding="utf-8")
        self.assertIn("except Exception", transaction_cases)
        self.assertIn("transaction.commit()", transaction_cases)
        self.assertIn("@db.transactional", (history / "src/framework_managed.py").read_text(encoding="utf-8"))
        self.assertIn("generated_defaults", (history / "src/config_fallback.py").read_text(encoding="utf-8"))
        state_cases = (history / "src/state_cases.py").read_text(encoding="utf-8")
        self.assertIn('return {"status": "completed"}', state_cases)
        self.assertEqual(state_cases.count("db.insert_payment(payment.id)"), 2)
        self.assertIn("notifier.send", (history / "src/unknown_boundary.py").read_text(encoding="utf-8"))


if __name__ == "__main__":
    unittest.main()
