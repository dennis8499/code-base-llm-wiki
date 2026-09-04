# Intent Routing

Use this table as the source of truth for the twelve user-facing intent groups.
`capabilities.json` maps them to thirteen machine operations because Guide and
Synthesis have distinct output contracts and NotebookLM export has a separate
artifact and authorization contract.

| Intent | User signals | Default action |
| --- | --- | --- |
| Install / setup | install, setup, use this framework, Codex bundle | Read `README.md` and `Codex.md`; explain or copy the required entrypoint surfaces. |
| Ingest | document, analyze, ingest, add to wiki, 文件化 | Read wiki state, inspect raw sources read-only, then create or update wiki pages. |
| Query | explain, find, where, how, 查詢 | Read `wiki/index.md`, then relevant pages; inspect sources only if wiki evidence is insufficient, stale, or contradictory. |
| Lint | health, stale, broken links, lint, 品質 | Audit wiki quality and report findings before broad repairs. |
| ADR | decision, ADR, architecture choice | Create or update a record under `wiki/decisions/` with ADR frontmatter. |
| Synthesis / Guide | save analysis, onboarding, guide, synthesis | Persist durable analysis under `wiki/synthesis/` or durable operational guidance under `wiki/guides/`. |
| Business Analysis / BA | BA文件, 業務分析文件, business analysis document | Generate a standard-aligned Markdown BA document under `wiki/synthesis/` from wiki-first evidence. |
| System Analysis / SA | SA文件, 系統分析, system analysis, SAD | Generate a solution-neutral, standard-aligned Markdown SA document under `wiki/synthesis/`. |
| System Design / SD | SD文件, 系統設計, system design, SDD | Generate a standard-aligned Markdown SD document under `wiki/synthesis/` with architecture views and decisions. |
| NotebookLM export | NotebookLM, export, source pack, upload plan, BA 匯出 | Read Wiki as baseline, scan the full safe text scope, preview BA processes/rules/terms/gaps, update the confirmed knowledge set, then require a second readiness preflight before generating `.notebooklm/`. |
| Archaeology | why, history, legacy, git, 考古 | Trace concrete entrypoints, call paths, and non-destructive git history; separate evidence from inference. |
| Delegation | subagents, parallel, delegation, swarm | Use platform-native custom agents only when the user or parent agent explicitly asks for delegation. |

## Notes

- Framework maintenance is a scope overlay on the selected intent, not an
  additional machine operation. Load `framework-maintenance.md` whenever the
  target is this framework repository.
- Interactive Ingest and Batch Ingest are ingest modes, not separate intents.
- Onboarding guides are a specialized guide workflow; keep them distinct from
  general `save-guide` prompts when the user specifically asks for newcomer
  onboarding.
- Explicit creation requests authorize ADR, Guide, Synthesis, BA, SA, and SD output.
- `BA文件` routes to Business Analysis. Any request containing `NotebookLM`,
  `export`, or `source pack` routes to NotebookLM export even if it also says
  BA. 只有裸稱 `BA`、沒有 document/export context 時才要求澄清。
- Interactive Ingest previews before confirmation; explicit Batch Ingest
  authorizes scoped Wiki writes.
- Lint reports before repairs, Query is read-only, and Delegation requires an
  explicit delegation request.
