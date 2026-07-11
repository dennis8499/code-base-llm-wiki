# Intent Routing

Use this table as the source of truth for Codebase LLM Wiki request routing.
Top-level instructions and agents may summarize it, but should not maintain a
separate intent taxonomy.

| Intent | User signals | Default action |
| --- | --- | --- |
| Install / setup | install, setup, use this framework, Codex bundle | Read `README.md` and `Codex.md`; explain or copy the required entrypoint surfaces. |
| Ingest | document, analyze, ingest, add to wiki, 文件化 | Read wiki state, inspect raw sources read-only, then create or update wiki pages. |
| Query | explain, find, where, how, 查詢 | Read `wiki/index.md`, then relevant pages; inspect sources only if wiki evidence is insufficient, stale, or contradictory. |
| Lint | health, stale, broken links, lint, 品質 | Audit wiki quality and report findings before broad repairs. |
| ADR | decision, ADR, architecture choice | Create or update a record under `wiki/decisions/` with ADR frontmatter. |
| Synthesis / Guide | save analysis, onboarding, guide, synthesis | Persist durable analysis under `wiki/synthesis/` or durable operational guidance under `wiki/guides/`. |
| System Analysis / SA | SA文件, 系統分析, system analysis, SAD | Generate a Markdown SA document under `wiki/synthesis/` from wiki-first evidence. |
| Archaeology | why, history, legacy, git, 考古 | Trace concrete entrypoints, call paths, and non-destructive git history; separate evidence from inference. |
| Delegation | subagents, parallel, delegation, swarm | Use platform-native custom agents only when the user or parent agent explicitly asks for delegation. |

## Notes

- SQL Server live evidence is a query sub-mode, not a separate intent.
- Interactive Ingest and Batch Ingest are ingest modes, not separate intents.
- Onboarding guides are a specialized guide workflow; keep them distinct from
  general `save-guide` prompts when the user specifically asks for newcomer
  onboarding.
