---
title: Solution-neutral System Analysis 文件
type: business-requirement
summary: 使用者可沿用既有 SA 入口產出以系統邊界、需求、介面、品質與驗證為核心的 solution-neutral 分析
requirement_id: fr-analysis-system-analysis-document
capability_id: cap-analysis-document-generation
applies_to: ["[[generate-analysis-document]]"]
evidence_state: implementation-observed
notebooklm_group: business-analysis-documents
notebooklm_role: business
notebooklm_terms: [System Analysis, SA文件, solution-neutral, 系統需求, 介面需求, 品質需求, 驗證需求]
sources:
  - .agents/skills/codebase-wiki/references/analysis-document-standards.md
  - .agents/skills/codebase-wiki/references/system-analysis-workflow.md
  - .agents/skills/codebase-wiki/assets/system-analysis-template.md
  - .github/prompts/system-analysis-doc.prompt.md
source_digest: sha256:74763f56f81ee3e98fefd185cab0db086561ea1ced0575b8cae5f51f4f2a9a03
derived_from: ["[[overview]]", "[[generate-analysis-document]]", "[[business-analysis-document]]", "[[standards-alignment-not-conformance]]", "[[missing-evidence-remains-gap]]"]
last_updated: 2026-09-07
tags: [business-requirement, system-analysis, standards-aligned, notebooklm]
status: active
---

# Solution-neutral System Analysis 文件

<!-- codebase-wiki:managed:start -->

## 業務目的

讓 analyst 與 stakeholder 在進入 solution design 前，以可驗證、無技術預設的方式
對齊 system boundary、needs、use cases、功能／介面／品質需求、概念資訊流、failure
與 verification needs，避免 SA 與 SD 責任混雜。

## 角色與權限

使用者可繼續使用既有 `/system-analysis-doc {scope}` 或自然語言 SA 請求；明確建立
要求即授權指定 Wiki scope。

## 前置條件

- BA 若存在則作為上游；若不存在仍產出 SA 並建立 `gap-*-ba-*`。
- 現有 implementation 只能證明 observed behavior，不能自動成為指定 solution。

## 功能行為

| 情境 | 系統行為 | 可觀察結果 | 證據狀態 |
| --- | --- | --- | --- |
| 系統分析 | 套用 `system-analysis-aligned-v1` | 預設或 scoped SA Markdown | implementation-observed |
| 需求識別 | 建立 `SR-*`、`NFR-*`、`IF-*` 與 verification method | 可追溯的 solution-neutral baseline | implementation-observed |
| 缺少 BA | 建立具體上游 Gap | 文件仍可使用且不虛構需求 | implementation-observed |
| Legacy SA 首次重跑 | 把完整原正文逐字移入 user-notes legacy snapshot | 人工／歷史內容不遺失 | implementation-observed |

## 業務規則與例外

- [[standards-alignment-not-conformance]]
- [[missing-evidence-remains-gap]]

## 輸入、輸出與狀態

Standalone SA 使用 `system-analysis-aligned-v1` 與 `notebooklm_role: traceability`，不進入
capability upload sources；NotebookLM export 另用 `codebase-system-analysis-v1` 產生可上傳的
現況 SA。設計選型、元件配置、protocol、storage 與 deployment topology 仍移交
[[system-design-document]] 或 ADR。

## 驗收條件

- `AC-DOC-SA-001`：Given 原 SA 入口與路徑，When 升級框架，Then `/system-analysis-doc`、預設路徑與 scoped 命名保持可用。
- `AC-DOC-SA-002`：Given stakeholder needs，When 產出 SA，Then 以 `SR-{SCOPE}-NNN`、`NFR-{SCOPE}-NNN`、`IF-{SCOPE}-NNN` 建立原子、可驗證、solution-neutral requirements。
- `AC-DOC-SA-003`：Given 品質需求，When 分類與描述，Then 使用 ISO/IEC 25010 characteristic 並記錄 condition、measure、target 或 Gap。
- `AC-DOC-SA-004`：Given BA 缺席，When 產出 SA，Then 建立具體 `gap-*-ba-*` 而不阻擋或虛構上游需求。
- `AC-DOC-SA-005`：Given 無 markers 的 legacy SA，When 首次重跑，Then 原正文逐字保存在 user-notes legacy 區塊，再產生新 managed 內容。
- `AC-DOC-SA-006`：Given standalone SA 文件，When NotebookLM export，Then它因 profile／role 不進入 upload content；每 capability 的專用 current-state SA 仍必須與 BA 成對輸出。

## 關聯流程

- [[generate-analysis-document]]

## 待確認事項

- `gap-analysis-doc-quality-targets`：框架尚未由產品 owner 核准跨專案通用的文件產出 latency 或規模門檻。

<!-- codebase-wiki:managed:end -->

<!-- codebase-wiki:user-notes:start -->
## BA 補充註記

目前無人工補充。
<!-- codebase-wiki:user-notes:end -->

<!-- notebooklm:local-only:start -->
## 本機追溯

- Workflow：`.agents/skills/codebase-wiki/references/system-analysis-workflow.md`
- Template：`.agents/skills/codebase-wiki/assets/system-analysis-template.md`
- Contract tests：`tests/test_contracts.py`、`tests/test_wiki_lint.py`
<!-- notebooklm:local-only:end -->
