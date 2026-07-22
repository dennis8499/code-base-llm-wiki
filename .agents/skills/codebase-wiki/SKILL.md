---
name: codebase-wiki
description: >
  Build, use, and maintain Codebase LLM Wiki, a persistent Markdown knowledge
  base for codebases. Use when the agent needs to install or operate this
  repo-local wiki framework, ingest modules, answer wiki-first questions, lint
  wiki health, create ADRs, save synthesis or onboarding guides, generate
  system analysis / SA documents, run code archaeology, update wiki/index.md
  or wiki/log.md, or explain how AGENTS.md,
  .codex/, .agents/skills/codebase-wiki/, .github/, and wiki/ fit together.
  Trigger on "Codebase LLM Wiki", "codebase wiki", "文件化", "知識庫",
  "ingest", "query wiki", "lint wiki", "onboarding", "程式碼考古", "技術債",
  "ADR", "SA文件", "系統分析", "system analysis", or "SAD".
---

# Codebase LLM Wiki

Use this skill to operate the Codebase LLM Wiki framework in a target repo, or
to maintain this framework repo itself. Treat the wiki as a durable Markdown
knowledge base that compounds over time. It is not RAG: query the existing wiki
first, then inspect raw sources only when the wiki is missing, stale, or
contradictory.

## Project Structure

Recognize these repo-level surfaces:

```text
AGENTS.md                         Codex rules, routing, and safety boundaries
Codex.md                          Human-facing Codex setup and usage guide
README.md                         Framework overview and install instructions
docs/                            Architecture, setup, workflows, validation, history
samples/                         Framework-only end-to-end validation codebases
tests/                           Deterministic framework regression tests
.codex/
  config.toml                     Codex hooks and bounded delegation settings
  hooks.json                      Hook wiring
  hooks/scripts/                  Guardrails and reminders
  agents/*.toml                   Optional custom agents for explicit delegation
.agents/skills/codebase-wiki/
  SKILL.md                        This workflow entrypoint
  capabilities.json                Shared intent and parity contract
  references/                     Detailed workflow specs loaded on demand
  assets/                         Page templates
    wiki-starter/                 Clean target Wiki skeleton used by installer
  scripts/                        Installer and deterministic wiki checks
  agents/openai.yaml              UI metadata for the skill
.github/                          GitHub Copilot entrypoint, prompts, agents, hooks
wiki/
  index.md                        Maintained navigation index
  log.md                          Append-only activity log
  overview.md                     Codebase overview
  architecture/ modules/ entities/
  patterns/ decisions/ dependencies/
  guides/ synthesis/              Typed wiki pages
```

In this framework repo, schema maintenance may update `README.md`, `Codex.md`,
`AGENTS.md`, `docs/`, `samples/`, `tests/`, `.codex/`, `.agents/`, `.github/`,
and `wiki/` when explicitly requested. In an installed target repo, wiki tasks
must keep raw sources read-only and write only the wiki or framework schema
files that the user asked to maintain. Framework-only `docs/`, `samples/`, and
`tests/` are not copied by the installer.

## Intent Routing

Classify the request before acting. The authoritative routing table is
`references/intent-routing.md`; keep this summary aligned with it.

| Intent | User signals | Default action |
| --- | --- | --- |
| Install / setup | install, setup, use this framework, Codex bundle | Read `README.md` and `Codex.md`; explain or copy required surfaces when requested |
| Ingest | document, analyze, ingest, add to wiki, 文件化 | Read wiki state, inspect sources read-only, then create or update wiki pages |
| Query | explain, find, where, how, 查詢 | Read `wiki/index.md`, then relevant pages; inspect sources only if needed |
| Lint | health, stale, broken links, lint, 品質 | Audit wiki quality and report findings before broad repairs |
| ADR | decision, ADR, architecture choice | Create `wiki/decisions/` record with ADR frontmatter |
| Synthesis / Guide | save analysis, onboarding, guide, synthesis | Persist durable analysis under `wiki/synthesis/` or `wiki/guides/` |
| System Analysis / SA | SA文件, 系統分析, system analysis, SAD | Generate a Markdown SA document under `wiki/synthesis/` from wiki-first evidence |
| Archaeology | why, history, legacy, git, 考古 | Trace code paths and non-destructive git history; separate evidence from inference |
| Delegation | subagents, parallel, delegation, swarm | Use `.codex/agents/*.toml` only when explicitly requested |

