# Codebase LLM Wiki

> 讓 GitHub Copilot 為任意 codebase 增量建構並維護結構化知識庫。

[![License: MIT](https://img.shields.io/badge/License-MIT-yellow.svg)](LICENSE)
[![GitHub Copilot](https://img.shields.io/badge/GitHub%20Copilot-Required-blue?logo=github)](https://github.com/features/copilot)
[![VS Code](https://img.shields.io/badge/VS%20Code-Extension-007ACC?logo=visualstudiocode)](https://code.visualstudio.com/)
[![Python](https://img.shields.io/badge/Python-3.8%2B-3776AB?logo=python)](https://www.python.org/)
[![Obsidian Compatible](https://img.shields.io/badge/Obsidian-Compatible-7C3AED?logo=obsidian)](https://obsidian.md/)

---

## 目錄

- [Codebase LLM Wiki](#codebase-llm-wiki)
  - [目錄](#目錄)
  - [這是什麼？](#這是什麼)
  - [核心概念](#核心概念)
  - [前置需求](#前置需求)
  - [安裝與設定](#安裝與設定)
    - [步驟 1：複製框架到你的 repo](#步驟-1複製框架到你的-repo)
    - [步驟 2：確認 VS Code 設定](#步驟-2確認-vs-code-設定)
    - [步驟 3：確認框架正確載入](#步驟-3確認框架正確載入)
  - [快速開始](#快速開始)
  - [使用方式](#使用方式)
    - [Agent 對話（推薦）](#agent-對話推薦)
    - [Slash Prompt 指令](#slash-prompt-指令)
    - [輔助腳本](#輔助腳本)
  - [元件說明](#元件說明)
    - [Agents](#agents)
      - [wiki-keeper 意圖路由邏輯](#wiki-keeper-意圖路由邏輯)
    - [Skill](#skill)
    - [Hooks](#hooks)
  - [Wiki 結構與格式](#wiki-結構與格式)
    - [目錄結構](#目錄結構)
    - [頁面 Frontmatter 規格](#頁面-frontmatter-規格)
    - [跨頁引用](#跨頁引用)
  - [典型工作流程](#典型工作流程)
    - [情境一：初始化全新專案的 wiki](#情境一初始化全新專案的-wiki)
    - [情境二：新功能上線後更新 wiki](#情境二新功能上線後更新-wiki)
    - [情境三：定期 wiki 健康維護](#情境三定期-wiki-健康維護)
    - [情境四：知識查詢與探索](#情境四知識查詢與探索)
  - [設計原則](#設計原則)
  - [目錄結構總覽](#目錄結構總覽)
  - [相容性](#相容性)

---

## 這是什麼？

**Codebase LLM Wiki** 是一套 GitHub Copilot 自訂化框架，透過自訂 Agent、Prompt、Hook 與 Skill，讓 Copilot 扮演技術文件架構師的角色，持續為你的 codebase 建立、更新並維護一座結構化的 Markdown 知識庫。

這**不是 RAG**（每次重新檢索原始碼）。而是**持久累積的知識庫**——讀過的模組被記錄成頁面，交叉引用持續建立，矛盾會被標記，綜合分析反映所有已讀內容。

```
你問：「OrderService 的退款邏輯在哪裡？」
Copilot：直接從 wiki 取出已整理好的知識，附帶可追溯的原始碼引用。
```

---

## 核心概念

```
┌─────────────────────────────────────────────────┐
│  Raw Sources  ← 唯讀。codebase 原始碼與設定檔    │
├─────────────────────────────────────────────────┤
│  Wiki         ← LLM 產生並維護的 Markdown 知識庫  │
│               wiki/ 目錄（index、modules、ADR 等） │
├─────────────────────────────────────────────────┤
│  Schema       ← 驅動 LLM 行為的 Copilot 元件     │
│               .github/ 下的 agents/prompts/      │
│               hooks/skills                       │
└─────────────────────────────────────────────────┘
```

| 層              | 位置          | 職責                           |
| --------------- | ------------- | ------------------------------ |
| **Raw Sources** | codebase 本身 | 唯讀。LLM 只讀取，**永不修改** |
| **Wiki**        | `wiki/`       | LLM 產出的 Markdown 知識庫     |
| **Schema**      | `.github/`    | 規則、工作流、範本             |

---

## 前置需求

| 需求                                                                                           | 版本   | 說明                                |
| ---------------------------------------------------------------------------------------------- | ------ | ----------------------------------- |
| [VS Code](https://code.visualstudio.com/)                                                      | 最新版 | 主要編輯器                          |
| [GitHub Copilot Chat](https://marketplace.visualstudio.com/items?itemName=GitHub.copilot-chat) | 最新版 | 需啟用 Agent 模式                   |
| [Python](https://www.python.org/)                                                              | 3.8+   | 輔助腳本與 Hooks 執行環境（非必要） |

> **注意：** 使用輔助腳本（`rebuild-index.py` 等）或 Hooks 時需要 Python。純 Agent / Prompt 使用不需要 Python。

---

## 安裝與設定

### 步驟 1：複製框架到你的 repo

```bash
# 複製 .github/ 目錄（框架核心）
cp -r .github/ /path/to/your-repo/.github/

# 複製 wiki/ 骨架目錄
cp -r wiki/ /path/to/your-repo/wiki/
```

> 如果你的 repo 已有 `.github/` 目錄，請手動合併 `agents/`、`prompts/`、`hooks/`、`skills/` 等子目錄。

### 步驟 2：確認 VS Code 設定

在 VS Code 中開啟你的 repo，確認以下設定已啟用：

- **GitHub Copilot Chat** 擴充套件已安裝並登入
- Copilot Chat 的 **Agent 模式**已開啟（Chat 視窗中可切換 Agent 下拉選單）

### 步驟 3：確認框架正確載入

開啟 Copilot Chat，點選 Agent 下拉選單，應可看到：

- `wiki-keeper`
- `wiki-ingest`
- `wiki-query`
- `wiki-lint`
- `wiki-archaeologist`

若看不到這些 Agent，請確認 `.github/agents/` 目錄下的 `.agent.md` 檔案存在。

---

## 快速開始

開啟 Copilot Chat 並切換到 **`wiki-keeper`** agent，然後：

```
把 src/auth/ 模組加進 wiki
```

就這樣。`wiki-keeper` 會自動分析意圖、呼叫適合的子 agent，並在 `wiki/` 目錄下建立結構化的文件頁面。

---

## 使用方式

### Agent 對話（推薦）

在 Copilot Chat 選擇 **`wiki-keeper`** agent，直接以自然語言描述需求。`wiki-keeper` 會自動判斷意圖並路由到正確的專業 agent。

**攝入程式碼：**
```
把 src/auth/ 模組加進 wiki
分析 services/payment/ 目錄並文件化
```

**查詢知識：**
```
解釋一下 OrderService 的退款邏輯
用戶登入流程的整個呼叫鏈是什麼？
PaymentService 依賴哪些外部服務？
```

**建立架構決策紀錄（ADR）：**
```
我要記錄一個架構決策：為什麼選 PostgreSQL
記錄我們採用 Event Sourcing 的原因
```

**健康檢查：**
```
幫我檢查 wiki 有沒有品質問題
有哪些 wiki 頁面已經過時了？
```

**程式碼考古：**
```
為什麼這段重試邏輯用指數退避？
這個 discount_code 欄位是什麼時候加進來的？
```

---

### Slash Prompt 指令

在 Copilot Chat 輸入 `/` 可叫出 Prompt 指令：

| 指令                | 用途                                        | 參數                                      |
| ------------------- | ------------------------------------------- | ----------------------------------------- |
| `/ingest-module`    | 互動式攝入單一模組（先預覽再寫入）          | `modulePath` — 模組路徑，例如 `src/auth/` |
| `/ingest-batch`     | 批次掃描整個目錄，自動推導模組邊界          | `targetPath` — 目標目錄，例如 `src/`      |
| `/query-wiki`       | 向 wiki 提問，回答附帶原始碼引用            | `question` — 問題文字                     |
| `/lint-wiki`        | 執行 8 項 wiki 健康檢查，列出問題並建議修復 | —                                         |
| `/new-adr`          | 以互動方式建立 Architecture Decision Record | `decisionTitle` — 決策標題                |
| `/onboarding-guide` | 掃描 wiki 自動產生新人 Onboarding 指南      | —                                         |
| `/update-index`     | 重新掃描 `wiki/` 並完整重建 `index.md`      | —                                         |
| `/save-synthesis`   | 將當前對話的分析結果存入 `wiki/synthesis/`  | `topicName`（可選）— 分析主題名稱         |

**使用範例：**

```
/ingest-module src/payment/
/ingest-batch src/
/query-wiki 用戶登入流程的整個呼叫鏈是什麼？
/new-adr 選擇 gRPC 取代 REST 作為 service-to-service 通訊協定
/save-synthesis 登入流程跨模組依賴分析
/lint-wiki
```

---

### 輔助腳本

位於 `.github/skills/codebase-wiki/scripts/`，可獨立在終端機執行：

```bash
# 重建 wiki/index.md（掃描所有頁面並重新產生索引）
python .github/skills/codebase-wiki/scripts/rebuild-index.py

# 檢查 frontmatter.sources 中的路徑是否仍存在
python .github/skills/codebase-wiki/scripts/check-stale.py

# 統計 wiki 概況（頁面數量、類型分佈、wikilink 密度）
python .github/skills/codebase-wiki/scripts/wiki-stats.py
```

---

## 元件說明

### Agents

框架包含 5 個專業 agent，各司其職：

| Agent                | 檔案                          | 職責                                                                                 |
| -------------------- | ----------------------------- | ------------------------------------------------------------------------------------ |
| `wiki-keeper`        | `wiki-keeper.agent.md`        | **路由器**。分析使用者意圖，派發到正確的子 agent。所有入口從這裡開始                 |
| `wiki-ingest`        | `wiki-ingest.agent.md`        | **攝入專家**。讀取原始碼，以互動或批次模式產出結構化 wiki 頁面                       |
| `wiki-query`         | `wiki-query.agent.md`         | **知識導航員**。搜尋 wiki 回答問題，可追溯到原始碼；重要分析可存入 synthesis         |
| `wiki-lint`          | `wiki-lint.agent.md`          | **品質審計員**。執行 8 項健康檢查：陳舊頁面、孤島頁面、斷裂連結、缺失 frontmatter 等 |
| `wiki-archaeologist` | `wiki-archaeologist.agent.md` | **程式碼考古師**。透過 git log 追蹤歷史、揭露隱含邏輯、分析技術債成因                |

#### wiki-keeper 意圖路由邏輯

`wiki-keeper` 根據使用者訊息中的關鍵詞自動路由：

| 關鍵詞特徵                                 | 路由目標              |
| ------------------------------------------ | --------------------- |
| 「讀取」「ingest」「文件化」「加入 wiki」  | `wiki-ingest`         |
| 「怎麼做」「在哪裡」「解釋」「查詢」「找」 | `wiki-query`          |
| 「檢查」「健康」「lint」「品質」「陳舊」   | `wiki-lint`           |
| 「歷史」「為什麼這樣寫」「追蹤」「legacy」 | `wiki-archaeologist`  |
| 「決策」「ADR」「架構選擇」                | 自行套用 ADR 範本處理 |

---

### Skill

| Skill           | 位置                            | 內容                                                                                                                         |
| --------------- | ------------------------------- | ---------------------------------------------------------------------------------------------------------------------------- |
| `codebase-wiki` | `.github/skills/codebase-wiki/` | 主方法論技能，包含攝入工作流、頁面類型規格、lint 清單、frontmatter 規格、6 個頁面範本（module/entity/pattern/adr/log/index） |

**Skill 的 reference 文件：**

| 檔案                             | 說明                                               |
| -------------------------------- | -------------------------------------------------- |
| `references/page-types.md`       | 各頁面類型（module/entity/pattern 等）的規格與用途 |
| `references/ingest-workflow.md`  | 攝入工作流程的詳細步驟說明                         |
| `references/lint-checklist.md`   | 8 項 wiki 健康檢查項目清單                         |
| `references/frontmatter-spec.md` | YAML frontmatter 的完整欄位規格                    |

---

### Hooks

Hooks 為自動觸發的保護機制，在 agent 執行工具前後自動運行：

| Hook 檔案                | 觸發時機       | 腳本                   | 職責                                                                   |
| ------------------------ | -------------- | ---------------------- | ---------------------------------------------------------------------- |
| `wiki-write-guard.json`  | `PreToolUse`   | `wiki-write-guard.py`  | 攔截寫入操作，防止 agent 意外修改 `wiki/` 以外的任何檔案（保護原始碼） |
| `wiki-log-reminder.json` | `PostToolUse`  | `wiki-log-reminder.py` | 偵測到 `wiki/` 頁面被修改後，提醒 agent 在 `log.md` 追加操作紀錄       |
| `wiki-session-init.json` | `sessionStart` | `wiki-session-init.py` | Session 開始時自動初始化，載入 wiki 狀態摘要供 agent 參考              |

---

## Wiki 結構與格式

### 目錄結構

```
wiki/
├── index.md          — 主索引（LLM 自動維護，列出所有頁面）
├── log.md            — 時序活動紀錄（append-only，只增不刪）
├── overview.md       — Codebase 高階總覽
├── architecture/     — 系統架構、部署架構、資料流圖
├── modules/          — 按模組/目錄對應的文件頁面
├── entities/         — 關鍵類別、服務、API 端點文件
├── patterns/         — Codebase 中使用到的設計模式
├── decisions/        — Architecture Decision Records (ADR)
├── dependencies/     — 相依性分析（外部套件、服務相依）
├── guides/           — Onboarding 指南、除錯指南、貢獻指南
└── synthesis/        — 綜合分析（技術債、風險區域、改善建議）
```

### 頁面 Frontmatter 規格

每個 wiki 頁面的 YAML frontmatter：

```yaml
---
title: 頁面標題
type: module | entity | pattern | decision | dependency | guide | synthesis | overview | architecture
sources:
  - path/to/source/file.ts   # 必須是真實存在的路徑
  - path/to/another/file.py
last_updated: YYYY-MM-DD
tags: [tag1, tag2]
status: active | stale | placeholder
---
```

| 欄位           | 必填 | 說明                                                     |
| -------------- | ---- | -------------------------------------------------------- |
| `title`        | ✅    | 頁面標題                                                 |
| `type`         | ✅    | 頁面類型（影響 agent 的分類與 lint 行為）                |
| `sources`      | ✅    | 引用的原始碼路徑清單，必須真實存在                       |
| `last_updated` | ✅    | 最後更新日期（`YYYY-MM-DD`）                             |
| `tags`         | ✅    | 標籤清單，用於分類與搜尋                                 |
| `status`       | ✅    | `active`（現行）/ `stale`（過時）/ `placeholder`（待補） |

### 跨頁引用

使用 **Wikilink 語法**（與 Obsidian 相容）：

```markdown
詳見 [[user-auth-service]] 的實作。
此模式源自 [[repository-pattern]]。
```

> **規定：** 提及其他 wiki 頁面時**必須**使用 `[[page-name]]`，不使用相對路徑連結。

---

## 典型工作流程

### 情境一：初始化全新專案的 wiki

```bash
# 1. 套用框架
cp -r .github/ your-repo/
cp -r wiki/ your-repo/

# 2. 在 Copilot Chat 中執行
/ingest-batch src/         # 批次掃描整個 src 目錄
/onboarding-guide          # 自動產生新人指南
/update-index              # 重建主索引
```

### 情境二：新功能上線後更新 wiki

```
# 單模組攝入（互動模式，先預覽再確認）
/ingest-module src/features/checkout/

# 記錄架構決策
/new-adr 為什麼在結帳流程中採用 Saga Pattern

# 儲存本次分析的綜合洞察
/save-synthesis 結帳流程跨服務依賴分析
```

### 情境三：定期 wiki 健康維護

```
/lint-wiki

# wiki-lint 會回報：
# - 哪些頁面的 sources 路徑已不存在（stale）
# - 哪些頁面沒有任何 wikilink（孤島頁面）
# - 哪些頁面缺少必要的 frontmatter 欄位
# - log.md 是否有近期更新
```

### 情境四：知識查詢與探索

```
# 理解某個服務的邏輯
/query-wiki PaymentService 如何處理退款？

# 追蹤跨模組的呼叫鏈
/query-wiki 用戶登入的完整流程從哪裡開始到哪裡結束？

# 深挖歷史（建議切換到 wiki-archaeologist agent）
為什麼這段重試邏輯要用指數退避而不是固定間隔？
discount_code 這個欄位是什麼時候、為什麼加進來的？
```

---

## 設計原則

| 原則                   | 說明                                                                     |
| ---------------------- | ------------------------------------------------------------------------ |
| **LLM 永不修改原始碼** | wiki agents 對 codebase 只讀不寫，`wiki-write-guard` hook 會攔截越界寫入 |
| **Log 為 append-only** | `log.md` 只能追加新條目，不得修改或刪除既有條目                          |
| **Sources 可追溯**     | 每個 wiki 頁面的 `frontmatter.sources` 必須指向真實存在的檔案路徑        |
| **Wiki 完整性**        | 新增或刪除 wiki 頁面後，必須同步更新 `wiki/index.md`                     |
| **增量建構**           | 不需要一次讀完整個 codebase，可按模組逐步累積知識                        |

---

## 目錄結構總覽

```
.github/
├── copilot-instructions.md               — 全域規則（wiki 慣例、禁止事項）
├── instructions/
│   └── wiki-pages.instructions.md        — 套用至 wiki/**/*.md 的頁面規則
├── agents/
│   ├── wiki-keeper.agent.md              — 路由器 agent
│   ├── wiki-ingest.agent.md              — 攝入 agent
│   ├── wiki-query.agent.md               — 查詢 agent
│   ├── wiki-lint.agent.md                — 健康檢查 agent
│   └── wiki-archaeologist.agent.md       — 程式碼考古 agent
├── prompts/
│   ├── ingest-module.prompt.md           — 互動式攝入單一模組
│   ├── ingest-batch.prompt.md            — 批次攝入目錄
│   ├── query-wiki.prompt.md              — 向 wiki 提問
│   ├── lint-wiki.prompt.md               — wiki 健康檢查
│   ├── new-adr.prompt.md                 — 建立 ADR
│   ├── onboarding-guide.prompt.md        — 產生新人指南
│   ├── update-index.prompt.md            — 重建主索引
│   └── save-synthesis.prompt.md          — 儲存分析結果到 synthesis
├── hooks/
│   ├── wiki-write-guard.json             — 寫入保護（PreToolUse）
│   ├── wiki-log-reminder.json            — Log 提醒（PostToolUse）
│   ├── wiki-session-init.json            — Session 初始化（sessionStart）
│   └── scripts/
│       ├── wiki-write-guard.py
│       ├── wiki-log-reminder.py
│       └── wiki-session-init.py
└── skills/
    └── codebase-wiki/
        ├── SKILL.md                      — 主方法論技能
        ├── references/
        │   ├── page-types.md             — 頁面類型規格
        │   ├── ingest-workflow.md        — 攝入工作流程
        │   ├── lint-checklist.md         — 健康檢查清單
        │   └── frontmatter-spec.md       — Frontmatter 規格
        ├── assets/
        │   ├── module-template.md        — 模組頁面範本
        │   ├── entity-template.md        — Entity 頁面範本
        │   ├── pattern-template.md       — 設計模式頁面範本
        │   ├── adr-template.md           — ADR 頁面範本
        │   ├── log-template.md           — Log 範本
        │   └── index-template.md         — Index 範本
        └── scripts/
            ├── rebuild-index.py          — 重建 index.md
            ├── check-stale.py            — 檢查 stale sources
            └── wiki-stats.py             — Wiki 統計報告
wiki/
├── index.md                              — 主索引
├── log.md                                — 活動紀錄
├── overview.md                           — 高階總覽
├── architecture/                         — 架構文件
├── modules/                              — 模組文件
├── entities/                             — Entity 文件
├── patterns/                             — 設計模式
├── decisions/                            — ADR
├── dependencies/                         — 相依性分析
├── guides/                               — 指南
└── synthesis/                            — 綜合分析
```

---

## 相容性

| 工具                    | 支援狀態 | 說明                                                                   |
| ----------------------- | -------- | ---------------------------------------------------------------------- |
| **GitHub Copilot Chat** | ✅ 必要   | 需要 VS Code 中的 GitHub Copilot Chat 擴充套件，啟用 Agent 模式        |
| **Obsidian**            | ✅ 相容   | `wiki/` 目錄可直接作為 Obsidian Vault 開啟，支援 Graph View 與雙向連結 |
| **Python 3.8+**         | ⚡ 選用   | 輔助腳本與 Hooks 的執行環境，純 Agent 使用不需要                       |
| **任意語言的 Codebase** | ✅ 通用   | 框架與語言無關，可套用到任何語言的 codebase                            |
