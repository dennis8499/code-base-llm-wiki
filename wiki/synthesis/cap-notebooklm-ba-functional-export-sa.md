---
title: NotebookLM 現況 BA／SA 匯出 SA
type: synthesis
summary: 依 exporter 現況整理 discovery/readiness identity、配對驗證、遮罩、容量與原子輸出。
standards_profile: codebase-system-analysis-v1
coverage_status: partial
analysis_status: traced
gap_classification: none
capability_id: cap-notebooklm-ba-functional-export
notebooklm_document: sa
notebooklm_group: business-notebooklm-export
notebooklm_role: analysis
notebooklm_terms: [schema v6, discovery_id, preflight_id, DLP, manifest, atomic commit]
sources:
  - .agents/skills/codebase-wiki/scripts/notebooklm_exporter.py
  - .agents/skills/codebase-wiki/scripts/validate-frontmatter.py
  - .agents/skills/codebase-wiki/capabilities.json
  - tests/notebooklm/test_notebooklm_acceptance.py
  - tests/notebooklm/test_notebooklm_contract.py
source_digest: sha256:5e64956dc6d4f12d35192617a3439f5a51de54a9f30b7cd491efa30cdd1bd137
source_locators:
  - ".agents/skills/codebase-wiki/scripts/notebooklm_exporter.py:1922"
  - ".agents/skills/codebase-wiki/scripts/validate-frontmatter.py:215"
  - ".agents/skills/codebase-wiki/capabilities.json:61"
  - "tests/notebooklm/test_notebooklm_acceptance.py:1"
  - "tests/notebooklm/test_notebooklm_contract.py:1"
derived_from: ["[[notebooklm-ba-functional-export]]", "[[notebooklm-ba-knowledge-export]]", "[[cap-notebooklm-ba-functional-export-ba]]"]
last_updated: 2026-09-09
tags: [synthesis, system-analysis, codebase-as-is, notebooklm]
status: active
---

# NotebookLM 現況 BA／SA 匯出 SA

<!-- codebase-wiki:managed:start -->
## 系統邊界、輸入與輸出

`notebooklm_exporter.py` 是 canonical 離線實作，compatibility wrapper 只呼叫其 `main()`。輸入是 repository root、可選 `notebooklm.toml`、Wiki pages，以及 apply 時的 `discovery_id`／`preflight_id`；輸出只寫 repository child `.notebooklm/`。

## 資料、狀態與轉換

Discovery identity 由 sorted safe raw path、category、bytes、SHA-256、排除處置、設定與語意契約組成，不含 Wiki bytes、輸出目錄或 exporter transaction artifacts。Readiness identity 另包含 Wiki hashes、lint、DLP 與 exact pack plan。Coverage ledger 的 analyzed discovery ID 必須等於 apply 當下 raw snapshot。

每個 active `cap-*` 必須有唯一 BA／SA，固定 path、profiles、roles、相同 group、雙向 link、real sources 與有效 `path:line` locators。Renderer 移除 local-only 區塊、保留 managed 內容與 user notes；DLP 分別遮罩 analysis copy、`documents/` 和 `sources/`，再執行 residual scan。

## 介面、依賴與錯誤處理

CLI 支援 `--preflight` 及 `--apply --discovery-id ... --preflight-id ...`。Upload sources 固定包含 query index、project map 與完整 capability documents，可無損合併及安全分割。硬上限是 300 sources、每 source 500 MB／500,000 estimated words，預設安全值較低。

Output commit 使用 sibling lock、journal、stage 與 backup；驗證全數完成後才替換，並保留非 managed unknown files。ID mismatch、非法設定／路徑、缺文件、容量超限或 DLP residual 都以 exit code 2 失敗。Codebase 未提供 NotebookLM API client、自動上傳或 Google Cloud tenant 設定寫入能力。

## 失敗、例外與重試

若 discovery、設定、Wiki、DLP 或容量 identity 改變，apply 會拒絕並保留舊 pack；若輸出程序中斷，journal／stage／backup 會恢復上一份有效輸出。source split 以完整行為內容保留，沒有 evidence 的租戶問答結果標為 `evidence-gap`，不把本機結構檢查當成 NotebookLM 問答驗證。

## 來源定位

- `.agents/skills/codebase-wiki/scripts/notebooklm_exporter.py:1922`
- `.agents/skills/codebase-wiki/scripts/validate-frontmatter.py:215`
- `.agents/skills/codebase-wiki/capabilities.json:61`
- `tests/notebooklm/test_notebooklm_acceptance.py:1`
- `tests/notebooklm/test_notebooklm_contract.py:1`

## 對應 BA

[[cap-notebooklm-ba-functional-export-ba]]
<!-- codebase-wiki:managed:end -->

<!-- codebase-wiki:user-notes:start -->
## Reviewer Notes

目前無人工補充。
<!-- codebase-wiki:user-notes:end -->
