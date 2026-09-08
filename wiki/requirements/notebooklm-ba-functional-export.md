---
title: NotebookLM 現況 BA／SA 匯出
type: business-requirement
summary: 將當下完整安全 Codebase 重新萃取成每功能 BA／SA 與單一 Notebook 可用的離線來源包
requirement_id: fr-notebooklm-ba-functional-export
capability_id: cap-notebooklm-ba-functional-export
applies_to: ["[[notebooklm-ba-knowledge-export]]"]
evidence_state: implementation-observed
notebooklm_group: business-notebooklm-export
notebooklm_role: business
notebooklm_terms: [NotebookLM 匯出, BA, SA, 完整 codebase 覆蓋, 一次確認, DLP 遮罩, NotebookLM Enterprise]
sources:
  - .agents/skills/codebase-wiki/scripts/notebooklm_exporter.py
  - .agents/skills/codebase-wiki/references/notebooklm-export-workflow.md
  - .agents/skills/codebase-wiki/assets/notebooklm.toml
  - tests/notebooklm/test_export_notebooklm.py
source_digest: sha256:2165ae78c2a217cd4a46d496246261614e7bfb4857c9af27eddfa4099ef41c11
derived_from: ["[[overview]]", "[[notebooklm-ba-knowledge-export]]"]
last_updated: 2026-09-08
tags: [business-requirement, notebooklm, export, dlp]
status: active
---

# NotebookLM 現況 BA／SA 匯出

<!-- codebase-wiki:managed:start -->
## 業務目的

知識維護者需要把目標專案的當下完整安全 Codebase 重新整理成 Business Analyst 與
System Analyst 可直接查詢的現況知識。程式、設定、schema、測試、README、規格與註解
都是唯讀證據；衝突時以程式碼為主，沒有證據時明列 `Codebase 未提供證據`。

## 角色與權限

| 角色 | 可執行行為 | 可觀察結果 |
| --- | --- | --- |
| 知識維護者 | 盤點、萃取、維護 Wiki、執行 preflight 與 apply | 取得完整、可審查的 BA／SA source pack |
| Business Analyst | 查詢功能、角色、流程、規則、狀態與驗收條件 | 不必閱讀 code 或 repository path 即可理解系統 |
| System Analyst | 查詢邊界、I/O、資料、狀態、介面與失敗 | 保留必要 identifier 與 source locator 的現況 SA |
| NotebookLM 管理員 | 查核 tenant IAM、資料位置與安全控制 | 雲端狀態有證據才標示已驗證 |
| 業務擁有者／PO | 確認政策與 gap | 實作觀察不會被誤稱為正式政策 |

## 前置條件

- 目標 repository 可讀，且 raw sources 保持唯讀。
- Wiki schema、必要 catalogs、coverage ledger 與 `notebooklm.toml` 已安裝。
- 交付者使用同一本 Notebook，並只手動上傳 exporter 產生的 `sources/*.md`。

## 功能行為

| 情境 | 系統行為 | 可觀察結果 | 證據狀態 |
| --- | --- | --- | --- |
| 執行 discovery | 盤點所有安全 UTF-8 runtime source、config、schema、docs 與 behavioral tests | 每個 included file 都出現在 inventory | implementation-observed |
| 建立 BA／SA 模型 | 每個 active `cap-*` 建立專用 profiles、互連與 locators 的 BA／SA | 業務與系統現況均可追到 Codebase | implementation-observed |
| 重新萃取 | 重建 managed sections 並保留 user-notes sections | code 變更可反映於文件，人工註記不被覆寫 | business-confirmed |
| 完整性檢核 | 以 coverage ledger 分類每個安全檔案 | uncovered、analysis-gap 或 dangling requirement 會阻擋匯出 | implementation-observed |
| DLP 命中 | 在 analysis、documents 與 sources 以規則名稱遮罩 | 原始敏感值不進入交付，raw file 不被修改 | implementation-observed |
| 產生 pack | 產生獨立 BA／SA documents 與無損 upload sources mapping | 只上傳 sources，governance 留在本機 | implementation-observed |
| 容量檢核 | 依 Enterprise hard limits 與保守 local limits 分割／壓縮 | 超限時在 atomic commit 前失敗並保留舊 pack | implementation-observed |

## 業務規則與例外

