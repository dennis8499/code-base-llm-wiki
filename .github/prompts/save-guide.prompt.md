---
name: save-guide
description: >
  將目前對話、wiki 內容或 source-backed 分析整理成 durable guide，
  存入 wiki/guides/ 並更新索引與 log。
agent: "wiki-keeper"
argument-hint: "指南主題，例如：本機開發環境設定、退款流程除錯、值班排查手冊"
---

將 `${input:guideTopic:（若未提供，從目前對話推導）}` 保存為 durable guide。

完整載入 [Guide workflow](../../.agents/skills/codebase-wiki/references/guide-workflow.md)。
先讀 `wiki/index.md`、近期 `wiki/log.md` 與相關 Wiki pages；只有缺漏、stale 或
矛盾時才回溯 raw sources。產出必須包含目標讀者、前置條件、可執行步驟、
常見陷阱、gaps 與相關頁面。

寫入 `wiki/guides/{kebab-topic}.md`，raw evidence 放 `sources`、Wiki evidence
放 `derived_from`；同步 `wiki/index.md` 並只追加一筆 guide log。不得編造
commands、secrets、owners 或 runtime behavior。
