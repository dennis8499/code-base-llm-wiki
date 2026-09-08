---
title: Codebase LLM Wiki — 業務總覽
type: overview
summary: 讓團隊把 codebase 建成可追溯 Wiki，並產出標準對齊 BA／SA／SD 與現況 NotebookLM BA／SA 知識包
sources:
  - README.md
  - AGENTS.md
  - .agents/skills/codebase-wiki/capabilities.json
  - .agents/skills/codebase-wiki/references/notebooklm-export-workflow.md
  - .agents/skills/codebase-wiki/references/analysis-document-standards.md
source_digest: sha256:86ed4b811bdae1a6ada215acb2e4a9402c67da2fbb1b3f0494ecbfa8c766eed2
derived_from: []
last_updated: 2026-09-08
tags: [framework, business-knowledge, wiki, notebooklm]
status: active
notebooklm_group: business-core
notebooklm_role: business
notebooklm_terms: [Codebase LLM Wiki, 功能需求, 驗收條件, Business Analyst, NotebookLM, 完整覆蓋, DLP 遮罩, BA文件, SA文件, SD文件, 標準對齊]
---

# Codebase LLM Wiki — 業務總覽

<!-- codebase-wiki:managed:start -->

## 業務目的

Codebase LLM Wiki 讓團隊把散落在程式、設定、既有文件與人員理解中的系統知識，整理成
可閱讀、可版本控制、可追溯的 Markdown Wiki。團隊可進一步從同一份 evidence 獨立
產出 Business Analysis、solution-neutral System Analysis 與 System Design，分開回答
「為何改／要什麼／如何設計」，並以 stable IDs 和 Gap 連結。Business Analyst 不必先
知道 class、API、資料表或 repository 路徑，便能從功能需求、驗收條件、角色、流程、
規則、詞彙與已知缺口開始理解系統。

NotebookLM Exporter 每次從當下完整安全 Codebase 重新盤點，以 Wiki 作比對與持久化基線，
再為每個 capability 建立互連的現況 BA／SA，整理成離線單一 Notebook source pack。Wiki 與
canonical `docs/knowledge/` 都是本機治理資料，不進 raw discovery identity。它不會自行上傳
或修改 NotebookLM；交付者先審查本機 pack，再依 upload plan 手動更新 Notebook。

## 主要角色與價值

| 角色 | 使用目的 | 得到的結果 |
| --- | --- | --- |
| Business Analyst | 理解系統如何支援業務、找出規則與例外 | 可直接詢問的功能需求、驗收條件、流程、規則與 gaps |
| Product Owner／領域擁有者 | 確認政策、邊界與優先順序 | 清楚區分已確認政策、目前實作與待確認事項 |
| System Analyst | 把 stakeholder needs 轉成 solution-neutral 系統／介面／品質需求 | `SR-*`／`IF-*`／`NFR-*` 與 verification needs |
| Architect／Engineer | 把 SA drivers 轉成可審查 solution design | `DE-*`／`VIEW-*`／ADR、五種 views 與品質策略 |
| 知識維護者 | 將來源證據整理成 durable knowledge | 可增量更新的 Wiki、index 與 append-only log |
| 工程／稽核角色 | 在本機 Wiki 追查 BA 說明對應的實作或設定 | 不會上傳的 local-only provenance |

## 對 BA 提供的知識能力

- 從 [[functional-requirement-catalog]] 找到 `fr-*`、capability、角色與 `AC-*` 驗收條件。
- 從 [[business-process-catalog]] 找到 actor、trigger、前置條件、主流程、替代／例外流程、
  狀態變更與業務結果。
- 從 [[business-rule-catalog]] 查明條件、決策、例外、適用流程與證據狀態。
- 從 [[business-glossary]] 對齊名詞、別名與容易混淆的語意邊界。
- 從 [[business-knowledge-gaps]] 看見無可靠證據、需要 stakeholder 確認或 v1 尚不支援的內容。
- 從 [[business-analysis]]、[[system-analysis]]、[[system-design]] 依序追查 business
  objective／BA IDs、SR/NFR/IF、DE/VIEW/ADR 與 verification strategy。
