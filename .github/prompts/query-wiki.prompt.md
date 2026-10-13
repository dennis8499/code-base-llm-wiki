---
name: query-wiki
description: >
  查詢 Codebase Wiki——搜尋知識庫回答關於 codebase 的問題，
  必要時回溯原始碼驗證，並保持唯讀。
agent: "agent"
argument-hint: "你想問的 codebase 問題，例如：登入流程在哪裡實作？"
---

回答 `${input:question}`，並保持唯讀。

依序完整載入 [Query workflow](../../.agents/skills/codebase-wiki/references/query-workflow.md)
與 [Follow-up actions](../../.agents/skills/codebase-wiki/references/follow-up-actions.md)。
先讀 `wiki/index.md`，再讀 1–5 個最相關頁面；只有 Wiki 缺漏、stale 或矛盾時
才回溯其 sources。回答需列出 Wiki/source evidence，並標示 inference、
contradiction 與 gap。

只有 shared contract 判定 eligible 時才提供最多三個有理由的後續選項。
每個建議列出來源證據、目標頁面與具體變更預覽，保留「暫不處理」。
本 Query 零寫入、零自動切換工作流程；未選擇或暫不處理時維持零寫入。
選擇已預覽動作後，依 shared contract 執行更新、保存或合併操作及驗證；
同範圍沿用這一次確認，不重複要求 Interactive Ingest／Synthesis 確認。
