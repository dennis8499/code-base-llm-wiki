---
title: NotebookLM 只接收 Codebase 現況 BA／SA 知識
type: business-rule
summary: NotebookLM source pack 只包含由當下 Codebase 支持的每功能 BA／SA 與導覽，不直接上傳 raw source
rule_id: br-notebooklm-ba-knowledge-first
applies_to: ["[[notebooklm-ba-knowledge-export]]"]
evidence_state: business-confirmed
notebooklm_group: business-notebooklm-export
notebooklm_role: business
notebooklm_terms: [BA, SA, codebase-only, code wins, source locator, raw code exclusion]
sources:
  - .agents/skills/codebase-wiki/references/notebooklm-export-workflow.md
source_digest: sha256:83f0b22e00e098dbe3034b62a2b347621e01fa59cdcd009cb19ad6d1dc2f6db1
derived_from: ["[[notebooklm-ba-knowledge-export]]"]
last_updated: 2026-09-08
tags: [business-rule, notebooklm, evidence]
status: active
---

# NotebookLM 只接收 Codebase 現況 BA／SA 知識

<!-- codebase-wiki:managed:start -->

## 規則敘述

NotebookLM source pack 只保留每個 active capability 的現況 BA／SA、跨功能 query index、
project map，以及共用詞彙與有證據支持的跨功能流程來源。Wiki 只作本機治理，不成為
raw discovery 或 upload source。內容只來自當下 Codebase 的
程式、設定、schema、測試、README、規格與註解；
衝突時以程式碼為主並揭露差異。每份文件可保留必要 identifier、API 與受控 source locator，
但 raw code body、raw config 與未規整的 repository content 不得成為 upload source。

## 條件與結果

| 條件 | 決策／結果 | 例外 | 證據狀態 |
| --- | --- | --- | --- |
| BA／SA 文件超過 source budget | deterministic pairing／splitting 後仍超限就整體失敗 | 保留上一份 pack，不可省略 capability | business-confirmed |
| 問題詢問正式政策 | 優先引用 business-confirmed evidence | 只有 implementation observation 時必須如此標示 | business-confirmed |
| Raw source 含敏感 pattern | 分析副本與 final payload 先遮罩 | 遮罩後仍有殘留即阻擋 commit | business-confirmed |
| Codebase 缺少某項目的或品質證據 | 文件明列 `Codebase 未提供證據` | 不可自行補成政策或目標 | business-confirmed |
| 分析尚未完成或缺少 BA／SA pair | readiness 阻擋 | 不得以 knowledge gap 當成完成 | business-confirmed |
| System Design、一般 Wiki 或其他 traceability 存在 | 保留本機，不成為 capability upload document | BA／SA 文件內的受控 locator 仍保留 | business-confirmed |

## 適用流程

- [[notebooklm-ba-knowledge-export]]

## 資料與詞彙

- `codebase-only`：文件內容的唯一事實依據是本次 discovery 所盤點的專案來源。
- `source locator`：供 SA 與維護者定位證據的 repo-relative path 加行號／symbol，不包含 raw code body。
- `local-only traceability`：governance、完整 documents 與 mapping 留在本機；只有 `sources/*.md` 是上傳候選。

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
