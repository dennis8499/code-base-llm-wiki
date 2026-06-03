# Codebase LLM Wiki for Codex

This guide is for people who want to use the OpenAI Codex version of Codebase LLM Wiki in a repository. `AGENTS.md` is the short machine-readable rule file; this document explains how to install, operate, verify, and troubleshoot the Codex entrypoint.

## Why Codex Is Different From Copilot Here

This repo supports both GitHub Copilot and OpenAI Codex, but each entrypoint uses its own native surfaces.

| Capability | GitHub Copilot | OpenAI Codex |
| --- | --- | --- |
| Persistent repo rules | `.github/copilot-instructions.md` | `AGENTS.md` |
| Reusable workflow | `.github/skills/codebase-wiki/` | `.agents/skills/codebase-wiki/` |
| Prompt entrypoints | `.github/prompts/*.prompt.md` | Natural language recipes and `$codebase-wiki` |
| Specialized agents | `.github/agents/*.agent.md` | `.codex/agents/*.toml`, explicit delegation only |
| Hooks | `.github/hooks/*.json` | `.codex/hooks.json` |
| Output | `wiki/` | `wiki/` |

Codex does not use project-level custom slash prompt files for this framework. Codex CLI and IDE slash commands are platform controls. Daily wiki operations should be phrased as natural language requests or explicit `$codebase-wiki` skill calls.

## Files To Copy Into A Target Repo

Minimum Codex bundle:

| Path | Required | Purpose |
| --- | --- | --- |
| `AGENTS.md` | Yes | Durable Codex project rules |
| `.agents/skills/codebase-wiki/` | Yes | Skill instructions, references, templates, and helper scripts |
| `.codex/` | Recommended | Hooks, config, and explicit-delegation custom agents |
| `wiki/` | Yes | Generated knowledge base |
| `.github/` | Optional | Only needed if the repo also supports GitHub Copilot |

Example copy commands:

```bash
cp AGENTS.md /path/to/your-repo/AGENTS.md
mkdir -p /path/to/your-repo/.agents/skills
cp -r .agents/skills/codebase-wiki /path/to/your-repo/.agents/skills/codebase-wiki
cp -r .codex /path/to/your-repo/.codex
cp -r wiki /path/to/your-repo/wiki
```

On Windows PowerShell:

```powershell
Copy-Item AGENTS.md C:\path\to\your-repo\AGENTS.md
New-Item -ItemType Directory -Force C:\path\to\your-repo\.agents\skills | Out-Null
Copy-Item -Recurse .agents\skills\codebase-wiki C:\path\to\your-repo\.agents\skills\codebase-wiki
Copy-Item -Recurse .codex C:\path\to\your-repo\.codex
Copy-Item -Recurse wiki C:\path\to\your-repo\wiki
```

## How Codex Uses The Bundle

1. Codex reads repo `AGENTS.md` before doing work.
2. When a request matches wiki work, Codex uses `$codebase-wiki`.
3. The skill loads detailed references, templates, and scripts only when needed.
4. Most tasks run in the main agent to save tokens.
5. `.codex/agents/*.toml` are used only when you explicitly ask Codex to delegate, spawn subagents, or run parallel agent work.
6. `.codex/hooks.json` loads project-local hooks after the project `.codex/` layer is trusted.

## Copilot Prompt To Codex Recipe

| Copilot prompt | Codex recipe |
| --- | --- |
| `/ingest-module src/auth/` | `請依照 AGENTS.md 的 Interactive Ingest 流程，分析 src/auth/，先摘要主要職責、相依關係與風險，再更新 wiki。` |
| `/ingest-batch src/` | `請依照 AGENTS.md 的 batch ingest 流程掃描 src/，建立初始 wiki，最後更新 index 與 log。` |
| `/query-wiki PaymentService 如何處理退款？` | `請先查 wiki，再必要時回溯 sources，解釋 PaymentService 如何處理退款。` |
| `/lint-wiki` | `請依 AGENTS.md 的 lint 流程檢查 wiki 健康狀態，列出 critical 和 warning。` |
| `/new-adr 採用 Saga Pattern` | `請建立一份 ADR，說明為什麼採用 Saga Pattern，寫入 wiki/decisions/，並同步更新 index 與 log。` |
| `/onboarding-guide` | `請根據目前 wiki 內容產出一份 onboarding guide，存到 wiki/guides/，並更新 index 與 log。` |
| `/save-synthesis 結帳流程跨服務依賴分析` | `請把這次對結帳流程跨服務依賴的分析整理成 wiki/synthesis/ 頁面，保留來源並更新 index 與 log。` |
| `/update-index` | `請重新掃描 wiki/ 目錄，依現有 frontmatter 重建 wiki/index.md，並追加 wiki/log.md。` |

