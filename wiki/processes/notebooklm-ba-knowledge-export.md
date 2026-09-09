---
title: 建立 NotebookLM 現況 BA／SA 知識包
type: business-process
summary: 知識維護者以當下完整安全 Codebase 全量萃取每功能 BA／SA，經一次確認後交付單一 Notebook 來源包
process_id: bp-notebooklm-ba-knowledge-export
actors: [知識維護者, Business Analyst, System Analyst, NotebookLM 管理員]
coverage_status: covered
analysis_status: traced
gap_classification: business-confirmation
notebooklm_group: business-notebooklm-export
notebooklm_role: business
notebooklm_terms: [NotebookLM 匯出, 全量萃取, discovery ID, readiness preflight, BA, SA, 單一 Notebook]
sources:
  - .agents/skills/codebase-wiki/references/notebooklm-export-workflow.md
source_digest: sha256:83f0b22e00e098dbe3034b62a2b347621e01fa59cdcd009cb19ad6d1dc2f6db1
derived_from: ["[[overview]]", "[[notebooklm-export]]"]
last_updated: 2026-09-09
tags: [business-process, notebooklm, export]
status: active
---

# 建立 NotebookLM 現況 BA／SA 知識包

<!-- codebase-wiki:managed:start -->

## 業務目的與範圍

把當下完整安全 Codebase 的可觀察行為整理成每功能一組 BA／SA，形成 BA 與 SA 可在
同一本 Notebook 交叉詢問的 static Markdown source pack。程式、設定、schema、測試、
README、規格與註解都是唯讀證據；內容衝突時以程式碼為主。流程止於本機 pack 與手動
upload plan，不包含雲端操作自動化。

## 角色

| 角色 | 責任 |
| --- | --- |
| 知識維護者 | 盤點證據、提出文件計畫、維護 Wiki、執行 readiness 與產生 pack |
| Business Analyst | 檢視目的、角色、流程、規則、結果與例外是否忠於 Codebase |
| System Analyst | 檢視邊界、I/O、資料、狀態、介面與錯誤處理是否可追溯 |
| NotebookLM 管理員 | 在上傳前另行驗證租戶 IAM、資料位置與適用安全控制 |

## 觸發與前置條件

- 觸發：使用者明確要求建立或更新 NotebookLM BA／SA source pack。
- 前置：存在可讀的 repo root、Codebase LLM Wiki schema 與安全 UTF-8 文字來源。
- 非文字來源尚未轉換時不阻止盤點，但必須登記 gap。

## 主流程

| 步驟 | 觸發／條件 | 角色 | 業務行為 | 資料讀寫 | 狀態前／後 | 成功結果 | 失敗／下一步 | 證據定位 |
| --- | --- | --- | --- | --- | --- | --- | --- | --- |
| 1 | 使用者要求建立或更新 source pack | 知識維護者 | 執行唯讀 discovery，盤點安全來源、排除、Wiki 覆蓋與差異 | 讀取 repo、Wiki、設定；建立 inventory | `discovery_pending`／`preview_ready` | 形成 capability、gap 與文件計畫 | 不可讀或未分類來源列 gap，停止 readiness | `.agents/skills/codebase-wiki/references/notebooklm-export-workflow.md:75` |
| 2 | preview 已產生且 discovery ID 穩定 | 使用者 | 審查納入／排除、流程深度、BA／SA 配對與容量 | 讀取 preflight JSON；寫入確認意圖 | `preview_ready`／`plan_confirmed` | 取得唯一一次確認 | 範圍有疑問時修改計畫並重新 preview | `.agents/skills/codebase-wiki/references/notebooklm-export-workflow.md:88` |
| 3 | `plan_confirmed` | 知識維護者 | 從入口沿呼叫鏈追查流程，重建 managed BA／SA、保留 user notes，完成 disposition | 讀取 runtime/config/schema/docs/tests；寫入 Wiki、index、log、ledger | `plan_confirmed`／`knowledge_ready` | 每個 active capability 有 pair，流程保留條件、資料／狀態、分支與 locator | `analysis-gap`、uncovered 或 dangling link 阻擋；先補證據再重跑 | `.agents/skills/codebase-wiki/references/notebooklm-export-workflow.md:131` |
| 4 | 完整 snapshot 已寫入 coverage ledger | 知識維護者 | 執行 readiness，檢查 analyzed ID、配對、locator、流程完整性、DLP、容量與 migration | 讀取 Wiki、inventory、exact masked payload；產生 plan | `knowledge_ready`／`readiness_pending`／`ready_to_export` | 取得 latest `preflight_id` 與 flow-integrity report | stale、流程正文缺漏或 DLP residual 時保留舊 pack並修正 | `.agents/skills/codebase-wiki/scripts/notebooklm_exporter.py:5012` |
| 5 | `ready_to_export` 且兩個 ID 相符 | 知識維護者 | 原子產生 schema-v6 pack，確認 sources 含完整流程與適用規則正文 | 寫入 `.notebooklm/documents/`、`sources/`、manifest、plan、governance | `ready_to_export`／`pack_generated` | documents、upload sources、mapping 與 governance 完整 | 超限、ID drift 或輸出邊界不安全時不替換舊 pack | `.agents/skills/codebase-wiki/scripts/notebooklm_exporter.py:3725` |
| 6 | `pack_generated` | 交付者 | 依 upload plan 在同一本 Notebook 完整替換 static sources | 讀取 `sources/*.md` 與 plan；手動上傳 tenant | `pack_generated`／`tenant_validation_pending` | 來源可供跨功能查詢 | NotebookLM 問答與租戶控制仍須人工驗證，不能由本機檢查代替 | `docs/operations/validation/notebooklm-ba-uat.md:1` |

