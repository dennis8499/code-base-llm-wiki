---
title: NotebookLM 現況 BA／SA 匯出 BA
type: synthesis
summary: 依 exporter 現況整理全量 discovery、一次確認、文件化與單一 Notebook 本機交付。
standards_profile: codebase-business-analysis-v1
coverage_status: partial
capability_id: cap-notebooklm-ba-functional-export
notebooklm_document: ba
notebooklm_group: business-notebooklm-export
notebooklm_role: business
notebooklm_terms: [NotebookLM Enterprise, BA, SA, discovery, 一次確認, source pack]
sources:
  - .agents/skills/codebase-wiki/scripts/notebooklm_exporter.py
  - .agents/skills/codebase-wiki/references/notebooklm-export-workflow.md
  - .github/prompts/export-notebooklm.prompt.md
  - notebooklm.toml
  - tests/notebooklm/test_notebooklm_acceptance.py
source_digest: sha256:c66f70ffcb51137874078862c4f2da1feb2d07e9aa70fae9f710417cbdeb15ba
source_locators:
  - ".agents/skills/codebase-wiki/scripts/notebooklm_exporter.py:4172"
  - ".agents/skills/codebase-wiki/references/notebooklm-export-workflow.md:1"
  - ".github/prompts/export-notebooklm.prompt.md:1"
  - "notebooklm.toml:1"
  - "tests/notebooklm/test_notebooklm_acceptance.py:1"
derived_from: ["[[notebooklm-ba-functional-export]]", "[[notebooklm-ba-knowledge-export]]", "[[cap-notebooklm-ba-functional-export-sa]]"]
last_updated: 2026-09-08
tags: [synthesis, business-analysis, codebase-as-is, notebooklm]
status: active
---

# NotebookLM 現況 BA／SA 匯出 BA

<!-- codebase-wiki:managed:start -->
## 功能目的、角色與觸發

知識維護者發起 Export NotebookLM 時，框架把當下 Codebase 整理成 Business Analyst 與 System Analyst 可在單一 Notebook 搜尋、問答的現況知識。Codebase 包含程式、設定、資料結構、behavioral tests、README、規格與註解；內容衝突時以程式碼為主。

## 流程與規則

1. `--preflight` 唯讀重掃完整安全 UTF-8 scope，不以既有 Wiki 作為 discovery 邊界。
2. Preview 顯示 `discovery_id`、功能清單、BA／SA 覆蓋、待分析、證據差異、排除／無法讀取、DLP 與容量。
3. 使用者對具體 preview 確認一次；確認前不修改 Wiki 或建立 pack。
4. 確認後重讀完整 snapshot、保留 user notes，更新 catalogs／ledger，並為每個 active capability 建立可追溯的 BA／SA 配對。
5. 完整處理後記錄 analyzed discovery ID，自動執行 readiness preflight，再以 confirmed discovery ID 與 latest preflight ID 原子產生本機 pack；readiness 不新增人工 gate。

沒有證據的現況使用 `Codebase 未提供證據`；`尚未完成分析`、缺配對、無效 locator、uncovered 或 analysis-gap 會阻擋。Raw/config/scope drift 需要重新 preview 與確認；Wiki-only 重建沿用原 discovery 確認。

## 結果、例外與治理

成功輸出包含 `documents/{cap}-ba.md`／`-sa.md`、只供上傳的 `sources/*.md`、manifest v6、upload plan、README 和 local-only governance。v1–v5 或 BA-only pack 必須在同一 Notebook 清除舊 static sources 後完整替換。單一 Notebook 超限、DLP residual、失敗或 drift 均保留上一份有效包。

本機治理依 Google 官方產品基準說明容量、靜態副本與控制責任；沒有 tenant evidence 時，IAM、VPC Service Controls、CMEK、data location、Sensitive Data Protection、Model Armor 與實際問答品質都標示未驗證。

## 來源定位

- `.agents/skills/codebase-wiki/scripts/notebooklm_exporter.py:4172`
- `.agents/skills/codebase-wiki/references/notebooklm-export-workflow.md:1`
- `.github/prompts/export-notebooklm.prompt.md:1`
- `notebooklm.toml:1`
- `tests/notebooklm/test_notebooklm_acceptance.py:1`

## 對應 SA

[[cap-notebooklm-ba-functional-export-sa]]
<!-- codebase-wiki:managed:end -->

<!-- codebase-wiki:user-notes:start -->
## Reviewer Notes

目前無人工補充。
<!-- codebase-wiki:user-notes:end -->
