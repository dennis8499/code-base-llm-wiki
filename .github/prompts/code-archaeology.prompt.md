---
name: code-archaeology
description: >
  追蹤 legacy 行為、欄位、功能或設計決策的 git history 與目前程式路徑，
  產出 evidence-first 考古報告，必要時保存到 wiki。
agent: "agent"
argument-hint: "要追蹤的功能、欄位、路由或問題，例如：discount_code 為什麼存在"
---

對 `${input:target}` 執行 **Code Archaeology**。

完整載入 [Code archaeology workflow](../../.agents/skills/codebase-wiki/references/code-archaeology-workflow.md)。
先讀 `wiki/index.md` 與相關頁面，再從具體 entrypoint 追蹤目前 inputs、processing、
outputs 與特殊分支；之後才使用非破壞性的 `git log`、`git blame`、`git show`
補足歷史。分開標示 source/Git evidence、inference、speculation 與 uncertainty。

預設零寫入。只有明確要求保存時，才更新 Wiki page、相關內容頁的語意 inbound
wikilink、`wiki/index.md`，並只追加一筆 `wiki/log.md` archaeology entry；index
與 log 的連結本身不解除 orphan。
