# Codebase LLM Wiki for Codex

This guide explains how to use the Codex-native entrypoint for Codebase LLM
Wiki. It is derived from the current GitHub Copilot workflow, but uses Codex
surfaces directly instead of Copilot slash prompt files.

## Codex Bundle

| Path                            | Required    | Purpose                                                       |
| ------------------------------- | ----------- | ------------------------------------------------------------- |
| `AGENTS.md`                     | Yes         | Durable Codex project rules                                   |
| `.agents/skills/codebase-wiki/` | Yes         | Skill instructions, installer, references, templates, helper scripts, and pinned tgrep bundle |
| `.codex/`                       | Recommended | Hooks and framework guard configuration                       |
| `wiki/`                         | Yes         | Generated knowledge base                                      |
| `.github/`                      | Optional    | Keep only when the repo also supports GitHub Copilot          |

The recommended installation is an idempotent dry-run followed by explicit
apply:

```powershell
python .agents\skills\codebase-wiki\scripts\install-framework.py install --target C:\path\to\your-repo --surface codex --guard-mode wiki-only --format json
python .agents\skills\codebase-wiki\scripts\install-framework.py install --target C:\path\to\your-repo --surface codex --guard-mode wiki-only --apply --format json
```

The installer defaults to `wiki-only`. Select `coexist` when normal coding and
Wiki work must share a repository session. Use `framework` only when maintaining
this framework repository; legacy `target` maps to `wiki-only`.

When upgrading an older target, replace `install` with `upgrade`. The installer
reports a legacy `.codebase-wiki/` directory through `obsolete_paths` but never
deletes it. Review that directory for user-authored content before removing it
manually.

## How Codex Uses It

1. Codex reads `AGENTS.md` before work starts.
2. Wiki requests can trigger `$codebase-wiki` implicitly, or you can invoke it explicitly.
3. The skill loads one branch reference and exact page asset only when needed.
4. The current agent performs the selected workflow under its authorization policy.
5. `.codex/hooks.json` runs after the project `.codex/` layer is trusted.

Queries use the Markdown Wiki directly. Read `wiki/index.md`, then 1–5 relevant
pages, and inspect their listed raw sources only when the Wiki is insufficient,
stale, or contradictory. The framework does not create a Wiki search database
or source-code structure index. Query does not invoke the optional tgrep source
discovery wrapper, connect to live databases, or use CLI fallbacks. Questions
that require current database state remain explicit unverified gaps.

Ingest and Code Archaeology may use the bundled Windows x64 tgrep wrapper to
locate candidate source files, symbols, imports, and exports. The wrapper is
read-only, uses an existing tgrep index/server when available, otherwise lets
tgrep scan the tree, and never starts `index` or `serve`. Always re-read current
source files before treating search output as evidence. Load
`.agents/skills/codebase-wiki/references/source-discovery-workflow.md` for its
allowlisted command contract and fallback behavior.

## Copilot Prompt To Codex Recipe

| Copilot prompt                 | Codex recipe                                                                                                           |
| ------------------------------ | ---------------------------------------------------------------------------------------------------------------------- |
| `/ingest-module {path}`        | `請依照 AGENTS.md 的 Interactive Ingest 流程，分析 {path}，先摘要主要職責、相依關係與風險，再更新 wiki。`              |
| `/ingest-batch {path}`         | `請依照 AGENTS.md 的 Batch Ingest 流程掃描 {path}，建立初始 wiki，最後更新 index 與 log。`                             |
| `/query-wiki {question}`       | `請先查 wiki，再必要時回溯 sources，回答：{question}`                                                                  |
| `/lint-wiki`                   | `請依 AGENTS.md 的 lint 流程檢查 wiki 健康狀態，列出 critical 和 warning。`                                            |
| `/new-adr {title}`             | `請建立一份 ADR：{title}，寫入 wiki/decisions/，並同步更新 index 與 log。`                                             |
| `/save-synthesis {topic}`      | `請把這次分析整理成 wiki/synthesis/{topic} 頁面，保留來源並更新 index 與 log。`                                        |
| `/code-archaeology {target}`   | `請依 code archaeology 流程追蹤 {target} 的目前行為與 git history，清楚區分證據、推測與不確定性。`                     |
| `/business-analysis-doc {scope}` | `請使用 $codebase-wiki 產出 {scope} 的 standard-aligned BA 文件，保留人工 notes、明列 Gap，並更新 index 與 log。` |
| `/system-analysis-doc {scope}` | `請基於目前 wiki 產出 {scope} 的 solution-neutral SA 文件，以 SR/NFR/IF 建立需求與驗證追溯，並更新 index 與 log。` |
| `/system-design-doc {scope}` | `請使用 $codebase-wiki 產出 {scope} 的 standard-aligned SD 文件，建立 concerns、views、DE/ADR 與 SA 追溯，並更新 index 與 log。` |
| `/export-notebooklm`          | `請使用現況 BA／SA NotebookLM export：全量預覽當下 Codebase 與缺口，取得一次確認後建立每功能 BA／SA，自動 readiness 並產生單一 Notebook 的本機 pack。` |
| `/update-index`                | `請重新掃描 wiki/ 目錄，依現有 frontmatter 重建 wiki/index.md，並追加 wiki/log.md。`                                   |

