# Codebase LLM Wiki

> 讓 GitHub Copilot 或 OpenAI Codex 為任意 codebase 增量建構並維護結構化知識庫。

[![GitHub Copilot](https://img.shields.io/badge/GitHub%20Copilot-Supported-blue?logo=github)](https://github.com/features/copilot)
[![OpenAI Codex](https://img.shields.io/badge/OpenAI%20Codex-Supported-111827?logo=openai)](https://openai.com/index/introducing-codex/)
[![VS Code](https://img.shields.io/badge/VS%20Code-Extension-007ACC?logo=visualstudiocode)](https://code.visualstudio.com/)
[![Python](https://img.shields.io/badge/Python-3.8%2B-3776AB?logo=python)](https://www.python.org/)
[![Obsidian Compatible](https://img.shields.io/badge/Obsidian-Compatible-7C3AED?logo=obsidian)](https://obsidian.md/)

---

## 目錄

- [這是什麼？](#這是什麼)
- [文件入口](#文件入口)
- [三層模型](#三層模型)
- [支援入口](#支援入口)
- [專案結構](#專案結構)
- [安裝與設定](#安裝與設定)
- [快速開始](#快速開始)
- [典型工作流程](#典型工作流程)
- [資料庫 Live Evidence](#資料庫-live-evidence)
- [元件一覽](#元件一覽)
- [Wiki 結構與規格](#wiki-結構與規格)
- [相容性](#相容性)
- [變更紀錄](#變更紀錄)

---

## 這是什麼？

**Codebase LLM Wiki** 是一套面向 coding agents 的框架，讓 LLM 把 codebase 持續整理成一個可累積、可交叉引用、可追溯來源的 Markdown wiki。

這不是每次查詢都重新檢索原始碼的 RAG，而是把已讀過的模組、服務、模式與決策沉澱成 wiki 頁面。之後再查詢時，LLM 會先讀 wiki，再必要時回溯原始碼驗證。

這個 repo 同時提供兩條入口：

- **GitHub Copilot 版**：以 `.github/` 內的 agents、prompts、hooks、skills 為主。
- **OpenAI Codex 版**：以 `AGENTS.md`、`.codex/`、`.agents/skills/codebase-wiki/` 為主。

兩者共用同一份 `wiki/` 骨架與方法論。

---

## 文件入口

| 文件 | 用途 |
| --- | --- |
| [README.md](README.md) | 專案總覽，說明 Copilot 與 Codex 兩種入口的定位與結構 |
| [Codex.md](Codex.md) | 給框架使用者的 Codex 專用安裝、操作、排錯手冊 |
| [AGENTS.md](AGENTS.md) | 給 Codex 讀取的機器指令，定義 wiki 邊界、流程與規則 |
| [ChangeLog.md](ChangeLog.md) | 框架版本變更紀錄 |
| [llm-wiki.md](llm-wiki.md) | 這套方法論的原始概念說明 |
| [prompt.txt](prompt.txt) | 早期設計此框架時使用的提示草稿 |

如果你是第一次接觸這個 repo，建議先讀 `README.md`；如果你要把這套框架套到自己的 repo 並用 Codex 操作，接著讀 [Codex.md](Codex.md)。

---

## 三層模型

| 層 | 位置 | 職責 |
| --- | --- | --- |
| **Raw Sources** | 目標 codebase 的原始碼、設定檔、既有文件 | 唯讀。wiki 任務中只讀取、不修改 |
| **Wiki** | `wiki/` | LLM 產生並維護的 Markdown 知識庫 |
| **Schema** | `.github/` 或 `AGENTS.md` + `.codex/` + `.agents/skills/` | 驅動 agent 行為的規則、模板、腳本與工作流程 |

---

## 支援入口

| 入口 | 主要檔案 | 適合情境 |
| --- | --- | --- |
| **GitHub Copilot 版** | `.github/copilot-instructions.md`、`.github/agents/`、`.github/prompts/`、`.github/hooks/`、`.github/skills/` | 你想在 VS Code Copilot Chat 中使用自訂 agent、slash prompt、hook，並讓 `wiki-query` 在可用時透過 VS Code MSSQL tools 取得唯讀資料庫證據 |
| **OpenAI Codex 版** | `AGENTS.md`、`.codex/config.toml`、`.codex/hooks.json`、`.codex/agents/`、`.agents/skills/codebase-wiki/` | 你想讓 Codex CLI、IDE extension、Codex app 或 cloud task 直接讀取專案規則與 repo-local skill；Codex query 流程會同步遵守 SQL Server live evidence 的唯讀規則 |
| **共用 Wiki 骨架** | `wiki/` | 兩種版本共用的知識庫輸出位置 |

你可以只選其中一條路線，也可以讓兩套檔案共存於同一個 repo。本框架採 **雙入口同權維護**：Copilot 與 Codex 共享同一組 wiki 能力、邊界、安全規則與驗收結果，但各自使用平台原生入口。

### Copilot ↔ Codex 功能對照

| 能力 | GitHub Copilot | OpenAI Codex |
| --- | --- | --- |
| 全域規則 | `.github/copilot-instructions.md` | `AGENTS.md` |
| 專業代理 | `.github/agents/*.agent.md` | `.codex/agents/*.toml` |
| 使用者入口 | `.github/prompts/*.prompt.md` slash prompts | `Codex.md` 內的自然語言 recipe |
| Workflow 細節 | `.github/skills/codebase-wiki/` | `.agents/skills/codebase-wiki/` |
| Hooks | `.github/hooks/*.json` | `.codex/hooks.json` |
| 輸出 | `wiki/` | `wiki/` |

Codex 不模擬 Copilot 的 project-level slash prompt files；Codex IDE / CLI 的 slash commands 是平台控制命令，日常 wiki 操作用自然語言 recipe 觸發。

---

## 專案結構

### 版本化元件

```text
AGENTS.md
Codex.md
README.md
ChangeLog.md
llm-wiki.md
prompt.txt
.codex/
├── config.toml
├── hooks.json
├── agents/
└── hooks/
    └── scripts/
.agents/
└── skills/
    └── codebase-wiki/
.github/
├── copilot-instructions.md
├── agents/
├── prompts/
├── hooks/
├── instructions/
└── skills/
wiki/
├── index.md
├── log.md
├── overview.md
├── architecture/
├── modules/
├── entities/
├── patterns/
├── decisions/
├── dependencies/
├── guides/
└── synthesis/
```

### 執行期產物

- `.codex/hooks/logs/`：當 Codex hooks 啟用時，SessionStart 與 log reminder 會優先在這裡留下執行期輸出。
- `.codex-hook-logs/`：若 Windows ACL 擋住 `.codex/hooks/logs/` 寫入，Codex hooks 會退到這個 root-level ignored 目錄。

---

## 安裝與設定

### GitHub Copilot 版

```bash
cp -r .github/ /path/to/your-repo/.github/
cp -r wiki/ /path/to/your-repo/wiki/
```

安裝後請確認：

- 已安裝並登入 GitHub Copilot Chat
- 已啟用 Agent 模式
- `.github/agents/` 下可看到 `wiki-keeper`、`wiki-ingest`、`wiki-query`、`wiki-lint`、`wiki-archaeologist`

### OpenAI Codex 版

```bash
cp AGENTS.md /path/to/your-repo/AGENTS.md
cp -r .codex/ /path/to/your-repo/.codex/
mkdir -p /path/to/your-repo/.agents/skills/
cp -r .agents/skills/codebase-wiki/ /path/to/your-repo/.agents/skills/codebase-wiki/
cp -r wiki/ /path/to/your-repo/wiki/
```

Codex 版的必要元件只有：

- `AGENTS.md`
- `.codex/`
- `.agents/skills/codebase-wiki/`
- `wiki/`

`.github/` 不是 Codex 的必要依賴。完整操作說明、自然語言範例與排錯請看 [Codex.md](Codex.md)。

---

## 快速開始

### Copilot

在 Copilot Chat 切到 `wiki-keeper`，直接輸入：

```text
把 src/auth/ 模組加進 wiki
```

或使用 slash prompt：

```text
/ingest-module src/auth/
```

### Codex

在 Codex CLI、IDE extension、Codex app 或 cloud task 中直接輸入：

```text
請依照 AGENTS.md 的 ingest 流程，把 src/auth/ 模組加進 wiki。
```

日常使用不需要手動切換 custom agent，也不需要 slash prompt。Codex 的完整安裝、hooks、delegation 與排錯說明請看 [Codex.md](Codex.md)。

---

## 典型工作流程

### 情境一：初始化全新專案的 wiki

**Copilot**

```text
/ingest-batch src/
/onboarding-guide
/update-index
```

**Codex**

```text
請依照 AGENTS.md 的 batch ingest 流程掃描 src/，建立初始 wiki，最後更新 index 與 log。
請根據目前的 wiki 內容產出一份 onboarding guide，存到 wiki/guides/，並更新 index 與 log。
```

更多 Codex 寫法可參考 [Codex.md](Codex.md)。

### 情境二：新功能上線後更新 wiki

**Copilot**

```text
/ingest-module src/features/checkout/
/new-adr 為什麼在結帳流程中採用 Saga Pattern
/save-synthesis 結帳流程跨服務依賴分析
```

**Codex**

```text
請依照 AGENTS.md 的 Interactive Ingest 流程，分析 src/features/checkout/，先摘要主要職責、相依關係與風險，再更新 wiki。

請建立一份 ADR，說明為什麼在結帳流程中採用 Saga Pattern，寫入 wiki/decisions/，並同步更新 index 與 log。

請把這次對結帳流程跨服務依賴的分析整理成 wiki/synthesis/ 頁面，保留來源並更新 index 與 log。
```

### 情境三：知識查詢與健康維護

**Copilot**

```text
/query-wiki PaymentService 如何處理退款？
/query-wiki Orders 資料表和 PaymentService 的退款流程有什麼關係？
/lint-wiki
```

**Codex**

```text
請先查 wiki，再必要時回溯 sources，解釋 PaymentService 的退款流程。
請先查 wiki，再必要時使用可用的 SQL Server 工具取得唯讀 live evidence，說明 Orders 資料表和 PaymentService 的退款流程有什麼關係。
請依 AGENTS.md 的 lint 流程檢查 wiki 健康狀態，列出 critical 和 warning。
```

### 情境四：程式碼考古與長期知識沉澱

**Copilot**

```text
discount_code 這個欄位是什麼時候、為什麼加進來的？
/save-synthesis 折扣碼設計演進分析
```

**Codex**

```text
請用 code archaeology 流程追蹤 discount_code 欄位的 git history，清楚區分證據與推測，最後更新 wiki。
請把這次分析整理成一份 synthesis 頁面，並更新 index 與 log。
```

---

## 資料庫 Live Evidence

`wiki-query` 現在支援在查詢流程中納入 SQL Server live evidence，用來回答「wiki / source 描述」和「目前資料庫 schema 或資料」之間的關係。

| 入口 | 行為 |
| --- | --- |
| GitHub Copilot | `.github/agents/wiki-query.agent.md` 宣告 VS Code Microsoft SQL Server extension tools；當工具可用時，可查 schema、metadata 與有界線的唯讀 `SELECT` |
| OpenAI Codex | `AGENTS.md` 與 `.codex/agents/wiki-query.toml` 同步定義相同行為；當 Codex 環境沒有 MSSQL tool 時，必須先詢問使用者是否改走 Copilot、MCP、CLI 或其他 fallback |

共同規則：

- 只允許 schema discovery、metadata lookup 與 bounded read-only `SELECT`
- 禁止 DML、DDL、`EXEC`、stored procedure execution、無限制全表掃描與任何會改變資料庫狀態的操作
- DB-derived 回答必須標註 `connected_at`、`source_tool`、`server`、`database`、`query_scope`、`result_limit`、`row_count`、`freshness_note`
- DB 證據不是 repo 檔案，不得寫入 wiki frontmatter `sources`；若要長期保存，應放在 `wiki/synthesis/` 或相關 wiki 頁面的正文 evidence block，並經使用者確認

---

## 元件一覽

### Copilot 版

| 元件 | 位置 | 用途 |
| --- | --- | --- |
| Agents | `.github/agents/` | `wiki-keeper` 等 5 個專業 agent，負責路由、ingest、query、lint、archaeology；`wiki-query` 可在 VS Code MSSQL tools 可用時取得唯讀 DB live evidence |
| Prompts | `.github/prompts/` | `/ingest-module`、`/lint-wiki`、`/save-synthesis` 等對話入口 |
| Hooks | `.github/hooks/` | 寫入保護與稽核提醒 |
| Skill | `.github/skills/codebase-wiki/` | 共用模板、reference 文件與腳本 |

### Codex 版

| 元件 | 位置 | 用途 |
| --- | --- | --- |
| Root instructions | `AGENTS.md` | Codex 讀取的主要規則、流程與禁止事項 |
| Repo-local skill | `.agents/skills/codebase-wiki/` | 模板、reference 文件與輔助腳本 |
| Hooks | `.codex/config.toml`、`.codex/hooks.json`、`.codex/hooks/scripts/` | SessionStart 狀態摘要、寫入保護、log reminder |
| Custom agents | `.codex/agents/` | 可委派的 specialized agents；只在明確要求 delegation 或 parallel agent work 時使用；`wiki-query` 內建 SQL Server live evidence 的唯讀與 fallback 規則 |

Codex 版的細節配置與常見誤解，集中整理在 [Codex.md](Codex.md)。

---

## Wiki 結構與規格

### 目錄結構

```text
wiki/
├── index.md
├── log.md
├── overview.md
├── architecture/
├── modules/
├── entities/
├── patterns/
├── decisions/
├── dependencies/
├── guides/
└── synthesis/
```

### Frontmatter 規格

每個 wiki 頁面都應包含：

```yaml
---
title: 頁面標題
type: module | entity | pattern | decision | dependency | guide | synthesis | overview | architecture | index | log
sources:
  - path/to/source/file.ts
last_updated: YYYY-MM-DD
tags: [tag1, tag2]
status: active | stale | placeholder
---
```

ADR 頁面另外需要：

```yaml
decision_date: YYYY-MM-DD
decision_status: proposed | accepted | deprecated | superseded
```

### 核心規則

- Raw sources 在 wiki 任務中只能讀取，不能修改
- `wiki/log.md` 是 append-only
- 新增、刪除、改名 wiki 頁面後必須更新 `wiki/index.md`
- `frontmatter.sources` 必須對應真實存在的 repo 相對路徑
- 引用其他 wiki 頁面時使用 `[[page-name]]`

---

## 相容性

| 工具 | 支援狀態 | 說明 |
| --- | --- | --- |
| GitHub Copilot Chat | ✅ 支援 | 使用 `.github/` 內的 agents、prompts、hooks、skills |
| OpenAI Codex | ✅ 支援 | 使用 `AGENTS.md`、`.codex/`、`.agents/skills/` 作為入口 |
| VS Code | ✅ 支援 | Copilot 與 Codex IDE extension 都可使用 |
| Python 3.8+ | ⚡ 選用 | hooks 與輔助腳本需要；純自然語言流程不一定需要 |
| Obsidian | ✅ 相容 | `wiki/` 可直接當作 Vault 使用 |
| 任意語言的 codebase | ✅ 通用 | 框架不依賴特定程式語言 |

---

## 變更紀錄

詳見 [ChangeLog.md](ChangeLog.md)。
