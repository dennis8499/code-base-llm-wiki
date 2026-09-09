from __future__ import annotations

import unittest

from .test_export_notebooklm import load_canonical_exporter


def make_input(module, path: str, text: str):
    return module.InputFile(path=path, text=text, digest=module.sha256_bytes(text.encode("utf-8")))


def close_process_text(*, analysis_status: str = "traced", gap_classification: str = "none") -> str:
    return f"""---
title: 日終關帳流程
type: business-process
process_id: bp-close
coverage_status: covered
analysis_status: {analysis_status}
gap_classification: {gap_classification}
notebooklm_role: business
sources: [src/close.py]
status: active
---

# 日終關帳流程

## 業務目的與範圍

每日營業日結束時計算並保存帳務淨值。

## 角色

營運人員觸發關帳，系統服務執行檢核與寫入。

## 觸發與前置條件

收到 `POST /close`，且當日批次尚未完成；前置檢核要求所有交易已對帳。

## 主流程

| 步驟 | 觸發／條件 | 角色 | 業務處理 | 資料讀寫 | 狀態前／後 | 成功結果 | 失敗／下一步 | 來源定位 |
| --- | --- | --- | --- | --- | --- | --- | --- | --- |
| 1 | 對帳完成且收到關帳請求 | 系統服務 | 讀取當日交易並檢核完整性 | 讀取交易表、寫入檢核紀錄 | open／validated | 檢核通過 | 缺交易時阻擋並回報待補資料 | `src/close.py:10` |
| 2 | 檢核通過 | 系統服務 | 計算淨值並保存結果 | 讀取餘額、寫入淨值表 | validated／valued | 產生日終淨值 | 計算錯誤轉入失敗狀態，不更新完成時間 | `src/close.py:24` |
| 3 | 淨值保存成功 | 系統服務 | 寫入關帳完成狀態並通知下游報表 | 寫入狀態表、發送事件 | valued／closed | 下游可讀取 closed 狀態 | 事件失敗保留 closed，重試由事件佇列處理 | `src/close.py:38` |

## 替代與例外流程

交易未對帳時流程在前置檢核停止；淨值寫入逾時時保留 validated 狀態並回復未完成結果。事件發送失敗不回滾已保存的淨值。

## 業務規則

淨值必須依 br-close-net-value 規則計算；同一營業日不得重複建立 closed 結果。

## 輸入、輸出與狀態轉換

輸入為營業日與交易資料，輸出為淨值與關帳事件；狀態依 open → validated → valued → closed 過渡。

## 上下游影響

上游對帳服務提供交易完成訊號，下游報表服務依 closed 事件讀取淨值。

## 成功結果

關帳狀態為 closed、淨值已保存且下游事件已排入佇列。

## 待確認事項

Codebase 未提供證據說明人工核准角色與 SLA。
"""


RULE_TEXT = """---
title: 關帳淨值規則
type: business-rule
rule_id: br-close-net-value
coverage_status: covered
analysis_status: traced
gap_classification: none
notebooklm_role: business
applies_to: ["[[bp-close]]"]
sources: [src/close.py]
status: active
---

# 關帳淨值規則

## 規則內容

淨值等於已對帳交易的收入減支出；若存在未對帳交易，規則拒絕計算並回傳阻擋原因。

## 例外與結果

重複關帳請求不得覆寫既有 closed 結果，呼叫端收到已完成狀態。
"""


