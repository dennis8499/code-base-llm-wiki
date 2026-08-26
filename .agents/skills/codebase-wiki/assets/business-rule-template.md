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

## 規則敘述

## 條件與結果

| 條件 | 決策／結果 | 例外 | 證據狀態 |
| --- | --- | --- | --- |
| {condition} | {outcome} | {exception} | business-confirmed / implementation-observed / inference / gap |

## 適用流程

- [[{business-process-page}]]

## 資料與詞彙

## 待確認事項

## 追溯關聯

- [[{traceability-page}]]（技術內容只保留在 `notebooklm_role: traceability` 頁；本頁不內嵌實作細節）
