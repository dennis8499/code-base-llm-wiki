---
name: agent-orchestration
description: >
  Designs multi-agent orchestration architectures for GitHub Copilot,
  including Router Agent dispatch, Sub-Agent delegation, closed-loop
  self-testing pipelines, and standardized JSON communication contracts.
  Use this skill whenever a user wants to design a multi-agent system,
  orchestrate multiple agents, create a router/dispatcher pattern,
  define agent-to-agent communication protocols, or plan sub-agent
  delegation strategies. Invoke even when the user mentions
  "多代理" "編排" "協作" "子代理" "runSubagent" or asks how agents
  should work together, pass data, or share state.
---

# Agent Orchestration — 多代理人編排架構設計

協助架構師與資深工程師，在 GitHub Copilot 生態系中設計**可落地的多代理人編排架構**。
涵蓋 Router Agent 動態分發、閉環鏈式自我驗證管線、Agent 間標準化通訊契約、
安全防護與容錯機制。

---

## 適用範圍

**適用**：
- 設計多代理編排架構（Router + N 個 Sub-Agent）
- 規劃 Agent 動態路由與意圖分類邏輯
- 建立閉環鏈式管線（Research → Plan → Implement → Self-Test）
- 定義 Agent 間 JSON 通訊契約（Contract-First Design）
- 整合 MCP 伺服器橋接外部資料庫與企業系統
- 設計模型分級路由策略（輕量模型 vs 重量模型）
- 規劃容錯、重試與降級機制

**不適用**：
- 建立單一 Agent 的 `.agent.md` → 應使用 `copilot-architect`
- SKILL.md 格式與內容設計 → 應使用 `skill-content-guide`
- MCP Server 實作細節 → 參閱 MCP 官方文件
- LangGraph / AutoGen / Semantic Kernel 等外部框架 → 本 Skill 專注 Copilot 原生能力
- 單一步驟、無需委派的任務 → 優先考慮 `Instructions`、`Prompts`、`Hooks` 或單一 `.agent.md`
- 流式對話 UI、自訂核准按鈕、長連線狀態管理 → 此屬 Extension / MCP / 應用層責任，無法僅靠 Markdown customizations 達成

### 先做元件選型，再做多代理

在設計 Router + Sub-Agent 前，先確認是否其實應使用更簡單的 Copilot 元件：

- **`copilot-instructions.md` / `AGENTS.md`**：全域背景規則與團隊慣例
- **`*.prompt.md`**：顯式觸發的單次工作流
- **Hooks**：確定性副作用攔截與合規保護
- **單一 `.agent.md`**：只需要 context isolation，不需要多代理網路

只有當任務同時需要**路由、委派、彙整、狀態傳遞**時，才應升級為多代理編排。

---

## 輸入收集

在開始設計前，確認以下資訊。若用戶未明確提供，主動詢問（使用 `askQuestions`）：

### Context（上下文）

- **任務性質**：用戶要解決什麼問題？涉及哪些業務領域？
- **技術棧**：語言版本、框架、資料庫、已接入的 MCP 伺服器
- **現有配置**：是否已有 `.agent.md`、`copilot-instructions.md`、`AGENTS.md`
- **宿主能力**：是否支援 `runSubagent`、memory、互動提問工具、Hooks；工具名稱是否與目前平台一致

### Intent（意圖）

- **複雜度等級**：
  - **簡單委派**：1 個 Router + 2-3 個獨立 Sub-Agent，無前後依賴
  - **鏈式管線**：Sub-Agent 之間有順序依賴，上游輸出是下游輸入
  - **自我驗證迴圈**：需要 Generate → Test → Fix 的閉環機制
- **子代理職責**：每個子代理負責什麼領域？（例如：資料存取層、安全審計、測試撰寫）
- **協作模式**：子代理之間需要共享狀態嗎？是否有平行執行需求？

### Constraints（約束）

- **安全需求**：是否有破壞性操作需要人工確認？（Drop Table、修改 CI/CD 等）
- **效能需求**：是否有延遲敏感的路由步驟？需要 SSE 串流回應？
- **合規要求**：組織對 AI 操作是否有治理政策或審計要求？

> **嚴禁猜測**：若用戶意圖模糊或參數不足，強制觸發 `askQuestions` 向用戶釐清。
> 不完整的需求直接進入設計，是多代理系統最常見的失敗根因。

---

## 工作流程

### Step 1：意圖拆解 — 將需求分解為可委派的子任務

分析用戶的需求，拆解為互相獨立（或有明確依賴鏈）的子任務。每個子任務應該：
- 有明確的輸入與輸出
- 可交由一個專業角色獨立完成
- 邊界清晰，不與其他子任務交叉

