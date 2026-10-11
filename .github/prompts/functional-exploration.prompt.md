---
name: functional-exploration
description: 先查目前原始碼，唯讀盤點完整功能、入口、流程、依賴、覆蓋與缺口。
agent: "agent"
argument-hint: "要探索的專案根目錄及範圍"
---

完整載入 [Functional exploration](../../.agents/skills/codebase-wiki/references/functional-exploration-workflow.md)。
對 `${input:target}` 先查目前原始碼，對帳所有納入檔案與入口；回報功能、來源、覆蓋與缺口。
分開事實、假設、需求與技術建議。預設零寫入，只有明確要求保存才產生授權文件。
