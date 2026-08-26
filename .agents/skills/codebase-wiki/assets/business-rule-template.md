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

## 規則敘述

## 條件與結果

| 條件 | 決策／結果 | 例外 | 證據狀態 |
| --- | --- | --- | --- |
| {condition} | {outcome} | {exception} | business-confirmed / implementation-observed / inference / gap |

## 適用流程

- [[{business-process-page}]]

## 資料與詞彙

## 待確認事項

<!-- codebase-wiki:managed:end -->

<!-- codebase-wiki:user-notes:start -->
## BA 補充註記

<!-- 保留人工維護內容；重新萃取時不得覆寫。 -->
<!-- codebase-wiki:user-notes:end -->

<!-- notebooklm:local-only:start -->
## 本機追溯關聯

- [[{traceability-page}]]（技術內容不進入 NotebookLM source pack）
<!-- notebooklm:local-only:end -->
