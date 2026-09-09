---
title: 分析文件產生 SA
type: synthesis
summary: 依框架現況整理分析文件產生的系統邊界、輸入輸出、狀態、介面與失敗行為。
standards_profile: codebase-system-analysis-v1
coverage_status: partial
capability_id: cap-analysis-document-generation
notebooklm_document: sa
notebooklm_group: business-analysis-documents
notebooklm_role: analysis
notebooklm_terms: [analysis workflow, template, frontmatter, managed markers, validation]
sources:
  - .agents/skills/codebase-wiki/references/business-analysis-workflow.md
  - .agents/skills/codebase-wiki/references/system-analysis-workflow.md
  - .agents/skills/codebase-wiki/references/system-design-workflow.md
  - .agents/skills/codebase-wiki/scripts/validate-frontmatter.py
  - tests/contracts/test_contracts.py
source_digest: sha256:3a0fc073e2c5623896be32dd41608c6e775fe107c198b365e6774a417e3e721f
source_locators:
  - ".agents/skills/codebase-wiki/references/business-analysis-workflow.md:12"
  - ".agents/skills/codebase-wiki/references/system-analysis-workflow.md:13"
  - ".agents/skills/codebase-wiki/references/system-design-workflow.md:14"
  - ".agents/skills/codebase-wiki/scripts/validate-frontmatter.py:215"
  - "tests/contracts/test_contracts.py:1"
derived_from: ["[[business-analysis-document]]", "[[system-analysis-document]]", "[[system-design-document]]", "[[cap-analysis-document-generation-ba]]"]
last_updated: 2026-09-09
tags: [synthesis, system-analysis, codebase-as-is, notebooklm]
status: active
---

# 分析文件產生 SA

<!-- codebase-wiki:managed:start -->
## 系統邊界、輸入與輸出

此能力由共享 Skill 的三份 workflow、對應 Markdown templates、Copilot prompts、Codex recipes 與 Wiki validators 組成。輸入是使用者文件類型與 scope、既有 Wiki、必要的唯讀 raw evidence；輸出是 `wiki/synthesis/` 下的 BA、SA 或 SD 文件以及 index/log 變更。

## 資料與狀態

文件以 YAML frontmatter 保存 `type`、`standards_profile`、`coverage_status`、`sources`、`derived_from`、日期、tags 與 status。正文以 managed、user-notes、local-only marker 分隔可重建內容、人工內容與本機追溯。需求及追溯使用 `cap-*`、`fr-*`、`SR-*`、`NFR-*`、`IF-*`、`VIEW-*`、`DE-*`、`AC-*` 和 `gap-*` 等穩定識別碼。

## 介面、依賴與錯誤處理

平台 adapter 只把意圖導向共享 workflow；installer 將同一 Skill 與 templates 複製至 target。Frontmatter、stale、link/index、log 與 lint scripts 驗證檔案契約。缺來源時 workflow 產生 Gap；不合法 frontmatter、錯誤路徑、marker 遺失或 Wiki checks 失敗時不得宣稱完成。

Codebase 未提供背景服務、資料庫、網路 API 或自動文件生成 runtime；實際內容由 agent 依 workflow 在本機檔案系統操作。Codebase 也未提供兩個平台完整 runtime UAT 的持續自動證據。

## 來源定位

- `.agents/skills/codebase-wiki/references/business-analysis-workflow.md:12`
- `.agents/skills/codebase-wiki/references/system-analysis-workflow.md:13`
- `.agents/skills/codebase-wiki/references/system-design-workflow.md:14`
- `.agents/skills/codebase-wiki/scripts/validate-frontmatter.py:215`
- `tests/contracts/test_contracts.py:1`

## 對應 BA

[[cap-analysis-document-generation-ba]]
<!-- codebase-wiki:managed:end -->

<!-- codebase-wiki:user-notes:start -->
## Reviewer Notes

目前無人工補充。
<!-- codebase-wiki:user-notes:end -->
