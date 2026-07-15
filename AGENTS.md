# AGENTS.md - Codebase LLM Wiki for Codex

This file is the Codex project guidance for Codebase LLM Wiki. Keep it short:
long workflows, templates, references, and scripts live in `$codebase-wiki` at
`.agents/skills/codebase-wiki/`.

This repository is the framework repository, so Codex may update framework files
such as `README.md`, `ChangeLog.md`, `AGENTS.md`, `Codex.md`, `.github/`,
`.codex/`, `.agents/`, and `wiki/` when the user explicitly asks for framework
maintenance. When the framework is installed into a target codebase, wiki tasks
must treat that target codebase as raw source and keep it read-only.

## Core Model

Codebase LLM Wiki is not RAG. It is a persistent Markdown wiki that compounds
knowledge over time.

| Layer       | Location                                                | Responsibility                                                   |
| ----------- | ------------------------------------------------------- | ---------------------------------------------------------------- |
| Raw Sources | Source code, config, existing docs                      | Read-only during wiki tasks                                      |
| Wiki        | `wiki/`                                                 | Codex-generated and maintained knowledge base                    |
| Schema      | `AGENTS.md`, `.agents/skills/codebase-wiki/`, `.codex/` | Rules, workflows, templates, scripts, hooks, and optional agents |

## Codex Surfaces

- Use `AGENTS.md` for durable repo rules and routing.
- Use `$codebase-wiki` for detailed wiki workflows.
- Use `.codex/hooks.json` and `.codex/hooks/scripts/` as deterministic guardrails and reminders.
- Use `.codex/agents/*.toml` only when the user explicitly asks for delegation, subagents, or parallel agent work.
- Do not create project-level Codex slash prompts for this framework. Codex usage is through natural language recipes and optional `$codebase-wiki` invocation.

## Intent Routing

Classify the user's wiki request before acting. The full routing source of
truth is `.agents/skills/codebase-wiki/references/intent-routing.md`.

| Intent               | Signals                                          | Workflow                                                                         |
| -------------------- | ------------------------------------------------ | -------------------------------------------------------------------------------- |
| Install / setup      | install, setup, use this framework, Codex bundle | Explain or copy the required entrypoint surfaces                                 |
| Ingest               | document, analyze, ingest, add to wiki, 文件化   | Read raw sources and update wiki pages                                           |
| Query                | explain, find, where, how, 查詢                  | Read wiki first, then sources only if needed                                     |
| Lint                 | health, stale, broken links, lint, 品質          | Audit wiki quality and report before broad fixes                                 |
| Archaeology          | why, history, legacy, git, 考古                  | Trace code paths and non-destructive git history                                 |
| ADR                  | decision, ADR, architecture choice               | Create `wiki/decisions/` record                                                  |
| Synthesis / Guide    | save analysis, onboarding, guide, synthesis      | Persist durable analysis under `wiki/synthesis/` or `wiki/guides/`               |
| System Analysis / SA | SA文件, 系統分析, system analysis, SAD           | Generate a Markdown SA document under `wiki/synthesis/` from wiki-first evidence |
| Delegation           | subagents, parallel, delegation, swarm           | Use `.codex/agents/*.toml` only when explicitly requested                        |

Ask a concise clarifying question only when local inspection cannot resolve
scope or intent safely.

## Wiki Rules

- Raw sources are read-only during wiki tasks.
- Codex may create and update Markdown pages under `wiki/`.
- `wiki/log.md` is append-only. Do not delete or rewrite existing log entries.
- Any wiki page add, delete, rename, or major update must be reflected in `wiki/index.md`.
- Any ingest, lint, ADR, synthesis, guide, SA document, or major wiki update must append `wiki/log.md`.
- `frontmatter.sources` must point to real repo-relative paths. Use `sources: []` when there is no direct raw source.
- Mention wiki pages with Obsidian-style `[[page-name]]` wikilinks, not relative Markdown links.
- Cite source paths with backticks, for example `src/auth/service.ts`.
- Distinguish evidence-backed statements from inference or speculation.
- Preserve user-authored wiki content; do not overwrite manual notes with regenerated text.

