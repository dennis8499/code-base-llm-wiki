---
title: NotebookLM BA 功能需求匯出
type: business-requirement
summary: 將完整安全 codebase 重新萃取成單一 Notebook 可使用、無 raw code 與敏感原文的 BA 功能需求來源包
requirement_id: fr-notebooklm-ba-functional-export
capability_id: cap-notebooklm-ba-functional-export
applies_to: ["[[notebooklm-ba-knowledge-export]]"]
evidence_state: implementation-observed
notebooklm_group: business-notebooklm-export
notebooklm_role: business
notebooklm_terms: [功能需求匯出, BA-only, 完整 codebase 覆蓋, DLP 遮罩, 驗收條件, NotebookLM Enterprise]
sources:
  - .agents/skills/codebase-wiki/scripts/notebooklm_exporter.py
  - .agents/skills/codebase-wiki/references/notebooklm-export-workflow.md
  - .agents/skills/codebase-wiki/assets/notebooklm.toml
  - tests/test_export_notebooklm.py
source_digest: sha256:3f57332396c9a618443114db603e2f675e89d51e1ba3994322424515955392d3
derived_from: ["[[overview]]", "[[notebooklm-ba-knowledge-export]]"]
last_updated: 2026-08-26
tags: [business-requirement, notebooklm, export, dlp]
status: active
---

# NotebookLM BA 功能需求匯出

<!-- codebase-wiki:managed:start -->
## 業務目的

知識維護者需要把目標專案的完整安全 codebase 重新整理成 Business Analyst 可直接查詢的
功能需求知識。上傳內容只包含 BA 文件；程式、設定、測試與 schema 只作為本機分析證據，
不得以 raw text 或技術追溯附錄進入 NotebookLM。

## 角色與權限

| 角色 | 可執行行為 | 可觀察結果 |
| --- | --- | --- |
| 知識維護者 | 盤點、萃取、維護 Wiki、執行 preflight 與 apply | 取得完整、可審查的 BA source pack |
| Business Analyst | 查詢功能、角色、流程、規則、狀態與驗收條件 | 不必閱讀 code 或 repository path 即可理解系統 |
| 業務擁有者／PO | 確認政策與 gap | 實作觀察不會被誤稱為正式政策 |

## 前置條件

- 目標 repository 可讀，且 raw sources 保持唯讀。
- Wiki schema、必要 BA 文件與 `notebooklm.toml` 已安裝。
- 交付者使用同一本 Notebook，並只手動上傳 exporter 標記的 BA Markdown sources。

## 功能行為

| 情境 | 系統行為 | 可觀察結果 | 證據狀態 |
| --- | --- | --- | --- |
| 執行 discovery | 盤點所有安全 UTF-8 runtime source、config、schema、docs 與 behavioral tests | 每個 included file 都出現在 inventory | implementation-observed |
| 建立 BA 模型 | 以 `fr-*`、`bp-*`、`br-*` 與 `AC-*` 描述可觀察行為 | BA 能由功能需求追到流程、規則與驗收條件 | implementation-observed |
| 重新萃取 | 重建 managed sections 並保留 user-notes sections | code 變更可反映於 BA 文件，人工註記不被覆寫 | business-confirmed |
| 完整性檢核 | 以 coverage ledger 分類每個安全檔案 | uncovered、analysis-gap 或 dangling requirement 會阻擋匯出 | implementation-observed |
| DLP 命中 | 在分析副本與最終 payload 以規則名稱遮罩 | 原始敏感值不進入 BA source，raw file 不被修改 | implementation-observed |
| 產生 pack | 只 materialize BA Wiki、query index 與 project map | source pack 不含 raw code、raw config 或 technical traceability | implementation-observed |
| 容量檢核 | 依 Enterprise hard limits 與保守 local limits 分割／壓縮 | 超限時在 atomic commit 前失敗並保留舊 pack | implementation-observed |

## 業務規則與例外

- [[ba-knowledge-precedes-traceability]]
- [[readiness-preflight-required]]
- `implementation-observed` 不能升格為 `business-confirmed`。
- 非 UTF-8 或非文字業務證據必須列為 gap，不得假設其內容。
- 舊 schema v1–v4 或非 `business-only-ba-v2` pack 必須完整重建。

## 輸入、輸出與狀態

| 階段 | 輸入 | 輸出／狀態 |
| --- | --- | --- |
| Analysis | 完整安全 inventory、既有 Wiki、設定 | masked working copies、coverage 與 BA regeneration plan |
| Readiness | 最新 Wiki、coverage ledger、exact source plan | `ready_to_export` 與綁定內容的 `preflight_id` |
| Apply | 相符 ID 與相同 filesystem state | schema-v5 local pack 與 upload plan |
| Manual delivery | Exporter 標記的 BA Markdown sources | 單一 Notebook 的 BA 功能需求知識 |

## 驗收條件

- `AC-NBLM-001`：Given 完整目標 repository，When 執行 preflight，Then runtime source、runtime config、data schema、project docs 與 behavioral tests 均被盤點或以安全理由排除。
- `AC-NBLM-002`：Given 任一安全檔案未分類、標為 `analysis-gap` 或連到不存在的需求，When 計算 readiness，Then `ready_to_export` 為 false。
- `AC-NBLM-003`：Given 每個可觀察行為已建模，When 產生 BA Wiki，Then 每個 active `fr-*` 均由 functional requirement catalog 連結，且至少包含一個穩定 `AC-*`。
- `AC-NBLM-004`：Given managed 與 user-notes markers，When 重新萃取，Then managed content 更新且人工 notes 被保留。
- `AC-NBLM-005`：Given raw analysis input 含 DLP pattern，When 執行 preflight／apply，Then working copy 以 `[MASKED:<RULE>]` 取代命中、報告不含原值、raw file 不變。
- `AC-NBLM-006`：Given final BA payload，When residual DLP scan 完成，Then零殘留才可 commit；任何殘留均保留上一份 pack。
- `AC-NBLM-007`：Given 成功匯出，When 檢查 final upload sources，Then只存在 router、navigation 與 business documentation，且不含 raw code／config／repository path／technical traceability。
- `AC-NBLM-008`：Given Enterprise 設定，When 驗證容量，Then hard limits 為 300 sources、500 MB/source、500,000 words/source，超限設定 fail closed。
- `AC-NBLM-009`：Given Wiki、inventory、設定或 output identity 在 preflight 後改變，When 使用舊 ID apply，Then apply 被拒絕並要求新 preflight。
- `AC-NBLM-010`：Given schema v1–v4 的既有 pack，When 產生 schema v5，Then upload plan 要求在同一本 Notebook 移除所有舊 static sources 後完整上傳新 sources。

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
- Tests：`tests/test_export_notebooklm.py`
<!-- notebooklm:local-only:end -->
