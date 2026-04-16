# 編排模式設計指引

## 目錄

1. [模式選型決策樹](#模式選型決策樹)
2. [Dynamic Router Pattern](#pattern-a-dynamic-router-pattern)
3. [Closed-Loop Sequential Chain](#pattern-b-closed-loop-sequential-chain)
4. [Fan-out / Fan-in Pattern](#pattern-c-fan-out--fan-in-pattern)
5. [混合模式](#混合模式)

---

## 模式選型決策樹

```
用戶請求抵達 Router Agent
│
├── 子任務之間有無前後依賴？
│   │
│   ├── 無依賴（各自獨立）
│   │   │
│   │   ├── 只需要分發給 1 個子代理 → Dynamic Router（單路由）
│   │   └── 需要分發給多個子代理 → Fan-out / Fan-in
│   │
│   └── 有依賴（上游輸出 = 下游輸入）
│       │
│       ├── 是否需要自我驗證（生成後測試、測試失敗後修正）？
│       │   ├── 需要 → Closed-Loop Sequential Chain
│       │   └── 不需要 → 簡單 Sequential Chain（Chain 的特例，無回饋迴圈）
│       │
│       └── 部分子任務可平行，部分有依賴？
│           └── 混合模式（Fan-out + Sequential）
```

---

## Pattern A: Dynamic Router Pattern

### 概念

最常見的編排方式。Router Agent 充當「調度員」（Dispatcher），接收用戶請求後，
透過意圖分類器判斷應交由哪個 Sub-Agent 處理，然後動態分發。

```
[用戶請求] → [Router Agent]
                 │
                 ├─ 意圖 = "資料查詢"    → [DataAccess Sub-Agent]
                 ├─ 意圖 = "安全審計"    → [Security Sub-Agent]
                 ├─ 意圖 = "測試撰寫"    → [Testing Sub-Agent]
                 └─ 意圖不明確           → [askQuestions] → 釐清後重新路由
```

### 核心元件

#### 1. 意圖分類器（Intent Classifier）

Router Agent 內建的分類邏輯，負責自然語言理解與決策。

**設計原則**：
- 使用低延遲的模型或等效的輕量分類策略處理分類，降低路由延遲
- 分類結果應為離散類別（明確對應到子代理），而非模糊描述
- 當信心度低於閾值時，不分發，直接觸發 `askQuestions`

若宿主無法為不同 Agent 綁定不同模型，也沒關係；重點是讓 Router 的分類任務保持短小、可快速決策。

**Copilot 原生實現**：
Router Agent 的 `.agent.md` 中，以條件式指令描述分類邏輯：

```markdown
## 路由規則

收到用戶請求後，先判斷意圖類型：

1. 若涉及資料庫 Schema、SQL 查詢、ORM 優化 → 委派給 `data-access-agent`
2. 若涉及安全漏洞、權限控制、OWASP 審計 → 委派給 `security-reviewer`
3. 若涉及測試撰寫、覆蓋率提升、Mock 設計 → 委派給 `test-writer`
4. 若無法判斷或同時符合多個類別 → 使用 askQuestions 釐清
```

#### 2. 釐清機制（Disambiguation）

**強制觸發條件**（寫入 Router Agent 的 `.agent.md`）：
- 用戶請求同時符合 ≥ 2 個子代理的職責
- 關鍵參數缺失（目標資料表、部署環境等）
- 用戶使用了模糊動詞（「優化」「調整」「修一下」）

**釐清後的行為**：
- 獲得釐清答案後，將答案作為額外上下文附加到分發請求中
- 不要要求用戶重複整個請求

#### 3. 動態分發（Dispatch via runSubagent）

在 Copilot 原生環境中，使用 `runSubagent` 進行委派：

```
使用 runSubagent 工具，將以下任務委派給 [Sub-Agent Name]：
- 任務描述：[精簡的任務摘要]
- 輸入資料：[已摘要的上下文]
- 期望輸出：[明確的輸出格式]
```

**分發時的上下文裁剪**：
Router 不要把完整對話歷史傳給 Sub-Agent。只傳遞：
1. 任務描述（一段話）
2. 相關的檔案路徑或程式碼片段
3. 用戶明確的約束條件

### 適用時機

- 用戶請求可明確歸類到單一領域
- 子代理之間不需要共享中間狀態
- 系統有 ≥ 3 個專業化子代理

---

## Pattern B: Closed-Loop Sequential Chain

### 概念

適用於具備高度前後依賴性，且需要「自我驗證」的 Meta-Agent 場景。
典型應用：自動生成程式碼 → 自動測試 → 發現問題 → 自動修正。

```
[Router Agent]
    ↓
[Research Agent] ── 產出分析報告 ──→ 寫入 Shared Blackboard
    ↓
[Planner Agent] ── 讀取報告，產出執行計畫 ──→ 寫入 Shared Blackboard
    ↓
[Implementer Agent] ── 讀取計畫，產出程式碼 ──→ 寫入 Shared Blackboard
    ↓
[Tester Agent] ── 讀取程式碼，執行測試
    │
    ├── 測試通過 → 彙整結果，回傳 Router
    └── 測試失敗 → Error Log 寫入 Blackboard → 回到 Implementer（最多 3 次）
```

### 核心元件

#### 1. Shared Blackboard（共享黑板）

在 Copilot 原生環境中，使用 `/memories/session/` 作為黑板：

```
/memories/session/
├── orchestration-plan.md          ← Router 寫入的全域計畫
├── research-output.md             ← Research Agent 的分析報告
├── implementation-plan.md         ← Planner Agent 的執行計畫
├── implementation-output.md       ← Implementer 的程式碼摘要
└── test-results.md                ← Tester 的驗證結果
```

**寫入規則**：
- 每個 Agent 只寫入自己負責的檔案
- 寫入前先讀取上游的產出，確認資料完整
- 寫入的內容應為**精簡摘要**，而非完整程式碼傾印

#### 2. 自我修正迴圈（Self-Correction Loop）

**迴圈規則**：
- 最大迴圈次數：3（防止無限迴圈）
- 每次迴圈，Tester 的 Error Log 會附加在 Implementer 的任務描述中
- 若 3 次仍未通過，升級回 Router，由 Router 決定是否：
  - 重新規劃（回到 Planner）
  - 請用戶介入
  - 降級為部分交付

#### 3. 階段閘門（Stage Gate）

每個階段之間可設置品質閘門：

```markdown
## 閘門條件

Research → Planner 的閘門：
- 分析報告是否包含至少 3 個可行方案？
- 是否標明了每個方案的 trade-off？

Planner → Implementer 的閘門：
- 計畫是否拆解為 ≤ 5 個可獨立實作的步驟？
- 是否標明了每步的預期輸出與驗收條件？
```

### 適用時機

- 任務需要「生成 → 驗證 → 修正」的迭代流程
- 有明確的品質驗收標準（可自動化測試）
- 子代理之間有嚴格的資料依賴

---

## Pattern C: Fan-out / Fan-in Pattern

### 概念

Router 將多個**無依賴**的子任務同時分發給不同 Sub-Agent，
所有子代理平行處理後，結果彙整回 Router。

```
                        ┌── [Sub-Agent A] ── 結果 A ──┐
[Router Agent] ── 分發 ─┼── [Sub-Agent B] ── 結果 B ──┼── [彙整] → 最終產出
                        └── [Sub-Agent C] ── 結果 C ──┘
```

### Copilot 原生實現

在同一個回合中，平行呼叫多個 `runSubagent`：

```markdown
## Fan-out 策略

將以下 3 個獨立子任務同時委派：

1. runSubagent → security-reviewer：審查 auth 模組的安全性
2. runSubagent → test-writer：為 auth 模組撰寫整合測試
3. runSubagent → doc-generator：更新 auth 模組的 API 文件
```

### 彙整策略（Fan-in）

Router 收到所有子代理的結果後，進行彙整：

- **合併型**：將所有結果直接串接（適用於各自獨立的審查報告）
- **衝突解決型**：若結果互相矛盾，由 Router 判斷優先級或請用戶裁決
- **摘要型**：Router 對所有結果進行摘要，產出精簡的綜合報告

### 適用時機

- 多個子任務完全獨立，無資料依賴
- 希望透過平行處理加速整體完成時間
- 每個子任務的結果可獨立評估品質

---

## 混合模式

實際專案中，常需組合多種模式。例如：

```
[Router Agent]
    ↓
[Fan-out] ── 平行收集資訊
    ├── [Schema Analyzer] ── DB 結構分析
    └── [Code Analyzer] ── 現有程式碼分析
    ↓
[Fan-in] ── 彙整分析結果
    ↓
[Sequential Chain] ── 基於分析結果執行
    ├── [Planner] ── 制定遷移計畫
    ├── [Implementer] ── 實作遷移腳本
    └── [Tester] ── 驗證遷移正確性（Closed-Loop 回饋修正）
```

**設計原則**：
- 先畫出完整的子任務依賴圖
- 無依賴的節點用 Fan-out 平行處理
- 有依賴的節點串成 Sequential Chain
- 需要品質驗證的環節加上 Closed-Loop
