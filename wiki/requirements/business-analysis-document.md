---
title: 標準對齊 Business Analysis 文件
type: business-requirement
summary: 使用者可依 Wiki-first 證據獨立產出標準對齊、可追溯且不隱藏缺口的繁中 BA Markdown
requirement_id: fr-analysis-business-analysis-document
capability_id: cap-analysis-document-generation
applies_to: ["[[generate-analysis-document]]"]
evidence_state: implementation-observed
notebooklm_group: business-analysis-documents
notebooklm_role: business
notebooklm_terms: [Business Analysis, BA文件, 業務需求, 現況目標, 能力, 成功指標, 變更影響]
sources:
  - .agents/skills/codebase-wiki/references/analysis-document-standards.md
  - .agents/skills/codebase-wiki/references/business-analysis-workflow.md
  - .agents/skills/codebase-wiki/assets/business-analysis-template.md
  - .github/prompts/business-analysis-doc.prompt.md
source_digest: sha256:53e3ac941a892821beee900c35675d4dd94783ea54ad5bac6ac34474e65531a4
derived_from: ["[[overview]]", "[[generate-analysis-document]]", "[[standards-alignment-not-conformance]]", "[[missing-evidence-remains-gap]]"]
last_updated: 2026-09-07
tags: [business-requirement, business-analysis, standards-aligned, notebooklm]
status: active
---

# 標準對齊 Business Analysis 文件

<!-- codebase-wiki:managed:start -->

## 業務目的

讓 Business Analyst、Product Owner 與知識維護者可把既有 Wiki 與可靠來源整理成
一致的 Business Analysis baseline，理解問題、價值、stakeholders、能力、流程、
規則、資料詞彙、成功指標與變更影響，而不把缺少證據的內容包裝成事實。

## 角色與權限

- 使用者明確要求 BA 文件即授權指定 Wiki scope 的輸出。
- `BA文件` 路由至本功能；含 NotebookLM、export 或 source pack 的請求改走
  [[notebooklm-ba-functional-export]]；只有裸稱 `BA` 才要求澄清。

## 前置條件

- 目標 Repo 已安裝 Codebase LLM Wiki；Wiki 可以只有 starter 或部分頁面。
- 缺少上游資料不是阻塞條件，必須改以具體 Gap 表達。

## 功能行為

| 情境 | 系統行為 | 可觀察結果 | 證據狀態 |
| --- | --- | --- | --- |
| 整體系統 BA | 套用 `business-analysis-aligned-v1` | `wiki/synthesis/business-analysis.md` | implementation-observed |
| Scoped BA | 將 scope 正規化為 kebab-case | `{kebab-scope}-business-analysis.md` | implementation-observed |
| 證據不完整 | 保留章節、coverage 與 Gap register | 不臆造政策、KPI、target state 或流程 | implementation-observed |
| 重跑文件 | 只更新 managed 並保留 user-notes/local-only 邊界 | 人工內容存續 | implementation-observed |

## 業務規則與例外

- [[standards-alignment-not-conformance]]
- [[missing-evidence-remains-gap]]

## 輸入、輸出與狀態

輸入是 Wiki-first evidence 與必要時的唯讀 raw sources。輸出是繁中 Markdown
synthesis、index 更新與 append-only log。這類 standalone BA 使用
`business-analysis-aligned-v1`；NotebookLM schema v6 只選取另行產生的
`codebase-business-analysis-v1` capability BA，因此兩種用途不會混合。

## 驗收條件

- `AC-DOC-BA-001`：Given 任意 Wiki evidence，When 使用者明確要求整體 BA，Then 產出預設路徑並使用 `business-analysis-aligned-v1`。
- `AC-DOC-BA-002`：Given 指定 scope，When 產出 BA，Then 路徑符合 `{kebab-scope}-business-analysis.md`。
- `AC-DOC-BA-003`：Given 已有 `cap-*`／`fr-*`／`bp-*`／`br-*`／`AC-*`，When 建立追溯，Then 重用穩定 ID 而不建立重複身分。
- `AC-DOC-BA-004`：Given 缺少 stakeholder、target state、KPI 或流程證據，When 產出文件，Then 保留 coverage／Mermaid 槽位並建立具體 `gap-*`，不得臆造。
- `AC-DOC-BA-005`：Given 已有人工作者註記，When 重跑 BA，Then user-notes 原文完整保留，技術追溯留在 local-only。
- `AC-DOC-BA-006`：Given standalone BA 文件存在或缺席，When 建立 NotebookLM schema-v6 pack，Then它不取代也不阻擋每 capability 的 current-state BA／SA pair。

## 關聯流程

- [[generate-analysis-document]]

## 待確認事項

- `gap-analysis-doc-runtime-uat`：Copilot host 尚未對新 BA prompt 執行 runtime UAT；目前只有 static contract tests。

<!-- codebase-wiki:managed:end -->

<!-- codebase-wiki:user-notes:start -->
## BA 補充註記

目前無人工補充。
<!-- codebase-wiki:user-notes:end -->

<!-- notebooklm:local-only:start -->
## 本機追溯

- Workflow：`.agents/skills/codebase-wiki/references/business-analysis-workflow.md`
- Template：`.agents/skills/codebase-wiki/assets/business-analysis-template.md`
- Contract tests：`tests/contracts/test_contracts.py`、`tests/notebooklm/test_export_notebooklm.py`
<!-- notebooklm:local-only:end -->
