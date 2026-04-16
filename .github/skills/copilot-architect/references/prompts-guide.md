# Prompt File 設計指南

## 適用場景

Prompt File（`.prompt.md`）是**顯式觸發**的可重用任務模板，適合以下情境：

| 情境       | 說明                                            |
| ---------- | ----------------------------------------------- |
| 重複性任務 | PR 摘要、Commit Message、文件整理、測試案例撰寫 |
| 元件腳手架 | 元件初始化、模組骨架生成、檔案群組建立          |
| 定向改寫   | 針對當前選取內容或檔案進行 edit / refactor      |
| 格式化輸出 | 需要固定輸出結構、檢核清單或審查格式            |

**與 Agent 的差異**：Prompt File 由使用者手動呼叫（通常透過 `/` 指令）；Agent 是持續性角色或工具受限的工作流。

---

## 動態變量語法

| 變量                    | 說明                             | 範例                       |
| ----------------------- | -------------------------------- | -------------------------- |
| `${selection}`          | 編輯器中當前選取的文字           | 選取一段程式碼後觸發       |
| `${file}`               | 當前開啟檔案的完整內容           | 針對整份檔案分析或重寫     |
| `${input:variableName}` | 觸發時彈出輸入框，讓使用者補參數 | `${input:componentName}`   |
| `#file:path/to/file`    | 靜態引用特定檔案                 | `#file:src/types/index.ts` |

---

## Frontmatter 規格

```yaml
---
name: prompt-name
description: >
  說明這個 Prompt 做什麼，以及什麼情境下要手動呼叫它。
mode: ask  # ask | edit | agent
inputs:
  - name: exampleInput
    description: "只有需要互動參數時才宣告"
# tools:    # 選填；僅在 mode=agent 且宿主支援時設定
#   - <host-specific-tool>
---
```

**命名建議**：將檔名、`name` 與 slash 指令顯示名稱保持一致，避免不同客戶端出現名稱對不起來的情況。

---

## 規則清單

1. **顯式觸發**：Prompt File 由使用者手動啟動，不要假設它會自動介入。
2. **單一任務原則**：每個 Prompt File 聚焦一個具體目標，不要做成萬用瑞士刀。
3. **模式要選對**：
   - `ask`：偏分析、寫作、整理
   - `edit`：偏直接改寫目前檔案或選取內容
   - `agent`：需要工具、跨檔案、多步驟流程
4. **上下文最小化**：只引用任務所需的檔案，避免用過大的工作區上下文把 Token 當煙火放。
5. **輸出規格明確**：如果輸出有固定格式，直接寫模板，不要只寫「請整理成清楚的格式」。
6. **輸入要有意義**：只有關鍵參數會因使用者而變時，才使用 `${input:...}`。
7. **`mode=agent` 要節制**：只有真的需要工具時才用，且工具清單應最小化並與宿主環境一致。

---

## 撰寫指南

### 模式選擇

```text
需要分析 / 整理 / 產生文字        → mode: ask
需要直接改寫當前內容              → mode: edit
需要搜尋、讀檔、建檔、跨檔案工作流 → mode: agent
```

### 建議結構

每個 Prompt File 的 body 建議分三區：

```text
[角色設定]   ← 選填：任務需要特定專業時才放
[任務描述]   ← 必填：說明做什麼、處理哪些輸入、產出什麼
[輸出規格]   ← 必填：格式、驗收條件、禁止事項
```

### 多場景結構優化與防幻覺機制

為了讓模型更容易理解與填寫，建議在 Prompts 中採用以下編排技巧：

- **虛擬程式碼編排（Pseudo-code Structure）**：將複雜邏輯拆解為 Agent 易於填充的骨架。
  ```text
  // STEP 1: 初始化配置
  // STEP 2: 資料驗證
  // STEP 3: 業務邏輯
  // STEP 4: 回應處理
  ```
- **Inline Comment 模式**：以「由大到小」的階層式註解撰寫導引，引導 Agent 補全。
- **Step-by-step 驗證**：要求 Agent 先提出步驟清單，待人工確認後再逐步產出程式碼，降低幻覺風險。
- **防禦性設計要求**：主動要求邊界檢查、Null 保護與輸入驗證，並指示失敗情境的處理方式。

### 變量注入時機

```text
自動帶入：
  ${file}       → 分析或重寫整份當前檔案
  ${selection}  → 只處理使用者選取的片段

互動輸入：
  ${input:...}  → 元件名稱、目標模組、版本號、環境名稱等關鍵參數
```

### 測試驅動與自動化驗證 (TDD/BDD)

若 Prompt 的目標是產出測試，建議在指引中明確要求：

