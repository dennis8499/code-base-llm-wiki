---
name: save-synthesis
description: >
  將當前對話中的分析結果存入 wiki/synthesis/——互動式引導命名、
  選擇分類，產出結構化 synthesis 頁面並更新索引。
agent: "wiki-keeper"
argument-hint: "可選：補充分析主題名稱，例如：登入流程跨模組依賴分析"
---

## 任務

將當前對話中的重要分析結果存入 `wiki/synthesis/`，讓探索性查詢的洞察能複利累積。

**分析主題**：${input:topicName:（若未提供，請從對話內容自動推導）}

## 流程

1. **確認內容**：
   - 摘要本次分析的核心發現（3-5 句話）
   - 向使用者確認是否正確，或請使用者補充重點

2. **決定分類**：
   - `wiki/synthesis/` 下已有哪些頁面？（讀取目錄）
   - 這份分析最適合放入哪個頁面？
     - 若主題已有對應頁面 → 追加到該頁面的適當段落
     - 若是全新主題 → 建立新頁面

3. **命名規則**（新建頁面時）：
   - 檔名：`wiki/synthesis/{kebab-case-topic}.md`
   - 範例：`cross-module-auth-flow.md`、`technical-debt-overview.md`

4. **寫入 Synthesis 頁面**：

```yaml
---
title: "{主題標題}"
type: synthesis
sources:
  - （引用本次對話涉及的原始碼或 wiki 頁面）
last_updated: { today }
tags: [synthesis, { 相關標籤 }]
status: active
---
```

頁面結構：

```markdown
# {主題標題}

## 摘要

{核心發現，2-4 句}

## 詳細分析

{展開說明，可包含表格、程式碼引用}

## 相關頁面

- [[wiki-page-a]]
- [[wiki-page-b]]

## 後續建議

{建議後續深入 ingest 的模組、值得追蹤的問題}
```

5. **更新 `wiki/index.md`**（在 Synthesis section 新增條目）
6. **追加 `wiki/log.md`** 條目：`## [YYYY-MM-DD] synthesis | {主題標題}`

## 品質要求

- `frontmatter.sources` 只列涉及分析的真實 repo-relative raw source 路徑；wiki 頁面請放在「相關頁面」wikilinks，不要放入 sources
- 每頁至少兩個對外的 `[[wikilink]]`
- 若分析跨越多個模組，清楚標記每個發現來源於哪個模組
