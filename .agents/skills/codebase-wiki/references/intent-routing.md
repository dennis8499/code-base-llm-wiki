# Intent Routing

Use this table as the source of truth for the eleven user-facing intent groups.
`capabilities.json` maps each group to one machine operation. NotebookLM export
has a separate artifact and authorization contract.

| Intent | User signals | Default action |
| --- | --- | --- |
| Install / setup | install, setup, use this framework, Codex bundle | Read `README.md` and `Codex.md`; explain or copy the required entrypoint surfaces. |
| Ingest | document, analyze, ingest, add to wiki, 文件化 | Read wiki state, inspect raw sources read-only, then create or update wiki pages. |
| Query | explain, find, where, how, 查詢 | Read `wiki/index.md`, then relevant pages; inspect sources only if wiki evidence is insufficient, stale, or contradictory. |
| Lint | health, stale, broken links, lint, 品質 | Audit wiki quality and report findings before broad repairs. |
| ADR | decision, ADR, architecture choice | Create or update a record under `wiki/decisions/` with ADR frontmatter. |
| Synthesis | save analysis, synthesis | Persist durable cross-cutting analysis under `wiki/synthesis/`. |
| Business Analysis / BA | BA文件, 業務分析文件, business analysis document | Generate a standard-aligned Markdown BA document under `wiki/synthesis/` from wiki-first evidence. |
| System Analysis / SA | SA文件, 系統分析, system analysis, SAD | Generate a solution-neutral, standard-aligned Markdown SA document under `wiki/synthesis/`. |
| System Design / SD | SD文件, 系統設計, system design, SDD | Generate a standard-aligned Markdown SD document under `wiki/synthesis/` with architecture views and decisions. |
| NotebookLM export | NotebookLM, export, source pack, upload plan, BA／SA 匯出 | Read Wiki as baseline, scan the full safe text scope, preview capabilities and BA／SA gaps, obtain one confirmation, update the complete confirmed knowledge set, then run readiness and generate `.notebooklm/` automatically. |
| Archaeology | why, history, legacy, git, 考古 | Trace concrete entrypoints, call paths, and non-destructive git history; separate evidence from inference. |

## Notes

- Framework maintenance is a scope overlay on the selected intent, not an
  additional machine operation. Load `framework-maintenance.md` whenever the
  target is this framework repository.
- Interactive Ingest and Batch Ingest are ingest modes, not separate intents.
- Existing `type: guide` pages remain readable legacy Wiki data. This framework
  no longer routes requests to a Guide creation operation or supplies a Guide
  workflow, template, or prompt.
- Explicit creation requests authorize ADR, Synthesis, BA, SA, and SD output.
- `BA文件` routes to Business Analysis. Any request containing `NotebookLM`,
  `export`, or `source pack` routes to NotebookLM export even if it also says
  BA. 只有裸稱 `BA`、沒有 document/export context 時才要求澄清。
- Interactive Ingest previews before confirmation; explicit Batch Ingest
  authorizes scoped Wiki writes.
- Lint reports before repairs, and Query is read-only.