Codex CLI and IDE slash commands are platform controls. Do not add project-level
Codex slash prompt files for this framework.

## Common Workflows

Interactive ingest:

```text
請依照 AGENTS.md 的 Interactive Ingest 流程，分析 src/features/checkout/，先摘要主要職責、相依關係與風險，再更新 wiki。
```

若需定位大量 symbol 或 import/export，可在 Windows x64 使用共用 wrapper：

```powershell
python .agents\skills\codebase-wiki\scripts\tgrep-search.py `
  --root . --path src/features/checkout --fixed --files-only --pattern "CheckoutService"
```

Batch ingest:

```text
請使用 $codebase-wiki，依照 Batch Ingest 流程掃描 src/，建立初始 wiki，最後更新 index 與 log。
```

Batch Ingest 使用 tgrep 時仍須以直接讀取的目前 source 驗證候選結果；需要最新
檔案狀態時加上 `--no-index`，不執行 `tgrep index` 或 `tgrep serve`。

Wiki-first query:

```text
請先查 wiki，再必要時回溯 sources，解釋 PaymentService 如何處理退款。
```

Query 若發現長期有價值的分析、Wiki stale/gap 或品質問題，會依
`.agents/skills/codebase-wiki/references/follow-up-actions.md` 顯示最多三個
有原因的後續選項與「暫不處理」。選項只是建議；Query 不會自動寫入或
切換工作流程。

Lint:

```text
請依 AGENTS.md 的 lint 流程檢查 wiki 健康狀態，列出 critical 和 warning。
```

Lint 先回報 findings，再依相同 follow-up contract 提供安全修復、重新
Ingest 或再次 Lint 選項；任何 repair 都要等待確認。

Code archaeology:

```text
請用 code archaeology 流程追蹤 discount_code 欄位的 git history，清楚區分證據與推測，最後更新 wiki。
```

來源位置難以定位時，可先用 tgrep wrapper 的 `--fixed --files-only` 找候選檔案，
再直接讀取檔案並使用 `git log`、`git blame`、`git show` 補足歷史。

Business analysis document:

```text
請使用 $codebase-wiki，基於目前 Wiki 產出整體系統的 BA 業務分析文件，寫入 wiki/synthesis/business-analysis.md；依 business-analysis-aligned-v1 建立 coverage、BA IDs 與 gaps，並保留 user notes。
```

System analysis document:

```text
請使用 $codebase-wiki，基於 BA 與目前 Wiki 產出整體系統的 solution-neutral SA 文件，寫入 wiki/synthesis/system-analysis.md；以 SR/NFR/IF 建立可驗證需求，不放技術選型或部署設計。
```

System design document:

```text
請使用 $codebase-wiki，基於 SA 與目前 Wiki 產出整體系統的 SD 文件，寫入 wiki/synthesis/system-design.md；依 system-design-aligned-v1 建立 stakeholder concerns、VIEW/DE/ADR、元件/runtime/資料/部署/安全視圖與 gaps。
```

NotebookLM Enterprise export:

```text
請使用 $codebase-wiki 執行現況 BA／SA NotebookLM export。先執行唯讀 discovery preflight，
以 `--root` 為檔案系統邊界，盤點安全 UTF-8 runtime source、config、schema、docs 與
behavioral tests。依可觀察行為建立 `fr-*`／`cap-*`、`AC-*`、流程、規則、詞彙、證據狀態
與 gaps，從入口沿實際呼叫鏈逐步記錄觸發／條件、資料讀寫、狀態變更、結果、失敗分支與
來源定位；不要只留下四步摘要或規則連結。讓每個安全檔案都有 non-gap disposition；
PDF/Office/圖片等只登記 gap。
列出 inventory、排除、coverage、每個功能預計 BA／SA、DLP masking 與容量後等待一次確認。
確認後重建 managed sections、保留 user notes，更新 requirement/process/rule pages、每個
`cap-*` 的現況 BA／SA、local coverage ledger、index 與一筆 log，並記錄 confirmed discovery ID。
完成後自動執行 readiness preflight；只有 raw/config/scope 漂移才重新預覽。以 confirmed
`discovery_id` 與 latest `preflight_id` 產生 `.notebooklm/documents/`、只供上傳的
`.notebooklm/sources/query-index.md`、`.notebooklm/sources/project-map.md`、
`.notebooklm/sources/shared-business-context.md`、capability sources、
  schema v6 `.notebooklm/manifest.json`、`.notebooklm/governance.md` 與 `.notebooklm/upload-plan.md`；
  sources 另包含共用詞彙、流程目錄、active evidence-backed 跨功能流程的完整步驟／分支，
  以及適用需求與規則正文。將 `analysis-gap`（尚未追查完成）、`evidence-gap`（已查但無證據）、
  `business-confirmation`（實作已知但營運政策待確認）分開；只有第一種阻擋匯出。Codebase 是唯一內容依據，衝突以程式碼為主；
