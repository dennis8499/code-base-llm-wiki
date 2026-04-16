# Instructions 設計指南

## 適用場景

| 需求                                     | 建議檔案                                 | 適用情境                                           |
| ---------------------------------------- | ---------------------------------------- | -------------------------------------------------- |
| 跨工具共用的倉庫規則                     | `AGENTS.md`                              | Claude / Gemini / Copilot 都要吃到相同背景規則     |
| GitHub Copilot 專用的 workspace 背景規則 | `.github/copilot-instructions.md`        | 專案主要使用 Copilot，且需要 IDE 深度整合          |
| 只套用到特定語言 / 子目錄 / 檔案類型     | `.github/instructions/*.instructions.md` | 例如 Python API、Terraform、前端元件各自有不同規範 |
| 個人偏好                                 | 使用者層級 instructions                  | 不影響其他倉庫成員的輸出風格                       |
| 組織共通安全 / 合規基線                  | Organization-level instructions          | 不能被 repo 規則稀釋的底線                         |

---

## 層次與疊加原則

實際合成順序以宿主平台為準，但在設計上應遵守以下原則：

```
組織層：安全與合規底線（不可降低）
  ↓
倉庫層：專案架構、團隊工作流程、共通命名規範
  ↓
檔案層：特定語言 / 資料夾 / glob 的精準規則
  ↓
個人層：個人輸出風格與偏好
```

**關鍵原則**：優先採用「加法補充」而非互相覆蓋。倉庫與個人規則可以更具體，但不應削弱組織安全基線。

---

## 規則清單

1. **三維覆蓋**：高品質 Instructions 應同時說明技術背景（WHAT）、專案意圖（WHY）、工作流程（HOW）。
2. **長度控制**：單份 workspace instructions 盡量控制在 300 行內；`AGENTS.md` 理想上 < 60 行。
3. **檔案規則要窄**：`*.instructions.md` 的 `applyTo` 應盡量精準，避免 `**` 造成不必要的上下文污染。
4. **不貼大段程式碼**：Instructions 應描述方向與引用位置，而不是貼滿實作範例。
5. **避免重複**：已寫在 `.github/copilot-instructions.md` 的共通規則，不要再完整複製到 `AGENTS.md`。
6. **規則可驗證**：每條規則都應能被觀察或驗證，避免「寫得漂亮一點」這類模糊要求。
7. **把人格留給 Agent**：像「請扮演資深工程師」這種角色設定應放 `.agent.md`，不是 instructions。

---

## 撰寫指南

### 如何選擇合適的 Instructions 載體

```text
需要跨工具共享       → AGENTS.md
只給 Copilot 用       → .github/copilot-instructions.md
只影響某些檔案       → .github/instructions/*.instructions.md
只屬於個人偏好       → 使用者層級 instructions
```

若同時存在 workspace instructions 與 file instructions：
- workspace instructions 放「全專案都成立」的規則
- file instructions 放「只在特定 glob 成立」的規則

### File Instructions 的設計重點

檔案層級 instructions 最適合處理語言、子目錄、框架差異。建議使用 `applyTo` 做明確匹配；若宿主支援，也可搭配 `description` 做語意發現。

```yaml
---
applyTo: "src/api/**/*.ts"
description: "Applies when editing TypeScript API handlers under src/api."
---
```

- `applyTo`：用於**確定性**套用，適合明確的 glob 規則
- `description`：用於**補充發現語境**，適合讓模型知道這份檔案大概解決什麼問題
- 若兩者同時存在，內容要一致，不要一個寫 API handler、一個其實限制在 migrations

### AGENTS.md vs `.github/copilot-instructions.md`

```text
使用 AGENTS.md 當：
  ✓ 團隊同時使用多種 AI 工具
  ✓ 希望規則隨 repo clone 一起被看見
  ✓ 想以開放格式維護同一份背景說明

使用 .github/copilot-instructions.md 當：
  ✓ 專案主要使用 GitHub Copilot
  ✓ 需要 Copilot 專用的背景行為約束
  ✓ 需要和其他 Copilot customization 搭配（prompt/agent/hook/skill）
```

### 常見陷阱

- ❌ 在 instructions 裡寫角色扮演敘事 → 應改放 `.agent.md`
- ❌ 在 file instructions 用 `applyTo: "**"` → 等於把所有互動都變成重負載
- ❌ 把整個 coding standard 貼進單一檔案 → 應拆成共通規則 + 檔案特定規則
- ❌ 用 instructions 複寫組織安全底線 → 應只做補充與細化

