# Codebase LLM Wiki for Codex

This guide explains how to use the Codex-native entrypoint for Codebase LLM
Wiki. It is derived from the current GitHub Copilot workflow, but uses Codex
surfaces directly instead of Copilot slash prompt files.

## Codex Bundle

| Path | Required | Purpose |
| --- | --- | --- |
| `AGENTS.md` | Yes | Durable Codex project rules |
| `.agents/skills/codebase-wiki/` | Yes | Skill instructions, references, templates, and helper scripts |
| `.codex/` | Recommended | Hooks, config, and explicit-delegation custom agents |
| `wiki/` | Yes | Generated knowledge base |
| `.github/` | Optional | Keep only when the repo also supports GitHub Copilot |

Copy into a target repository:

```powershell
Copy-Item AGENTS.md C:\path\to\your-repo\AGENTS.md
New-Item -ItemType Directory -Force C:\path\to\your-repo\.agents\skills | Out-Null
Copy-Item -Recurse .agents\skills\codebase-wiki C:\path\to\your-repo\.agents\skills\codebase-wiki
Copy-Item -Recurse .codex C:\path\to\your-repo\.codex
Copy-Item -Recurse wiki C:\path\to\your-repo\wiki
```

## How Codex Uses It

1. Codex reads `AGENTS.md` before work starts.
2. Wiki requests can trigger `$codebase-wiki` implicitly, or you can invoke it explicitly.
3. The skill loads detailed references and scripts only when needed.
4. Most work should stay in the main agent.
5. `.codex/agents/*.toml` are for explicit delegation, subagents, or parallel work.
6. `.codex/hooks.json` runs after the project `.codex/` layer is trusted.

## Copilot Prompt To Codex Recipe

| Copilot prompt | Codex recipe |
| --- | --- |
| `/ingest-module {path}` | `請依照 AGENTS.md 的 Interactive Ingest 流程，分析 {path}，先摘要主要職責、相依關係與風險，再更新 wiki。` |
| `/ingest-batch {path}` | `請依照 AGENTS.md 的 Batch Ingest 流程掃描 {path}，建立初始 wiki，最後更新 index 與 log。` |
| `/query-wiki {question}` | `請先查 wiki，再必要時回溯 sources，回答：{question}` |
| `/lint-wiki` | `請依 AGENTS.md 的 lint 流程檢查 wiki 健康狀態，列出 critical 和 warning。` |
| `/new-adr {title}` | `請建立一份 ADR：{title}，寫入 wiki/decisions/，並同步更新 index 與 log。` |
| `/onboarding-guide` | `請根據目前 wiki 內容產出一份 onboarding guide，存到 wiki/guides/，並更新 index 與 log。` |
| `/save-synthesis {topic}` | `請把這次分析整理成 wiki/synthesis/{topic} 頁面，保留來源並更新 index 與 log。` |
| `/system-analysis-doc {scope}` | `請基於目前 wiki 內容產出 {scope} 的 SA 系統分析文件，寫入 wiki/synthesis/，標示 coverage gaps，並更新 index 與 log。` |
| `/update-index` | `請重新掃描 wiki/ 目錄，依現有 frontmatter 重建 wiki/index.md，並追加 wiki/log.md。` |

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

System analysis document:

```text
請使用 $codebase-wiki，基於目前 wiki 內容產出整體系統的 SA 系統分析文件，寫入 wiki/synthesis/system-analysis.md，標示 coverage gaps，並更新 index 與 log。
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

[agents]
max_threads = 6
max_depth = 1
```

`.codex/hooks.json` configures:

| Event | Script | Purpose |
| --- | --- | --- |
| `SessionStart` | `.codex/hooks/scripts/wiki-session-init.py` | Adds bounded wiki state context |
| `PreToolUse` | `.codex/hooks/scripts/wiki-write-guard.py` | Blocks unexpected writes outside wiki/schema/framework paths |
| `PostToolUse` | `.codex/hooks/scripts/wiki-log-reminder.py` | Reminds Codex to append `wiki/log.md` after wiki page edits |

Project-local hooks run only after Codex trusts the project `.codex/` layer. In
the CLI, use `/hooks` to review and trust new or changed hooks.

Hook audit files are written to `.codex/hooks/logs/` when possible, with fallback
to `.codex-hook-logs/`. Both paths should stay ignored by git.

## SQL Server Live Evidence

The Codex query workflow supports SQL Server live evidence only when the active
Codex environment exposes MSSQL tools or an approved MCP/app/CLI fallback.

Allowed:

- Connection metadata.
- Schema discovery.
- Metadata lookup.
- Bounded read-only `SELECT`.

Forbidden:

- DML or DDL.
- `EXEC` or stored procedure execution.
- Unbounded table scans.
- Credential disclosure.
- Any operation that changes persistent database state.

Every DB-derived answer must include `connected_at`, `source_tool`, `server`,
`database`, `query_scope`, `result_limit`, `row_count`, and `freshness_note`. DB
evidence must not be put in frontmatter `sources`.

## Validation Checklist

Run after installing or updating the Codex bundle:

```powershell
Test-Path AGENTS.md
Test-Path Codex.md
Test-Path .codex\config.toml
Test-Path .codex\hooks.json
Test-Path .agents\skills\codebase-wiki\SKILL.md
python -m py_compile .codex\hooks\scripts\wiki-session-init.py .codex\hooks\scripts\wiki-write-guard.py .codex\hooks\scripts\wiki-log-reminder.py
python -m py_compile .agents\skills\codebase-wiki\scripts\frontmatter.py .agents\skills\codebase-wiki\scripts\check-stale.py .agents\skills\codebase-wiki\scripts\rebuild-index.py .agents\skills\codebase-wiki\scripts\wiki-stats.py
python .agents\skills\codebase-wiki\scripts\check-stale.py wiki\
python .agents\skills\codebase-wiki\scripts\wiki-stats.py wiki\
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
- Framework maintenance may also update `AGENTS.md`, `Codex.md`, `README.md`, `ChangeLog.md`, `.github/`, `.codex/`, and `.agents/`.
- If a raw source change is desired, ask Codex for a normal coding task rather than a wiki task.

Skill does not trigger:

- Invoke it explicitly with `$codebase-wiki`.
- Check that `.agents/skills/codebase-wiki/SKILL.md` exists under the repo root or a parent directory scanned by Codex.
- Restart Codex if the skill was just added.
