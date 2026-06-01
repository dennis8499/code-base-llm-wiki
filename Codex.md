# Codebase LLM Wiki for Codex

這份文件寫給想把 **OpenAI Codex 版 Codebase LLM Wiki** 套到自己 repo 的使用者。
[README.md](README.md) 說明 Copilot / Codex 雙入口；`AGENTS.md` 是 Codex 讀取的精簡機器指令；`Codex.md` 專注在人類如何安裝、操作、排錯與驗收 Codex 版。

---

## 雙入口同權維護

本 repo 同時支援 GitHub Copilot 與 OpenAI Codex。兩邊維護同一組 wiki 能力、邊界、安全規則與驗收結果，但用各自平台原生入口呈現：

| 能力 | GitHub Copilot 入口 | OpenAI Codex 入口 |
| --- | --- | --- |
| 全域規則 | `.github/copilot-instructions.md` | `AGENTS.md` |
| Wiki skill | `.github/skills/codebase-wiki/` | `.agents/skills/codebase-wiki/` |
| 專業 agents | `.github/agents/*.agent.md` | `.codex/agents/*.toml` |
| 對話入口 | `.github/prompts/*.prompt.md` slash prompts | 自然語言 recipe，本檔列出對應寫法 |
| Hooks | `.github/hooks/*.json` | `.codex/hooks.json` |
| Wiki 輸出 | `wiki/` | `wiki/` |

Codex 不偽造 project-level custom slash prompts。Codex IDE / CLI 的 slash commands 是控制 Codex 的內建命令；本框架在 Codex 端用自然語言 recipe 取代 Copilot prompt files。

---

## 你需要搬哪些檔案？

如果你只打算使用 Codex，最小必要集合如下：

| 路徑 | 是否必須 | 用途 |
| --- | --- | --- |
| `AGENTS.md` | 必須 | Codex 的精簡專案指令，定義 wiki 任務邊界、路由與 token 原則 |
| `.codex/` | 必須 | Codex hooks 與可委派 custom agents |
| `.agents/skills/codebase-wiki/` | 必須 | Codex repo-local skill，提供模板、reference 文件與腳本 |
| `wiki/` | 必須 | 知識庫輸出位置與初始骨架 |
| `.github/` | 選用 | 只有在你同時要支援 GitHub Copilot 版時才需要 |

建議複製方式：

```bash
cp AGENTS.md /path/to/your-repo/AGENTS.md
cp -r .codex/ /path/to/your-repo/.codex/
mkdir -p /path/to/your-repo/.agents/skills/
cp -r .agents/skills/codebase-wiki/ /path/to/your-repo/.agents/skills/codebase-wiki/
cp -r wiki/ /path/to/your-repo/wiki/
```

---

## Codex 如何執行這套框架？

日常 wiki 任務的執行模型：

1. Codex 讀 repo root 的 `AGENTS.md`
2. 任務符合 wiki 需求時，使用 `$codebase-wiki` skill
3. 需要模板、reference 或腳本時，才從 `.agents/skills/codebase-wiki/` 載入細節
4. 一般 ingest、query、lint、ADR、guide、synthesis 任務由主 agent 直接處理
5. 只有你明確要求委派、spawn、subagents 或 parallel agent work 時，才使用 `.codex/agents/*.toml`

這樣做的原因是 token 最佳化：`AGENTS.md` 保持短小，長流程放進 skill；Codex 只在需要時載入完整 skill 內容。

---

## Copilot Prompt 對應 Codex Recipe

| Copilot prompt | Codex 自然語言 recipe |
| --- | --- |
| `/ingest-module src/auth/` | `請依照 AGENTS.md 的 Interactive Ingest 流程，分析 src/auth/，先摘要主要職責、相依關係與風險，再更新 wiki。` |
| `/ingest-batch src/` | `請依照 AGENTS.md 的 batch ingest 流程掃描 src/，建立初始 wiki，最後更新 index 與 log。` |
| `/query-wiki PaymentService 如何處理退款？` | `請先查 wiki，再必要時回溯 sources，解釋 PaymentService 如何處理退款。` |
| `/lint-wiki` | `請依 AGENTS.md 的 lint 流程檢查 wiki 健康狀態，列出 critical 和 warning。` |
| `/new-adr 採用 Saga Pattern` | `請建立一份 ADR，說明為什麼採用 Saga Pattern，寫入 wiki/decisions/，並同步更新 index 與 log。` |
| `/onboarding-guide` | `請根據目前 wiki 內容產出一份 onboarding guide，存到 wiki/guides/，並更新 index 與 log。` |
| `/save-synthesis 結帳流程跨服務依賴分析` | `請把這次對結帳流程跨服務依賴的分析整理成 wiki/synthesis/ 頁面，保留來源並更新 index 與 log。` |
| `/update-index` | `請重新掃描 wiki/ 目錄，依現有 frontmatter 重建 wiki/index.md，並追加 wiki/log.md。` |

---

## Custom Agents 對照