- 技術 provenance 只留在本機 Wiki，不進入 NotebookLM upload sources。

## 知識與證據狀態

| 狀態 | BA 應如何理解 |
| --- | --- |
| `business-confirmed` | 明確產品／流程契約，已有業務來源或授權文件支持 |
| `implementation-observed` | 程式、設定或 schema 顯示目前如此運作，但不代表已核准政策 |
| `inference` | 由多項證據合理推得，仍需標示推論 |
| `gap` | 證據不足、互相矛盾，或需要外部角色確認 |

## 主要業務能力

標準對齊文件能力由 [[business-analysis-document]]、[[system-analysis-document]]、
[[system-design-document]] 與共用流程 [[generate-analysis-document]] 定義；三份文件可
獨立產出，上游不足以具體 Gap 降級。[[standards-alignment-not-conformance]] 限制宣稱，
[[missing-evidence-remains-gap]] 防止以推測補滿。

NotebookLM 交付功能需求是 [[notebooklm-ba-functional-export]]，其端到端流程是
[[notebooklm-ba-knowledge-export]]：
知識維護者先完成 discovery preflight，展示全部安全來源、capability、未完成分析與文件
計畫；使用者一次確認後，全量產生 BA／SA 並自動完成 readiness，最後以相符雙 ID 產生
本機 pack。相關約束見
[[ba-knowledge-precedes-traceability]] 與 [[readiness-preflight-required]]。

框架也支援一般 Ingest、Query、Lint、Archaeology、ADR 與 Synthesis；這些
能力的工程入口與治理細節保留在 [[project-function-catalog]] 與
[[framework-introduction]]。Query
只使用 Wiki 與 Repo source evidence，不連線即時資料庫或呼叫資料庫工具 fallback。

## 範圍與邊界

### 包含

- 可全量重新萃取並持久維護的功能需求、驗收條件、流程、規則、詞彙與缺口；
- GitHub Copilot 與 OpenAI Codex 共用的 Wiki 工作流契約；
- 每 capability 現況 BA／SA、schema-v6 單一 Notebook source pack 與手動 upload plan；
- 可審查的安全排除、DLP、容量與 migration 狀態。
- Versioned standards profiles、coverage、markers、evidence-gated Mermaid 與
  BA → SA → SD traceability。

### 不包含

- NotebookLM API、自動雲端上傳或雲端 source 刪除；
- 向量資料庫、常駐搜尋服務或 deterministic NotebookLM 回答保證；
- 將未轉成 UTF-8 repo text 的 PDF、Office、圖片或訪談內容自動視為證據；
- 自動把實作行為提升為已核准業務政策。
- 正式 ISO／IEEE／IIBA conformance、認證或稽核，以及付費標準全文複製。

## 已知缺口

未支援的非文字證據、外部 stakeholder 確認與 NotebookLM 實際回答品質，都保留在
[[business-knowledge-gaps]]。固定 BA 驗收題組未達門檻時，應修正 BA Wiki 後重跑
readiness preflight。

<!-- codebase-wiki:managed:end -->

<!-- codebase-wiki:user-notes:start -->
## BA 補充註記

目前無人工補充。
<!-- codebase-wiki:user-notes:end -->

<!-- notebooklm:local-only:start -->
## 本機技術追溯入口

- [[notebooklm-export]] — 操作者的一次確認與雙識別碼匯出指南
- [[notebooklm-exporter]] — schema v6、BA／SA 配對、完整覆蓋、DLP、容量與原子輸出實作
- [[system-architecture]] — 框架元件、資料流與安全邊界
- [[wiki-quality-and-provenance]] — frontmatter、digest、index、log 與 lint
- [[system-analysis]] — 跨模組風險與非功能需求
- [[business-analysis]] — 文件能力的業務脈絡、需求、成功指標與 change impact
- [[system-design]] — profiles、workflows、adapters、validators、installer 與 exporter views
<!-- notebooklm:local-only:end -->
