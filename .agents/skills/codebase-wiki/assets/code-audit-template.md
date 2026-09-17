---
title: "Codebase 健檢：{Scope}"
type: synthesis
summary: "以靜態檢視盤點 {Scope} 的入口與呼叫路徑，分列證據、業務疑點及覆蓋缺口"
sources: []
derived_from: []
source_digest: "sha256:{64-lowercase-hex}"
last_updated: YYYY-MM-DD
tags: [synthesis, code-audit, static-review]
status: active
notebooklm_group: local-governance
notebooklm_role: exclude
---

# Codebase 健檢：{Scope}

<!-- codebase-wiki:managed:start -->

## 結果摘要

- 範圍：`all` 或具體模組／入口
- 檢查日期：YYYY-MM-DD
- 檢查方式：唯讀靜態追查；沒有執行目標程式或測試
- 入口覆蓋：checked N、partial N、not checked N
- 確定缺陷：N；待確認業務疑點：N
- 限制：列出動態路由、外部依賴或未能取得的規格

## 檢查範圍與排除

列出納入的模組與入口類型、排除目錄／行為，以及排除理由。不要把未讀或無法解析的項目寫成已檢查。

## 入口覆蓋

| 入口 | 類型 | 狀態 | 追查路徑 | 未完成原因 |
| --- | --- | --- | --- | --- |
| `{route / command / handler}` | `{API / UI / CLI / job / event / public API / other}` | `checked / partial / not checked` | `{entry → validation → service → data/state → result}` | `{none or reason}` |

## 確定缺陷

若本次已檢查範圍沒有確定問題，寫：「本次已檢查範圍未發現具體缺陷。」不要暗示未檢查範圍也沒有問題。

### BUG-001 — {短標題}

- 狀態：`open`、`not-rechecked` 或 `rechecked-no-longer-observed`
- 證據確定度：`confirmed`
- 影響程度：`high`、`medium` 或 `low`
- 受影響入口：
- 可達觸發條件：
- 呼叫路徑：
- 證據：`path/to/file.ext:line`；說明上游防護、下游約束及為何可達
- 預期行為／明確規則：
- 實際行為與影響：
- 修正方向（不執行修正）：
- 建議驗證案例：

## 待確認業務疑點

若沒有，寫「未發現需要業務確認的事項」。每個疑點都要說明推論依據與未知政策。

### BIZ-001 — {待確認問題}

- 狀態：`needs-business-confirmation`、`not-rechecked` 或 `rechecked-no-longer-observed`
- 證據確定度：`unresolved`（業務政策待確認）
- 可能影響程度：`high`、`medium` 或 `low`
- 受影響入口：
- 呼叫路徑：
- 目前行為：
- 推論依據：`path/to/file.ext:line`；明確標示為推論
- 尚未明確的預期政策：
- 需確認的業務問題：
- 確認不同答案可能造成的差異：
- 建議驗證案例：

## 未完成工作與驗證建議

列出 partial/not checked 項目、資料或環境限制，以及建議由專案端執行的測試案例。此工作流未執行這些測試。

## 相關頁面

- 列出本次實際使用的相關 Wiki 頁面；若無則移除此項。

<!-- codebase-wiki:managed:end -->

<!-- codebase-wiki:user-notes:start -->
## 使用者筆記

<!-- 保留使用者補充的政策、註記與覆核意見；重跑時不得覆寫此區。 -->
<!-- codebase-wiki:user-notes:end -->
