# 標準化通訊協定與 Contract-First 設計

## 目錄

1. [Contract-First 設計原則](#contract-first-設計原則)
2. [JSON Payload 標準格式](#json-payload-標準格式)
3. [欄位規格說明](#欄位規格說明)
4. [C-I-C Prompt 注入框架](#c-i-c-prompt-注入框架)
5. [與強型別系統的對應](#與強型別系統的對應)
6. [Contract 驗證流程](#contract-驗證流程)

---

## Contract-First 設計原則

在多代理系統中，Agent 之間的通訊必須像 API 一樣有明確的「契約」（Contract）。
這意味著：

1. **先定義格式，再寫邏輯**：在設計任何 Agent 的行為前，先確定它的輸入/輸出 JSON 結構
2. **Schema 是唯一真相**：所有 Agent 都依照同一份 Schema 解讀資料，不允許隱性假設
3. **版本化契約**：當 Schema 需要變更時，透過版本號管理向後相容性
4. **驗證在邊界**：每個 Agent 在接收輸入時驗證 Schema，在產出時確保符合 Schema

這種方式的核心好處：Router Agent 和 Sub-Agent 完全解耦。只要雙方遵守契約，
內部實作可以獨立演化，不會因為一方的改動導致另一方崩潰。

在 GitHub Copilot 原生 Markdown customizations 中，這份契約首先是**邏輯協定**。
也就是說：狀態碼、欄位結構、重試上下文可以被明確設計，但最終如何呈現人工確認 UI、
如何中止執行中工作，仍取決於宿主環境是否提供對應能力。

---

## JSON Envelope 標準格式

所有 Agent 之間的訊息都應遵循同一種 Envelope，並依用途分為「請求」與「回應」。

### 請求訊息

```json
{
  "traceId": "a1b2c3d4-e5f6-4890-ab34-56789abcdef0",
  "sender": "RouterAgent",
  "target": "DataAccessSubAgent",
  "timestamp": "2026-04-16T10:30:00Z",
  "payload": {
    "action": "generate_dapper_query",
    "parameters": {
      "targetTable": "Users",
      "performanceRequirement": "high_throughput",
      "constraints": ["avoid_n_plus_one", "use_parameterized_query"]
    }
  },
  "context": {
    "retryCount": 0,
    "maxRetries": 3,
    "parentTraceId": null,
    "sessionMemoryPath": "/memories/session/orchestration-plan.md"
  }
}
```

### 成功完成的回應訊息

```json
{
  "traceId": "b2c3d4e5-f6a7-4901-8b45-6789abcdef01",
  "sender": "DataAccessSubAgent",
  "target": "RouterAgent",
  "timestamp": "2026-04-16T10:30:15Z",
  "status": "completed",
  "payload": {
    "action": "generate_dapper_query",
    "result": {
      "generatedCode": "...",
      "warnings": [],
      "performanceNotes": "使用 Batch Query 避免 N+1"
    }
  },
  "context": {
    "retryCount": 0,
    "maxRetries": 3,
    "durationMs": 15000,
    "tokensUsed": 4500
  }
}
```

### 需要人工確認的回應訊息

```json
{
  "traceId": "c3d4e5f6-a7b8-4a12-9c56-789abcdef012",
  "sender": "DataAccessSubAgent",
  "target": "RouterAgent",
  "timestamp": "2026-04-16T10:30:15Z",
  "status": "confirmation_required",
  "payload": {
    "action": "execute_migration",
    "pendingOperation": {
      "description": "即將對 Users 表執行 DROP COLUMN email_verified",
      "impact": "將永久移除舊欄位",
      "reversibility": "不可逆",
      "suggestedAlternative": "建議先以 deprecated 標記舊欄位，再安排後續版本移除"
    }
  },
  "context": {
    "retryCount": 0,
    "maxRetries": 3
  }
}
```

---

## 欄位規格說明

### 頂層欄位

| 欄位 | 類型 | 必填 | 說明 |
|------|------|------|------|
| `traceId` | string (UUID v4) | 是 | 此次請求的唯一追蹤 ID，用於日誌關聯與除錯 |
| `sender` | string | 是 | 發送者的 Agent 識別名稱 |
| `target` | string | 是 | 目標 Agent 的識別名稱 |
| `timestamp` | string (ISO 8601) | 是 | 訊息發送時間 |
| `status` | string | 否 | 回應狀態；請求訊息通常不帶此欄位 |
| `payload` | object | 是 | 實際任務內容 |
| `context` | object | 是 | 編排上下文（重試、追蹤鏈） |

### payload 欄位

| 欄位 | 類型 | 必填 | 說明 |
|------|------|------|------|
| `action` | string | 是 | 要執行的動作名稱（使用 snake_case） |
| `parameters` | object | 請求時必填 | Router 傳給 Sub-Agent 的輸入參數 |
| `result` | object | `completed` / `failed` / `partial` 時必填 | 任務結果、警告、分析摘要、錯誤細節 |
| `pendingOperation` | object | `confirmation_required` 時必填 | 待授權操作的描述、影響範圍、可逆性與替代方案 |

### context 欄位

| 欄位 | 類型 | 必填 | 說明 |
|------|------|------|------|
| `retryCount` | integer | 是 | 當前重試次數（從 0 開始） |
| `maxRetries` | integer | 是 | 最大允許重試次數 |
| `parentTraceId` | string \| null | 否 | 若此請求是由另一個請求觸發，記錄父級 traceId |
| `sessionMemoryPath` | string \| null | 否 | 共享黑板的路徑，供子代理讀寫狀態 |
| `durationMs` | integer | 否 | 回應時可附帶執行耗時 |
| `tokensUsed` | integer | 否 | 回應時可附帶估計 Token 使用量 |

### status 欄位值

| 值 | 說明 |
|---|------|
| `completed` | 任務成功完成 |
| `failed` | 任務失敗，`payload.result` 中包含錯誤詳情 |
| `confirmation_required` | 子代理遇到需要人工確認的操作，暫停等待授權 |
| `partial` | 部分完成，可用但不完整 |

> `confirmation_required` 是邏輯狀態碼；在 VS Code / Copilot Chat 的原生 Markdown customizations 中，不應假設它一定會自動渲染成自訂按鈕。至少要做到：停止副作用步驟、清楚說明影響、向使用者請求確認。

---

## C-I-C Prompt 注入框架

在將任務分發給 Sub-Agent 前，Router Agent 應自動在子代理的任務描述中
注入 C-I-C（Context, Intent, Constraints）框架，確保子代理不會偏離目標。

### 結構

```markdown
## Context（上下文）
[專案背景、技術棧、相關檔案路徑]
目前正在處理的功能：[功能描述]
已知的技術限制：[列舉]

## Intent（意圖）
你的任務是：[精確的一句話描述]
期望產出：[明確的輸出格式]
成功標準：[怎樣算「做好了」]

## Constraints（約束）
- 不得 [禁止行為 1]
- 不得 [禁止行為 2]
- 輸出必須符合 [Schema 名稱] 的格式
- 若遇到不確定的情況，回傳 status: "confirmation_required" 而非自行決定
```

### 使用時機

- **每次** Router 透過 `runSubagent` 分發任務時，都應包含 C-I-C 區段
- 不是死板的模板填空——根據任務性質調整三個區段的詳細程度
- 對於簡單任務，C-I-C 可以很精簡（各一句話）
- 對於涉及破壞性操作的任務，Constraints 區段應詳細列舉防護條件
- 工具名稱（例如 `runSubagent`、互動提問工具）是宿主能力，不應硬編碼進 JSON Contract

---

## 與強型別系統的對應

在系統實作底層（如 .NET 8 後端），JSON Payload 應對應至強型別資料結構：

### C# / .NET 8 範例

```csharp
public record AgentMessage(
    Guid TraceId,
    string Sender,
    string Target,
    DateTime Timestamp,
    AgentPayload Payload,
    AgentContext Context
);

public record AgentPayload(
    string Action,
    Dictionary<string, object> Parameters
);

public record AgentContext(
    int RetryCount,
    int MaxRetries,
    Guid? ParentTraceId = null,
    string? SessionMemoryPath = null
);

public record AgentResponse(
    Guid TraceId,
    string Sender,
    string Target,
    DateTime Timestamp,
    string Status,  // "completed" | "failed" | "confirmation_required" | "partial"
    AgentPayload Payload,
    AgentResponseContext Context
);
```

### TypeScript 範例

```typescript
interface AgentMessage {
  traceId: string;
  sender: string;
  target: string;
  timestamp: string;
  payload: {
    action: string;
    parameters: Record<string, unknown>;
  };
  context: {
    retryCount: number;
    maxRetries: number;
    parentTraceId?: string | null;
    sessionMemoryPath?: string | null;
  };
}
```

這些型別定義確保反序列化時能快速捕獲格式錯誤，而非在運行時才發現欄位缺失。

---

## Contract 驗證流程

### 設計階段驗證

使用 `scripts/validate_contract.py` 驗證 JSON 檔案是否符合標準格式：

```bash
python scripts/validate_contract.py <contract-file.json>
```

### 運行時驗證原則

- 每個 Agent 在**接收輸入**時驗證 Schema（防禦性程式設計）
- 驗證腳本應同時接受「請求訊息」與「回應訊息」兩種 Envelope
- 驗證失敗時，回傳帶有操作指導的錯誤訊息：
  - ✗ 「JSON 格式錯誤」
  - ✓ 「缺少必要欄位 'payload.action'，期望值為 string 類型（如 'generate_dapper_query'）」
- 不要在中間環節重複驗證已確認正確的欄位——驗證在邊界進行即可
