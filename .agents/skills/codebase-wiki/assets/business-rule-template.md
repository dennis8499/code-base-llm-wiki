---
title: "{業務規則名稱}"
type: business-rule
summary: "{在什麼條件下必須產生什麼業務結果}"
rule_id: "br-{domain}-{rule}"
applies_to: ["[[{business-process-page}]]"]
evidence_state: implementation-observed
notebooklm_group: "business-{capability-slug}"
notebooklm_role: business
notebooklm_terms: ["{規則名稱}", "{條件}", "{結果}"]
analysis_status: untraced
gap_classification: analysis-gap
sources:
  - "{path/to/business-or-implementation-evidence}"
derived_from: ["[[{business-process-page}]]"]
source_digest: "sha256:{64-lowercase-hex}"
last_updated: YYYY-MM-DD
tags: [business-rule, notebooklm]
status: active
---

# {業務規則名稱}

<!-- codebase-wiki:managed:start -->

## 分析狀態與缺口分類

| 欄位 | 值 |
| --- | --- |
| Evidence trace | `untraced`／`traced` |
| Gap classification | `analysis-gap`／`evidence-gap`／`business-confirmation`／`none` |

規則必須從實際判斷入口追到條件、決策、資料／狀態結果與例外；只列規則名稱或 Wiki
連結不算完成。政策、核准或責任若需外部確認，仍保留已觀察的程式行為。

## 規則敘述

## 條件與結果

| 條件 | 決策／結果 | 例外 | 證據狀態 |
| --- | --- | --- | --- |
| {condition} | {outcome} | {exception} | business-confirmed / implementation-observed / inference / gap |

## 適用流程

- [[{business-process-page}]]

## 資料與詞彙

## 待確認事項

- `gap-{domain}-{topic}`：{evidence-gap 或 business-confirmation 的具體問題與確認對象}

<!-- codebase-wiki:managed:end -->

<!-- codebase-wiki:user-notes:start -->
## BA 補充註記

<!-- 保留人工維護內容；重新萃取時不得覆寫。 -->
<!-- codebase-wiki:user-notes:end -->

<!-- notebooklm:local-only:start -->
## 本機追溯關聯

- [[{traceability-page}]]（技術內容不進入 NotebookLM source pack）
<!-- notebooklm:local-only:end -->