class NotebookLMFlowDepthTests(unittest.TestCase):
    def test_complete_process_and_rule_body_are_independently_materialized(self) -> None:
        module = load_canonical_exporter()
        process = make_input(module, "wiki/processes/bp-close.md", close_process_text())
        rule = make_input(module, "wiki/rules/br-close-net-value.md", RULE_TEXT)
        requirement = make_input(
            module,
            "wiki/requirements/close.md",
            """---\ntitle: 關帳需求\ntype: business-requirement\nstatus: active\nnotebooklm_role: business\napplies_to: [\"[[bp-close]]\"]\nsources: [src/close.py]\n---\n\n# 關帳需求\n\n## 需求\n系統完成檢核、淨值保存與 closed 狀態寫入。\n""",
        )
        quality = module.process_flow_quality(process)
        self.assertEqual(quality["analysis_status"], "traced")
        self.assertEqual(quality["blocking_issues"], [])

        shared = module.shared_business_context_units([process, rule, requirement])[0]
        self.assertIn("POST /close", shared.content)
        self.assertIn("讀取交易表、寫入檢核紀錄", shared.content)
        self.assertIn("淨值等於已對帳交易的收入減支出", shared.content)
        self.assertIn("系統完成檢核、淨值保存與 closed 狀態寫入", shared.content)

        integrity = module.process_source_integrity(
            [process, rule, requirement], [(shared, "shared.md", "digest")]
        )
        self.assertEqual(integrity["status"], "complete")
        self.assertEqual(integrity["embedded_requirement_count"], 1)
        self.assertEqual(integrity["embedded_rule_count"], 1)
        self.assertEqual(integrity["issues"], [])

    def test_title_only_and_four_step_summary_are_blocked(self) -> None:
        module = load_canonical_exporter()
        title_only = make_input(
            module,
            "wiki/processes/bp-title-only.md",
            """---\ntitle: 只有標題\ntype: business-process\nstatus: active\nanalysis_status: traced\ngap_classification: none\n---\n\n# 只有標題\n""",
        )
        self.assertTrue(module.process_flow_quality(title_only)["blocking_issues"])

        summary = close_process_text().replace(
            "| 1 | 對帳完成且收到關帳請求 | 系統服務 | 讀取當日交易並檢核完整性 | 讀取交易表、寫入檢核紀錄 | open／validated | 檢核通過 | 缺交易時阻擋並回報待補資料 | `src/close.py:10` |\n| 2 | 檢核通過 | 系統服務 | 計算淨值並保存結果 | 讀取餘額、寫入淨值表 | validated／valued | 產生日終淨值 | 計算錯誤轉入失敗狀態，不更新完成時間 | `src/close.py:24` |\n| 3 | 淨值保存成功 | 系統服務 | 寫入關帳完成狀態並通知下游報表 | 寫入狀態表、發送事件 | valued／closed | 下游可讀取 closed 狀態 | 事件失敗保留 closed，重試由事件佇列處理 | `src/close.py:38` |",
            "1. 檢核交易。\n2. 計算淨值。\n3. 寫入狀態。\n4. 通知下游。",
        )
        summary_page = make_input(module, "wiki/processes/bp-summary.md", summary)
        issues = module.process_flow_quality(summary_page)["blocking_issues"]
        self.assertTrue(any("step-level" in issue for issue in issues))

        missing_branch = close_process_text().replace("## 替代與例外流程", "## 未追查分支")
        missing_branch_page = make_input(module, "wiki/processes/bp-missing-branch.md", missing_branch)
        branch_issues = module.process_flow_quality(missing_branch_page)["blocking_issues"]
        self.assertTrue(any("alternate_exceptions" in issue for issue in branch_issues))

    def test_untraced_evidence_and_business_confirmation_are_distinct(self) -> None:
        module = load_canonical_exporter()
        untraced = make_input(
            module,
            "wiki/processes/bp-untraced.md",
            close_process_text(analysis_status="untraced", gap_classification="analysis-gap"),
        )
        evidence_gap = make_input(
            module,
            "wiki/processes/bp-evidence-gap.md",
            close_process_text(analysis_status="evidence-gap", gap_classification="evidence-gap"),
        )
        confirmation = make_input(
            module,
            "wiki/processes/bp-confirmation.md",
            close_process_text(
                analysis_status="business-confirmation", gap_classification="business-confirmation"
            ),
        )
        coverage = module.process_flow_coverage([untraced, evidence_gap, confirmation])
        self.assertIn(untraced.path, coverage["analysis_gaps"])
        self.assertIn(evidence_gap.path, coverage["evidence_gaps"])
        self.assertIn(confirmation.path, coverage["business_confirmation_gaps"])
        self.assertTrue(any("not completed" in issue for issue in coverage["blocking_issues"]))

    def test_final_source_integrity_rejects_title_only_payload(self) -> None:
        module = load_canonical_exporter()
        process = make_input(module, "wiki/processes/bp-close.md", close_process_text())
        rule = make_input(module, "wiki/rules/br-close-net-value.md", RULE_TEXT)
        truncated = module.Unit(
            logical_source_id="shared-business-context",
            kind="shared_business_context",
            group="business-core",
            title="共用業務詞彙與跨功能流程",
            inputs=(process, rule),
            content="# 共用業務詞彙與跨功能流程\n\n## 日終關帳流程\n",
        )
        integrity = module.process_source_integrity(
            [process, rule], [(truncated, "shared.md", "digest")]
        )
        self.assertEqual(integrity["status"], "blocked")
        self.assertTrue(any("process content missing" in issue for issue in integrity["issues"]))

    def test_title_only_related_rule_does_not_count_as_rule_body(self) -> None:
        module = load_canonical_exporter()
        process = make_input(module, "wiki/processes/bp-close.md", close_process_text())
        title_only_rule = make_input(
            module,
            "wiki/rules/br-close-net-value.md",
            """---\ntitle: 關帳淨值規則\ntype: business-rule\nstatus: active\nnotebooklm_role: business\napplies_to: [\"[[bp-close]]\"]\nsources: [src/close.py]\n---\n\n# 關帳淨值規則\n""",
        )
        shared = module.shared_business_context_units([process, title_only_rule])[0]
        integrity = module.process_source_integrity(
            [process, title_only_rule], [(shared, "shared.md", "digest")]
        )
        self.assertEqual(integrity["status"], "blocked")
        self.assertTrue(
            any("rule body has no substantive content" in issue for issue in integrity["issues"])
        )


if __name__ == "__main__":
    unittest.main()
