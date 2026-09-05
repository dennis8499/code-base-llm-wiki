---
name: ingest-batch
description: >
  批次攝入整個目錄到 wiki——掃描指定路徑下所有模組，
  按依賴順序批次產出 wiki 頁面，最終產出完整摘要報告。
agent: "agent"
argument-hint: "目標路徑，例如：src/、services/ 或 packages/core"
---

對 `${input:targetPath}` 執行 **Batch Ingest**。

完整載入並遵守 [Ingest workflow](../../.agents/skills/codebase-wiki/references/ingest-workflow.md)。
使用者選擇本 prompt 已明確授權指定 scope 的 Batch Ingest；不得擴張範圍，
也不需要再次要求 interactive confirmation。依相依順序處理模組，定期回報進度，
並只建立有證據支持的 overview、module、entity、pattern 或 architecture pages。

Raw sources 全程唯讀。收尾必須驗證 frontmatter、stale 與 lint，更新
`wiki/index.md`，只追加一筆 `wiki/log.md` ingest entry，再輸出建立／更新摘要。
