---
name: visualize-wiki
description: Create an evidence-backed interactive diagram from the Codebase LLM Wiki.
agent: agent
argument-hint: <diagram request and optional type>
---

Use `$codebase-wiki` and read `references/intent-routing.md` and
`references/visualization-workflow.md`. The user's explicit request authorizes
the requested diagram and its bounded Wiki update.

Read `wiki/index.md` and relevant Wiki pages first. Inspect only selected raw
sources needed to fill stale, missing, or contradictory evidence. Choose one of
the ten supported types. Run `wiki-visualize.py prepare`, complete the private
`candidate.json` and `evidence-map.json`, then run `publish`. Each semantic
element must cite a selected file hash or be recorded as a Gap. Never invent
code behavior, relationships, dates, or durations. Timeline and Waterfall
values require evidence; use clearly labeled illustrative values only when the
user explicitly requests an illustrative diagram.

Do not publish unless Archify `validate`, `deliver`, strict `check`, and
`browser-check` all pass and the source/Wiki snapshots still match. Keep failed
attempts out of the Wiki. After publication, run `verify` and the relevant Wiki
frontmatter, stale, index, `wiki/log.md`, and lint checks. Preserve previous runs
and the user notes block.