## 替代與例外流程

- 若任一安全來源未分類、仍為 `analysis-gap`、coverage ledger 的 analyzed ID 不符，或 capability
  缺少任一 BA／SA 文件，readiness 不通過；分析未完成不得被當成 Codebase 無證據。
- 若 confirmed discovery 後 raw source 或 discovery 設定改變，停止並重新 discovery；若只有 Wiki
  文件更新，保留 discovery ID，重新產生 readiness ID 後繼續，不要求第二次人工確認。
- DLP finding 會在 analysis、documents 與 sources 遮罩；若 final payload 仍有殘留、必要內容
  超過單一 Notebook 容量，或 output boundary 不安全，保留上一份 pack。
- 若上一份 manifest 是 schema v1–v5 或非 `codebase-ba-sa-retrieval-v1`，採 full rebuild，不混用舊來源。
- 無可靠 Codebase 證據的欄位明列 `Codebase 未提供證據`；這是可交付知識狀態，不是未完成分析。
- 已查到實作但沒有營運政策、核准角色、重跑權限或 SLA 時標成 `business-confirmation`，保留已知行為；來源查過仍不存在的事實標成 `evidence-gap`。兩者都不應抹去程式已證明的結果。

## 業務規則

`ba-knowledge-precedes-traceability`：先確立業務目的、流程與規則，再補技術定位；
`readiness-preflight-required`：完成分析、同步 ledger 後，必須通過最新 readiness preflight 才能產生 pack。

- [[ba-knowledge-precedes-traceability]]
- [[readiness-preflight-required]]

## 輸入、輸出與狀態轉換

| 階段 | 輸入 | 狀態 | 輸出 |
| --- | --- | --- | --- |
| Discovery | 安全 raw inventory、設定與既有 Wiki baseline | `discovery_pending` → `plan_confirmed` | capability、缺口與 BA／SA 文件計畫、`discovery_id` |
| Knowledge update | confirmed snapshot、來源證據 | `knowledge_updating` → `knowledge_ready` | BA／SA Wiki、coverage、index、log |
| Readiness | 最新 Wiki、相同 raw snapshot、設定 | `readiness_pending` → `ready_to_export` | exact source plan 與 `preflight_id` |
| Delivery | confirmed `discovery_id` 與 latest `preflight_id` | `ready_to_export` → `pack_generated` | schema-v6 local pack |

## 上下游影響

- 上游：業務文件、程式／設定觀察、領域擁有者確認與既有 Wiki。
- 下游：NotebookLM BA／SA 問答、人工審查、後續 gap closure 與 full-replacement upload plan。

## 成功結果

BA 與 SA 能以 capability ID 跨查目的、角色、流程、規則、邊界、I/O、資料、狀態、介面、
錯誤與 gaps。shared business context 會保留流程的完整步驟、條件、狀態／資料變更、失敗去向，
以及適用需求／規則正文。每份文件保留受控 locator，但不含 raw code body；交付者另在 tenant 驗證
存取、安全控制與問答品質，本機報告不代替該項驗證。

## 待確認事項

- `gap-notebooklm-non-text-evidence`：未轉成 UTF-8 repo text 的業務證據由誰整理與核准？
- `gap-notebooklm-tenant-uat`：目標 NotebookLM tenant 的實際回答是否通過固定 BA 題組？

<!-- codebase-wiki:managed:end -->

<!-- codebase-wiki:user-notes:start -->
## BA 補充註記

目前無人工補充。
<!-- codebase-wiki:user-notes:end -->

<!-- notebooklm:local-only:start -->
## 本機追溯關聯

- [[notebooklm-exporter]]（只有需要實作定位時才進入此 traceability page）
- [[notebooklm-export]]（操作者命令與安全檢查另置於此 traceability guide）
<!-- notebooklm:local-only:end -->

## 相關頁面

- [[business-process-catalog]]
- [[functional-requirement-catalog]]
- [[business-rule-catalog]]
- [[business-glossary]]
- [[business-knowledge-gaps]]
- [[business-analysis]]
