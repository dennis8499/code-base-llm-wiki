---
title: "{模組名稱}"
type: module
summary: "{模組核心職責的一句話摘要}"
notebooklm_group: "function-{functional-area-slug}"
notebooklm_role: traceability
sources:
  - "{path/to/module/directory/}"
derived_from: []
source_digest: "sha256:{64-lowercase-hex}"
last_updated: YYYY-MM-DD
tags: []
status: active
---

# {模組名稱}

> 一句話摘要：描述這個模組的核心職責。

## 職責

- 職責 1
- 職責 2

## 核心檔案

| 檔案             | 用途       |
| ---------------- | ---------- |
| `{path/to/file}` | {用途說明} |

## 主要類別 / 函式

### `{ClassName}`

- **用途**：...
- **關鍵方法**：`methodA()`、`methodB()`

## 相依關係

- **依賴**：[[{module-a}]]、[[{module-b}]]
- **被依賴**：[[{module-c}]]

## 對外介面

- Export 的 public API
- 提供的 Event / Message

## 相關頁面

- [[overview]]
