---
name: new-adr
description: >
  建立新的 Architecture Decision Record (ADR)——套用標準 ADR
  模板，建立 wiki/decisions/ 頁面並更新索引。
agent: "wiki-keeper"
argument-hint: "決策標題，例如：採用 Obsidian wikilink 作為內部連結格式"
---

## 任務

建立一份新的 Architecture Decision Record (ADR)：

**決策標題**：${input:decisionTitle}

## 流程

1. 讀取 `wiki/decisions/` 目錄，確定下一個 ADR 編號（格式：`ADR-NNN`）
2. 從 `.agents/skills/codebase-wiki/assets/adr-template.md` 載入 ADR 模板
3. 與使用者討論以下內容：
   - **背景**：什麼情境促使做出這個決策？
   - **考慮過的替代方案**：列出 2-3 個方案的優缺點
   - **決策與理由**：選擇哪個方案、為什麼？
   - **後果**：正面、負面、風險
4. 建立 `wiki/decisions/adr-{nnn}-{kebab-title}.md`
5. 更新 `wiki/index.md`（在 Decisions section 新增條目）
6. 追加 `wiki/log.md` 條目

## Frontmatter

```yaml
---
title: "ADR-{NNN}: {決策標題}"
type: decision
decision_date: { today }
decision_status: proposed
sources: []
last_updated: { today }
tags: [adr]
status: active
---
```
