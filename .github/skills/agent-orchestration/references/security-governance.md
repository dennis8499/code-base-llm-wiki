# 安全防護與治理機制

## 目錄

1. [模型分級路由](#模型分級路由)
2. [最小權限原則](#最小權限原則)
3. [副作用攔截機制](#副作用攔截機制)
4. [反幻覺策略](#反幻覺策略)
5. [稽核與可追蹤性](#稽核與可追蹤性)

---

## 模型分級路由

不要讓單一模型處理所有事情。根據任務的認知複雜度，選擇對應能力等級的模型：

### 分級路由表

| 任務類型 | 認知複雜度 | 建議模型等級 | 範例 |
|---------|-----------|------------|------|
| 意圖分類 / Schema 驗證 | 低 | 低延遲策略 | 「這個請求是資料查詢還是安全審計？」 |
| 格式轉換 / 模板填充 | 低-中 | 輕量策略 | 將 JSON Contract 轉為 TypeScript Interface |
| 程式碼審查 / 技術分析 | 中 | 平衡型推理策略 | 分析 SQL 查詢效能、找出 N+1 問題 |
| 架構設計 / 業務邏輯推理 | 高 | 強推理策略 | 設計零停機遷移策略、規劃微服務拆分 |
| 安全漏洞深層分析 | 高 | 強推理策略 | OWASP 綜合風險評估、權限模型設計 |

### 實作方式

在 Router Agent 的路由邏輯中體現分級：

```markdown
## 路由決策

1. 意圖分類：由 Router 自身完成（Router 使用輕量模型）
2. 簡單格式任務 → 委派給配置為輕量模型的 Sub-Agent
3. 複雜推理任務 → 委派給配置為強推理模型的 Sub-Agent
```

> 注意：在 VS Code Copilot Chat 中，模型選擇通常由用戶或宿主環境決定。
> 因此這裡的分級策略，應優先被視為「路由與推理深度策略」；
> 除非宿主明確支援，否則不要假設每個 `.agent.md` 都能穩定綁定不同模型。

---

## 最小權限原則

### 核心規則

**子代理擁有的環境與 API 權限，絕不可高於主代理。**

### 工具權限矩陣

| Agent 類型 | 讀取工具 | 搜尋工具 | 編輯工具 | 執行工具 | MCP 工具 |
|-----------|---------|---------|---------|---------|---------|
| **Router Agent** | ✅ | ✅ | ✅ | ✅ | ✅（受限） |
| **分析型 Sub-Agent**（如安全審計） | ✅ | ✅ | ❌ | ❌ | ❌ |
| **生成型 Sub-Agent**（如程式碼撰寫） | ✅ | ✅ | ✅ | ❌ | ❌ |
| **執行型 Sub-Agent**（如測試執行） | ✅ | ✅ | ❌ | ✅（受限） | ❌ |
| **整合型 Sub-Agent**（如 DB 操作） | ✅ | ✅ | ❌ | ❌ | ✅（唯讀） |

### 工具白名單設計

在每個 Agent 的 `.agent.md` frontmatter 中明列允許的工具：

```yaml
tools:
  # 讀取類 — 幾乎所有 Agent 都可以開放
  - read_file
  - grep_search
  - file_search
  - semantic_search
  - get_errors

  # 搜尋類 — 分析型 Agent 需要
  - list_dir

  # 編輯類 — 僅生成型 Agent 開放
  # - apply_patch
  # - create_file

  # 執行類 — 僅測試執行 Agent 開放，且需加護欄
  # - run_in_terminal

  # MCP 類 — 按需開放，務必指定具體工具名稱
  # - mcp_github_create_issue    ← 具體名稱，不要寫 "mcp_github_*"
```

### 逐步提權模式

對於需要多種權限等級的複雜工作流：

1. **初始階段**：所有 Sub-Agent 以唯讀權限啟動
2. **分析完成後**：Router 根據分析結果，為特定 Sub-Agent 「升級」工具權限
3. **執行前確認**：涉及寫入或執行的操作，由 Router 透過 `askQuestions` 請用戶授權

---

## 副作用攔截機制

### 須攔截的高風險操作

以下操作**嚴禁自動執行**，必須經過人工確認：

| 操作類型 | 範例 | 風險等級 |
|---------|------|---------|
| 資料庫結構變更 | `DROP TABLE`、`ALTER COLUMN`、`TRUNCATE` | 🔴 Critical |
| 不可逆刪除 | `rm -rf`、刪除分支、刪除檔案 | 🔴 Critical |
| CI/CD 修改 | 修改 pipeline 配置、更新 secrets | 🟠 High |
| Git 強制操作 | `git push --force`、`git reset --hard` | 🟠 High |
| 外部系統寫入 | 發送 Slack 訊息、建立 Jira ticket | 🟡 Medium |

### `confirmation_required` 機制

Sub-Agent 遇到高風險操作時，不執行操作，而是回傳特殊狀態：

```json
{
  "traceId": "...",
  "sender": "DataAccessSubAgent",
  "target": "RouterAgent",
  "status": "confirmation_required",
  "payload": {
    "action": "execute_migration",
    "pendingOperation": {
      "description": "即將對 Users 表執行 DROP COLUMN email_verified",
      "impact": "將永久刪除 50,000 筆記錄的 email_verified 欄位",
      "reversibility": "不可逆",
      "suggestedAlternative": "建議先新增 is_verified 欄位，資料遷移完成後再刪除舊欄位"
    }
  }
}
```

Router 收到此狀態後，透過 Copilot Chat 介面向用戶展示確認資訊，
待用戶明確授權後方可繼續執行。若宿主沒有自訂確認 UI，則至少以清楚的文字說明影響範圍並要求用戶確認。

### Hooks 作為確定性護欄

若倉庫支援 Hooks，應優先將下列規則做成 `preToolUse` / `postToolUse`：

- 刪除檔案或分支前的確認
- 修改部署、CI/CD、secrets 相關檔案時的攔截
- 進入高風險 `run_in_terminal` 或外部寫入前的政策檢查

原因很簡單：文字規則是在勸代理自律；Hooks 則是在工具邊界上建立真正的護欄。

### 在 `.agent.md` 中的實作

```markdown
## 副作用防護

你在執行任何操作前，必須先檢查：

1. **這個操作是否可逆？** 若不可逆 → 暫停，回傳 confirmation_required
2. **這個操作是否會影響共享資源？** 若會 → 暫停，說明影響範圍
3. **這個操作是否超出你的工具白名單？** 若超出 → 回報 Router，請求權限升級

絕對不要用「為了效率」作為跳過確認的理由。
```

---

## 反幻覺策略

### 上下文精簡（Context Trimming）

幻覺的最大來源是冗長且不相關的上下文。在多代理系統中：

**Router Agent 的責任**：
- 在分發任務前，對對話歷史進行摘要
- 只傳遞與當前子任務**直接相關**的資訊
- 移除閒聊、修正過的錯誤嘗試、已取消的請求

**Sub-Agent 的 System Prompt 規則**：
- 只包含角色定義 + 當前任務 + 輸入資料 + 輸出格式
- 不包含其他 Sub-Agent 的資訊（除非有直接依賴）
- 不包含完整對話歷史

### Schema 強制驗證

- Sub-Agent 的輸出必須通過 JSON Schema 驗證
- 若輸出不符合 Schema，直接拒絕並要求重新生成
- 驗證錯誤訊息應告知「缺了什麼」而非「哪裡錯了」

### C-I-C Prompt 注入

在每次委派時，自動嵌入 C-I-C 框架
（詳見 `communication-protocol.md` 的 C-I-C 區段）。
Constraints 區段中應包含反幻覺邊界：

```markdown
## Constraints
- 只使用我提供的資料進行分析，不要從訓練資料中推測
- 若資訊不足以完成任務，回傳 status: "confirmation_required" 而非猜測
- 輸出中的每個技術建議必須附帶具體的程式碼或設定範例
```

---

## 稽核與可追蹤性

### traceId 追蹤鏈

每個 Agent 間的訊息都攜帶 `traceId`，形成完整的追蹤鏈：

```
用戶請求 → Router (traceId: A)
  → Sub-Agent 1 (traceId: B, parentTraceId: A)
    → Sub-Sub-Agent (traceId: C, parentTraceId: B)
  → Sub-Agent 2 (traceId: D, parentTraceId: A)
```

### 稽核日誌建議

對於有合規要求的組織，建議在 Router Agent 中記錄：

1. 每次路由決策（選了哪個 Sub-Agent、為什麼）
2. 每次 `confirmation_required` 事件（誰要求、用戶是否批准）
3. 每次重試（失敗原因、重試次數）
4. 最終產出摘要

日誌寫入 `/memories/session/audit-log.md`，由 Router 負責維護。