- **BDD 語意轉譯**：將 Gherkin（Given-When-Then）轉為實作步驟以產生對應測試。
- **Test Double 精準生成**：依介面產生 Mock / Stub / Fake，指示隔離外部系統（DB、API）。
- **覆蓋率導向補強**：要求分析未覆蓋邊界與分支，並生成補強案例。

### Few-shot 範例放置策略

只在以下情況加入 few-shot 範例：
- 輸出格式非常特定（例如公司專屬 commit 規格）
- 任務涉及內部術語、縮寫、固定措辭
- 模型容易踩到相同邊界條件，需要示範正反例

2-3 個高信號範例通常就夠了；不用把 20 個 edge case 塞進去讓 Prompt 變成百科全書。

---

## 模板

### 模板 A：PR 摘要生成器（`mode: ask`）

```markdown
---
name: pr-summary
description: >
  根據選取的 diff 或變更描述，生成結構化的 Pull Request 摘要。
mode: ask
---

你是一位熟悉技術寫作的 Senior Engineer，負責撰寫清晰的 PR 描述。

## 任務

根據以下變更內容，產出 PR 摘要：

${selection}

## 輸出格式

### 變更摘要
[1-2 句話說明這個 PR 解決了什麼問題]

### 主要變更
- [變更項目 1，說明「做了什麼」以及「為什麼」]
- [變更項目 2]

### 影響範圍
- 涉及模組：[列出受影響模組 / 服務]
- 破壞性變更：[有 / 無，若有請說明]

### 測試說明
[說明如何驗證此 PR]
```

### 模板 B：選取內容重構器（`mode: edit`）

```markdown
---
name: refactor-selection
description: >
  Refactors the selected code into project-consistent style without changing behavior.
mode: edit
---

## 任務

重構以下選取內容，但不要改變對外行為：

${selection}

## 要求

- 保持原本邏輯與輸出
- 優先降低重複、改善命名與可讀性
- 沿用目前專案既有風格，不要引入新框架或大規模重寫

## 驗收條件

- 沒有新增未使用的 import
- 沒有改動 public API 名稱（除非 Prompt 另有要求）
- 產出可直接套用的修改結果
```

### 模板 C：React 元件腳手架（`mode: agent`）

```markdown
---
name: react-component
description: >
  Generates a standardized React component scaffold with TypeScript props,
  tests, and a Storybook story.
mode: agent
inputs:
  - name: componentName
    description: "元件名稱（PascalCase），例如：UserCard"
  - name: hasChildren
    description: "是否接受 children prop（yes/no）"
---

你是一位熟悉 React 18 + TypeScript 5 最佳實踐的 Senior Frontend Engineer。

## 任務

建立一個名為 `${input:componentName}` 的 React 函式元件，遵循以下規範：

參照現有元件結構：#file:src/components/Button/Button.tsx

## 要求

1. 使用 TypeScript，所有 Props 以 `interface ${input:componentName}Props` 定義
2. 是否包含 children：${input:hasChildren}
3. 匯出：優先具名匯出（named export），除非專案慣例另有要求
4. 若需要支援 ref，使用 `React.forwardRef`

## 輸出

產出以下檔案：
- `src/components/${input:componentName}/${input:componentName}.tsx`
- `src/components/${input:componentName}/${input:componentName}.test.tsx`
- `src/components/${input:componentName}/${input:componentName}.stories.tsx`
```

---

## 使用範例

### 範例 1：自動化 API 文件更新 Prompt

**使用者需求**：每次修改 API handler 後，更新對應的 OpenAPI 規格片段

```markdown
---
name: update-api-doc
description: >
  根據當前 API handler 實作，更新對應的 OpenAPI 3.1 規格片段。
mode: agent
---

參照現有 API 規格：#file:docs/openapi.yaml

根據以下 handler 實作：
${file}

更新 `docs/openapi.yaml` 中對應 path 的：
- summary
- description
- requestBody schema
- responses（至少包含 200、400、401、500）
```

### 範例 2：測試案例補強 Prompt

**使用者需求**：分析現有函式，找出未覆蓋的邊界條件並生成補強測試

```markdown
---
name: test-coverage-boost
description: >
  分析選取的函式，找出未覆蓋的 edge case，並生成補強測試案例。
mode: ask
---

分析以下函式的邏輯分支：

${selection}

識別尚未被測試的邊界條件，包括：
- null / undefined 輸入
- 空陣列 / 空字串
- 邊界值（最大值、最小值、0）
- 錯誤路徑（exception 拋出）

為每個未覆蓋情境生成對應測試，使用 Jest / Vitest 格式。
```
