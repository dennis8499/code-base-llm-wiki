---
title: 標準對齊 System Design 文件
type: business-requirement
summary: 使用者可將 SA 需求轉成 stakeholders/concerns、架構決策、views、元件、runtime、資料、介面、部署、安全與品質策略
requirement_id: fr-analysis-system-design-document
capability_id: cap-analysis-document-generation
applies_to: ["[[generate-analysis-document]]"]
evidence_state: implementation-observed
notebooklm_group: business-analysis-documents
notebooklm_role: business
notebooklm_terms: [System Design, SD文件, architecture view, 設計決策, 元件, runtime, 部署, 安全]
sources:
  - .agents/skills/codebase-wiki/references/analysis-document-standards.md
  - .agents/skills/codebase-wiki/references/system-design-workflow.md
  - .agents/skills/codebase-wiki/assets/system-design-template.md
  - .github/prompts/system-design-doc.prompt.md
source_digest: sha256:b6b4b1a37e73d8d34ac122e16acb4219df732317f626f2084bca5bb40137e0d9
derived_from: ["[[overview]]", "[[generate-analysis-document]]", "[[system-analysis-document]]", "[[standards-alignment-not-conformance]]", "[[missing-evidence-remains-gap]]"]
last_updated: 2026-09-04
tags: [business-requirement, system-design, standards-aligned, notebooklm]
status: active
---

# 標準對齊 System Design 文件

<!-- codebase-wiki:managed:start -->

## 業務目的

讓 architect、developer、operator 與 security reviewer 可從已知 SA requirements
理解 solution structure、decisions、views、quality/security effects 與 verification
strategy，同時看見未核准或證據不足的設計缺口。

## 角色與權限

使用者明確要求 SD 文件即授權指定 Wiki scope 的輸出。工作流重用既有 ADR，不因產出
SD 而重複建立決策身分。

## 前置條件

- SA 若存在則提供 `SR/NFR/IF-*`；若不存在，仍產出並建立 `gap-*-sa-*`。
- Implementation observation 與 approved architecture decision 必須分開標示。

## 功能行為

| 情境 | 系統行為 | 可觀察結果 | 證據狀態 |
| --- | --- | --- | --- |
| 系統設計 | 套用 `system-design-aligned-v1` | 預設或 scoped SD Markdown | implementation-observed |
| Architecture description | 建立 stakeholder/concern、viewpoint、`VIEW-*`、`DE-*`／ADR | 可跨 view 追溯的設計 baseline | implementation-observed |
| 五種設計視圖 | 對元件、runtime、資料、部署、安全各自做 evidence gate | 有證據的 Mermaid 或具體 Gap | implementation-observed |
| 缺少 SA | 建立具體 upstream Gap | 文件不中止、不虛構 driver | implementation-observed |

## 業務規則與例外

- [[standards-alignment-not-conformance]]
- [[missing-evidence-remains-gap]]

## 輸入、輸出與狀態

輸出包含 `DE-{SCOPE}-NNN`、`VIEW-{SCOPE}-{SLUG}`、既有 ADR 連結與
SA → design → verification 追溯。SD 使用 `notebooklm_role: traceability`，不進入 BA
upload payload。

## 驗收條件

- `AC-DOC-SD-001`：Given 明確 SD 請求，When 產出文件，Then 使用 `system-design-aligned-v1` 與預設／scoped 固定路徑。
- `AC-DOC-SD-002`：Given stakeholder concerns，When 建立 architecture description，Then 每個 `VIEW-{SCOPE}-{SLUG}` 說明 viewpoint、audience、model 與 correspondence。
- `AC-DOC-SD-003`：Given SA requirements，When 記錄設計，Then `DE-{SCOPE}-NNN` 或既有 ADR 追溯到 `SR/NFR/IF-*` 與 verification strategy。
- `AC-DOC-SD-004`：Given 任一元件、runtime、資料、部署或安全視圖缺少證據，When 產出 SD，Then 該槽位顯示具體 Gap 而非虛構圖。
- `AC-DOC-SD-005`：Given 缺少 SA，When 產出 SD，Then 建立 `gap-*-sa-*` 並明示哪些 design drivers 未確認。
- `AC-DOC-SD-006`：Given SD 文件，When NotebookLM export，Then SD 因 traceability role 不進入 upload content。

## 關聯流程

- [[generate-analysis-document]]

## 待確認事項

- `gap-analysis-doc-formal-adr`：目前文件工作流決策尚未建立獨立 ADR；SD 以 implementation-observed `DE-*` 記錄，不冒稱已核准 ADR。

<!-- codebase-wiki:managed:end -->

<!-- codebase-wiki:user-notes:start -->
## BA 補充註記

目前無人工補充。
<!-- codebase-wiki:user-notes:end -->

<!-- notebooklm:local-only:start -->
## 本機追溯

- Workflow：`.agents/skills/codebase-wiki/references/system-design-workflow.md`
- Template：`.agents/skills/codebase-wiki/assets/system-design-template.md`
- Contract tests：`tests/test_contracts.py`、`tests/test_install_framework.py`
<!-- notebooklm:local-only:end -->
