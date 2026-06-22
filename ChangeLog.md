# Changelog

本檔案記錄 Codebase LLM Wiki 框架的所有重要變更。格式基於 [Keep a Changelog](https://keepachangelog.com/)。

---

## [Unreleased] — 2026-06-22

### 新增

- **Codex 版完整重建**：依 OpenAI Codex 官方 customization surface 重新落地 `AGENTS.md`、`Codex.md`、`.agents/skills/codebase-wiki/`、`.codex/config.toml`、`.codex/hooks.json`、`.codex/hooks/scripts/` 與 `.codex/agents/*.toml`，讓 README 宣稱的 Codex 支援重新有實體檔案支撐
- **Codex hook 官方 schema 對齊**：Codex hooks 使用 `SessionStart`、`PreToolUse`、`PostToolUse` 事件與 `hookSpecificOutput` 輸出格式，並保留 `.codex/hooks/logs/` 到 `.codex-hook-logs/` 的 audit fallback
- **README 新增 Codex 版完整使用範例**：新增從安裝、初始化、增量維護、wiki-first query、synthesis 保存、SA 系統分析文件、SQL Server live evidence、lint 修復、custom agents delegation 到交付前檢查的端到端操作劇本
- **雙入口同權維護說明**：README 與 Codex.md 補上 Copilot ↔ Codex parity table，明確定義兩邊維持同一組 wiki 能力、邊界、安全規則與驗收結果，但各自使用平台原生入口
- **Codex 自然語言 recipe 對照**：Codex.md 新增 9 個 Copilot slash prompt 對應的 Codex recipe，包含 SA 系統分析文件產出，避免偽造 Codex project-level custom slash prompts
- **wiki-query SQL Server live evidence 同步支援**：GitHub Copilot 端 `wiki-query` 新增 VS Code Microsoft SQL Server extension tools 後，Codex 端同步在 `AGENTS.md` 與 `.codex/agents/wiki-query.toml` 補上資料庫證據規則，允許 schema discovery、metadata lookup 與有界線的唯讀 `SELECT`
- **新增 Codex 原生框架結構**：加入 `.codex/` 與 `.agents/skills/codebase-wiki/`，讓 OpenAI Codex 可使用 project-local hooks、custom agents 與 repo-local skill，而不必依賴 Copilot `.github/` 元件
- **新增 Codex custom agents**：將 `.github/agents/` 五個 Copilot agent 轉寫為 `.codex/agents/*.toml`，包含 `wiki-keeper`、`wiki-ingest`、`wiki-query`、`wiki-lint`、`wiki-archaeologist`
- **新增 Codex hooks**：加入 `.codex/hooks.json` 與 `.codex/hooks/scripts/`，提供 `SessionStart` wiki 狀態摘要、`PreToolUse` 寫入保護與 `PostToolUse` log reminder
- **新增 Codex repo-local skill**：將 `codebase-wiki` skill 複製到 `.agents/skills/codebase-wiki/`，並加入 `agents/openai.yaml` 作為 Codex skill metadata
- **新增 SA 系統分析文件 workflow**：`$codebase-wiki` 現在可依 wiki-first 流程產生 Markdown SA 文件，使用 `wiki/synthesis/`、`type: synthesis` 與 `tags: [synthesis, system-analysis]`，並提供 coverage gap 標示規則與模板
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

- **README Codex Workflow 功能範例擴寫**：新增「Codex 版完整使用範例」與「Codex Workflow 功能範例（逐項）」章節，逐項覆蓋 Interactive Ingest、Batch Ingest、Query、Query+SQL Server live evidence、Lint、Archaeology、ADR、Synthesis、Guide、System Analysis / SA、Delegation，每項皆提供何時使用、可直接貼上的 prompt、預期產出與驗收重點
- **Codex project instructions token 最佳化**：AGENTS.md 收斂為短核心規則，長流程與模板維持在 `$codebase-wiki` skill 的 `.agents/skills/codebase-wiki/` 下，讓 Codex 透過 progressive disclosure 按需載入
- **Codex hooks feature key 更新**：`.codex/config.toml` 改用 `[features] hooks = true`，保留 `agents.max_threads = 6` 與 `agents.max_depth = 1`，避免遞迴 subagent fan-out 增加 token 與 latency
- **Codex hook audit fallback**：`.codex/hooks/scripts/` 在 `.codex/hooks/logs/` 因 Windows ACL 無法寫入時，會退到 root-level `.codex-hook-logs/`，避免 SessionStart / log reminder 失去稽核輸出
- **Codex Query 流程加入 DB live evidence 契約**：Query 回答若使用 DB-derived result，必須標註 `connected_at`、`source_tool`、`server`、`database`、`query_scope`、`result_limit`、`row_count`、`freshness_note`；DB 證據不得寫入 wiki frontmatter `sources`
- **README 補上資料庫 Live Evidence 說明**：新增 Copilot / Codex 入口的 SQL Server live evidence 對照、唯讀限制、fallback 原則與查詢範例
- **AGENTS.md 對齊 Codex 原生路徑**：將 Codex skill 與輔助腳本路徑從 `.github/skills/codebase-wiki/` 更新為 `.agents/skills/codebase-wiki/`，並補充 `.codex/agents` 只在明確委派時使用
- **README 改為三層 Codex 說明**：Codex 版文件現在同時描述 `AGENTS.md`、`.codex/`、`.agents/skills/`，並新增 Codex Custom Agents 對照表與 Codex Hooks 說明
- **wiki-query 禁止行為更新**：從「不得修改任何檔案」調整為「不得直接修改任何檔案」，所有寫入操作僅能透過委派子代理間接執行
- **query-wiki prompt 更新**：同步加入 Hand-Off 流程說明與新的建議行動回答格式
- **統一 wiki agents 的 `tools` 宣告格式**：`wiki-keeper`、`wiki-query`、`wiki-ingest`、`wiki-lint`、`wiki-archaeologist` 全數改為 inline YAML array（例如 `tools: [read, edit, search]`），讓代理能力清單更精簡且更容易比對
- **Hook 設定對齊 GitHub Copilot hooks schema**：三個 hook 設定檔改為 `version: 1`，事件名稱改用 `preToolUse`、`postToolUse`、`sessionStart`，並改以 `bash` / `powershell` 與 `timeoutSec` 宣告執行方式
- **wiki agents manifest 移除非官方 frontmatter 欄位**：`wiki-keeper`、`wiki-query`、`wiki-ingest`、`wiki-lint`、`wiki-archaeologist` 不再在 frontmatter 中宣告 `hooks:` 或 `agents:`，避免讓維護者誤以為 Copilot 會自動載入這些非標準欄位
- **Hook 輸出策略調整為稽核工件**：`wiki-log-reminder.py` 與 `wiki-session-init.py` 不再嘗試輸出 `systemMessage` 注入 agent context，改為寫入 `.github/hooks/logs/` 下的稽核檔案
- **Index / Log frontmatter 規格正式化**：`index.md`、`log.md` 現在明確使用 `type: index` / `type: log`，並要求 `sources: []` 與 `tags`
- **ADR 規格統一**：ADR 的決策狀態改由 `decision_status` 表示，`status` 保留給頁面生命週期（`active` / `stale` / `placeholder`）

### 修正

- **README / 實體檔案一致性修復**：恢復 README 中列出的 Codex 入口檔案，避免 `AGENTS.md`、`Codex.md`、`.codex/` 與 `.agents/skills/codebase-wiki/` 被文件引用但不存在
- **Codex write guard 對齊框架維護規則**：`.codex/hooks/scripts/wiki-write-guard.py` 現在允許明確的框架維護工作更新根目錄 `README.md`、`ChangeLog.md`、`Codex.md`、`llm-wiki.md`、`prompt.txt` 與 `AGENTS.md`
- **`wiki-write-guard.py` 改為真正可執行的寫入保護**：直接輸出 `permissionDecision` / `permissionDecisionReason`，並解析 `toolArgs`，現在會實際拒絕對 `wiki/`、`.github/` 以外路徑的寫入
- **三個輔助腳本移除 `PyYAML` 硬依賴**：`check-stale.py`、`rebuild-index.py`、`wiki-stats.py` 已改用內建 frontmatter parser
- **Windows 終端輸出相容性修正**：三個輔助腳本在執行前會切換為 UTF-8 stdio，避免 CP950 主控台因 emoji 或非 ASCII 字元輸出失敗
- **`rebuild-index.py` 產出的 `index.md` frontmatter 與規格同步**：自動補上 `sources: []` 與 `tags: [index]`

### 受影響的檔案

| 檔案 | 變更類型 |
|------|----------|
| `AGENTS.md` | 新增 / 更新（OpenAI Codex 版專案指令；Query 流程新增 SQL Server live evidence 規則） |
| `README.md` | 更新（新增 Copilot / Codex 雙版本說明、Codex custom agents、hooks、資料庫 Live Evidence，以及 Codex workflow 功能逐項範例） |
| `ChangeLog.md` | 更新（追加 README 的 Codex workflow 功能範例擴寫紀錄） |
| `.agents/skills/codebase-wiki/references/system-analysis-workflow.md` | 新增（Codex SA 系統分析文件 workflow） |
| `.agents/skills/codebase-wiki/assets/system-analysis-template.md` | 新增（Codex SA 文件模板） |
| `.github/prompts/system-analysis-doc.prompt.md` | 新增（Copilot SA 文件 slash prompt） |
| `.github/skills/codebase-wiki/references/system-analysis-workflow.md` | 新增（Copilot SA 系統分析文件 workflow） |
| `.github/skills/codebase-wiki/assets/system-analysis-template.md` | 新增（Copilot SA 文件模板） |
| `.codex/config.toml` | 新增（Codex hooks 與 subagent defaults） |
| `.codex/hooks.json` | 新增（Codex hook 事件設定） |
| `.codex/agents/wiki-keeper.toml` | 新增（Codex wiki 路由 custom agent） |
| `.codex/agents/wiki-ingest.toml` | 新增（Codex wiki 攝入 custom agent） |
| `.codex/agents/wiki-query.toml` | 新增 / 更新（Codex wiki 查詢 custom agent；同步 SQL Server live evidence 規則） |
| `.codex/agents/wiki-lint.toml` | 新增（Codex wiki 健康檢查 custom agent） |
| `.codex/agents/wiki-archaeologist.toml` | 新增（Codex 程式碼考古 custom agent） |
| `.codex/hooks/scripts/wiki-write-guard.py` | 新增 / 更新（Codex 寫入保護 hook；允許明確框架維護文件） |
| `.codex/hooks/scripts/wiki-log-reminder.py` | 新增（Codex log reminder hook） |
| `.codex/hooks/scripts/wiki-session-init.py` | 新增（Codex session state hook） |
| `.agents/skills/codebase-wiki/` | 新增（Codex repo-local skill，含 templates、references、scripts） |
| `.github/agents/wiki-query.agent.md` | 更新（Hand-Off 流程與 VS Code MSSQL tools） |
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