產出物：子任務清單 + 依賴關係圖（文字描述即可）。

### Step 2：模式選型 — 選擇編排架構

根據子任務的依賴關係，選擇最適合的編排模式：

| 模式 | 適用場景 | 特徵 |
|------|---------|------|
| **Dynamic Router** | 子任務間無依賴，可獨立分發 | 1 Router → N 個獨立 Sub-Agent |
| **Closed-Loop Chain** | 有嚴格前後依賴，需自我驗證 | A → B → C → 驗證 → 回饋修正 |
| **Fan-out / Fan-in** | 多個子任務可平行，最終彙整 | Router 分發 → 平行執行 → 彙整 |

> 載入 `references/patterns-guide.md` 取得每個模式的完整設計指引與 Copilot 原生實現方式。

### Step 3：Agent 角色設計 — 定義每個代理的職責與工具

為 Router Agent 和每個 Sub-Agent 分別定義：

1. **角色敘述**（Persona）：用「流動意識」式描述代理的專業背景與思維方式
2. **工具白名單**（Tools）：遵循最小權限原則，只開放任務所需的工具
3. **輸入/輸出 Schema**：明確定義代理接收與產出的資料結構
4. **觸發條件**：什麼情況下 Router 應將任務分發給此 Sub-Agent
5. **元件分工**：哪些規則放 `Instructions`，哪些做成 `Prompt`，哪些改由 `Hooks` 做確定性攔截

> 使用 `assets/router-agent-template.md` 和 `assets/sub-agent-template.md` 作為起點。
> 模板已內建 Agent 設計最佳實踐，填入具體領域知識即可。
> Router / Sub-Agent 負責推理與委派；Hooks 負責確定性攔截；Instructions 負責 always-on 規則；Prompts 負責顯式可重用工作流。

### Step 4：通訊契約與狀態傳遞設計

所有 Agent 之間的資料傳遞應使用結構化 JSON（Contract-First Design），確保：
- **可追蹤性**：每個訊息都可追蹤（`traceId`），發送者與接收者明確（`sender` / `target`）
- **重試上下文**：重試次數與狀態被保留（`context.retryCount`）
- **精準上下文傳遞**：子代理的 Prompt 應只包含該子任務所需的已摘要上下文與明確輸出格式。嚴禁將整段歷史對話原封不動丟給每個子代理，避免 Context Window 爆炸與引發幻覺。
- **共享黑板（Shared Blackboard）**：若需跨代理狀態同步，評估宿主是否支援 Session-scoped Memory；若無，則規劃使用 Workspace 暫存檔（Scratch files）儲存摘要與進度狀態。

> 載入 `references/communication-protocol.md` 取得完整 JSON Protocol 規格與 Contract-First 設計原則。
> 使用 `assets/json-contract-template.json` 作為 Payload 結構起點。

### Step 5：安全防護層設計

針對多代理系統的安全風險，設計以下防護機制：

1. **模型分級路由**：快速路由決策用輕量模型；深層業務邏輯用強推理模型
2. **最小權限**：子代理的工具權限絕不高於主代理
3. **副作用攔截**：破壞性操作必須回傳 `confirmation_required`，或由 Hook 在工具層直接攔截，等待人工授權
4. **反幻覺策略**：子代理的 System Prompt 必須極度聚焦，由主代理負責歷史摘要

> 載入 `references/security-governance.md` 取得模型分級路由表、攔截機制設計與反幻覺策略。
> `confirmation_required` 是邏輯狀態碼，不代表原生 Markdown customizations 一定能渲染自訂按鈕；在 VS Code / Copilot Chat 中，至少要停下來向用戶確認。

### Step 6：容錯、降級與中斷機制

為每個 Agent 交互點設計失敗處理：

1. **自動重試**：對暫時性錯誤採用指數退避（1s → 2s → 4s），最大重試 3 次
2. **失敗升級**：重試耗盡後，將異常拋回主代理
3. **具指導意義的降級回饋**：回報錯誤時，必須提供開發者「下一步能做什麼」（如替代路徑、需補充的資訊），嚴禁只丟出一句「失敗」。主代理將系統錯誤轉譯為開發者易讀格式，並主動詢問是否手動介入。
4. **中斷與中止**：規劃明確的中止點，避免失控的自我修正迴圈。即使宿主不支援真正的取消執行，也要設計機制停止再委派、保存已完成結果，並向用戶回報目前進度。

> 載入 `references/error-handling.md` 取得完整的重試、降級與取消策略。

### Step 7：組裝與驗證

將所有設計組裝為可落地的檔案：