### 企業級架構與護欄防護

為減少 AI 產出「能跑但難以維護」的程式碼，應在 Instructions 內明確規範護欄：
- 必須指明架構設計模式（如 Clean Architecture、SOLID 原則）與邊界約束。
- 強制遵循 CI/CD 護欄，要求所有產出代碼必須符合專案現有 Linter（如 Prettier, ESLint, Ruff 等）與嚴格型別檢查。
- 要求在網路邊界、中介層執行 PII 脫敏與輸入驗證，落實資安防護。

---

## 模板

### 模板 A：`.github/copilot-instructions.md`（Copilot 專用倉庫指令）

```markdown
# Copilot Instructions — [專案名稱]

## 技術背景 (WHAT)
- 語言/框架：[例如：Python 3.12 + FastAPI 0.115]
- 架構：[例如：微服務；每個服務獨立部署]
- 主要依賴：[例如：PostgreSQL 16、Redis 7、Pydantic v2]
- 測試框架：[例如：pytest + pytest-asyncio]

## 專案意圖 (WHY)
- [核心業務目標，1-2 句話]
- 設計優先順序：可讀性 > 效能 > 功能完整性
- 禁止：[例如：Service 層直接操作 DB]

## 工作流程 (HOW)
- 命名規範：[例如：類別 PascalCase，函式 snake_case]
- 錯誤處理：[例如：所有外部 API 呼叫一律記錄結構化錯誤]
- 日誌格式：參照 `src/core/logger.py`
- PR 規範：[例如：每個 PR 需附帶測試]
```

### 模板 B：`.github/instructions/python-api.instructions.md`（檔案層級指令）

```markdown
---
applyTo: "src/api/**/*.py"
description: "Applies when editing Python API handlers in src/api."
---

# Python API File Instructions

## 這份規則只適用於 `src/api/**/*.py`

- Endpoint 一律回傳明確的 response schema
- 路由層不直接操作 ORM session；透過 service 或 use case 層
- 驗證錯誤需轉成一致的 API error payload
- 若新增 endpoint，請同步更新對應的 OpenAPI / 測試
```

### 模板 C：`AGENTS.md`（跨工具相容指令）

```markdown
# AGENTS.md — [專案名稱]

## What（技術背景）
[技術棧簡述，2-3 句話]

## Why（專案意圖）
[業務目標與設計哲學，2-3 句話]

## How（工作流程規範）

### 程式碼規範
- [命名規範]
- [格式與縮排]
- [禁止行為]

### 安全要求
- 不得將敏感資料（API Key、密碼、Token）寫入程式碼
- 所有使用者輸入必須通過驗證層

### 測試要求
- 新功能需附帶單元測試
- 覆蓋率目標：[例如：75%]

## 參考文件
- 架構圖：`docs/architecture.md`
- API 規格：`docs/api-spec.yaml`
- 貢獻指南：`CONTRIBUTING.md`
```

---

## 使用範例

### 範例 1：Python FastAPI 微服務專案

```markdown
# Copilot Instructions — OrderService

## 技術背景 (WHAT)
- Python 3.12 + FastAPI 0.115 + Pydantic v2
- 微服務架構，透過 RabbitMQ 發送/接收事件
- 資料層：PostgreSQL 16（SQLAlchemy 2.0 async）、Redis 7
- 測試：pytest + pytest-asyncio + httpx

## 專案意圖 (WHY)
- 訂單服務負責訂單生命週期管理，不涉及金流（金流由 PaymentService 處理）
- 設計原則：Clean Architecture（Domain → Application → Infrastructure）
- 嚴禁 Service 層直接使用 SQLAlchemy Session；一律透過 OrderRepository

## 工作流程 (HOW)
- 命名：類別 PascalCase，函式/變數 snake_case，常數 UPPER_SNAKE_CASE
- Repository 方法命名：`find_by_*`、`save`、`delete_by_id`
- 所有 API endpoint 需類型標注，回傳明確 Response Schema
- 日誌格式參照 `src/core/logging.py`
```

### 範例 2：前端元件專用 file instructions

```markdown
---
applyTo: "src/components/**/*.tsx"
description: "Applies when editing React UI components under src/components."
---

# React Component File Instructions

- 元件 Props 需使用 TypeScript interface，並與檔名同名
- 預設使用具名匯出，除非現有目錄慣例明確要求 default export
- 若元件有互動行為，新增或更新對應測試與 Story
- 樣式優先沿用現有 design system token，不要硬編碼色碼
```
