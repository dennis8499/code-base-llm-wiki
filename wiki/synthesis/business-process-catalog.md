---
title: 業務流程目錄
type: synthesis
summary: 框架可供 BA 查詢的 NotebookLM 交付與 BA／SA／SD 文件產出流程、角色、觸發、結果與覆蓋
notebooklm_group: business-core
notebooklm_role: business
notebooklm_terms: [業務流程, 業務能力, 知識包, Business Analyst, NotebookLM 匯出, BA文件, SA文件, SD文件]
sources: []
derived_from: ["[[overview]]", "[[notebooklm-ba-knowledge-export]]", "[[generate-analysis-document]]"]
last_updated: 2026-09-09
tags: [synthesis, business-process-catalog, notebooklm]
status: active
---

# 業務流程目錄

<!-- codebase-wiki:managed:start -->

## 文件與證據範圍

本目錄只列出有獨立 BA 流程頁、穩定 process ID、actors、trigger、outcome 與 coverage
狀態的端到端流程。一般 Ingest／Query／Lint 等框架功能目前保留在技術功能目錄，尚未
全部轉成 BA process pages，並已列入 [[business-knowledge-gaps]]；分析文件產出則由
[[generate-analysis-document]] 統一描述三種可獨立工作流。

流程頁的完整度另由 `analysis_status`／`gap_classification` 與 exporter 的 flow-integrity
檢查負責：主流程必須逐步保留條件、資料／狀態、結果、例外、失敗去向與定位；適用需求／規則
正文會在 shared business context 一併提供。`analysis-gap` 會阻擋，`evidence-gap` 與
`business-confirmation` 則保留已知實作行為並列出待補證據。

## 業務流程覆蓋矩陣

| 業務能力 | 功能需求 | 流程 ID | 流程 | 主要角色 | 觸發 | 業務結果 | 覆蓋狀態 |
| --- | --- | --- | --- | --- | --- | --- | --- |
| 現況 BA／SA 知識交付 | [[notebooklm-ba-functional-export]] | `bp-notebooklm-ba-knowledge-export` | [[notebooklm-ba-knowledge-export]] | 知識維護者、BA、SA、NotebookLM 管理員 | 明確要求建立／更新 NotebookLM pack | 經全量覆蓋與一次確認的單一 Notebook BA／SA source pack | covered |
| 標準對齊分析文件 | [[business-analysis-document]]、[[system-analysis-document]]、[[system-design-document]] | `bp-analysis-document-generation` | [[generate-analysis-document]] | 知識維護者、BA、System Analyst、Architect、Reviewer | 明確要求 BA文件／SA文件／SD文件 | 可獨立、可重產、Gap-visible 且可跨層追溯的 Markdown | partial |

## 跨流程關係

兩個流程都使用一般 Wiki Ingest、index、log、lint 與 source provenance 能力，但這些
是支援活動，不另宣稱為已完整建模的 BA 端到端流程。Standalone 分析文件與 NotebookLM
專用 current-state BA／SA 使用不同 profile；只有後者會進入 capability upload sources。

## 未覆蓋與明確排除

- 非 NotebookLM 的一般 Wiki 使用旅程尚未拆成 business-process pages。
- NotebookLM 雲端上傳、tenant 管理與回答生成不在本框架自動化範圍。
<!-- codebase-wiki:managed:end -->

<!-- codebase-wiki:user-notes:start -->
## BA 補充註記

目前無人工補充。
<!-- codebase-wiki:user-notes:end -->

## 相關頁面

- [[overview]]
- [[functional-requirement-catalog]]
- [[business-rule-catalog]]
- [[business-glossary]]
- [[business-knowledge-gaps]]