## Wiki Structure

```text
wiki/
├── index.md
├── log.md
├── overview.md
├── architecture/
├── modules/
├── entities/
├── patterns/
├── decisions/
├── dependencies/
├── guides/
└── synthesis/
```

## Frontmatter

Every wiki page must follow
`.agents/skills/codebase-wiki/references/frontmatter-spec.md`. The common
required fields are:

```yaml
---
title: Page Title
type: module | entity | pattern | decision | dependency | guide | synthesis | overview | architecture | index | log
sources:
  - path/to/source/file.ts
last_updated: YYYY-MM-DD
tags: [tag1, tag2]
status: active | stale | placeholder
---
```

`wiki/index.md` uses `type: index`; `wiki/log.md` uses `type: log`. Both still
need `sources: []`, `tags`, `last_updated`, and `status`.

ADR, dependency, index, and log page-specific fields are defined in
`frontmatter-spec.md`.

## Workflow Summaries

Ingest:

1. Load `.agents/skills/codebase-wiki/references/ingest-workflow.md`.
2. Read `wiki/index.md` and recent `wiki/log.md`.
3. Inspect target paths, prioritizing README files, entrypoints, exports/imports, routes, services, models, and config.
4. Summarize responsibilities, public interfaces, dependencies, patterns, special logic, and risks before writing when the task is interactive.
5. Create or update wiki pages only when source evidence supports them.
6. Add cross-references, rebuild or update `wiki/index.md`, and append `wiki/log.md`.

Query:

1. Read `wiki/index.md`.
2. Read 1-5 relevant wiki pages.
3. Inspect `sources` only when wiki content is insufficient, stale, or contradictory.
4. Answer with wiki links and source paths. Do not persist query results unless the user confirms.

System Analysis / SA:

1. Load `.agents/skills/codebase-wiki/references/system-analysis-workflow.md`.
2. Build the SA document from wiki pages first, then inspect raw sources only for gaps, stale content, or contradictions.
3. Write Markdown output under `wiki/synthesis/` using `type: synthesis` and `tags: [synthesis, system-analysis]`.
4. Preserve standard SA sections and mark missing evidence as gaps instead of inventing behavior.
5. Update `wiki/index.md` and append `wiki/log.md`.

ADR / Synthesis / Guide:

1. Load the matching workflow reference: `adr-workflow.md`,
   `synthesis-workflow.md`, or `guide-workflow.md`.
2. Persist only evidence-backed durable content under `wiki/decisions/`,
   `wiki/synthesis/`, or `wiki/guides/`.
3. Update `wiki/index.md` and append `wiki/log.md` with the operation from
   `.agents/skills/codebase-wiki/references/log-operations.md`.

Lint:

1. Load `.agents/skills/codebase-wiki/references/lint-checklist.md`.
2. Check stale sources, orphan pages, broken wikilinks, missing pages, frontmatter, contradictions, index completeness, and coverage.
3. Use helper scripts under `.agents/skills/codebase-wiki/scripts/` when useful.
4. Report findings by severity before broad repairs.

Archaeology:

1. Load `.agents/skills/codebase-wiki/references/code-archaeology-workflow.md`.
2. Start from concrete entrypoints.
3. Trace call paths and unusual branches.
4. Use only non-destructive git commands such as `git log`, `git blame`, and `git show`.
5. Persist findings only when requested, then update index/log.

## SQL Server Live Evidence

For query tasks that need database facts, use
`.agents/skills/codebase-wiki/references/mssql-evidence-rules.md` as the source
of truth. In short: use SQL Server / MSSQL tools only when available; allow only
schema discovery, metadata lookup, connection details, and bounded read-only
`SELECT`; never run DML, DDL, `EXEC`, stored procedure execution, unbounded
scans, credential disclosure, or persistent state changes. DB evidence requires
the reference metadata and must not be placed in frontmatter `sources`.

## Verification

After Codex changes wiki or schema files, report:

- Which wiki/schema files changed.
- Whether `wiki/index.md` was updated when required.
- Whether `wiki/log.md` was appended when required.
- Which checks were run and their results.
- Any unresolved stale, speculative, or unverified points.