Ask at most one clarifying question only when local inspection cannot resolve
scope safely.

## Resource Loading

Keep `SKILL.md` as the router. Load deeper files only when the task needs them:

| Need | Load |
| --- | --- |
| Intent routing and delegation boundaries | `references/intent-routing.md` |
| Ingest sequence, page creation rules, dependency ordering | `references/ingest-workflow.md` |
| Wiki health checks, severities, report format | `references/lint-checklist.md` |
| Required frontmatter fields and allowed values | `references/frontmatter-spec.md` |
| Allowed `wiki/log.md` operations and append format | `references/log-operations.md` |
| Page structures and examples by type | `references/page-types.md` |
| ADR creation and numbering | `references/adr-workflow.md` |
| Durable guide creation | `references/guide-workflow.md` |
| Durable synthesis creation | `references/synthesis-workflow.md` |
| SA document generation, coverage map, gap handling | `references/system-analysis-workflow.md` |
| Code archaeology and git-history evidence | `references/code-archaeology-workflow.md` |
| SQL Server live evidence rules | `references/mssql-evidence-rules.md` |
| Hook trigger, I/O, and guard-mode contract | `references/hooks-specification.md` |
| New page starting points | Matching template under `assets/` |
| Stale source checks, stats, or index rebuilds | Matching script under `scripts/` |

Read the chosen reference file completely before using it. Prefer scripts for
deterministic checks instead of reimplementing parsing in prose.

## Core Rules

- Keep raw sources read-only during wiki tasks.
- Preserve user-authored wiki notes; update around them instead of overwriting.
- Use `[[page-name]]` wikilinks between wiki pages.
- Cite source paths with backticks, for example `src/auth/service.ts`.
- Put only real repo-relative paths in `frontmatter.sources`; use `sources: []`
  when there is no direct raw source.
- Distinguish source-backed facts, inference, and speculation.
- Do not create project-level Codex slash prompt files. Codex usage is through
  natural-language recipes and optional `$codebase-wiki` invocation.
- Use `.codex/agents/*.toml` only for explicit delegation requests.

## Framework Installer

Both Copilot and Codex use the dependency-free installer at
`scripts/install-framework.py`. It supports `install` and `upgrade`, plans
changes by default, and writes only when `--apply` is supplied and no conflicts
exist. The installer never deletes a legacy `.codebase-wiki/` directory from a
target repository; it reports that path through `obsolete_paths` for manual
review.

The framework repository's own `wiki/` documents this framework and is not
copied into targets. Target `wiki/` files are seeded from
`assets/wiki-starter/`, preventing framework-only sources and activity history
from leaking into installed codebases.

The framework has no local search database or source parser. Query workflows
read `wiki/index.md` and relevant Markdown pages first, then inspect listed raw
sources only when the Wiki is insufficient, stale, or contradictory.

## Wiki Update Rules

Every wiki page must follow `references/frontmatter-spec.md`. The common
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

When adding, deleting, renaming, or substantially updating wiki pages, update
`wiki/index.md`. For ingest, lint, ADR, synthesis, guide, or major wiki updates,
append a new entry to `wiki/log.md`; never delete or rewrite existing log
entries. Allowed log operations are defined in `references/log-operations.md`.

## Workflows

### Install Or Upgrade

1. Run `scripts/install-framework.py install` or `upgrade` with `--target` and
   `--surface copilot|codex` to preview the file plan.
