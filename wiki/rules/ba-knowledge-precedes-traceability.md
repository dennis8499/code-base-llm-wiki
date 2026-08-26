---
title: BA 知識優先於技術追溯
type: business-rule
summary: NotebookLM 必須先以業務流程、規則、詞彙與缺口作答，技術細節只能作獨立附錄
rule_id: br-notebooklm-ba-knowledge-first
applies_to: ["[[notebooklm-ba-knowledge-export]]"]
evidence_state: business-confirmed
notebooklm_group: business-notebooklm-export
notebooklm_role: business
notebooklm_terms: [BA-first, business evidence, technical traceability, 業務知識優先]
sources:
  - .agents/skills/codebase-wiki/references/notebooklm-export-workflow.md
source_digest: sha256:d3bde1dadd5f7a68634c81cf7bd6c93b33b5bb5a948221edd2ec686aaf8284d8
derived_from: ["[[notebooklm-ba-knowledge-export]]"]
last_updated: 2026-08-26
tags: [business-rule, notebooklm, evidence]
status: active
---

# BA 知識優先於技術追溯

## 規則敘述

NotebookLM source pack 必須先保留 BA 主文件與指定 business evidence。回答必須先說明業務
目的、流程、規則、詞彙、資料語意與 gaps；class、function、API、table、config 與 path 只能
出現在獨立 technical traceability appendix，不能取代業務解釋。

## 條件與結果

| 條件 | 決策／結果 | 例外 | 證據狀態 |
| --- | --- | --- | --- |
| BA 文件或指定 business evidence 與 traceability 爭用 source budget | 保留 BA 文件與 business evidence，省略最低優先 traceability 並明列 omission | 必要 BA 內容仍無法容納時整體失敗並保留舊 pack | business-confirmed |
| 問題詢問正式政策 | 優先引用 business-confirmed evidence | 只有 implementation observation 時必須如此標示 | business-confirmed |
| 問題要求實作位置 | 先給業務脈絡，再引用 traceability | 不得把 observed behavior 升格為核准政策 | business-confirmed |

## 適用流程

- [[notebooklm-ba-knowledge-export]]

## 資料與詞彙

- `business evidence`：業務擁有的需求、流程、決策表或 acceptance specification。
- `technical traceability`：把 BA knowledge 連回目前程式、設定、schema 或工程 Wiki 的附錄。

## 待確認事項

無。個別規則是否已獲業務核准，仍由該規則自身的 `evidence_state` 表示。

## 追溯關聯

- [[notebooklm-exporter]]（實作細節不內嵌於本 BA 規則頁）
