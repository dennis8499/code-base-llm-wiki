# Codebase LLM Wiki for Codex

這份文件寫給想把 **Codex 版 Codebase LLM Wiki** 套到自己 repo 的使用者。  
[README.md](README.md) 負責說明整體框架與雙版本入口；`AGENTS.md` 是給 Codex 讀取的機器指令；`Codex.md` 則專注在 **人類如何安裝、操作、排錯 Codex 版**。

---

## 你需要搬哪些檔案？

如果你只打算使用 Codex，最小必要集合如下：

| 路徑 | 是否必須 | 用途 |
| --- | --- | --- |
| `AGENTS.md` | 必須 | Codex 的主要專案指令，定義 wiki 任務邊界、工作流程與禁止事項 |
| `.codex/` | 必須 | 啟用 hooks 與可委派 custom agents |
| `.agents/skills/codebase-wiki/` | 必須 | Codex repo-local skill，提供模板、reference 文件與腳本 |
| `wiki/` | 必須 | 知識庫輸出位置與初始骨架 |
| `.github/` | 非必須 | 只有在你同時要支援 GitHub Copilot 版時才需要 |

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

日常 wiki 任務的執行模型很簡單：

1. Codex 先讀 repo root 的 `AGENTS.md`
2. 偵測到你是在做 wiki 任務後，套用 `$codebase-wiki` skill
3. 需要模板、reference 文件或腳本時，從 `.agents/skills/codebase-wiki/` 取用
4. 如果你只是一般的 ingest、query、lint、ADR、guide、synthesis 任務，主 agent 直接處理
5. 只有在你**明確要求**委派、spawn、subagents 或 parallel agent work 時，才會動用 `.codex/agents/*.toml`

### 這代表什麼？

- 你平常**不用手動切 custom agent**
- 你平常**不用 slash prompt**
- 你只要用自然語言描述工作即可

例如這種寫法就夠了：

```text
請依照 AGENTS.md 的 ingest 流程，分析 src/auth/ 並更新 wiki。
```

---

## Hooks 怎麼運作？

Codex 版 hooks 由兩層設定組成：

### 1. `.codex/config.toml`

目前 repo 內啟用了：

```toml
[features]
codex_hooks = true
```

這代表專案允許 Codex hooks 生效。

### 2. `.codex/hooks.json`

這份檔案把三個 hook 接到實際腳本：

| 觸發時機 | 腳本 | 作用 |
| --- | --- | --- |
| `SessionStart` | `.codex/hooks/scripts/wiki-session-init.py` | 啟動或恢復 session 時摘要 `wiki/index.md` 與 `wiki/log.md` |
| `PreToolUse` | `.codex/hooks/scripts/wiki-write-guard.py` | 在寫入前檢查是否越界，避免誤改 raw sources |
| `PostToolUse` | `.codex/hooks/scripts/wiki-log-reminder.py` | wiki 被修改後提醒補上 `wiki/log.md` |

### 3. 還要信任 `.codex/` layer

即使檔案都在，若你的環境沒有信任 `.codex/` layer，hooks 也可能不會跑。  
這種情況下：

- `AGENTS.md` 仍然會被讀取
- repo-local skill 仍然可以使用
- 只是少了自動寫入保護、session state 與 log reminder

---

## 日常工作流範例

Codex 版一律用自然語言，不用 slash prompt。

### 1. 初始化 batch ingest

```text
請依照 AGENTS.md 的 batch ingest 流程掃描 src/，建立初始 wiki，最後更新 index 與 log。
```

### 2. 新功能上線後做增量更新

```text
請依照 AGENTS.md 的 Interactive Ingest 流程，分析 src/features/checkout/，先摘要主要職責、相依關係與風險，再更新 wiki。
```

### 3. Query

```text
請先查 wiki，再必要時回溯 sources，解釋 PaymentService 的退款流程。
```

### 4. Lint

```text
請依 AGENTS.md 的 lint 流程檢查 wiki 健康狀態，列出 critical 和 warning。
```

### 5. Archaeology

```text
請用 code archaeology 流程追蹤 discount_code 欄位的 git history，清楚區分證據與推測，最後更新 wiki。
```

### 6. ADR

```text
請建立一份 ADR，說明為什麼在結帳流程中採用 Saga Pattern，寫入 wiki/decisions/，並同步更新 index 與 log。
```

### 7. Guide / Synthesis

```text
請根據目前 wiki 內容產出一份 onboarding guide，存到 wiki/guides/，並更新 index 與 log。

請把這次對結帳流程跨服務依賴的分析整理成 wiki/synthesis/ 頁面，保留來源並更新 index 與 log。
```

---

## 什麼時候才需要 custom agents 或 subagents？

大部分情況下不需要。

### 直接交給主 agent 的情況

- 單一模組 ingest
- 一般 query
- 例行 lint
- 單份 ADR
- 單份 guide 或 synthesis

### 值得明確要求 delegation 的情況

- 你要平行處理多個互不重疊的 wiki 子任務
- 你要把 archaeology、lint、ingest 拆成獨立 sidecar 工作
- 你明確希望 Codex 使用 subagents 或 parallel agent work

### 重要限制

`.codex/agents/*.toml` 不是日常操作的必切換入口。  
這些檔案是 **可委派的 specialized agents**，不是 Copilot 那種平常手動選單式的使用方式。

---

## 常見誤解與排錯

### hooks 沒有觸發

先檢查：

- `.codex/config.toml` 是否有 `codex_hooks = true`
- `.codex/hooks.json` 是否存在
- 環境是否已信任 `.codex/` layer
- Python 是否可執行 hooks 腳本

如果 hooks 仍未生效，Codex 還是可以靠 `AGENTS.md` 與 skill 執行 wiki 流程，只是少了自動保護與提醒。

### 寫入被 guard 擋下

通常表示你正在嘗試寫入 wiki 邊界外的檔案。

在套用到一般目標 codebase 時，wiki 任務預設：

- raw sources 只能讀
- `wiki/` 可以寫
- 框架相關檔案只有在你明確維護框架本身時才應修改

如果你的任務其實是在改產品原始碼，那就不該走 wiki 任務流程。

### 為什麼我沒有手動切 custom agent？

這是正常的。Codex 版的主入口是 `AGENTS.md`，不是 `.codex/agents/*.toml`。  
主 agent 會先依 `AGENTS.md` 與 `$codebase-wiki` skill 行動；只有在你明確要求委派時，才會使用 custom agents。

### 什麼時候才值得要求 spawn 或 subagents？

當任務可被切成多個互不干擾的子工作，而且你真的希望平行處理時才值得。  
如果只是一般的單一路徑 wiki 任務，直接讓主 agent 做通常更快也更穩定。

---

## 建議驗收清單

套用完成後，可快速確認：

- `AGENTS.md` 在 repo root
- `.codex/config.toml` 與 `.codex/hooks.json` 存在
- `.agents/skills/codebase-wiki/SKILL.md` 存在
- `wiki/index.md`、`wiki/log.md`、`wiki/overview.md` 存在
- 能成功用自然語言要求一次 ingest 或 query

完成以上幾項後，你就可以把 Codex 當成這個 repo 的 wiki 維護者來使用。
