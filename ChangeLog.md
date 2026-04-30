# Changelog

本檔案記錄 Codebase LLM Wiki 框架的所有重要變更。格式基於 [Keep a Changelog](https://keepachangelog.com/)。

---

## [Unreleased] — 2026-04-29

### 新增

- **新增 OpenAI Codex 版入口**：加入根目錄 `AGENTS.md`，將 Codebase LLM Wiki 的意圖路由、Ingest / Query / Lint / Archaeology / ADR 工作流程、frontmatter 規格與禁止事項整理成 Codex 可直接讀取的專案指令
- **README 新增雙版本使用說明**：補上 GitHub Copilot 版與 OpenAI Codex 版的支援矩陣、安裝方式、快速開始、自然語言工作流與相容性說明
- **wiki-query 建議行動與自動交接（Hand-Off）功能**：查詢代理在產生建議後，會透過 `vscode/askQuestions` 向使用者呈現可執行的行動清單，使用者確認後自動委派給對應的專業子代理執行。
  - 三種建議行動類型：
    - `save-synthesis`：將有持續價值的綜合分析存入 `wiki/synthesis/`（委派 `wiki-keeper`）
    - `re-ingest`：對內容過時的 wiki 頁面重新執行知識攝入（委派 `wiki-ingest`）
    - `lint-fix`：修復斷裂連結、缺失 frontmatter 等品質問題（委派 `wiki-lint`）
  - 標準化的交接摘要格式，確保子代理獲得充足的背景脈絡
- **wiki-query 新增子代理協作能力**：工具清單加入 `agent` 與 `vscode/askQuestions`，代理清單加入 `wiki-ingest`、`wiki-lint`、`wiki-keeper`
- **新增無外部依賴的 frontmatter parser**：加入 `.github/skills/codebase-wiki/scripts/frontmatter.py`，讓 `check-stale.py`、`rebuild-index.py`、`wiki-stats.py` 在沒有 `PyYAML` 的環境也能執行
- **新增 hook 稽核輸出忽略規則**：根目錄 `.gitignore` 新增 `.github/hooks/logs/` 與 `__pycache__/`

### 變更

- **wiki-query 禁止行為更新**：從「不得修改任何檔案」調整為「不得直接修改任何檔案」，所有寫入操作僅能透過委派子代理間接執行
- **query-wiki prompt 更新**：同步加入 Hand-Off 流程說明與新的建議行動回答格式
- **統一 wiki agents 的 `tools` 宣告格式**：`wiki-keeper`、`wiki-query`、`wiki-ingest`、`wiki-lint`、`wiki-archaeologist` 全數改為 inline YAML array（例如 `tools: [read, edit, search]`），讓代理能力清單更精簡且更容易比對
- **Hook 設定對齊 GitHub Copilot hooks schema**：三個 hook 設定檔改為 `version: 1`，事件名稱改用 `preToolUse`、`postToolUse`、`sessionStart`，並改以 `bash` / `powershell` 與 `timeoutSec` 宣告執行方式
- **wiki agents manifest 移除非官方 frontmatter 欄位**：`wiki-keeper`、`wiki-query`、`wiki-ingest`、`wiki-lint`、`wiki-archaeologist` 不再在 frontmatter 中宣告 `hooks:` 或 `agents:`，避免讓維護者誤以為 Copilot 會自動載入這些非標準欄位
- **Hook 輸出策略調整為稽核工件**：`wiki-log-reminder.py` 與 `wiki-session-init.py` 不再嘗試輸出 `systemMessage` 注入 agent context，改為寫入 `.github/hooks/logs/` 下的稽核檔案
- **Index / Log frontmatter 規格正式化**：`index.md`、`log.md` 現在明確使用 `type: index` / `type: log`，並要求 `sources: []` 與 `tags`
- **ADR 規格統一**：ADR 的決策狀態改由 `decision_status` 表示，`status` 保留給頁面生命週期（`active` / `stale` / `placeholder`）

### 修正

- **`wiki-write-guard.py` 改為真正可執行的寫入保護**：直接輸出 `permissionDecision` / `permissionDecisionReason`，並解析 `toolArgs`，現在會實際拒絕對 `wiki/`、`.github/` 以外路徑的寫入
- **三個輔助腳本移除 `PyYAML` 硬依賴**：`check-stale.py`、`rebuild-index.py`、`wiki-stats.py` 已改用內建 frontmatter parser
- **Windows 終端輸出相容性修正**：三個輔助腳本在執行前會切換為 UTF-8 stdio，避免 CP950 主控台因 emoji 或非 ASCII 字元輸出失敗
- **`rebuild-index.py` 產出的 `index.md` frontmatter 與規格同步**：自動補上 `sources: []` 與 `tags: [index]`

### 受影響的檔案

| 檔案 | 變更類型 |
|------|----------|
| `AGENTS.md` | 新增（OpenAI Codex 版專案指令） |
| `README.md` | 更新（新增 Copilot / Codex 雙版本說明） |
| `.github/agents/wiki-query.agent.md` | 大幅擴充（+59/-3） |
| `.github/prompts/query-wiki.prompt.md` | 更新（+11/-2） |
| `.github/agents/wiki-keeper.agent.md` | 格式整理（`tools` 改為 inline array） |
| `.github/agents/wiki-ingest.agent.md` | 格式整理（`tools` 改為 inline array） |
| `.github/agents/wiki-lint.agent.md` | 格式整理（`tools` 改為 inline array） |
| `.github/agents/wiki-archaeologist.agent.md` | 格式整理（`tools` 改為 inline array） |
| `.github/hooks/wiki-write-guard.json` | Hook schema 對齊（`version: 1`、`preToolUse`、`bash` / `powershell`） |
| `.github/hooks/wiki-log-reminder.json` | Hook schema 對齊（`version: 1`、`postToolUse`、`bash` / `powershell`） |
| `.github/hooks/wiki-session-init.json` | Hook schema 對齊（`version: 1`、`sessionStart`、`bash` / `powershell`） |
| `.github/hooks/scripts/wiki-write-guard.py` | 寫入防護邏輯修正（改為直接回傳 `permissionDecision`） |
| `.github/hooks/scripts/wiki-log-reminder.py` | 行為調整（改寫入 `.github/hooks/logs/wiki-log-reminder.jsonl`） |
| `.github/hooks/scripts/wiki-session-init.py` | 行為調整（改寫入 `.github/hooks/logs/wiki-session-state.md`） |
| `.github/copilot-instructions.md` | Frontmatter 規格補強（加入 `index` / `log` 與 `sources: []` 說明） |
| `.github/instructions/wiki-pages.instructions.md` | Frontmatter 規格補強（加入 `index` / `log` 與 `sources: []` 說明） |
| `.github/skills/codebase-wiki/assets/index-template.md` | 模板修正（補 `sources: []`、`tags: [index]`） |
| `.github/skills/codebase-wiki/assets/log-template.md` | 模板修正（補 `sources: []`、`tags: [log]`） |
| `.github/skills/codebase-wiki/references/page-types.md` | ADR 規格修正（加入 `decision_status`，釐清 `status` 語意） |
| `.github/skills/codebase-wiki/references/lint-checklist.md` | `type` 驗證規則補上 `index` / `log` |
| `.github/skills/codebase-wiki/scripts/frontmatter.py` | 新增（無外部依賴 frontmatter parser） |
| `.github/skills/codebase-wiki/scripts/check-stale.py` | 相依修正（移除 `PyYAML`） |
| `.github/skills/codebase-wiki/scripts/rebuild-index.py` | 相依與輸出修正（移除 `PyYAML`、補齊 index frontmatter） |
| `.github/skills/codebase-wiki/scripts/wiki-stats.py` | 相依與輸出修正（移除 `PyYAML`、UTF-8 stdio） |
| `.gitignore` | 新增忽略規則（hook logs、`__pycache__/`） |
