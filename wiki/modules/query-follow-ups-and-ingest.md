---
title: 查詢後續處理與全量 Ingest
type: module
summary: 查詢先提供具體預覽，選擇一次後完成更新或保存；全量 Ingest 用安全快照與逐檔處置驗證完成性
sources:
  - .agents/skills/codebase-wiki/references/follow-up-actions.md
  - .agents/skills/codebase-wiki/references/ingest-workflow.md
  - .agents/skills/codebase-wiki/scripts/ingest_coverage.py
  - .agents/skills/codebase-wiki/scripts/ingest-coverage.py
  - tests/contracts/test_ingest_coverage.py
source_digest: "sha256:0c44c7e61449b20c4f3935d8c2c6826de0a9087f7dbeed217e18827d30de9079"
last_updated: 2026-10-13
tags: [module, query, ingest, coverage, authorization]
status: active
notebooklm_role: exclude
notebooklm_group: query-and-ingest
---

# 查詢後續處理與全量 Ingest

查詢先完成 Wiki-first 的有據回答。過時、缺漏或矛盾的內容先回查來源再提出更新；
可重用分析提出保存，同主題優先更新既有 Synthesis；兩者同時需要則提供合併選項。
每個選項列出理由、來源證據、目標頁面及具體變更預覽，最多三個動作另加暫不處理。
單純查詢、未選擇或暫不處理均零寫入，包括 index、log 與處置清單。

選擇已預覽動作即授權該範圍。Ingest 或 Synthesis 不再重複確認，完成保留人工內容、
來源摘要、索引、各子流程日誌與品質檢查。必要決策未答、範圍擴大或來源實質改變使
預覽失效時才再詢問；來源本身永遠唯讀。這是 Agent 工作流程契約，並非自動執行器。

單一路徑沿用 Interactive／Batch；全部專案使用 `ingest-coverage.py inventory` 的
共用 scanner 快照，涵蓋設定、schema、文件、測試、部署與工具，以及未追蹤、ignored、
巢狀 Repo 安全來源。獲授權後保存 `wiki/ingest-coverage.json`，逐檔記錄 hash、分類、
已處理／受阻、頁面或不需成頁理由，另記錄 scanner 的排除檔案與目錄邊界。敏感排除
不讀內容，因此不計 hash。`exports/megin/` 交付產物排除；其他 exports 仍可作來源。

validate 依原請求 scope 重掃；遺漏、重複、映射不存在、受阻或快照改變，均只能回報
部分完成。Group 擴充以全部合法直屬本機 Repo 為預設，明確清單才限縮；原生模式只
涵蓋目前專案。完成性驗證只證明處置與來源快照完整，來源理解與頁面品質仍由 Agent
核對。相關邊界見 [[wiki-quality-and-provenance]] 與 [[development-specification]]。
