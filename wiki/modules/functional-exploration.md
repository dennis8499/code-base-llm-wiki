---
title: Functional exploration
type: module
summary: ???????????????????????
notebooklm_group: local-governance
notebooklm_role: exclude
sources:
  - .agents/skills/codebase-wiki/references/functional-exploration-workflow.md
  - .agents/skills/codebase-wiki/scripts/functional_inventory.py
  - .agents/skills/codebase-wiki/scripts/explore-functions.py
  - .agents/skills/codebase-wiki/capabilities.json
source_digest: sha256:60166e5f1977a4119826525adc2479e425f1d5cfa00c020f20ddd1984dae328f
last_updated: 2026-10-17
tags: [functional-exploration, coverage]
status: active
---

# 功能探索

`functional_exploration` 先盤點當前 source，依功能說明入口、輸入、流程、
依賴、狀態與輸出。報告綁定 scanner snapshot，逐檔與逐入口對帳；未讀、
部分覆蓋、排除及業務問題都保持可見。靜態盤點無法證明執行期行為。

預設不寫檔。明確要求保存才產生授權文件；一般 Query 維持 Wiki-first。
與 [[code-audit]] 共用來源 scanner，功能探索負責現況能力盤點，audit 再追查缺陷。
