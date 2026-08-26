---
title: NotebookLM 只接收 BA 功能知識
type: business-rule
summary: NotebookLM source pack 只能包含功能需求、流程、規則、詞彙、驗收條件與缺口
rule_id: br-notebooklm-ba-knowledge-first
applies_to: ["[[notebooklm-ba-knowledge-export]]"]
evidence_state: business-confirmed
notebooklm_group: business-notebooklm-export
notebooklm_role: business
notebooklm_terms: [BA-only, functional requirement, acceptance criteria, raw code exclusion]
sources:
  - .agents/skills/codebase-wiki/references/notebooklm-export-workflow.md
source_digest: sha256:5106684498c329561f25e419d8dd19e52a4d227c2ae958aee26dd06c42bafce8
derived_from: ["[[notebooklm-ba-knowledge-export]]"]
last_updated: 2026-08-26
tags: [business-rule, notebooklm, evidence]
status: active
---

# NotebookLM 只接收 BA 功能知識

<!-- codebase-wiki:managed:start -->

## 規則敘述

NotebookLM source pack 只能保留 BA 功能需求文件。回答以 `fr-*` 需求與 `AC-*` 驗收條件為
主，再說明流程、規則、詞彙、資料語意與 gaps。Raw code、raw config、class、function、API、
table、repository path 與 technical traceability appendix 均不得成為 upload source。

## 條件與結果

| 條件 | 決策／結果 | 例外 | 證據狀態 |
| --- | --- | --- | --- |
| BA 文件超過 source budget | deterministic compaction／splitting 後仍超限就整體失敗 | 保留上一份 pack，不可省略功能需求 | business-confirmed |
| 問題詢問正式政策 | 優先引用 business-confirmed evidence | 只有 implementation observation 時必須如此標示 | business-confirmed |
| Raw source 含敏感 pattern | 分析副本與 final payload 先遮罩 | 遮罩後仍有殘留即阻擋 commit | business-confirmed |

## 適用流程

- [[notebooklm-ba-knowledge-export]]

## 資料與詞彙

- `BA-only`：upload source 只含 BA 能理解與驗收的功能知識，不含原始技術證據。
- `local-only traceability`：留在 Wiki／manifest 供維護者查核，但匯出 renderer 會移除。

## 待確認事項

無。個別規則是否已獲業務核准，仍由該規則自身的 `evidence_state` 表示。

<!-- codebase-wiki:managed:end -->

<!-- codebase-wiki:user-notes:start -->
## BA 補充註記

目前無人工補充。
<!-- codebase-wiki:user-notes:end -->

<!-- notebooklm:local-only:start -->
## 本機追溯關聯

- [[notebooklm-exporter]]（實作細節不內嵌於本 BA 規則頁）
<!-- notebooklm:local-only:end -->
