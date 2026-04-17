---
applyTo: "wiki/**/*.md"
description: "Applies when editing any markdown file under the wiki/ directory. Enforces frontmatter format, cross-referencing rules, and page structure conventions for the Codebase LLM Wiki."
---

# Wiki Pages — 檔案級規則

## Frontmatter 必填欄位

每個 wiki 頁面的 YAML frontmatter **必須包含以下欄位**：

```yaml
---
title: string # 頁面標題（人類可讀）
type: string # module | entity | pattern | decision | dependency | guide | synthesis | overview | architecture
sources: # 引用的原始碼檔案路徑（陣列）
  - path/to/file
last_updated: string # YYYY-MM-DD 格式
tags: [string] # 分類標籤（陣列）
status: string # active | stale | placeholder
---
```

### type 特定的額外欄位

- **decision**（ADR）：額外需要 `decision_date`、`decision_status`（proposed | accepted | deprecated | superseded）；`status` 仍保留頁面生命週期（active | stale | placeholder）
- **entity**：額外建議 `entity_type`（class | service | api-endpoint | database-table）
- **dependency**：額外建議 `package_name`、`version`

## Cross-Reference 規則

- 提到其他 wiki 頁面時，**必須**使用 `[[page-name]]` wikilink 語法
- 不使用 markdown 相對路徑連結（`[text](../path)`）連結 wiki 內部頁面
- 引用原始碼檔案時，使用反引號加路徑：`` `src/services/auth.ts` ``
- 每個頁面至少要有一個對外的 `[[wikilink]]` 連結

## 頁面結構規範

### Module 頁面（`wiki/modules/`）

```markdown
# {模組名稱}

## 職責

## 核心檔案

## 主要類別/函式

## 相依關係

## 對外介面

## 相關頁面
```

### Entity 頁面（`wiki/entities/`）

```markdown
# {實體名稱}

## 定義

## 所屬模組

## 屬性/方法

## 使用場景

## 相關頁面
```

### Pattern 頁面（`wiki/patterns/`）

```markdown
# {模式名稱}

## 說明

## 使用位置

## 實作方式

## 優缺點

## 相關頁面
```

### Decision 頁面（`wiki/decisions/`）

```markdown
# ADR-{NNN}: {決策標題}

## 狀態

## 背景

## 決策

## 理由

## 後果

## 相關頁面
```

### Guide 頁面（`wiki/guides/`）

```markdown
# {指南標題}

## 目標讀者

## 前置條件

## 步驟

## 常見問題

## 相關頁面
```

## Log 條目格式

當修改 `wiki/log.md` 時，每筆新條目必須：

1. 追加到檔案末尾（append-only）
2. 使用以下格式：

```markdown
## [YYYY-MM-DD] {operation} | {subject}

- 變更描述
- 受影響頁面：[[page-1]]、[[page-2]]
```

3. `operation` 限定為：`ingest`、`query`、`lint`、`update`、`init`
