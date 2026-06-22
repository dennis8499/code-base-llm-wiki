---
name: system-analysis-doc
description: >
  基於現有 Codebase LLM Wiki 內容產生 SA 系統分析文件，輸出到
  wiki/synthesis/，並標示 coverage gaps 與待補來源。
agent: "wiki-keeper"
argument-hint: "可選：補充範圍，例如：整體系統、src/auth/、結帳流程"
---

## 任務

基於現有 wiki 內容產出一份 SA 系統分析文件。

**分析範圍**：${input:scopeName:整體系統}

## 流程

1. 讀取 `wiki/index.md` 與近期 `wiki/log.md`。
2. 讀取 `wiki/overview.md`，以及與範圍相關的 architecture、modules、entities、patterns、dependencies、decisions、synthesis 頁面。
3. 載入 `.github/skills/codebase-wiki/references/system-analysis-workflow.md`。
4. 建立 SA coverage map，判斷每個章節是 `covered`、`partial` 或 `gap`。
5. 只有在 wiki 不足、過時或互相矛盾時，才依相關頁面的 `sources` 回溯 raw sources。
6. 使用 `.github/skills/codebase-wiki/assets/system-analysis-template.md` 產出 SA 文件：
   - 整體系統：`wiki/synthesis/system-analysis.md`
   - 指定範圍：`wiki/synthesis/{kebab-scope}-system-analysis.md`
7. 更新 `wiki/index.md`。
8. 追加 `wiki/log.md` 條目：`## [YYYY-MM-DD] synthesis | system analysis`

## 品質要求

- frontmatter 使用 `type: synthesis` 與 `tags: [synthesis, system-analysis]`。
- `sources` 只能列真實 repo-relative wiki/source 路徑。
- 不足章節要保留並標示 `待補` / `Gap`，不得編造。
- 若使用 DB evidence，只能放正文 evidence block，不得放入 frontmatter `sources`。