2. Resolve any reported conflicts before rerunning with `--apply`.
3. If `obsolete_paths` reports `.codebase-wiki/`, review and remove it manually
   only when it contains no user-authored content.

### Ingest

1. Read `wiki/index.md` and recent `wiki/log.md`.
2. Load `references/ingest-workflow.md`.
3. Inspect target paths read-only, prioritizing README files, entrypoints,
   exports/imports, routes, services, models, and config.
4. For interactive ingest, summarize responsibilities, public interfaces,
   dependencies, patterns, special logic, risks, and open questions before
   writing.
5. Create or update only evidence-backed wiki pages.
6. Add cross-references, update `wiki/index.md`, and append `wiki/log.md`.

### Query

1. Read `wiki/index.md`.
2. Read 1-5 relevant wiki pages.
3. Inspect listed `sources` only when wiki content is insufficient, stale, or
   contradictory.
4. Answer with `[[wiki-page]]` links and source paths.
5. Do not persist query output unless the user asks to save it.

### Lint

1. Load `references/lint-checklist.md`.
2. Check stale sources, orphan pages, broken wikilinks, missing pages,
   frontmatter, contradictions, index completeness, and coverage.
3. Use `scripts/check-stale.py`, `scripts/wiki-stats.py`, or
   `scripts/rebuild-index.py` when useful.
4. Report Critical, Warning, and Info findings before broad automatic repairs.

### ADR, Guide, And Synthesis

- Load `references/adr-workflow.md`, `references/guide-workflow.md`, or
  `references/synthesis-workflow.md` for non-trivial persisted output.
- Use `wiki/decisions/` for ADRs, `wiki/guides/` for onboarding or operation
  guides, and `wiki/synthesis/` for durable cross-cutting analysis.
- Base content on wiki pages, raw source evidence, or clearly labeled inference.
- Update `wiki/index.md` and append `wiki/log.md` after writing.

### System Analysis Documents

- Load `references/system-analysis-workflow.md` before producing SA documents.
- Use `assets/system-analysis-template.md` as the starting structure.
- Write Markdown output under `wiki/synthesis/`; use `system-analysis.md` for
  whole-system output and `{kebab-scope}-system-analysis.md` for scoped output.
- Keep `type: synthesis` and `tags: [synthesis, system-analysis]`; do not add a
  new wiki type or `wiki/sa/` directory.
- Preserve standard SA sections and mark missing evidence as gaps instead of
  inventing system behavior.

### Code Archaeology

- Load `references/code-archaeology-workflow.md` for non-trivial archaeology.
- Start from concrete entrypoints or field names.
- Trace call paths and unusual branches.
- Use only non-destructive git commands such as `git log`, `git blame`, and
  `git show`.
- Persist findings only when requested, then update index and log.

## SQL Server Live Evidence

Use `references/mssql-evidence-rules.md` as the source of truth. In short:
SQL Server / MSSQL tools may be used only when available, only for schema
discovery, metadata lookup, connection details, and bounded read-only `SELECT`.
Never run DML, DDL, `EXEC`, stored procedure execution, unbounded scans,
credential disclosure, or persistent state changes. DB evidence requires the
metadata listed in the reference and must not be placed in frontmatter
`sources`.

## Verification

Before finishing wiki or schema work, report:

- Files changed.
- Whether `wiki/index.md` was updated when required.
- Whether `wiki/log.md` was appended when required.
- Checks run and their results.
- Any stale, speculative, skipped, or unverified points.

Useful checks:

```powershell
python .agents\skills\codebase-wiki\scripts\check-stale.py wiki\
python .agents\skills\codebase-wiki\scripts\validate-frontmatter.py wiki\
python .agents\skills\codebase-wiki\scripts\wiki-stats.py wiki\
python .agents\skills\codebase-wiki\scripts\rebuild-index.py wiki\
```