1. **產出 Router Agent `.agent.md`**：從模板填入實際路由邏輯與意圖分類規則
2. **產出 N 個 Sub-Agent `.agent.md`**：每個子代理一份，含完整職責與工具限制
3. **產出 JSON Contract 定義**：所有 Agent 間的通訊格式
4. **執行 Contract 驗證**：使用 `scripts/validate_contract.py` 驗證 JSON 結構一致性
5. **走查完整流程**：從用戶請求開始，模擬 Router 分發 → Sub-Agent 執行 → 結果彙整的全路徑

```bash
# 驗證 JSON Contract 結構
python scripts/validate_contract.py <contract-file.json>
```

---

## 輸出格式

每次完整的編排設計應包含以下產出物：

### 1. 編排架構總覽

```
[用戶請求]
    ↓
[Router Agent] ── 意圖分類 ──┬── [Sub-Agent A] ── 產出 A
                              ├── [Sub-Agent B] ── 產出 B
                              └── [Sub-Agent C] ── 產出 C
                                       ↓
                              [結果彙整 / 驗證]
```

### 2. Router Agent `.agent.md` 完整檔案

依照 `assets/router-agent-template.md` 模板，填入：
- 意圖分類規則
- 子代理分發邏輯
- `askQuestions` 強制觸發條件

### 3. 每個 Sub-Agent `.agent.md` 完整檔案

依照 `assets/sub-agent-template.md` 模板，填入：
- 領域專業角色描述
- 工具白名單
- 輸入/輸出 Schema
- 交接摘要格式

### 4. JSON Communication Contract

Agent 間通訊的標準 JSON Payload 定義，包含 schema 說明。

### 5. 安全防護清單

列出所有需要人工確認的操作、工具權限矩陣、模型分級建議。

---

## 領域知識

### 意圖分類器的模型選用

Router Agent 中的意圖分類不需要強推理能力，應選用推論速度快、延遲低的模型
（或等效的低延遲策略）。將分類器視為「快速攔截閘門」：她的職責是理解用戶說了什麼，
然後把球傳給正確的專家。複雜的業務邏輯判斷則交給更高推理深度的 Sub-Agent 處理。

在 VS Code 原生 customizations 中，實際模型通常由宿主或使用者選擇；因此請把分級路由設計成
「任務分流策略」，不要假設每個 Agent 都能穩定綁定不同模型。

### 子代理 Prompt 聚焦原則

冗長的歷史對話是多代理系統幻覺的最大來源。主代理在委派任務前，應對對話歷史進行
摘要（Summarization），僅將最核心的 Token 傳遞給子代理。每個子代理的 System Prompt
應只包含：

1. 角色定義（你是誰、擅長什麼）
2. 當前任務的精確描述
3. 輸入資料（已摘要的上下文）
4. 期望的輸出格式

### 跨代理狀態共享

在 Copilot 原生環境中，若宿主支援 memory，使用 `/memories/session/` 作為「Shared Blackboard」：

- Router Agent 將全域計畫寫入 session memory
- 每個 Sub-Agent 完成後將產出摘要寫回
- 下游 Sub-Agent 讀取上游的產出，而非完整對話歷史

這種模式讓每個代理保持輕量的上下文，同時確保資訊不會在傳遞中遺失。

若宿主不支援 memory，改用 workspace scratch files 或專案中的暫存文件來保存摘要狀態。

### 嚴禁猜測原則

多代理系統中最危險的行為是「主代理替用戶做決定」。當以下情況發生時，
Router Agent **必須**觸發 `askQuestions` 向用戶釐清：

- 用戶請求可同時符合 2 個以上子代理的職責
- 關鍵參數缺失（如：目標資料庫、部署環境、效能要求）
- 用戶使用了模糊詞彙（「優化一下」「改改看」「搞定它」）

寧可多問一個問題，也不要讓 3 個子代理基於錯誤假設各跑一遍。

---

## 快速路由

| 需要了解 | 載入 |
|---------|------|
| 編排模式的完整設計指引 | `references/patterns-guide.md` |
| JSON 通訊契約規格 | `references/communication-protocol.md` |
| 安全防護與模型分級 | `references/security-governance.md` |
| 容錯、重試與降級策略 | `references/error-handling.md` |
| 需要確定性攔截高風險操作 | 優先交給 Hooks；本 Skill 僅負責協作設計 |
| Router Agent 即用模板 | `assets/router-agent-template.md` |
| Sub-Agent 即用模板 | `assets/sub-agent-template.md` |
| JSON Payload 結構模板 | `assets/json-contract-template.json` |
| Contract 驗證腳本 | 執行 `scripts/validate_contract.py` |
