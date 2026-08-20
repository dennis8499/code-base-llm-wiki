# Codebase LLM Wiki for Codex

This guide explains how to use the Codex-native entrypoint for Codebase LLM
Wiki. It is derived from the current GitHub Copilot workflow, but uses Codex
surfaces directly instead of Copilot slash prompt files.

## Codex Bundle

| Path                            | Required    | Purpose                                                       |
| ------------------------------- | ----------- | ------------------------------------------------------------- |
| `AGENTS.md`                     | Yes         | Durable Codex project rules                                   |
| `.agents/skills/codebase-wiki/` | Yes         | Skill instructions, installer, references, templates, and helper scripts |
| `.codex/`                       | Recommended | Hooks, config, and explicit-delegation custom agents          |
| `wiki/`                         | Yes         | Generated knowledge base                                      |
| `.github/`                      | Optional    | Keep only when the repo also supports GitHub Copilot          |

The recommended installation is an idempotent dry-run followed by explicit
apply:

```powershell
python .agents\skills\codebase-wiki\scripts\install-framework.py install --target C:\path\to\your-repo --surface codex --format json
python .agents\skills\codebase-wiki\scripts\install-framework.py install --target C:\path\to\your-repo --surface codex --apply --format json
```

The installer uses target mode for application repositories. Use framework mode
only when maintaining this framework repository.

When upgrading an older target, replace `install` with `upgrade`. The installer
reports a legacy `.codebase-wiki/` directory through `obsolete_paths` but never
deletes it. Review that directory for user-authored content before removing it
manually.

## How Codex Uses It

1. Codex reads `AGENTS.md` before work starts.
2. Wiki requests can trigger `$codebase-wiki` implicitly, or you can invoke it explicitly.
3. The skill loads one branch reference and exact page asset only when needed.
4. Most work should stay in the main agent.
5. `.codex/agents/*.toml` are for explicit delegation, subagents, or parallel work.
6. `.codex/hooks.json` runs after the project `.codex/` layer is trusted.

Queries use the Markdown Wiki directly. Read `wiki/index.md`, then 1–5 relevant
pages, and inspect their listed raw sources only when the Wiki is insufficient,
stale, or contradictory. The framework does not create a local search database
or source-code structure index.

## Copilot Prompt To Codex Recipe

| Copilot prompt                 | Codex recipe                                                                                                           |
| ------------------------------ | ---------------------------------------------------------------------------------------------------------------------- |
| `/ingest-module {path}`        | `請依照 AGENTS.md 的 Interactive Ingest 流程，分析 {path}，先摘要主要職責、相依關係與風險，再更新 wiki。`              |
| `/ingest-batch {path}`         | `請依照 AGENTS.md 的 Batch Ingest 流程掃描 {path}，建立初始 wiki，最後更新 index 與 log。`                             |
| `/query-wiki {question}`       | `請先查 wiki，再必要時回溯 sources，回答：{question}`                                                                  |
| `/lint-wiki`                   | `請依 AGENTS.md 的 lint 流程檢查 wiki 健康狀態，列出 critical 和 warning。`                                            |
| `/new-adr {title}`             | `請建立一份 ADR：{title}，寫入 wiki/decisions/，並同步更新 index 與 log。`                                             |
| `/onboarding-guide`            | `請根據目前 wiki 內容產出一份 onboarding guide，存到 wiki/guides/，並更新 index 與 log。`                              |
| `/save-guide {topic}`          | `請把目前分析整理成 wiki/guides/{topic} 指南，標示來源、gap 與步驟，並更新 index 與 log。`                             |
| `/save-synthesis {topic}`      | `請把這次分析整理成 wiki/synthesis/{topic} 頁面，保留來源並更新 index 與 log。`                                        |
| `/code-archaeology {target}`   | `請依 code archaeology 流程追蹤 {target} 的目前行為與 git history，清楚區分證據、推測與不確定性。`                     |
| `/system-analysis-doc {scope}` | `請基於目前 wiki 內容產出 {scope} 的 SA 系統分析文件，寫入 wiki/synthesis/，標示 coverage gaps，並更新 index 與 log。` |
| `/export-notebooklm`          | `請使用 NotebookLM export 流程：以 Wiki 為基線全量掃描安全的 runtime/config/schema/docs，先預覽功能 Ingest，確認後增量更新繁中 Wiki 並產生 .notebooklm pack。` |
| `/update-index`                | `請重新掃描 wiki/ 目錄，依現有 frontmatter 重建 wiki/index.md，並追加 wiki/log.md。`                                   |

