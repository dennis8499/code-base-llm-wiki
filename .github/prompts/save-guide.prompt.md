---
name: save-guide
description: >
  將目前對話、wiki 內容或 source-backed 分析整理成 durable guide，
  存入 wiki/guides/ 並更新索引與 log。
agent: "wiki-keeper"
argument-hint: "指南主題，例如：本機開發環境設定、退款流程除錯、值班排查手冊"
---

## 任務

將目前對話或指定主題整理成一份 durable guide。

**指南主題**：${input:guideTopic:（若未提供，請從對話內容自動推導）}

## 流程

1. 讀取 `wiki/index.md` 與近期 `wiki/log.md`。
2. 載入 `.github/skills/codebase-wiki/references/guide-workflow.md`。
3. 讀取 `wiki/overview.md` 與相關 architecture、modules、entities、patterns、dependencies、decisions、synthesis 頁面。
4. 只有 wiki 不足、過時或互相矛盾時，才回溯 raw sources。
5. 決定輸出檔名：`wiki/guides/{kebab-topic}.md`。
6. 建立或更新 guide 頁面。
7. 更新 `wiki/index.md`。
8. 追加 `wiki/log.md` 條目：`## [YYYY-MM-DD] guide | {指南標題}`。

## 品質要求

- 寫清楚目標讀者、前置條件、步驟、常見問題與相關頁面。
- 使用 `[[page-name]]` wikilink 與 source path 引用。
- 缺少可靠 evidence 時標示 gap，不得編造 setup commands、secrets、owners 或 runtime behavior。
- 若使用 DB evidence，只能放正文 evidence block，不得放入 frontmatter `sources`。
