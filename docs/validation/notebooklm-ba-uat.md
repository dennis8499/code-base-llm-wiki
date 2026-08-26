# NotebookLM BA-only 功能需求固定驗收題組

本題組驗證 NotebookLM source pack 是否真的讓 Business Analyst 了解業務，而不是只把
程式碼改寫成技術摘要。驗收資料必須包含一個「訂單取消」業務能力；每次評估都依下列固定
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

## 評分方式

每題以 0–2 分評分：

- **2 分**：直接回答題意，引用 `fr-*`／`AC-*` 與 BA 主文件；規則附證據狀態，未知事項明確列為 gap，且不揭露 raw evidence。
- **1 分**：答案部分完整或可追溯，但遺漏重要 actor、條件、例外、狀態、證據標籤或 gap。
- **0 分**：無法回答、臆測業務事實、主要以程式 symbol／檔案路徑作答，或把 implementation-observed 說成已確認政策。

第 1–10 題計入 20 分；第 11 題是額外必過 gate。通過條件：

- 總分至少 17/20，且第 4、6、10 題不得為 0 分；
- 每個事實都能追溯至 BA 文件，推論與 gap 不得偽裝成既定規則；
- 第 11 題必須回傳至少一個 cataloged `fr-*` 與 stable `AC-*`，且 AC 能客觀驗收；
- 回答先使用 functional requirement、business process/rule、glossary 與 gaps；
- 回答與上傳 sources 不得包含 raw code、raw config、secret、repository path 或 technical traceability；
- 不因缺少 PDF、Office、圖片、訪談或外部系統資料而自行補寫答案；
- 答案對 BA 可讀，不要求先知道 repository path、class、function、table 或 API 名稱。

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
