---
title: {capability-title} BA
type: synthesis
summary: 依當下 Codebase 整理 {capability-title} 的現況業務分析。
standards_profile: codebase-business-analysis-v1
coverage_status: gap
capability_id: cap-{capability}
notebooklm_document: ba
notebooklm_group: business-{capability}
notebooklm_role: business
notebooklm_terms: [{capability-title}]
analysis_status: untraced
gap_classification: analysis-gap
sources: []
source_locators: []
derived_from: ["[[{requirement-page}]]", "[[cap-{capability}-sa]]"]
last_updated: YYYY-MM-DD
tags: [synthesis, business-analysis, codebase-as-is, notebooklm]
status: active
---

# {capability-title} BA

<!-- codebase-wiki:managed:start -->
## 分析狀態與缺口分類

| 欄位 | 值 |
| --- | --- |
| Evidence trace | `traced`／`evidence-gap`／`business-confirmation`／`untraced` |
| Gap classification | `analysis-gap`／`evidence-gap`／`business-confirmation`／`none` |
| 判定 | {完成全量追查，或列出仍缺少的來源與需確認的業務政策} |

`analysis-gap` 只表示尚未完成入口、呼叫鏈、分支或資料操作的追查；完成追查後若來源沒有
證據寫 `Codebase 未提供證據` 並標成 `evidence-gap`，若實作可見但營運責任、核准或
SLA 尚未確認則標成 `business-confirmation`。不可用後兩者掩蓋未完成分析。

## 功能目的、角色與觸發

{以業務語言說明目的、適用範圍、不適用範圍、角色責任與觸發事件；每一項標示證據狀態。}

## 前置條件與完整流程

### 前置條件

{列出每個必要輸入、資料可用性、狀態與權限條件；沒有證據時逐項寫 Codebase 未提供證據。}

### 逐步流程

| 步驟 | 觸發／條件 | 角色 | 業務行為 | 讀取／寫入資料 | 狀態變更 | 成功結果 | 失敗／下一步 | 證據狀態／locator |
| --- | --- | --- | --- | --- | --- | --- | --- | --- |
| 1 | {condition} | {actor} | {observable action} | {read/write or Codebase 未提供證據} | {state transition} | {outcome} | {failure branch or Codebase 未提供證據} | {state} / {path:line} |

每一個步驟都必須能從入口追到實際呼叫鏈、條件分支、資料操作與結果；不得把多個呼叫
壓成一個概括步驟。

## 業務規則正文

| 規則 ID／名稱 | 適用條件 | 決策／結果 | 例外 | 證據狀態／locator |
| --- | --- | --- | --- | --- |
| `br-*`／{rule} | {condition} | {decision and result} | {exception} | {state} / {path:line} |

規則不可只保留 `[[page]]` 連結；請在此保留可獨立閱讀的條件、結果與例外摘要。

## 結果、狀態與例外

{說明完成條件、不可逆狀態、替代／例外流程、阻擋原因、失敗後續、回滾或重跑行為。}

## 上下游影響

{說明付款、庫存、履約、通知或其他相鄰能力的可觀察影響；沒有證據時寫 Codebase 未提供證據。}

## 驗收對應

- `fr-*`：{功能需求}
- `AC-*`：{可由外部觀察的 Given／When／Then 結果}

## 來源衝突

Codebase 未提供證據。若 README、規格、測試或註解與程式碼衝突，以程式碼現況為主並逐項記錄。

## 來源定位

- Codebase 未提供證據。

## 對應 SA

[[cap-{capability}-sa]]
<!-- codebase-wiki:managed:end -->

<!-- codebase-wiki:user-notes:start -->
## Reviewer Notes

<!-- Preserve manual notes across regeneration. -->
<!-- codebase-wiki:user-notes:end -->
