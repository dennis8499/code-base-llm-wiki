# AGENTS.md — Codebase LLM Wiki

Detailed workflows, templates, references, and scripts live in
`$codebase-wiki` at `.agents/skills/codebase-wiki/`.

This repository is the framework repository, so Codex may update framework files
such as `README.md`, `ChangeLog.md`, `AGENTS.md`, `Codex.md`, `docs/`,
`samples/`, `tests/`, `.github/`, `.codex/`, `.agents/`, and `wiki/` when the
user explicitly asks for framework maintenance. When the framework is installed
into a target codebase, wiki tasks must treat that target codebase as raw source
and keep it read-only.

## Core Model

Codebase LLM Wiki is not RAG. It is a persistent Markdown wiki that compounds
knowledge over time.

| Layer       | Location                                                | Responsibility                                                   |
| ----------- | ------------------------------------------------------- | ---------------------------------------------------------------- |
| Raw Sources | Source code, config, existing docs                      | Read-only during wiki tasks                                      |
| Wiki        | `wiki/`                                                 | Codex-generated and maintained knowledge base                    |
| Schema      | `AGENTS.md`, `.agents/skills/codebase-wiki/`, `.codex/` | Rules, workflows, templates, scripts, hooks, and optional agents |

## Routing

Use `$codebase-wiki` for install, ingest, query, lint, ADR, guide, synthesis,
system analysis, archaeology, Wiki maintenance, or framework maintenance.
Classify the branch with
`.agents/skills/codebase-wiki/references/intent-routing.md` and load its exact
reference before acting.

Custom agents under `.codex/agents/` are explicit-delegation surfaces. Normal
requests stay with the current agent; use custom agents only when the user asks
for delegation, subagents, parallel work, or a named Wiki agent.

## Durable Invariants

- Raw sources remain read-only during Wiki tasks.
- Wiki writes stay within the authorized Wiki or framework surface.
- `wiki/log.md` is append-only; existing entries remain unchanged.
- Page add, delete, rename, or major update synchronizes `wiki/index.md`.
- Durable Wiki or framework updates append one valid log operation.
- `frontmatter.sources` contains real repo-relative paths or `sources: []`.
- Mention Wiki pages with `[[page-name]]` wikilinks.
- Cite source paths with backticks, for example `src/auth/service.ts`.
- Distinguish evidence-backed statements from inference or speculation.
- Preserve user-authored Wiki content.

Project-level Codex slash prompt files are outside this framework; Codex uses
natural-language recipes and `$codebase-wiki`.

## Live Database Evidence

SQL Server evidence follows
`.agents/skills/codebase-wiki/references/mssql-evidence-rules.md`: bounded
read-only discovery or `SELECT`, required evidence metadata, and body-only
persistence. Database evidence never enters `frontmatter.sources`.

## Verification

After Codex changes wiki or schema files, report:

- Which wiki/schema files changed.
- Whether `wiki/index.md` was updated when required.
- Whether `wiki/log.md` was appended when required.
- Which checks were run and their results.
- Any unresolved stale, speculative, or unverified points.

Framework maintenance normally runs the unit suite, parity check, frontmatter
validation, stale check, and `lint-wiki.py`.
