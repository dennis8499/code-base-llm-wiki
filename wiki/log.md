---
title: Wiki Activity Log
type: log
sources: []
last_updated: 2026-06-01
tags: [log]
status: active
---

# Activity Log

> Append-only 時序紀錄。每次 Ingest / Query / Lint / 手動修改操作後追加條目。
> 格式：`## [YYYY-MM-DD] {operation} | {subject}`

---

## [2026-04-16] init | Wiki 初始化

- 建立 Wiki 目錄骨架
- 建立 index.md、log.md、overview.md
- 建立子目錄：architecture、modules、entities、patterns、decisions、dependencies、guides、synthesis

## [2026-05-14] ingest | 框架本身文件化

- 全面閱讀專案所有核心文件（README.md、AGENTS.md、Codex.md、llm-wiki.md、agents、hooks、skills、prompts）
- 更新 wiki/overview.md：從佔位符升級為詳細框架總覽（含三層架構圖、目錄結構、兩種入口對比）
- 建立 wiki/guides/framework-introduction.md：完整功能介紹（五大 agents、六大操作、hooks、頁面規格、slash prompts、輔助腳本、模板、安裝指南、工作流程範例、相容性）
- 更新 wiki/index.md：加入 framework-introduction 條目，補齊 frontmatter（sources、tags）
- 受影響頁面：overview.md、index.md、log.md、guides/framework-introduction.md

## [2026-06-01] update | Codex workflow 雙入口同權化

- 重建並優化 Codex 入口：`AGENTS.md`、`Codex.md`、`.codex/`，改用短 AGENTS.md + `$codebase-wiki` skill 的 token-friendly 流程
- README 與 Codex.md 補上 Copilot ↔ Codex 功能對照，明確 Codex 使用自然語言 recipe 而不是偽造 Copilot slash prompt files
- 更新 wiki/overview.md 與 wiki/guides/framework-introduction.md，記錄雙入口同權維護與 Codex recipe 對照
- 受影響頁面：[[overview]]、[[framework-introduction]]、[[index]]
