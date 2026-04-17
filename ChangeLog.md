# Changelog

本檔案記錄 Codebase LLM Wiki 框架的所有重要變更。格式基於 [Keep a Changelog](https://keepachangelog.com/)。

---

## [Unreleased] — 2026-04-17

### 新增

- **wiki-query 建議行動與自動交接（Hand-Off）功能**：查詢代理在產生建議後，會透過 `vscode/askQuestions` 向使用者呈現可執行的行動清單，使用者確認後自動委派給對應的專業子代理執行。
  - 三種建議行動類型：
    - `save-synthesis`：將有持續價值的綜合分析存入 `wiki/synthesis/`（委派 `wiki-keeper`）
    - `re-ingest`：對內容過時的 wiki 頁面重新執行知識攝入（委派 `wiki-ingest`）
    - `lint-fix`：修復斷裂連結、缺失 frontmatter 等品質問題（委派 `wiki-lint`）
  - 標準化的交接摘要格式，確保子代理獲得充足的背景脈絡
- **wiki-query 新增子代理協作能力**：工具清單加入 `agent` 與 `vscode/askQuestions`，代理清單加入 `wiki-ingest`、`wiki-lint`、`wiki-keeper`

### 變更

- **wiki-query 禁止行為更新**：從「不得修改任何檔案」調整為「不得直接修改任何檔案」，所有寫入操作僅能透過委派子代理間接執行
- **query-wiki prompt 更新**：同步加入 Hand-Off 流程說明與新的建議行動回答格式

### 受影響的檔案

| 檔案 | 變更類型 |
|------|----------|
| `.github/agents/wiki-query.agent.md` | 大幅擴充（+59/-3） |
| `.github/prompts/query-wiki.prompt.md` | 更新（+11/-2） |
