# Intent Routing

Use this table as the source of truth for the ten user-facing intent groups.
`capabilities.json` maps them to eleven machine operations because Guide and
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
| System Analysis / SA | SA文件, 系統分析, system analysis, SAD | Generate a Markdown SA document under `wiki/synthesis/` from wiki-first evidence. |
| NotebookLM export | NotebookLM, export, source pack, upload plan, BA, 匯出 | Read Wiki as baseline, scan the full safe text scope, preview BA processes/rules/terms/gaps, update the confirmed knowledge set, then require a second readiness preflight before generating `.notebooklm/`. |
| Archaeology | why, history, legacy, git, 考古 | Trace concrete entrypoints, call paths, and non-destructive git history; separate evidence from inference. |
| Delegation | subagents, parallel, delegation, swarm | Use platform-native custom agents only when the user or parent agent explicitly asks for delegation. |

## Notes

- Framework maintenance is a scope overlay on the selected intent, not an
  additional machine operation. Load `framework-maintenance.md` whenever the
  target is this framework repository.
- SQL Server live evidence is a query sub-mode, not a separate intent.
- Interactive Ingest and Batch Ingest are ingest modes, not separate intents.
- Onboarding guides are a specialized guide workflow; keep them distinct from
  general `save-guide` prompts when the user specifically asks for newcomer
  onboarding.
- Explicit creation requests authorize ADR, Guide, Synthesis, and SA output.
- Interactive Ingest previews before confirmation; explicit Batch Ingest
  authorizes scoped Wiki writes.
- Lint reports before repairs, Query is read-only, and Delegation requires an
  explicit delegation request.
