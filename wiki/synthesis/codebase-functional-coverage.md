---
title: Codebase Functional Coverage
type: synthesis
summary: 本機完整性 gate，將 framework scan profile 的每個安全檔案歸屬到功能需求或無可觀察行為
notebooklm_group: local-governance
notebooklm_role: exclude
sources: []
derived_from: ["[[functional-requirement-catalog]]", "[[notebooklm-ba-functional-export]]"]
last_updated: 2026-08-26
tags: [synthesis, coverage, notebooklm, local-only]
status: active
---

# Codebase Functional Coverage

> 本頁只作為本機 readiness gate，不會進入 NotebookLM source pack。

<!-- codebase-wiki:managed:start -->
## Disposition Ledger

以下 prefix 使用 most-specific match。框架 schema、adapters、tests、文件與 release
surface 共同實作或驗證 [[notebooklm-ba-functional-export]]；repository metadata 檔案不產生
獨立可觀察行為。

| Path or prefix | Disposition | Functional requirements |
| --- | --- | --- |
| `.agents/skills/codebase-wiki/` | functional-evidence | [[notebooklm-ba-functional-export]] |
| `.codex/` | supporting-technical | [[notebooklm-ba-functional-export]] |
| `.github/` | supporting-technical | [[notebooklm-ba-functional-export]] |
| `docs/` | supporting-technical | [[notebooklm-ba-functional-export]] |
| `tests/` | supporting-technical | [[notebooklm-ba-functional-export]] |
| `tools/` | supporting-technical | [[notebooklm-ba-functional-export]] |
| `.gitattributes` | no-observable-behavior | |
| `.gitignore` | no-observable-behavior | |
| `AGENTS.md` | supporting-technical | [[notebooklm-ba-functional-export]] |
| `ChangeLog.md` | supporting-technical | [[notebooklm-ba-functional-export]] |
| `Codex.md` | supporting-technical | [[notebooklm-ba-functional-export]] |
| `README.md` | supporting-technical | [[notebooklm-ba-functional-export]] |
| `VERSION` | no-observable-behavior | |
| `notebooklm.toml` | functional-evidence | [[notebooklm-ba-functional-export]] |

## Gate 結果

- Uncovered safe files：0
- Analysis gaps：0
- Dangling requirement links：0
<!-- codebase-wiki:managed:end -->

<!-- codebase-wiki:user-notes:start -->
## Reviewer Notes

新增安全檔案時必須在下一次全量萃取重新分類，不得依賴舊 ledger 靜默通過。
<!-- codebase-wiki:user-notes:end -->
