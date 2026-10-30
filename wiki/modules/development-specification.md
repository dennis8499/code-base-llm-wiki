---
title: 開發規格功能移除紀錄
type: module
summary: 保留歷史 Wiki 連結，記錄開發規格入口已移除及既有文件的保留方式
sources:
  - .agents/skills/codebase-wiki/capabilities.json
  - .agents/skills/codebase-wiki/scripts/install-framework.py
  - tests/installer/test_development_spec_removal.py
source_digest: sha256:5d5adb10ccb97b3960a2439c89933dcc0a351a1890cb6b7dd91db5d45a69b59a
last_updated: 2026-10-30
tags: [module, history]
status: active
notebooklm_role: exclude
notebooklm_group: local-governance
---

# 開發規格功能移除紀錄

開發規格路由、模板、驗證器及 Copilot 提示詞已移除。此頁僅保留既有
`wiki/log.md` 的歷史連結；目前的功能入口見 [[index]]。

既有規格仍是使用者的 synthesis 文件。升級只移除安裝紀錄可驗證歸屬且未修改的
舊功能檔案；本機修改或歸屬不明時停止並列出衝突。交易失敗或程序中斷時復原原檔。

BA／SA／SD 與一般 Synthesis 工作流程仍可使用。`exports/` 依一般來源規則處理。
