---
title: NotebookLM 現況 BA／SA 匯出 BA
type: synthesis
summary: 依 exporter 現況整理全量 discovery、一次確認、文件化與單一 Notebook 本機交付。
standards_profile: codebase-business-analysis-v1
coverage_status: partial
analysis_status: traced
gap_classification: none
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
source_digest: sha256:8ef9f4f5d3ff48627314c263b0da302b64881dac3775dda4fb7dc05ac59acba0
source_locators:
  - ".agents/skills/codebase-wiki/scripts/notebooklm_exporter.py:4172"
  - ".agents/skills/codebase-wiki/references/notebooklm-export-workflow.md:1"
  - ".github/prompts/export-notebooklm.prompt.md:1"
  - "notebooklm.toml:1"
  - "tests/notebooklm/test_notebooklm_acceptance.py:1"
derived_from: ["[[notebooklm-ba-functional-export]]", "[[notebooklm-ba-knowledge-export]]", "[[cap-notebooklm-ba-functional-export-sa]]"]
last_updated: 2026-09-09
tags: [synthesis, business-analysis, codebase-as-is, notebooklm]
status: active
---

# NotebookLM 現況 BA／SA 匯出 BA

<!-- codebase-wiki:managed:start -->
## 功能目的、角色與觸發

知識維護者發起 Export NotebookLM 時，框架把當下 Codebase 整理成 Business Analyst 與 System Analyst 可在單一 Notebook 搜尋、問答的現況知識。Codebase 包含程式、設定、資料結構、behavioral tests、README、規格與註解；內容衝突時以程式碼為主。

## 前置條件、流程與規則

| 步驟 | 觸發／條件 | 處理與資料／狀態變更 | 結果 | 失敗去向／定位 |
| --- | --- | --- | --- | --- |
| 1 | 執行 `--preflight` | 讀取完整安全 UTF-8 scope，建立 inventory 與 `discovery_id` | 形成功能、覆蓋、排除、DLP 與容量 preview | 未分類或不可讀來源列 gap；`.agents/skills/codebase-wiki/scripts/notebooklm_exporter.py:5018` |
| 2 | preview 已建立 | 使用者讀取 BA／SA 覆蓋與待分析差異，確認一次 | `discovery_pending` → `plan_confirmed` | 範圍變更須重新 preview；`.agents/skills/codebase-wiki/references/notebooklm-export-workflow.md:88` |
| 3 | `plan_confirmed` | 沿入口追蹤呼叫鏈，將每一步的條件、資料讀寫、狀態、結果、失敗分支與 locator 寫入 managed Wiki；保留 user notes | 每個 capability 有可追溯 BA／SA pair | `analysis-gap`、uncovered、dangling link 阻擋；`.agents/skills/codebase-wiki/references/business-analysis-workflow.md:45` |
| 4 | ledger 與 Wiki 已更新 | 再讀 Wiki、inventory、exact masked payload，檢查 source integrity、DLP、容量與 migration | 取得 latest `preflight_id` | stale、規則正文缺漏或 residual 時保留舊 pack；`.agents/skills/codebase-wiki/scripts/notebooklm_exporter.py:5012` |
| 5 | discovery／readiness ID 相符 | 原子寫入 documents、sources、mapping、manifest 與 plan | `ready_to_export` → `pack_generated` | 超限、ID drift 或 boundary 失敗不替換舊 pack；`.agents/skills/codebase-wiki/scripts/notebooklm_exporter.py:3725` |

流程問題要保留觸發、前置條件、每一步行為、資料／狀態與失敗去向；只有標題、四步摘要或規則連結不算完整。沒有證據的現況使用 `Codebase 未提供證據`；`analysis-gap` 代表尚未追查完成並阻擋，`evidence-gap` 代表已查來源但沒有該事實，`business-confirmation` 代表實作可見但營運政策仍待確認。Raw/config/scope drift 需要重新 preview 與確認；Wiki-only 重建沿用原 discovery 確認。

## 輸入、輸出與狀態

輸入是安全 raw inventory、Wiki baseline、設定與確認後的兩個 identity；輸出是帶有完整流程正文與適用規則／需求正文的 `sources/*.md`、本機 documents、mapping、manifest 與 upload plan。`analysis-gap` → `knowledge_ready` 前不可進入 `ready_to_export`；`evidence-gap` 與 `business-confirmation` 要保留已知的 implementation-observed 行為。

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
