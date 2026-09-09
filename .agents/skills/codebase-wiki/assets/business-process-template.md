---
title: "{業務流程名稱}"
type: business-process
summary: "{此流程為哪個角色在什麼條件下達成什麼結果}"
process_id: "bp-{domain}-{process}"
actors: ["{primary-actor}"]
coverage_status: partial
analysis_status: untraced
gap_classification: analysis-gap
notebooklm_group: "business-{capability-slug}"
notebooklm_role: business
notebooklm_terms: ["{流程名稱}", "{角色}", "{觸發事件}"]
sources:
  - "{path/to/business-or-implementation-evidence}"
source_locators: ["{path/to/evidence:line}"]
derived_from: ["[[overview]]"]
source_digest: "sha256:{64-lowercase-hex}"
last_updated: YYYY-MM-DD
tags: [business-process, notebooklm]
status: active
---

# {業務流程名稱}

<!-- codebase-wiki:managed:start -->

## 分析狀態與缺口分類

| 欄位 | 值 |
| --- | --- |
| Evidence trace | `untraced`／`traced` |
| Gap classification | `analysis-gap`／`evidence-gap`／`business-confirmation`／`none` |
| 判定 | {是否已完成入口、呼叫鏈、分支與資料操作追查} |

`analysis-gap` 代表尚未完成分析，不能寫成 Codebase 未提供證據；`evidence-gap` 代表已查
過安全來源仍無證據；`business-confirmation` 代表目前實作可見但營運政策、責任、核准或
SLA 需要業務確認。保留已知 implementation-observed 行為。

## 業務目的與範圍

## 角色

## 觸發與前置條件

## 主流程

| 步驟 | 觸發／條件 | 角色 | 業務行為 | 讀取／寫入資料 | 狀態變更 | 結果 | 失敗／下一步 | 證據狀態／locator |
| --- | --- | --- | --- | --- | --- | --- | --- | --- |
| 1 | {condition} | {actor} | {business-action} | {read/write} | {state transition} | {outcome} | {failure branch or gap} | implementation-observed / {path:line} |

每一步都要能由入口追到呼叫鏈與實際資料操作；若有多個分支，分別列出，不把整段流程
濃縮成一個摘要。

## 替代與例外流程

| 條件／失敗 | 偵測結果 | 替代處理 | 是否可重跑／回滾 | 證據狀態／locator |
| --- | --- | --- | --- | --- |
| {condition} | {observable error or block} | {next path} | {observed behavior or Codebase 未提供證據} | {state} / {path:line} |

## 業務規則

- [[{business-rule-page}]]

## 輸入、輸出與狀態轉換

| 輸入／資料 | 處理 | 輸出／副作用 | 前後狀態 | 證據狀態／locator |
| --- | --- | --- | --- | --- |
| {input} | {action} | {output} | {before → after} | {state} / {path:line} |

## 上下游影響

{付款、庫存、履約、通知或其他相鄰流程的可觀察影響；沒有證據時逐項寫 Codebase 未提供證據。}

## 成功結果

## 待確認事項

- `gap-{domain}-{topic}`：{question}

## 相關頁面

- [[functional-requirement-catalog]]
- [[business-process-catalog]]
- [[business-rule-catalog]]
- [[business-glossary]]
<!-- codebase-wiki:managed:end -->

<!-- codebase-wiki:user-notes:start -->
## BA 補充註記

<!-- 保留人工維護內容；重新萃取時不得覆寫。 -->
<!-- codebase-wiki:user-notes:end -->

<!-- notebooklm:local-only:start -->
## 本機追溯關聯

- [[{traceability-page}]]（技術內容不進入 NotebookLM source pack）
<!-- notebooklm:local-only:end -->
