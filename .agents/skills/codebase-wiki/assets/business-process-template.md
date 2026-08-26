---
title: "{業務流程名稱}"
type: business-process
summary: "{此流程為哪個角色在什麼條件下達成什麼結果}"
process_id: "bp-{domain}-{process}"
actors: ["{primary-actor}"]
coverage_status: partial
notebooklm_group: "business-{capability-slug}"
notebooklm_role: business
notebooklm_terms: ["{流程名稱}", "{角色}", "{觸發事件}"]
sources:
  - "{path/to/business-or-implementation-evidence}"
derived_from: ["[[overview]]"]
source_digest: "sha256:{64-lowercase-hex}"
last_updated: YYYY-MM-DD
tags: [business-process, notebooklm]
status: active
---

# {業務流程名稱}

## 業務目的與範圍

## 角色

## 觸發與前置條件

## 主流程

| 步驟 | 角色 | 業務行為 | 結果 | 證據狀態 |
| --- | --- | --- | --- | --- |
| 1 | {actor} | {business-action} | {outcome} | business-confirmed / implementation-observed / inference / gap |

## 替代與例外流程

## 業務規則

- [[{business-rule-page}]]

## 輸入、輸出與狀態轉換

## 上下游影響

## 成功結果

## 待確認事項

- `gap-{domain}-{topic}`：{question}

## 追溯關聯

- [[{traceability-page}]]（技術內容只保留在 `notebooklm_role: traceability` 頁；本頁不內嵌實作細節）

## 相關頁面

- [[business-process-catalog]]
- [[business-rule-catalog]]
- [[business-glossary]]
