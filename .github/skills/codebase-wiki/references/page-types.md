# 頁面類型與結構範例

## Module 頁面（`wiki/modules/`）

Module 頁面對應 codebase 中的一個邏輯模組（通常是一個目錄或子專案）。

### 結構

```markdown
---
title: {模組名稱}
type: module
sources:
  - src/modules/{module-name}/
  - src/modules/{module-name}/index.ts
last_updated: YYYY-MM-DD
tags: [{domain}, {layer}]
status: active
---

# {模組名稱}

> 一句話摘要：描述這個模組的核心職責。

## 職責

- 職責 1
- 職責 2

## 核心檔案

| 檔案 | 用途 |
|------|------|
| `src/modules/{name}/index.ts` | 模組入口點 |
| `src/modules/{name}/service.ts` | 核心業務邏輯 |

## 主要類別 / 函式

### `ClassName`
- **用途**：...
- **關鍵方法**：`methodA()`、`methodB()`

### `functionName()`
- **用途**：...
- **參數**：...
- **回傳**：...

## 相依關係

- **依賴**：[[module-a]]、[[module-b]]
- **被依賴**：[[module-c]]

## 對外介面

- Export 的 public API
- 提供的 Event / Message

## 相關頁面

- [[related-entity]]
- [[related-pattern]]
```

---

## Entity 頁面（`wiki/entities/`）

Entity 頁面描述 codebase 中的關鍵實體——類別、服務、API 端點、資料庫表。

### 結構

```markdown
---
title: {實體名稱}
type: entity
entity_type: class | service | api-endpoint | database-table
sources:
  - src/services/{name}.ts
last_updated: YYYY-MM-DD
tags: [{domain}]
status: active
---

# {實體名稱}

> 一句話定義。

## 所屬模組

[[parent-module]]

## 定義

詳細說明此實體的職責、設計決策、邊界。

## 屬性 / 方法

### 屬性

| 名稱 | 型別 | 說明 |
|------|------|------|
| `propA` | `string` | ... |

### 方法

| 名稱 | 參數 | 回傳 | 說明 |
|------|------|------|------|
| `doSomething()` | `input: string` | `Result` | ... |

## 使用場景

- 何時使用此實體
- 常見呼叫路徑

## 相關頁面

- [[related-module]]
- [[related-pattern]]
```

---

## Pattern 頁面（`wiki/patterns/`）

Pattern 頁面記錄 codebase 中使用的設計模式。

### 結構

```markdown
---
title: {模式名稱}
type: pattern
sources:
  - src/patterns/{name}.ts
  - src/services/{example-usage}.ts
last_updated: YYYY-MM-DD
tags: [design-pattern, {category}]
status: active
---

# {模式名稱}

> 一句話說明此模式在本 codebase 中的用途。

## 說明

這個模式解決什麼問題？為什麼選擇它？

## 使用位置

| 位置 | 用途 |
|------|------|
| `src/services/auth.ts` | 用於驗證流程的 Strategy 模式 |

## 實作方式

程式碼結構說明與關鍵實作細節。

## 優缺點

### 優點
- ...

### 缺點
- ...

## 相關頁面

- [[related-module]]
- [[related-entity]]
```

---

## Decision 頁面（`wiki/decisions/`）

ADR (Architecture Decision Records) 記錄重要的架構決策。

### 結構

```markdown
---
title: "ADR-{NNN}: {決策標題}"
type: decision
decision_date: YYYY-MM-DD
sources:
  - path/to/related/code
last_updated: YYYY-MM-DD
tags: [adr, {domain}]
status: proposed | accepted | deprecated | superseded
---

# ADR-{NNN}: {決策標題}

## 狀態

{proposed | accepted | deprecated | superseded}
（若 superseded，標註：被 [[adr-xxx]] 取代）

## 背景

什麼情境促使做出這個決策？

## 決策

我們決定...

## 理由

為什麼選擇這個方案？考慮過哪些替代方案？

## 後果

### 正面
- ...

### 負面
- ...

### 風險
- ...

## 相關頁面

- [[related-module]]
- [[related-pattern]]
```

---

## Dependency 頁面（`wiki/dependencies/`）

記錄關鍵外部相依套件。

### 結構

```markdown
---
title: {套件名稱}
type: dependency
package_name: {npm/pypi/maven package name}
version: {current version}
sources:
  - package.json
  - src/config/{name}.ts
last_updated: YYYY-MM-DD
tags: [dependency, {category}]
status: active
---

# {套件名稱}

> 一句話說明此相依套件在本專案中的用途。

## 用途

為什麼引入這個套件？

## 使用方式

在 codebase 中如何使用。

## 設定

關鍵設定項目與預設值。

## 注意事項

- 版本限制、已知問題、安全考量

## 相關頁面

- [[related-module]]
```

---

## Guide 頁面（`wiki/guides/`）

指南類頁面，適用於 Onboarding、除錯、貢獻流程。

### 結構

```markdown
---
title: {指南標題}
type: guide
sources: []
last_updated: YYYY-MM-DD
tags: [guide, {category}]
status: active
---

# {指南標題}

## 目標讀者

此指南適用於...

## 前置條件

- [ ] 條件 1
- [ ] 條件 2

## 步驟

### 1. {步驟標題}

詳細操作說明。

### 2. {步驟標題}

詳細操作說明。

## 常見問題

### Q: {問題}
A: {回答}

## 相關頁面

- [[overview]]
- [[related-module]]
```

---

## Synthesis 頁面（`wiki/synthesis/`）

綜合分析頁面——技術債、風險區域、改善建議、跨模組分析。

### 結構

```markdown
---
title: {分析標題}
type: synthesis
sources:
  - wiki/modules/{module-a}.md
  - wiki/modules/{module-b}.md
last_updated: YYYY-MM-DD
tags: [synthesis, {topic}]
status: active
---

# {分析標題}

## 摘要

一段話概括分析結論。

## 分析

詳細分析內容。

## 發現

1. 發現 1
2. 發現 2

## 建議

1. 建議 1
2. 建議 2

## 資料來源

基於以下 wiki 頁面綜合分析：
- [[page-a]]
- [[page-b]]
```

---

## Architecture 頁面（`wiki/architecture/`）

架構文件——系統架構、部署架構、資料流。

### 結構

```markdown
---
title: {架構主題}
type: architecture
sources:
  - src/
  - docker-compose.yml
last_updated: YYYY-MM-DD
tags: [architecture, {aspect}]
status: active
---

# {架構主題}

## 總覽

高階架構描述。

## 架構圖

（文字描述或 Mermaid diagram）

## 組件

| 組件 | 職責 | 技術 |
|------|------|------|
| ... | ... | ... |

## 資料流

描述主要資料流路徑。

## 部署

部署架構與環境說明。

## 相關頁面

- [[overview]]
- [[related-module]]
```
