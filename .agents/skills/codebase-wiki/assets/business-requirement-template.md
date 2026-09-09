---
title: "{功能需求名稱}"
type: business-requirement
summary: "{哪個角色在什麼條件下需要系統提供什麼可觀察結果}"
requirement_id: "fr-{domain}-{capability}"
capability_id: "cap-{domain}-{capability}"
applies_to: ["[[{business-process-page}]]"]
evidence_state: implementation-observed
notebooklm_group: "business-{capability-slug}"
notebooklm_role: business
notebooklm_terms: ["{功能名稱}", "{角色}", "{業務結果}"]
analysis_status: untraced
gap_classification: analysis-gap
sources:
  - "{path/to/implementation-evidence}"
derived_from: ["[[overview]]", "[[{business-process-page}]]"]
source_digest: "sha256:{64-lowercase-hex}"
last_updated: YYYY-MM-DD
tags: [business-requirement, notebooklm]
status: active
---

# {功能需求名稱}

<!-- codebase-wiki:managed:start -->
## 分析狀態與缺口分類

| 欄位 | 值 |
| --- | --- |
| Evidence trace | `untraced`／`traced` |
| Gap classification | `analysis-gap`／`evidence-gap`／`business-confirmation`／`none` |

完成需求分析前，須把入口、條件、主流程、例外、資料／狀態與可驗收結果逐一追查；
營運政策或權限若只需要外部確認，保留已知 implementation-observed 行為並標成
`business-confirmation`。

## 業務目的

## 角色與權限

## 前置條件

## 功能行為

| 情境 | 系統行為 | 可觀察結果 | 證據狀態 |
| --- | --- | --- | --- |
| {scenario} | {behavior} | {outcome} | business-confirmed / implementation-observed / inference / gap |

## 完整流程與失敗分支

| 步驟 | 觸發／前置條件 | 行為與資料變更 | 狀態前後值 | 成功結果 | 例外／重跑 | 證據狀態／locator |
| --- | --- | --- | --- | --- | --- | --- |
| 1 | {condition} | {observable action} | {before → after} | {result} | {failure branch} | {state} / {path:line} |

## 業務規則與例外

- [[{business-rule-page}]]

## 輸入、輸出與狀態

## 驗收條件

- `AC-{DOMAIN}-{NNN}`：Given {context}，When {action}，Then {observable-result}。

## 關聯流程

- [[{business-process-page}]]

## 待確認事項

- `gap-{domain}-{topic}`：{question}
<!-- codebase-wiki:managed:end -->

<!-- codebase-wiki:user-notes:start -->
## BA 補充註記

<!-- 保留人工維護內容；重新萃取時不得覆寫。 -->
<!-- codebase-wiki:user-notes:end -->

<!-- notebooklm:local-only:start -->
## 本機追溯

- 原始證據：`{path/to/implementation-evidence}`
<!-- notebooklm:local-only:end -->
