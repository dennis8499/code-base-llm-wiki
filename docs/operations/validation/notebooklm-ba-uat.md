# NotebookLM 現況 BA／SA 固定驗收題組

本題組驗證 NotebookLM source pack 是否讓 Business Analyst 與 System Analyst 依當下
Codebase 理解同一功能。驗收資料必須包含一個「訂單取消」業務能力；每次評估都依下列固定
順序提問，不改寫題意，也不先提供實作路徑提示。

## 固定問題

1. 訂單取消要解決什麼業務問題？適用範圍與不適用範圍是什麼？
2. 哪些角色可以發起、核准或受到訂單取消影響？各自的責任是什麼？
3. 發起取消前必須滿足哪些前置條件？
4. 請逐步說明訂單取消的主要流程，從觸發到完成為止。
5. 訂單無法取消、重複取消或處理中失敗時，會走哪些替代或例外流程？
6. 哪些業務規則決定訂單是否可取消、是否需核准，以及取消結果？
7. 取消過程會改變哪些業務狀態與重要資料？哪些狀態不可逆？
8. 取消會如何影響付款／退款、庫存、履約與通知等下游業務？
9. 「取消」、「作廢」、「退款」與其他相關詞彙在本系統各代表什麼？是否有別名或容易混淆的邊界？
10. 關於訂單取消，目前有哪些未確認、證據不足或互相矛盾的知識？應由誰確認？
11. 請列出對應的功能需求 ID 與可驗收的 AC ID；每項驗收條件的可觀察結果是什麼？
12. 訂單取消的系統邊界、輸入、輸出與對外介面是什麼？
13. 哪些資料與狀態會被讀取或改變？請保留實際 API、symbol 或 schema 識別碼。
14. 系統如何表達、傳遞或回應失敗？Codebase 沒有提供哪些錯誤處理證據？
15. BA 與 SA 的敘述是否互相連結，並能指出支持結論的 source locator？

## 評分方式

每題以 0–2 分評分：

- **2 分**：直接回答題意，引用 capability BA／SA、相關 ID 與來源；未知事項使用 `Codebase 未提供證據`，且不揭露敏感值。
- **1 分**：答案部分完整或可追溯，但遺漏重要 actor、條件、例外、狀態、證據標籤或 gap。
- **0 分**：無法回答、臆測業務事實、主要以程式 symbol／檔案路徑作答，或把 implementation-observed 說成已確認政策。

第 1–10 題計入 BA 20 分；第 11–15 題是 BA／SA 追溯必過 gates。通過條件：

- 總分至少 17/20，且第 4、6、10 題不得為 0 分；
- 每個事實都能追溯至 BA 或 SA 文件，推論與 gap 不得偽裝成既定規則；
- 第 11 題必須回傳至少一個 cataloged `fr-*` 與 stable `AC-*`，且 AC 能客觀驗收；
- 回答先使用 functional requirement、business process/rule、glossary 與 gaps；
- 第 8、9 題必須能從 `shared-business-context` 取得跨功能流程與共用詞彙，
  再以相關 capability BA／SA 交叉驗證；
- 回答與上傳 sources 不得包含 secret；SA 可保留文件已列出的必要 API、symbol、schema 與 source locator；
- 不因缺少 PDF、Office、圖片、訪談或外部系統資料而自行補寫答案；
- BA 答案不要求先知道技術識別碼；SA 答案保留 Codebase 中實際存在的必要識別碼。

## 失敗診斷

若不通過，先依問題類型修正 Wiki，再重新跑 readiness preflight：

| 失敗型態 | 優先修正 |
| --- | --- |
| 目的、角色或主流程不清 | `wiki/overview.md`、對應 `wiki/processes/*.md` |
| 功能或驗收條件不清 | `wiki/requirements/*.md`、functional requirement catalog |
| 規則、條件或證據狀態不清 | `wiki/rules/*.md`、business rule catalog |
| 詞彙混用 | business glossary |
| 未知事項被臆測 | business knowledge gaps 與 `evidence_state` |
| 只能從 code/path 回答 | 補 BA 主文件；把 code/path 留在 local-only Wiki provenance，不上傳 |

## 2026-09-07 schema v6 驗證紀錄

### Static Task Tracker journey

`BDD-005` 會在兩個彼此隔離的 `samples/task-tracker` 副本分別安裝 Codex 與
GitHub Copilot surface，執行完整 discovery preflight，保存一次 confirmed
`discovery_id`，套入已人工核對的 current-state Wiki fixture，再執行 readiness 與
local apply。測試同時核對原始 sample hashes、BA／SA 配對、人工註記與輸出內容。

- GitHub Copilot：runtime-unverified；本次只完成 installed static journey，沒有可用的 Copilot host runtime 證據。
- OpenAI Codex：runtime-unverified；本次只完成 installed static journey，沒有另啟 Codex host runtime 互動。
- NotebookLM／Google Cloud tenant：runtime-unverified；沒有上傳、問答或租戶控制實測。

因此，static journey 證明安裝後兩個 surface 共用相同的一次確認與離線匯出契約；
它不冒充實際 agent UI 的人類確認事件，也不冒充 NotebookLM 問答品質或租戶合規。

### 人工語意 evidence

| 核對項目 | Evidence 與結果 |
| --- | --- |
| 程式碼優先衝突核對 | Task Tracker fixture 故意讓 README 宣稱 completed task 可再次完成；current-state BA 依 `TaskTrackerService.complete_task` 的拒絕行為記錄差異，`BDD-005` 核對輸出仍含此結論。Pass。 |
| 未知值核對 | Fixture 對缺少的核准角色與政策保留 `Codebase 未提供證據`，沒有補寫目標政策。Pass。 |
| 繁體中文與識別碼核對 | BA 敘述保留繁體中文，並保留 `TaskTrackerService.complete_task`、`cap-task-tracking` 等實際識別碼。Pass。 |
| 重新產生與人工註記 | Fixture 的 `codebase-wiki:user-notes` 內容進入完整 local document；原始 Task Tracker hashes 在 apply 後完全相同。Pass。 |
| standalone 邊界 | `BDD-004` 放入 standalone BA、standalone SA 與 SD decoys；最終 upload sources 均不含其 sentinel。Pass。 |
| 共用檢索內容 | `BDD-004` 驗證 glossary 與 active evidence-backed process body 實際存在於 `shared-business-context` upload bytes，且 BA／SA mapping 未遺漏。Pass。 |
