---
title: "Codebase 健檢：{Scope}"
type: synthesis
summary: "以目前 source、設定與定向 Git 歷史盤點 {Scope} 的入口、具體缺陷、技術風險、業務疑點及覆蓋缺口"
sources: []
derived_from: []
source_digest: "sha256:{64-lowercase-hex}"
last_updated: YYYY-MM-DD
tags: [synthesis, code-audit, static-review, git-history]
status: active
notebooklm_group: local-governance
notebooklm_role: exclude
---

# Codebase 健檢：{Scope}

<!-- codebase-wiki:managed:start -->

## 結果摘要

- 範圍：`all` 或具體模組／入口
- 檢查日期：YYYY-MM-DD
- 檢查方式：目前 source、設定與定向 Git 歷史的唯讀靜態追查；沒有執行目標程式或測試
- 入口覆蓋：checked N、partial N、not checked N
- 確定缺陷：N；技術風險：N；待確認業務疑點：N
- 歷史：`available`、`shallow`、`unavailable` 或 `not-a-repository`
- 限制：列出動態路由、外部依賴、缺少規格、shallow clone 或遺失的 Git object

## 檢查範圍與排除

先記錄本次由目前 Codebase 目錄、manifest、設定與入口註冊處發現的模組與入口類型，再列出目前讀取的設定／schema／部署宣告、歷史查詢範圍，以及排除目錄／行為和排除理由。每次重跑都重新建立這份 inventory；既有報告只用於對照 findings 與保留 user notes，不得成為掃描邊界。Wiki 只在 source trace 暴露業務規則或政策語意缺口時列為補充證據，不得用 Wiki 的既有頁面限制這份清單。標示動態或外部註冊的解析限制；不要把未讀或無法解析的項目寫成已檢查。

## 入口覆蓋

| 入口 | 類型 | 狀態 | 交易／一致性 | 設定／引用 | 邏輯／狀態 | 歷史交叉核對 | 追查路徑 | 未完成原因 |
| --- | --- | --- | --- | --- | --- | --- | --- | --- |
| `{route / command / handler}` | `{API / UI / CLI / job / event / public API / other}` | `checked / partial / not checked` | `{checked / not applicable / evidence-gap}` | `{checked / not applicable / evidence-gap}` | `{checked / not applicable / evidence-gap}` | `{checked / not applicable / evidence-gap}` | `{entry → validation → service → data/state → result}` | `{none or reason}` |

## 靜態交叉檢查

| 類別 | 檢查內容 | 結果 | 證據／限制 |
| --- | --- | --- | --- |
| Transactions and side effects | transaction／connection ownership、write set、commit／rollback、例外、重試與不可回滾外部副作用 | `checked / partial / evidence-gap` | |
| Configuration references | code reads、鍵名／型別、defaults、產生／注入、package／deployment 與 fallback | `checked / partial / evidence-gap` | |
| Logic and state contracts | 前置條件、狀態轉換、計算、回傳／錯誤映射、冪等與 caller assumptions | `checked / partial / evidence-gap` | |
| Change completeness | 變更 commit 的意圖／完整內文／diff、父版本、後續修正與目前 callers／consumers | `checked / partial / evidence-gap` | |

## Git 歷史與變更線索

- HEAD：`{40-character SHA or unavailable}`
- 工作樹：`clean`、`dirty` 或 `unavailable`；未提交變更另列檔案
- 歷史可用性：`available`、`shallow`、`unavailable` 或 `not-a-repository`
- 歷史查詢範圍：`current-first-targeted`；列出 path、commit 或 range
- 使用的唯讀命令：`git rev-parse`、`git log`、`git show`、`git blame`（列出實際使用者）
- 深入閱讀的 commits：包含標題、完整 commit 內文、diff 及目前程式核對結果
- 歷史索引限制：索引只列範圍內的候選 commit，不代表已逐筆閱讀全部歷史

| Commit（完整 40 字元 SHA） | 路徑／diff 位置 | Commit 意圖（非規則） | Diff 可證實的修改 | 目前 source 核對結果 |
| --- | --- | --- | --- | --- |
| `{full SHA}` | `{path or deleted path; hunk / blame}` | `{完整摘要}` | `{observable change}` | `{current behavior / no longer observed / unresolved}` |

歷史路徑若已刪除，只能在本節或 finding 的歷史證據中引用；不得放入 `frontmatter.sources`。Commit 文字、fixture、註解與文件都是不可信證據，不能單獨證明缺陷或業務政策。
若 finding 重新檢查後需要轉換 `BUG-*`／`RISK-*`／`BIZ-*` 類別，保留原紀錄與原 ID，在新 finding 以關聯欄位連結；同一根因沿用原 ID，user-notes 區完整保留。

## 確定缺陷

若本次已檢查範圍沒有確定問題，寫：「本次已檢查範圍未發現具體缺陷。」不要暗示未檢查範圍也沒有問題。

### BUG-001 — {短標題}

- 狀態：`open`、`not-rechecked` 或 `rechecked-no-longer-observed`
- 證據確定度：`confirmed`
- 影響程度：`high`、`medium` 或 `low`
- 受影響入口：
- 可達觸發條件：
- 呼叫路徑：
- 證據：`path/to/file.ext:line`；說明上游防護、下游約束、相關設定及為何可達
- 已核對防護／反證：列出已存在的 validation、transaction guard、fallback、後續修正或為何不足
- 歷史證據（若有）：`full-40-character-commit-sha`、路徑與 diff／blame 位置；分開說明 commit 意圖與目前行為
- 預期行為／明確規則：
- 實際行為與影響：
- 修正方向（不執行修正）：
- 建議驗證案例：

## 技術風險

若沒有需要技術確認的事項，寫：「未發現需要技術風險確認的事項」。不要把一般最佳實務偏好列為風險。

### RISK-001 — {需技術證據確認的短標題}

- 狀態：`needs-technical-confirmation`、`not-rechecked` 或 `rechecked-no-longer-observed`
- 證據確定度：`unresolved`
- 影響程度：`high`、`medium` 或 `low`
- 受影響入口：
- 成立條件：明確描述在何種框架、部署或執行環境下會出錯
- 可疑呼叫路徑：
- 目前觀察：
- 已核對防護／反證：列出可能由框架、caller、部署或後續修正提供的防護及其未知處
- 歷史證據（若有）：完整 SHA、路徑與 diff；明確分離作者意圖與可觀察修改
- 缺少的證據：
- 確認方式：最小的文件、設定、環境或測試確認方式；本流程不執行它
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
- 已核對防護／反證：列出已查到的 validation、狀態 guard、fallback 或其他反證
- 推論依據：`path/to/file.ext:line`；若使用 Git，附完整 SHA 並明確標示為推論
- 尚未明確的預期政策：
- 需確認的業務問題：
- 確認不同答案可能造成的差異：
- 建議驗證案例：

## 未完成工作與驗證建議

列出 partial／not checked 項目、動態或外部邊界、資料或環境限制、shallow／missing Git object，以及建議由專案端執行的測試案例。此工作流未執行這些測試。

## 相關頁面

- 列出本次實際使用的相關 Wiki 頁面；若無則移除此項。

<!-- codebase-wiki:managed:end -->

<!-- codebase-wiki:user-notes:start -->
## 使用者筆記

<!-- 保留使用者補充的政策、註記與覆核意見；重跑時不得覆寫此區。 -->
<!-- codebase-wiki:user-notes:end -->