## Common Workflows

Interactive ingest:

```text
請依照 AGENTS.md 的 Interactive Ingest 流程，分析 src/features/checkout/，先摘要主要職責、相依關係與風險，再更新 wiki。
```

Expected output:

- One or more pages under `wiki/modules/`, `wiki/entities/`, `wiki/patterns/`, or `wiki/dependencies/`.
- Updated `wiki/index.md`.
- Appended `wiki/log.md`.

Wiki-first query:

```text
請先查 wiki，再必要時回溯 sources，解釋 PaymentService 如何處理退款。
```

Expected output:

- Answer cites `[[wiki-page]]`.
- Source paths appear only when wiki evidence is insufficient or needs verification.
- No files are edited unless you ask Codex to save the synthesis.

Lint:

```text
請依 AGENTS.md 的 lint 流程檢查 wiki 健康狀態，列出 critical 和 warning。
```

Expected output:

- Findings grouped as Critical, Warning, or Info.
- Broad fixes are proposed before they are applied.

Archaeology:

```text
請用 code archaeology 流程追蹤 discount_code 欄位的 git history，清楚區分證據與推測，最後更新 wiki。
```

Expected output:

- Entry point and call-path explanation.
- Non-destructive git evidence from `git log`, `git blame`, or `git show`.
- Persisted wiki updates only when requested.

Delegation:

```text
請使用 delegation，把工作拆成兩條平行子任務：委派 wiki-ingest 分析 src/features/checkout/，委派 wiki-lint 做全站健康檢查，最後整合結果。
```

Expected output:

- Codex may spawn `.codex/agents/wiki-ingest.toml` and `.codex/agents/wiki-lint.toml`.
- The parent agent consolidates results.
- Raw sources remain read-only.

## Hooks

`.codex/config.toml` enables hooks:

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
| `SessionStart` | `.codex/hooks/scripts/wiki-session-init.py` | Adds a bounded wiki state summary as Codex context |
| `PreToolUse` | `.codex/hooks/scripts/wiki-write-guard.py` | Blocks unexpected writes outside wiki/schema/framework paths |
| `PostToolUse` | `.codex/hooks/scripts/wiki-log-reminder.py` | Reminds Codex to append `wiki/log.md` after wiki page edits |

Project-local hooks run only after Codex trusts the project `.codex/` layer. In the CLI, use `/hooks` to review and trust changed hooks. If hooks are not trusted yet, Codex can still follow `AGENTS.md` and `$codebase-wiki`; it simply loses the automatic guard/reminder layer.

Hook audit files are written to `.codex/hooks/logs/` when possible, with fallback to `.codex-hook-logs/`. Both paths should stay ignored by git.

## SQL Server Live Evidence

The Codex query workflow supports SQL Server live evidence only when the active Codex environment exposes MSSQL tools.

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

Every DB-derived answer must include `connected_at`, `source_tool`, `server`, `database`, `query_scope`, `result_limit`, `row_count`, and `freshness_note`. DB evidence must not be put in frontmatter `sources`.

## Validation Checklist

Run these checks after installing or updating the Codex bundle:

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

For CLI setup, also ask Codex:

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

- For normal target codebases, wiki tasks should write only `wiki/`.
- Framework maintenance may also update `AGENTS.md`, `Codex.md`, `README.md`, `ChangeLog.md`, `.github/`, `.codex/`, and `.agents/`.
- If a raw source change is actually desired, ask Codex for a normal coding task rather than a wiki task.

Codex does not use custom agents:

- This is expected. Custom agents are for explicit delegation/subagents, not day-to-day wiki work.

Skill does not trigger:

- Invoke it explicitly with `$codebase-wiki`.
- Check that `.agents/skills/codebase-wiki/SKILL.md` exists under the repo root or a parent directory scanned by Codex.
- Restart Codex if the skill was just added.
