---
name: system-analysis-doc
description: >
  基於 Codebase LLM Wiki 產生 solution-neutral、standard-aligned SA 系統分析文件，
  建立可驗證需求並明列 Gap。
agent: "agent"
argument-hint: "可選：補充範圍，例如：整體系統、src/auth/、結帳流程"
---

## 任務

基於現有 Wiki 內容產出一份繁中 Markdown SA 系統分析文件。

**分析範圍**：${input:scopeName:整體系統}

## 流程

1. 完整載入 `.agents/skills/codebase-wiki/references/system-analysis-workflow.md`、
   `.agents/skills/codebase-wiki/references/analysis-document-standards.md` 與
   `.agents/skills/codebase-wiki/assets/system-analysis-template.md`。
2. 讀取 `wiki/index.md`、近期 `wiki/log.md`、對應 BA、overview、requirements、
   processes、rules 與 gaps；缺少 BA 時建立具體 Gap，不阻擋產出。
3. 建立 SA coverage map，以 `SR-{SCOPE}-NNN`、`NFR-{SCOPE}-NNN` 與
   `IF-{SCOPE}-NNN` 表達 solution-neutral、可驗證需求。
4. 只有在 Wiki 不足、過時或互相矛盾時，才唯讀回溯 raw sources；現有技術只能
   作 observed evidence，不得偷渡成必要方案。
5. 有證據才產出系統脈絡與主要情境 Mermaid；否則保留槽位並寫 Gap。
6. 使用模板產出 SA 文件：
   - 整體系統：`wiki/synthesis/system-analysis.md`
   - 指定範圍：`wiki/synthesis/{kebab-scope}-system-analysis.md`
7. 首次重跑無 markers 的 legacy SA 時，把原正文逐字保存到 user-notes legacy
   區塊；其後只重建 managed 並保留 user-notes/local-only。
8. 更新 `wiki/index.md`，並在 `wiki/log.md` 追加一筆 `synthesis` 記錄。

## 品質要求

- Frontmatter 必須有 `standards_profile: system-analysis-aligned-v1`、
  `coverage_status` 與 `notebooklm_role: traceability`。
- `sources` 只能列真實 repo-relative raw source 路徑；Wiki 依賴請放在
  `derived_from` 的 `[[wikilinks]]`，沒有直接 raw evidence 時使用 `sources: []`。
- 不足章節要保留並標示 `待補` / `Gap`，不得編造；SA 不得包含技術選型、
  元件配置或部署設計，這些內容交由 SD／ADR。
- 完成前執行 frontmatter、stale、index、log 與 lint 檢查。
