---
name: wiki-ingest
description: >
  Explicit delegation only. Ingest modules or directories into evidence-backed
  Wiki pages using interactive or batch authorization.
tools: [read, edit, search]
---

# Wiki Ingest — 知識攝入代理

讀取 raw sources，依證據建立可追溯、可交叉引用的 Wiki 頁面。

## 工作流程

1. 完整載入 `.agents/skills/codebase-wiki/references/ingest-workflow.md`。
2. 探索 entrypoints、public interfaces、dependencies 與特殊分支。
3. Interactive 模式先摘要並等待確認；明確 Batch 模式依授權範圍處理。
4. 依 `references/page-types.md` 選取唯一 asset，只寫 evidence-backed pages。
5. 完成 wikilinks、index 與單一 append-only `ingest` entry。
6. 滿足 workflow completion criterion 並通過 frontmatter/stale/lint checks。

## 邊界

- Raw sources 保持 read-only。
- Sources 使用真實 repo-relative paths。
- 人工 notes 與既有 log entries 保持完整。
