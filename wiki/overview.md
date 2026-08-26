---
title: Codebase LLM Wiki — 業務總覽
type: overview
summary: 讓知識維護者把完整安全 codebase 重新萃取成功能需求、驗收條件、流程、規則與缺口
sources:
  - README.md
  - AGENTS.md
  - .agents/skills/codebase-wiki/capabilities.json
  - .agents/skills/codebase-wiki/references/notebooklm-export-workflow.md
source_digest: sha256:6bb88a4c12b56f0a8979f6b511102525bbca70417faf5c5b1866cb377e930207
derived_from: []
last_updated: 2026-08-26
tags: [framework, business-knowledge, wiki, notebooklm]
status: active
notebooklm_group: business-core
notebooklm_role: business
notebooklm_terms: [Codebase LLM Wiki, 功能需求, 驗收條件, Business Analyst, NotebookLM, 完整覆蓋, DLP 遮罩]
---

# Codebase LLM Wiki — 業務總覽

<!-- codebase-wiki:managed:start -->

## 業務目的

Codebase LLM Wiki 讓團隊把散落在程式、設定、既有文件與人員理解中的系統知識，整理成
可閱讀、可版本控制、可追溯的 Markdown Wiki。Business Analyst 不必先知道 class、API、
資料表或 repository 路徑，便能從功能需求、驗收條件、角色、流程、規則、詞彙與已知缺口
開始理解系統。

NotebookLM Exporter 進一步把這份持久 Wiki 整理成離線 BA source pack。它不是 RAG，也不會
自行上傳或修改 NotebookLM；交付者先審查本地 pack，再依 upload plan 手動更新 Notebook。

## 主要角色與價值

| 角色 | 使用目的 | 得到的結果 |
| --- | --- | --- |
| Business Analyst | 理解系統如何支援業務、找出規則與例外 | 可直接詢問的功能需求、驗收條件、流程、規則與 gaps |
| Product Owner／領域擁有者 | 確認政策、邊界與優先順序 | 清楚區分已確認政策、目前實作與待確認事項 |
| 知識維護者 | 將來源證據整理成 durable knowledge | 可增量更新的 Wiki、index 與 append-only log |
| 工程／稽核角色 | 在本機 Wiki 追查 BA 說明對應的實作或設定 | 不會上傳的 local-only provenance |

## 對 BA 提供的知識能力

- 從 [[functional-requirement-catalog]] 找到 `fr-*`、capability、角色與 `AC-*` 驗收條件。
- 從 [[business-process-catalog]] 找到 actor、trigger、前置條件、主流程、替代／例外流程、
  狀態變更與業務結果。
- 從 [[business-rule-catalog]] 查明條件、決策、例外、適用流程與證據狀態。
- 從 [[business-glossary]] 對齊名詞、別名與容易混淆的語意邊界。
- 從 [[business-knowledge-gaps]] 看見無可靠證據、需要 stakeholder 確認或 v1 尚不支援的內容。
- 技術 provenance 只留在本機 Wiki，不進入 NotebookLM upload sources。

## 知識與證據狀態

| 狀態 | BA 應如何理解 |
| --- | --- |
| `business-confirmed` | 明確產品／流程契約，已有業務來源或授權文件支持 |
| `implementation-observed` | 程式、設定或 schema 顯示目前如此運作，但不代表已核准政策 |
| `inference` | 由多項證據合理推得，仍需標示推論 |
| `gap` | 證據不足、互相矛盾，或需要外部角色確認 |

## 主要業務能力

目前與 NotebookLM 交付直接相關的功能需求是 [[notebooklm-ba-functional-export]]，其端到端
流程是 [[notebooklm-ba-knowledge-export]]：
知識維護者先完成 discovery preflight 與文件計畫確認，補齊 BA 知識後再完成 readiness
preflight 與第二次確認，最後產生本地 pack。相關約束見
[[ba-knowledge-precedes-traceability]] 與 [[readiness-preflight-required]]。

框架也支援一般 Ingest、Query、Lint、Archaeology、ADR、Synthesis、Guide 與 System
Analysis；這些能力的工程入口與治理細節保留在 [[project-function-catalog]]、
[[framework-introduction]] 與 [[system-analysis]]，不作為 BA 問答的主要敘事。

## 範圍與邊界

### 包含

- 可全量重新萃取並持久維護的功能需求、驗收條件、流程、規則、詞彙與缺口；
- GitHub Copilot 與 OpenAI Codex 共用的 Wiki 工作流契約；
- BA-only NotebookLM source pack、schema-v5 manifest 與手動 upload plan；
- 可審查的安全排除、DLP、容量與 migration 狀態。

### 不包含

- NotebookLM API、自動雲端上傳或雲端 source 刪除；
- 向量資料庫、常駐搜尋服務或 deterministic NotebookLM 回答保證；
- 將未轉成 UTF-8 repo text 的 PDF、Office、圖片或訪談內容自動視為證據；
- 自動把實作行為提升為已核准業務政策。

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

- [[notebooklm-export]] — 操作者的兩階段匯出指南
- [[notebooklm-exporter]] — schema v5、完整覆蓋、DLP masking、容量與原子輸出實作
- [[system-architecture]] — 框架元件、資料流與安全邊界
- [[wiki-quality-and-provenance]] — frontmatter、digest、index、log 與 lint
- [[system-analysis]] — 跨模組風險與非功能需求
<!-- notebooklm:local-only:end -->