Codex CLI and IDE slash commands are platform controls. Do not add project-level
Codex slash prompt files for this framework.

## Common Workflows

Interactive ingest:

```text
請依照 AGENTS.md 的 Interactive Ingest 流程，分析 src/features/checkout/，先摘要主要職責、相依關係與風險，再更新 wiki。
```

Batch ingest:

```text
請使用 $codebase-wiki，依照 Batch Ingest 流程掃描 src/，建立初始 wiki，最後更新 index 與 log。
```

Wiki-first query:

```text
請先查 wiki，再必要時回溯 sources，解釋 PaymentService 如何處理退款。
```

Lint:

```text
請依 AGENTS.md 的 lint 流程檢查 wiki 健康狀態，列出 critical 和 warning。
```

Code archaeology:

```text
請用 code archaeology 流程追蹤 discount_code 欄位的 git history，清楚區分證據與推測，最後更新 wiki。
```

Durable guide:

```text
請使用 $codebase-wiki，把這次排查流程整理成 wiki/guides/refund-debugging.md，寫清楚目標讀者、前置條件、步驟、常見問題與 gap，並更新 index 與 log。
```

System analysis document:

```text
請使用 $codebase-wiki，基於目前 wiki 內容產出整體系統的 SA 系統分析文件，寫入 wiki/synthesis/system-analysis.md，標示 coverage gaps，並更新 index 與 log。
```

NotebookLM Enterprise export:

```text
請使用 $codebase-wiki 執行 NotebookLM export：先讀完整 Wiki，再執行 exporter
的唯讀 --preflight，掃描全部 runtime source、必要 config/manifests、schema/migrations
與既有文件；排除 tests、CI/CD、IaC、build/dev tooling、依賴、產物、binary、secret
與 framework adapters。依 entrypoint/use case/data boundary 建立功能 coverage，列出
Wiki/evidence/容量預覽並等待確認。確認後只增量更新繁中功能文件、index 與一筆
ingest log，再產生 .notebooklm source pack、manifest 與 upload plan。文件優先，
因額度略過的 evidence 必須明列；不呼叫雲端 API。
```

Explicit delegation:

```text
請使用 delegation，把工作拆成兩條平行子任務：委派 wiki-ingest 分析 src/features/checkout/，委派 wiki-lint 做全站健康檢查，最後整合結果。
```

## Hooks

`.codex/config.toml` enables Codex hooks and keeps subagent fan-out bounded:

```toml
[features]
hooks = true

[wiki_guard]
mode = "framework" # change to "target" after installing into an application repo

[agents]
max_threads = 6
max_depth = 1
```

`.codex/hooks.json` configures:

| Event          | Script                                      | Purpose                                                                          |
| -------------- | ------------------------------------------- | -------------------------------------------------------------------------------- |
| `SessionStart` | shared `wiki-session-init.py` | Adds a ≤30-line / ≤4 KB Wiki state summary |
| `PreToolUse`   | shared `wiki-write-guard.py` | Enforces the configured `target` or `framework` boundary |
| `PostToolUse`  | shared `wiki-log-reminder.py` | Reminds Codex to append `wiki/log.md` after durable edits |

All three implementations live under
`.agents/skills/codebase-wiki/scripts/hooks/`; `.codex/hooks.json` supplies
`--platform codex`.