- [[ba-knowledge-precedes-traceability]]
- [[readiness-preflight-required]]
- `implementation-observed` 不能升格為 `business-confirmed`。
- 非 UTF-8 或非文字業務證據必須列為 gap，不得假設其內容。
- 舊 schema v1–v5 或非 `codebase-ba-sa-retrieval-v1` pack 必須完整重建。

## 輸入、輸出與狀態

| 階段 | 輸入 | 輸出／狀態 |
| --- | --- | --- |
| Discovery | 完整安全 inventory、既有 Wiki 與設定 | preview 與 confirmed `discovery_id` |
| Analysis | confirmed snapshot | 每功能 BA／SA、coverage ledger 與 preserved notes |
| Readiness | 最新 Wiki、analyzed discovery ID、exact source plan | `ready_to_export` 與 latest `preflight_id` |
| Apply | confirmed discovery ID 與 latest readiness ID | schema-v6 local pack、governance 與 upload plan |
| Manual delivery | `sources/*.md` | 單一 Notebook 的現況 BA／SA 知識 |

## 驗收條件

- `AC-NBLM-001`：Given 已有完整 Wiki 但 Codebase 新增功能，When 重新 discovery，Then 新功能出現在預覽與文件計畫，所有安全來源也都有 disposition 或安全排除理由。
- `AC-NBLM-002`：Given 使用者確認 discovery 預覽一次，When 執行完整流程，Then 系統自動完成文件、readiness 與本機交付，不再要求第二次確認。
- `AC-NBLM-003`：Given 專案具有多個業務功能，When 文件化完成，Then 每個 active capability 都有 BA／SA 配對、雙向連結、專用 profile 與有效 source locator。
- `AC-NBLM-004`：Given README、規格、測試或註解與程式碼不一致，When 產生文件，Then 採用程式碼現況並把差異列為可見 gap。
- `AC-NBLM-005`：Given Codebase 未提供目的、政策或品質指標，When 產生文件，Then 標示 `Codebase 未提供證據`，不產生推測值，也不因此阻擋交付。
- `AC-NBLM-006`：Given 任一安全檔案尚未分析、`analyzed_discovery_id` 不符，或 capability 缺少 BA／SA，When 執行 readiness，Then `ready_to_export=false` 並列出缺漏。
- `AC-NBLM-007`：Given 完整 BA／SA upload sources 超出單一 Notebook 容量，When deterministic packing 後仍超限，Then 匯出失敗且不得省略功能或分成多本 Notebook。
- `AC-NBLM-008`：Given analysis、documents 或 sources 有敏感資料殘留、處理失敗或來源版本漂移，When apply，Then不得替換上一份有效 pack，raw sources 維持不變。
- `AC-NBLM-009`：Given 本機治理檢查完成但沒有租戶證據，When 產生 governance report，Then IAM、VPC Service Controls、CMEK、data location、Sensitive Data Protection 與 Model Armor 都標示管理員未驗證。
- `AC-NBLM-010`：Given schema v1–v5 或 BA-only pack，When 升級到 schema v6，Then同一 Notebook 的 upload plan 要求移除所有舊 static sources，再完整上傳新的 BA／SA sources。
- `AC-NBLM-011`：Given 文件含人工註記與程式識別碼，When 重新萃取及匯出，Then raw sources 與 user-notes 保持完整，敘述使用繁體中文並保留必要 identifier、API 與英文專有名詞。

## 關聯流程

- [[notebooklm-ba-knowledge-export]]

## 待確認事項

- `gap-notebooklm-non-text-evidence`：非 UTF-8／Office／影像型業務證據由誰轉換與核准？
- `gap-notebooklm-tenant-uat`：目標 tenant 的實際 DLP 與回答品質是否通過企業驗收？
<!-- codebase-wiki:managed:end -->

<!-- codebase-wiki:user-notes:start -->
## BA 補充註記

目前無人工補充。
<!-- codebase-wiki:user-notes:end -->

<!-- notebooklm:local-only:start -->
## 本機追溯

- Exporter：`.agents/skills/codebase-wiki/scripts/notebooklm_exporter.py`
- Workflow：`.agents/skills/codebase-wiki/references/notebooklm-export-workflow.md`
- Tests：`tests/notebooklm/test_export_notebooklm.py`
<!-- notebooklm:local-only:end -->