| Copilot agent | Codex custom agent | Codex 使用時機 |
| --- | --- | --- |
| `wiki-keeper` | `.codex/agents/wiki-keeper.toml` | 明確要求路由、ADR、跨流程協調或 delegation |
| `wiki-ingest` | `.codex/agents/wiki-ingest.toml` | 明確要求委派 module / directory / batch ingest |
| `wiki-query` | `.codex/agents/wiki-query.toml` | 明確要求委派查詢、關係分析或 SQL Server live evidence lookup |
| `wiki-lint` | `.codex/agents/wiki-lint.toml` | 明確要求委派 wiki 健康檢查或修復 |
| `wiki-archaeologist` | `.codex/agents/wiki-archaeologist.toml` | 明確要求委派 git history、legacy 行為或設計脈絡分析 |

`.codex/agents/*.toml` 是可委派的 specialized agents，不是日常必切換入口。一般任務直接讓主 agent 依 `AGENTS.md` 與 `$codebase-wiki` skill 執行通常更快、更省 token。

---

## Hooks 怎麼運作？

Codex hooks 由 `.codex/config.toml` 與 `.codex/hooks.json` 啟用。

### `.codex/config.toml`

```toml
[features]
hooks = true

[agents]
max_threads = 6
max_depth = 1
```

`hooks = true` 是目前使用的 feature key。`max_depth = 1` 讓直接子代理可用，但避免遞迴 fan-out 造成 token 與 latency 膨脹。

### `.codex/hooks.json`

| 觸發時機 | 腳本 | 作用 |
| --- | --- | --- |
| `SessionStart` | `.codex/hooks/scripts/wiki-session-init.py` | 啟動或恢復 session 時摘要 `wiki/index.md` 前 60 行與 `wiki/log.md` 最近 10 筆 |
| `PreToolUse` | `.codex/hooks/scripts/wiki-write-guard.py` | 寫入前檢查 wiki / schema 邊界，避免誤改 raw sources |
| `PostToolUse` | `.codex/hooks/scripts/wiki-log-reminder.py` | wiki markdown 被修改後提醒補上 `wiki/log.md` |

Project-local hooks 需要信任 `.codex/` layer。若 hooks 尚未受信任，Codex 仍可依 `AGENTS.md` 與 skill 工作，只是少了自動 guard/reminder。
Hook audit 檔會優先寫入 `.codex/hooks/logs/`；若 Windows ACL 擋住該路徑，會退到 root-level `.codex-hook-logs/`。

---

## SQL Server Live Evidence

`wiki-query` 的資料庫證據契約與 Copilot 端一致：

- Copilot 端可在 VS Code MSSQL tools 可用時查 schema、metadata 與 bounded read-only `SELECT`
- Codex 端只有在目前環境真的暴露 SQL Server / MSSQL tool 時才可取得 live evidence
- 若 Codex 沒有可用 MSSQL tool，必須先明確告知，並詢問是否改走 GitHub Copilot、MCP、CLI 或其他 fallback

共同限制：

- 禁止 DML、DDL、`EXEC`、stored procedure execution、無限制全表掃描與 credential disclosure
- DB-derived 結果必須標註 `connected_at`、`source_tool`、`server`、`database`、`query_scope`、`result_limit`、`row_count`、`freshness_note`
- DB evidence 不得放入 wiki frontmatter `sources`

---

## 建議驗收清單

套用到目標 repo 後可快速確認：

```powershell
Test-Path AGENTS.md
Test-Path .codex\config.toml
Test-Path .codex\hooks.json
Test-Path .agents\skills\codebase-wiki\SKILL.md
Test-Path wiki\index.md
Test-Path wiki\log.md
python .agents\skills\codebase-wiki\scripts\check-stale.py wiki\
python .agents\skills\codebase-wiki\scripts\wiki-stats.py wiki\
```

若有 hook scripts：

```powershell
python -m py_compile .codex\hooks\scripts\wiki-session-init.py .codex\hooks\scripts\wiki-write-guard.py .codex\hooks\scripts\wiki-log-reminder.py
```

成功後，你可以用自然語言要求一次 ingest 或 query，確認 Codex 會先讀 wiki，再必要時回溯 sources。

---

## 常見誤解與排錯

### hooks 沒有觸發

檢查：

- `.codex/config.toml` 是否有 `hooks = true`
- `.codex/hooks.json` 是否存在
- 環境是否已信任 `.codex/` layer
- Python 是否可執行 hook scripts

### 寫入被 guard 擋下

通常表示你正在嘗試寫入 wiki/schema 邊界外的檔案。套用到一般目標 codebase 時：

- raw sources 只能讀
- `wiki/` 可以寫
- framework/schema 檔案只有在你明確維護框架本身時才應修改

### 為什麼 Codex 沒有手動切 custom agent？

這是正常行為。Codex 版主入口是 `AGENTS.md` + `$codebase-wiki` skill；custom agents 只有在你明確要求 delegation、spawn、subagents 或 parallel work 時才使用。