v1–v5 或 BA-only retrieval contract 必須 full rebuild。Exporter 不呼叫雲端 API。
```

## Hooks

`.codex/config.toml` enables Codex hooks and selects the framework guard mode:

```toml
[features]
hooks = true

[wiki_guard]
mode = "framework" # installer chooses "wiki-only" or explicit "coexist"
```

`.codex/hooks.json` configures:

| Event          | Script                                      | Purpose                                                                          |
| -------------- | ------------------------------------------- | -------------------------------------------------------------------------------- |
| `SessionStart` | shared `wiki-session-init.py` | Adds a ≤30-line / ≤4 KB Wiki state summary on `startup`, `resume`, `clear`, and `compact` |
| `PreToolUse`   | shared `wiki-write-guard.py` | Enforces `wiki-only`, `coexist`, or `framework` boundary |
| `PostToolUse`  | shared `wiki-log-reminder.py` | Reminds Codex to append `wiki/log.md` after durable edits |

All three implementations live under
`.agents/skills/codebase-wiki/scripts/hooks/`; `.codex/hooks.json` supplies
`--platform codex`.

Codex starts hooks from the session cwd. Each command therefore resolves the
Git root with `git rev-parse --show-toplevel` before joining the canonical hook
path. A non-Git installation is supported only when the session starts at its
Repo root, where the command falls back to the current directory. On Windows,
`commandWindows` uses a PowerShell wrapper plus `Join-Path`; POSIX uses
`git rev-parse ... || pwd`. This matches the
[Codex hooks guidance](https://learn.chatgpt.com/docs/hooks) and keeps spaces or
non-ASCII root paths intact.

Project-local hooks run only after Codex trusts the project `.codex/` layer. In
the CLI, use `/hooks` to review and trust new or changed hooks.

Query, Lint, and Archaeology retain their read-only or report-first boundaries
through the shared capability and workflow contracts. Prompt metadata does not
grant writes, and shell access is not a technical write sandbox; host
permissions must deny unapproved shell writes. Hook guards remain a
defense-in-depth layer and do not replace platform sandbox or host permission
controls.

Hook audit files are written to `.codex/hooks/logs/` when possible, with fallback
to `.codex-hook-logs/`. Both paths should stay ignored by git. The complete hook
I/O contract is in `.agents/skills/codebase-wiki/references/hooks-specification.md`.

## Validation Checklist

Run after installing or updating the Codex bundle:

```powershell
Test-Path AGENTS.md
Test-Path Codex.md
Test-Path .codex\config.toml
Test-Path .codex\hooks.json
Test-Path .agents\skills\codebase-wiki\SKILL.md
Test-Path .agents\skills\codebase-wiki\scripts\install-framework.py
python -m compileall -q .agents\skills\codebase-wiki\scripts
python .agents\skills\codebase-wiki\scripts\validate-frontmatter.py wiki\
python .agents\skills\codebase-wiki\scripts\check-stale.py wiki\ .
python .agents\skills\codebase-wiki\scripts\validate-log.py wiki\log.md --repo-root .
python .agents\skills\codebase-wiki\scripts\wiki-stats.py wiki\
python .agents\skills\codebase-wiki\scripts\lint-wiki.py wiki
python .agents\skills\codebase-wiki\scripts\rebuild-index.py wiki --check
python .agents\skills\codebase-wiki\scripts\parity-check.py
python .agents\skills\codebase-wiki\scripts\export-notebooklm.py --root . --preflight --format json
python .agents\skills\codebase-wiki\scripts\export-notebooklm.py --root . --apply --discovery-id DISCOVERY_ID --preflight-id PREFLIGHT_ID --output .notebooklm --format json
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

PostToolUse reports `hook exited with code 1`:

- From a Git subdirectory, run `git rev-parse --show-toplevel` and confirm it
  points to the installed framework root.
- On Windows, confirm `commandWindows` still uses the PowerShell `$wikiRoot`
  wrapper, `Get-Location` fallback, and `Join-Path` to the canonical hook.
- In a non-Git target, start Codex from the target root; a nested cwd has no
  repository marker from which to recover the installation root.
- Restart Codex and review `/hooks` so the updated project-local definition is
  trusted.

Write guard blocks a change:

- Normal wiki work should write only `wiki/`.
- In installed repos, keep `wiki-only` for dedicated Wiki work or explicitly
  install `coexist` for normal coding sessions.
- Framework maintenance uses `framework` for approved root entrypoints plus
  `docs/`, `samples/`, `tests/`, `tools/`, `wiki/`, `.github/`, `.codex/`, and `.agents/`.
- If a raw source change is desired, ask Codex for a normal coding task rather than a wiki task.

Skill does not trigger:

- Invoke it explicitly with `$codebase-wiki`.
- Check that `.agents/skills/codebase-wiki/SKILL.md` exists under the repo root or a parent directory scanned by Codex.
- Restart Codex if the skill was just added.
