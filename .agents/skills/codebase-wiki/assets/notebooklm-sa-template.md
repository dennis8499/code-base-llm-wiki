---
title: {capability-title} SA
type: synthesis
summary: 依當下 Codebase 整理 {capability-title} 的現況系統分析。
standards_profile: codebase-system-analysis-v1
coverage_status: gap
capability_id: cap-{capability}
notebooklm_document: sa
notebooklm_group: business-{capability}
notebooklm_role: analysis
notebooklm_terms: [{capability-title}]
analysis_status: untraced
gap_classification: analysis-gap
sources: []
source_locators: []
derived_from: ["[[{requirement-page}]]", "[[cap-{capability}-ba]]"]
last_updated: YYYY-MM-DD
tags: [synthesis, system-analysis, codebase-as-is, notebooklm]
status: active
---

# {capability-title} SA

<!-- codebase-wiki:managed:start -->
## 分析狀態與缺口分類

| 欄位 | 值 |
| --- | --- |
| Evidence trace | `traced`／`evidence-gap`／`business-confirmation`／`untraced` |
| Gap classification | `analysis-gap`／`evidence-gap`／`business-confirmation`／`none` |
| 判定 | {已完成入口、呼叫鏈、資料與失敗分支追查，或列出缺少的 evidence} |

`analysis-gap` 表示尚未完成技術追查，必須在 readiness 前補完；`evidence-gap` 表示已檢查
安全來源但沒有行為證據；`business-confirmation` 表示目前實作可觀察但政策、責任、
核准或 SLA 仍待業務確認。後兩者不得抹去已知的實作行為。

## 系統邊界、輸入與輸出

{列出入口、系統邊界、外部 actor／服務、輸入、輸出與觸發條件，保留實際 API／symbol 名稱。}

## 資料、狀態與轉換

| 步驟／操作 | 讀取資料 | 寫入資料 | 狀態前 | 狀態後 | 一致性／交易邊界 | 證據狀態／locator |
| --- | --- | --- | --- | --- | --- | --- |
| 1 | {input or schema} | {output or schema} | {before} | {after} | {boundary or Codebase 未提供證據} | {state} / {path:line} |

必須從入口逐步追蹤呼叫鏈、分支與資料操作；不可只列 service 或 controller 名稱。

## 介面、依賴與錯誤處理

| 介面／依賴 | 請求／事件 | 回應／副作用 | 失敗表達 | 重試／回滾 | 證據狀態／locator |
| --- | --- | --- | --- | --- | --- |
| {API／symbol} | {input} | {output} | {error/status} | {observed retry or Codebase 未提供證據} | {state} / {path:line} |

## 逐步執行與失敗分支

| 步驟 | 呼叫／判斷 | 前置條件 | 成功結果 | 阻擋／例外 | 後續或重跑 | 證據狀態／locator |
| --- | --- | --- | --- | --- | --- | --- |
| 1 | {call or branch} | {condition} | {observable result} | {failure branch} | {next action} | {state} / {path:line} |

## 來源衝突

Codebase 未提供證據。若 README、規格、測試或註解與程式碼衝突，以程式碼現況為主並逐項記錄。

## 來源定位

- Codebase 未提供證據。

## 對應 BA

[[cap-{capability}-ba]]
<!-- codebase-wiki:managed:end -->

<!-- codebase-wiki:user-notes:start -->
## Reviewer Notes

<!-- Preserve manual notes across regeneration. -->
<!-- codebase-wiki:user-notes:end -->
