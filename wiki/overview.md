---
title: Codebase LLM Wiki — 專案總覽
type: overview
sources:
  - README.md
  - AGENTS.md
  - Codex.md
  - llm-wiki.md
  - .github/copilot-instructions.md
  - .agents/skills/codebase-wiki/SKILL.md
  - .agents/skills/codebase-wiki/capabilities.json
  - .agents/skills/codebase-wiki/scripts/install-framework.py
last_updated: 2026-07-15
tags: [framework, llm, wiki, copilot, codex]
status: active
---

# Codebase LLM Wiki — 專案總覽

> 讓 GitHub Copilot 或 OpenAI Codex 為任意 codebase 增量建構並維護結構化知識庫。

## 專案簡介

**Codebase LLM Wiki** 是一套面向 coding agents 的框架，讓 LLM 把 codebase 持續整理成一個可累積、可交叉引用、可追溯來源的 Markdown wiki。

**核心差異：這不是 RAG。**

| 模式     | RAG（傳統）                  | Codebase LLM Wiki                |
| -------- | ---------------------------- | -------------------------------- |
| 知識儲存 | 向量資料庫，每次查詢重新檢索 | 持久 Markdown wiki，知識不斷累積 |
| 交叉引用 | 查詢時動態拼裝               | 事先建立，wikilink 已存在        |
| 矛盾偵測 | 無                           | Lint 流程主動發現並標記          |
| 歷史脈絡 | 無                           | Archaeology 流程追蹤 git history |
| 維護方式 | 無須維護                     | LLM 增量維護，人類導向           |

## 技術棧

- **語言**：Markdown（wiki 頁面）、Python 3.11+（安裝器、Hooks 與輔助腳本）、TOML（設定）、JSON（Hook／capability）、YAML（Frontmatter）
- **整合平台**：GitHub Copilot（VS Code）、OpenAI Codex（CLI / IDE / Cloud Tasks）
- **相容工具**：Obsidian（wikilink 語法）、Marp（簡報）、Dataview（動態查詢）

## 架構模式：三層模型

```
┌─────────────────────────────────────────────────────┐
│                     Schema 層                        │
│   .github/ 或 AGENTS.md + .codex/ + .agents/        │
│   驅動 agent 行為的規則、模板、腳本與工作流程         │
└───────────────────┬─────────────────────────────────┘
                    │ 讀取規則，產出 wiki
┌───────────────────▼─────────────────────────────────┐
│                      Wiki 層                         │
│                     wiki/                            │
│         LLM 產生並維護的 Markdown 知識庫             │
└───────────────────┬─────────────────────────────────┘
                    │ 讀取來源，寫入 wiki
┌───────────────────▼─────────────────────────────────┐
│                  Raw Sources 層                      │
│           目標 codebase 的原始碼、設定檔             │
│                   唯讀，永不修改                     │
└─────────────────────────────────────────────────────┘
```

## 目錄結構

```text
code-base-llm-wiki/
├── README.md                     — 專案總覽
├── AGENTS.md                     — Codex 版機器指令
├── Codex.md                      — Codex 版人類操作手冊
├── ChangeLog.md                  — 版本變更紀錄
├── llm-wiki.md                   — 框架方法論原始概念（歷史參考）
├── prompt.txt                    — 早期設計草稿（歷史參考）
│
├── .github/                      — GitHub Copilot 版元件
│   ├── copilot-instructions.md   — Copilot 全域指令
│   ├── agents/                   — 5 個 Copilot 自訂 agents
│   ├── prompts/                  — 11 個 Slash prompts（IDE 專用）
│   ├── hooks/                    — 3 個 Copilot hooks
│   └── instructions/             — wiki 頁面格式規範
│
├── .codex/                       — OpenAI Codex 版元件
│   ├── config.toml               — Codex 設定
│   ├── hooks.json                — Codex hook 事件設定
│   ├── agents/                   — 5 個 Codex 自訂 agents
│   └── hooks/scripts/            — Hook 腳本
│
├── .agents/                      — 跨平台共用元件
│   └── skills/codebase-wiki/     — Repo-local skill
│       ├── SKILL.md              — Skill 主文件
│       ├── assets/               — 6 種頁面模板
│       ├── references/           — 工作流、規格與安全參考
│       └── scripts/              — Wiki 檢查與 parity scripts
│
└── wiki/                         — 知識庫輸出位置
    ├── index.md                  — 主索引
    ├── log.md                    — 時序活動紀錄
    ├── overview.md               — 高階總覽（本頁）
    ├── architecture/
    ├── modules/
    ├── entities/
    ├── patterns/
    ├── decisions/
    ├── dependencies/
    ├── guides/
    └── synthesis/
```

## 兩種入口

| 入口                  | 主要檔案                             | 適合情境                                                   |
| --------------------- | ------------------------------------ | ---------------------------------------------------------- |
| **GitHub Copilot 版** | `.github/`                           | VS Code Copilot Chat，支援自訂 agent、slash prompt 與 hook |
| **OpenAI Codex 版**   | `AGENTS.md` + `.codex/` + `.agents/` | Codex CLI / IDE / 雲端任務，以自然語言驅動                 |

兩版共用同一個 `wiki/` 骨架，可共存於同一個 repo。

本框架採雙入口同權維護：Copilot 與 Codex 維持同一組 wiki 能力、邊界、安全規則與驗收結果。兩者共用 `.agents/skills/codebase-wiki/`，包含零依賴安裝器與 Wiki 輔助腳本；Copilot 額外使用 agents、prompts、hooks，Codex 使用 `AGENTS.md`、`.codex/agents/` 與 `.codex/hooks.json`。Codex 不模擬 Copilot 的 project-level slash prompt files，而是以自然語言 recipe 觸發同等工作流程。Query 直接讀取 Markdown Wiki，再按需回溯 raw sources，不建立衍生搜尋索引。

## 核心功能

詳細說明請參閱 [[framework-introduction]]。

## 相關頁面

- [[framework-introduction]] — 完整功能介紹與使用指南
