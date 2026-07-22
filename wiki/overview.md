---
title: Codebase LLM Wiki — 專案總覽
type: overview
sources:
  - README.md
  - AGENTS.md
  - docs/architecture/README.md
  - .agents/skills/codebase-wiki/SKILL.md
  - .agents/skills/codebase-wiki/scripts/install-framework.py
last_updated: 2026-07-22
tags: [framework, llm, wiki, copilot, codex]
status: active
---

# Codebase LLM Wiki — 專案總覽

> 讓 GitHub Copilot 或 OpenAI Codex 為任意 codebase 增量建構並維護可追溯的 Markdown 知識庫。

## 核心定位

Codebase LLM Wiki 是面向 coding agents 的持久知識框架。Agent 將已理解的模組、實體、模式、決策與操作經驗保存到 `wiki/`；後續問題先讀 Wiki，只有內容不足、過時或矛盾時才回溯 raw sources。

**這不是 RAG。** 框架不建立向量資料庫、本機 source index 或完整原始碼副本。知識直接以可閱讀、可版本控制、可交叉引用的 Markdown 累積。

## 三層模型

| 層 | 位置 | 責任 |
| --- | --- | --- |
| Raw Sources | 目標專案的原始碼、設定與既有文件 | Wiki 任務中唯讀 |
| Wiki | `wiki/` | 持久知識、主索引、活動紀錄 |
| Schema | `AGENTS.md`、`.agents/`、`.github/`、`.codex/` | 意圖、工作流、模板、scripts、hooks 與平台入口 |

```text
Schema instructions + Skill
            │
            ▼
     Copilot / Codex
       │           │
       │ Wiki-first│ evidence gap
       ▼           ▼
     wiki/      Raw Sources
       ▲           │
       └───────────┘
       evidence-backed updates
```

## Repo 產品結構

```text
code-base-llm-wiki/
├── .agents/skills/codebase-wiki/  — 雙平台共用 Skill、規格、模板與 scripts
├── .github/                        — Copilot agents、prompts、hooks、instructions
├── .codex/                         — Codex hooks、設定與 optional agents
├── docs/                           — 架構、安裝、工作流、驗證與歷史文件
├── samples/task-tracker/           — 無第三方依賴的 E2E 驗證 codebase
├── tests/                          — Deterministic regression tests
├── wiki/                           — 本 Repo 的持久知識庫
├── AGENTS.md                       — Codex 專案規則
├── Codex.md                        — 可隨 Codex surface 安裝的操作手冊
├── ChangeLog.md                    — 重要變更
└── README.md                       — 公開導覽與快速開始
```

`docs/`、`samples/`、`tests/` 是框架 Repo 的產品文件與驗證資產，不會被 installer 複製到目標專案。框架自己的 `wiki/` 也不會外洩到目標；installer 由 `.agents/skills/codebase-wiki/assets/wiki-starter/` 建立乾淨 Wiki 骨架。原始方法論與早期 prompt 保留於 `docs/history/`。

## 雙平台入口

| 能力 | GitHub Copilot | OpenAI Codex |
| --- | --- | --- |
| 全域規則 | `.github/copilot-instructions.md` | `AGENTS.md` |
| 共用工作流 | `.agents/skills/codebase-wiki/` | `.agents/skills/codebase-wiki/` |
| 專業代理 | `.github/agents/*.agent.md` | `.codex/agents/*.toml` |
| 使用者入口 | `.github/prompts/*.prompt.md` | `Codex.md` recipes |
| Hooks | `.github/hooks/` | `.codex/hooks.json`、`.codex/hooks/scripts/` |

兩個入口共用 contract version 2、九類意圖、Wiki page schema、安全邊界與驗收標準。Delegation 只有使用者明確要求時啟用，不是日常工作流的必要階段。

## 核心工作流

- **Install / setup**：Installer 先 dry-run，`--apply` 且無 conflicts 才寫入。
- **Ingest**：讀 source evidence，建立或更新 module、entity、pattern 等頁面。
- **Query**：先讀 `wiki/index.md` 與 1–5 個相關頁面，預設唯讀。
- **Lint**：檢查 stale、orphan、broken link、frontmatter、index 與 coverage。
- **Archaeology**：追蹤 call path 與非破壞性 Git history。
- **ADR / Synthesis / Guide / SA**：保存 durable decision、analysis 與操作知識。
- **Delegation**：明確要求時才路由給專業代理。

## 安全與品質

- `frontmatter.sources` 只能列出真實 Repo-relative paths。
- Wiki pages 透過 `[[wikilink]]` 互相引用。
- `wiki/log.md` 只能追加，不能刪除或改寫既有條目。
- Target guard mode 只允許 Wiki 寫入；framework mode 才允許維護 schema、docs、samples 與 tests。
- SQL Server live evidence 只允許 bounded read-only 查詢，且不得放入 frontmatter sources。

## 驗證方式

框架提供 installer/contract/guard/format tests，以及 parity、frontmatter、stale-source 與 Wiki stats scripts。`samples/task-tracker/` 讓 Copilot 與 Codex 以相同 raw source 分別驗證 Ingest → Query → Lint，同時確認 raw source hashes 未變更。

## 相關頁面

- [[framework-introduction]] — 安裝、操作、驗收與常見陷阱指南
