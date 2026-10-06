---
title: 獨立開發規格流程
type: module
summary: 查閱目前 Codebase、逐題釐清必要決策，再交付五部分的獨立實作規格
sources:
  - .agents/skills/codebase-wiki/references/development-spec-workflow.md
  - .agents/skills/codebase-wiki/assets/development-spec-template.md
  - .agents/skills/codebase-wiki/scripts/validate-development-spec.py
  - .agents/skills/codebase-wiki/capabilities.json
  - .github/prompts/development-spec.prompt.md
  - tests/contracts/test_development_spec.py
source_digest: "sha256:cebc548662a9bf69dd472fdc894e91e6ee4286799b85e2cdd71658a3f46a4c6a"
last_updated: 2026-10-03
tags: [module, development-spec, standalone]
status: active
notebooklm_group: development-spec
notebooklm_role: exclude
---

# 獨立開發規格流程

`development_spec` 是 `$codebase-wiki` 的獨立路由，在目前單一 Codebase 中查證程式／介面事實，
再每輪詢問一個最高影響的未決問題。
影響範圍、行為、權限、相依契約或驗收的必要問題沒有回答時，只能保存 draft。

輸出 `wiki/synthesis/<scope>-development-spec.md`，以五部分說明目的與範圍、適用專案、
功能行為與限制、相依契約與確認決策、帶 SCN 編號的 Given／When／Then 驗收情境。
實作必要資訊直接放入正文，使文件不依賴特定 Issue 或工作流。來源、索引與 log 沿用共享規則。

`spec_revision` 是正整數；`spec_status` 是 draft 或 ready；`blocking_questions` 列出未決必要
問題。驗證器拒絕含問題、範本佔位、空章節或缺少驗收結果的 ready。文件排除 NotebookLM 匯出。
ready 只代表規格完整；Issue 建立及實作流程由使用者自行決定。BA／SA／SD 及既有 NotebookLM 流程保留。
