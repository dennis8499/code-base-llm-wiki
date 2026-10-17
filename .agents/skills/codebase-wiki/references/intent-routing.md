# Intent Routing

This is the single workflow index for thirteen user-facing intent groups.
`capabilities.json` maps them to machine operations and authorization policies.
Interpret signals in the requested Wiki/framework context; the explicit deliverable
takes precedence over generic words such as "explain", "analyze" or "review".

| Intent | User signals | Read and perform |
| --- | --- | --- |
| Install / setup | install or upgrade this Wiki framework | [install-workflow.md](install-workflow.md); inspect `README.md` and `Codex.md`; dry-run before apply. |
| Ingest | 文件化、加入 Wiki、單一路徑、Ingest 全部 | [ingest-workflow.md](ingest-workflow.md); interactive preview/confirmation or explicit scoped Batch authorization. Full-project completion requires scanner snapshot and `ingest-coverage.py` ledger validation. |
| Query | 查詢、解釋 Wiki 中的功能、where/how | [query-workflow.md](query-workflow.md); start with `wiki/index.md` and relevant pages, inspect sources only for missing, stale or contradictory evidence. Read-only until a concrete follow-up is selected. |
| Lint | Wiki health, stale links, Wiki 品質 | [lint-checklist.md](lint-checklist.md); report findings, then confirm repairs. |
| Functional exploration | 功能探索、盤點目前完整功能 | [functional-exploration-workflow.md](functional-exploration-workflow.md); inventory current source, reconcile every included file/entrypoint, report capabilities, dependencies, coverage and gaps. Zero writes unless persistence is requested. |
| Codebase audit | 程式健檢、Codebase audit、目前程式的邏輯缺陷 | [code-audit-workflow.md](code-audit-workflow.md); rebuild the current source/entrypoint inventory, trace reachable paths, consult Wiki only for business-rule gaps, then check transactions, config, logic/state and targeted Git history statically. Save a coverage-aware report unless chat-only is requested. |
| ADR | record an architecture decision, ADR | [adr-workflow.md](adr-workflow.md); explicit creation authorizes an ADR under `wiki/decisions/`. |
| Synthesis | save this cross-cutting analysis | [synthesis-workflow.md](synthesis-workflow.md); explicit creation authorizes durable output under `wiki/synthesis/`. |
| Business Analysis / BA | BA文件、業務分析文件 | [business-analysis-workflow.md](business-analysis-workflow.md); produce a standard-aligned BA document from Wiki-first evidence. |
| System Analysis / SA | SA文件、系統分析、SAD | [system-analysis-workflow.md](system-analysis-workflow.md); produce solution-neutral requirements and verification needs from Wiki-first evidence. |
| System Design / SD | SD文件、系統設計、SDD | [system-design-workflow.md](system-design-workflow.md); produce standard-aligned architecture views, decisions and quality strategy from Wiki-first evidence. |
| NotebookLM export | NotebookLM、source pack、BA／SA 匯出 | [notebooklm-export-workflow.md](notebooklm-export-workflow.md); scan the full safe text scope of the explicit project first, preview capabilities/gaps, obtain one confirmation, update the confirmed knowledge set, then run readiness and generate `.notebooklm/`. Wiki supplements current source. |
| Archaeology | why this code changed, legacy, Git 考古 | [code-archaeology-workflow.md](code-archaeology-workflow.md); trace entrypoints/calls and non-destructive Git history, separating evidence from inference. Read-only by default. |

## Resolve overlaps

- Framework maintenance overlays the selected intent. When changing this framework,
  also load [framework-maintenance.md](framework-maintenance.md).
- NotebookLM/export/source-pack context takes precedence over BA/SA document wording.
  A downstream profile-specific export takes precedence over generic NotebookLM routing.
  只有裸稱 `BA`、沒有 document/export context 時才要求澄清。
- Explicit creation authorizes ADR, Synthesis, BA, SA and SD output.
- Interactive and Batch are Ingest modes. Query/Lint follow-up choices use
  [follow-up-actions.md](follow-up-actions.md): a selected concrete preview authorizes
  its bounded update/save and checks once; no selection or none means zero writes.
- A branch-to-branch merge/release review is distinct from a static current-source
  Codebase audit. Follow the requested review workflow rather than converting it into Wiki work.
- Existing `type: guide` pages remain readable legacy data; there is no Guide creation operation.
- Audit does not execute the target application/tests or automatic fixes. Missing or
  incomplete Wiki coverage never narrows its current-source inventory.

## Integrated routing examples

- **「說明退款流程」** → Query reads index/pages and cites evidence. Missing/stale facts
  may justify source reads; an offered save/update stays a preview until selected.
- **「盤點目前全部功能，只在聊天回答」** → Functional exploration scans current source,
  accounts for every included file/entrypoint and reports gaps; Wiki/index/log remain unchanged.
- **「程式健檢，只回報」** → Audit traces current entrypoints and targeted history,
  separates `BUG-*` / `RISK-*` / `BIZ-*`, reports coverage and makes no Wiki writes.
- **「把 BA 匯出給 NotebookLM」** → Export scans current source before the one confirmation;
  it then finishes confirmed knowledge updates, readiness and the source pack as one workflow.