Project-local hooks run only after Codex trusts the project `.codex/` layer. In
the CLI, use `/hooks` to review and trust new or changed hooks.

Hook audit files are written to `.codex/hooks/logs/` when possible, with fallback
to `.codex-hook-logs/`. Both paths should stay ignored by git. The complete hook
I/O contract is in `.agents/skills/codebase-wiki/references/hooks-specification.md`.

## SQL Server Live Evidence

The Codex query workflow supports SQL Server live evidence only when the active
Codex environment exposes MSSQL tools or an approved MCP/app/CLI fallback. The
source of truth is
`.agents/skills/codebase-wiki/references/mssql-evidence-rules.md`.

Summary: allow schema discovery, metadata lookup, connection details, and
bounded read-only `SELECT`; forbid DML, DDL, `EXEC`, stored procedure execution,
unbounded scans, credential disclosure, and persistent state changes. DB-derived
answers must include the metadata listed in the reference, and DB evidence must
not be put in frontmatter `sources`.

## Validation Checklist

Run after installing or updating the Codex bundle:

```powershell
Test-Path AGENTS.md
Test-Path Codex.md
Test-Path .codex\config.toml
Test-Path .codex\hooks.json
Test-Path .agents\skills\codebase-wiki\SKILL.md
Test-Path .agents\skills\codebase-wiki\scripts\install-framework.py
python -m py_compile .agents\skills\codebase-wiki\scripts\hooks\common.py .agents\skills\codebase-wiki\scripts\hooks\wiki-session-init.py .agents\skills\codebase-wiki\scripts\hooks\wiki-write-guard.py .agents\skills\codebase-wiki\scripts\hooks\wiki-log-reminder.py
python -m py_compile .agents\skills\codebase-wiki\scripts\install-framework.py .agents\skills\codebase-wiki\scripts\frontmatter.py .agents\skills\codebase-wiki\scripts\check-stale.py .agents\skills\codebase-wiki\scripts\validate-frontmatter.py .agents\skills\codebase-wiki\scripts\rebuild-index.py .agents\skills\codebase-wiki\scripts\wiki-stats.py
python .agents\skills\codebase-wiki\scripts\validate-frontmatter.py wiki\
python .agents\skills\codebase-wiki\scripts\check-stale.py wiki\
python .agents\skills\codebase-wiki\scripts\wiki-stats.py wiki\
python .agents\skills\codebase-wiki\scripts\lint-wiki.py wiki
python .agents\skills\codebase-wiki\scripts\rebuild-index.py wiki --check
python .agents\skills\codebase-wiki\scripts\parity-check.py
python .agents\skills\codebase-wiki\scripts\export-notebooklm.py --root . --preflight --format json
python .agents\skills\codebase-wiki\scripts\export-notebooklm.py --root . --output .notebooklm --format json
```

Ask Codex to confirm setup:

```text
請列出你目前載入的 AGENTS.md 規則與可用的 codebase-wiki skill。
```

## Troubleshooting

Hooks do not run:

- Confirm `.codex/config.toml` contains `[features] hooks = true`.
- Open `/hooks` and trust the project-local hook definitions.
- Confirm Python is available.
- Restart Codex after changing config or hooks.

Write guard blocks a change:

- Normal wiki work should write only `wiki/`.
- In installed target repos, keep `.codex/config.toml` `[wiki_guard] mode = "target"`.
- Framework maintenance may set `[wiki_guard] mode = "framework"` to update the approved root entrypoints plus `docs/`, `samples/`, `tests/`, `wiki/`, `.github/`, `.codex/`, and `.agents/`.
- If a raw source change is desired, ask Codex for a normal coding task rather than a wiki task.

Skill does not trigger:

- Invoke it explicitly with `$codebase-wiki`.
- Check that `.agents/skills/codebase-wiki/SKILL.md` exists under the repo root or a parent directory scanned by Codex.
- Restart Codex if the skill was just added.
