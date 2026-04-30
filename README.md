# Codebase LLM Wiki

> 讓 GitHub Copilot 或 OpenAI Codex 為任意 codebase 增量建構並維護結構化知識庫。

[![License: MIT](https://img.shields.io/badge/License-MIT-yellow.svg)](LICENSE)
[![GitHub Copilot](https://img.shields.io/badge/GitHub%20Copilot-Supported-blue?logo=github)](https://github.com/features/copilot)
[![OpenAI Codex](https://img.shields.io/badge/OpenAI%20Codex-Supported-111827?logo=openai)](https://openai.com/index/introducing-codex/)
[![VS Code](https://img.shields.io/badge/VS%20Code-Extension-007ACC?logo=visualstudiocode)](https://code.visualstudio.com/)
[![Python](https://img.shields.io/badge/Python-3.8%2B-3776AB?logo=python)](https://www.python.org/)
[![Obsidian Compatible](https://img.shields.io/badge/Obsidian-Compatible-7C3AED?logo=obsidian)](https://obsidian.md/)

---

## 目錄

- [Codebase LLM Wiki](#codebase-llm-wiki)
  - [目錄](#目錄)
  - [這是什麼？](#這是什麼)
  - [核心概念](#核心概念)
  - [支援版本](#支援版本)
  - [前置需求](#前置需求)
  - [安裝與設定](#安裝與設定)
    - [GitHub Copilot 版](#github-copilot-版)
    - [OpenAI Codex 版](#openai-codex-版)
  - [快速開始](#快速開始)
  - [使用方式](#使用方式)
    - [Agent 對話（推薦）](#agent-對話推薦)
    - [Codex 自然語言工作流](#codex-自然語言工作流)
    - [Slash Prompt 指令](#slash-prompt-指令)
    - [輔助腳本](#輔助腳本)
  - [元件說明](#元件說明)
    - [Agents](#agents)
      - [wiki-keeper 意圖路由邏輯](#wiki-keeper-意圖路由邏輯)
    - [Skill](#skill)
    - [Hooks](#hooks)
    - [Codex Instructions](#codex-instructions)
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
  - [變更紀錄](#變更紀錄)

---

## 這是什麼？

**Codebase LLM Wiki** 是一套面向 coding agents 的自訂化框架，讓 GitHub Copilot 或 OpenAI Codex 扮演技術文件架構師的角色，持續為你的 codebase 建立、更新並維護一座結構化的 Markdown 知識庫。

Copilot 版透過自訂 Agent、Prompt、Hook 與 Skill 運作；Codex 版則透過根目錄 `AGENTS.md` 收斂同一套 wiki 方法論，讓 Codex 在 CLI、IDE 或雲端任務中可以依照相同規格行動。

這**不是 RAG**（每次重新檢索原始碼）。而是**持久累積的知識庫**——讀過的模組被記錄成頁面，交叉引用持續建立，矛盾會被標記，綜合分析反映所有已讀內容。

```
你問：「OrderService 的退款邏輯在哪裡？」
LLM：直接從 wiki 取出已整理好的知識，附帶可追溯的原始碼引用。
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
│  Schema       ← 驅動 LLM 行為的規則與工作流       │
│               Copilot: .github/ agents/prompts/   │
│               hooks/skills                        │
│               Codex: AGENTS.md                    │
└─────────────────────────────────────────────────┘
```

| 層              | 位置          | 職責                           |
| --------------- | ------------- | ------------------------------ |
| **Raw Sources** | codebase 本身 | 唯讀。LLM 只讀取，**永不修改** |
| **Wiki**        | `wiki/`       | LLM 產出的 Markdown 知識庫     |
| **Schema**      | `.github/` 或 `AGENTS.md` | 規則、工作流、範本             |

---

## 支援版本

| 版本 | 入口檔案 | 適合情境 |
| ---- | -------- | -------- |
| **GitHub Copilot 版** | `.github/copilot-instructions.md`、`.github/agents/`、`.github/prompts/`、`.github/hooks/`、`.github/skills/` | 你想在 VS Code Copilot Chat 中使用自訂 agent、slash prompt 與 hook |
| **OpenAI Codex 版** | `AGENTS.md` | 你想讓 Codex CLI、IDE extension、Codex app 或 cloud task 直接讀取專案規則 |
| **共用 wiki 骨架** | `wiki/` | 兩種版本共用的知識庫輸出位置 |

你只需要選擇其中一個入口使用；兩者可共存於同一 repo，但不互相依賴。

---

## 前置需求

| 需求 | 版本 | 說明 |
| ---- | ---- | ---- |
| [GitHub Copilot Chat](https://marketplace.visualstudio.com/items?itemName=GitHub.copilot-chat) | 最新版 | Copilot 版需要，並需啟用 Agent 模式 |
| [OpenAI Codex](https://platform.openai.com/docs/codex) | 最新版 | Codex 版需要，可使用 CLI、IDE extension、Codex app 或 cloud task |
| [VS Code](https://code.visualstudio.com/) | 最新版 | Copilot 版主要編輯器；Codex IDE extension 也可使用 |
| [Python](https://www.python.org/) | 3.8+ | 輔助腳本與 Copilot Hooks 執行環境（非必要） |

> **注意：** 使用輔助腳本（`rebuild-index.py` 等）或 Hooks 時需要 Python，但目前不需要額外安裝 `PyYAML` 等第三方套件。純 Agent / Prompt / Codex `AGENTS.md` 使用不需要 Python。

---

## 安裝與設定

### GitHub Copilot 版

```bash
# 複製 .github/ 目錄（框架核心）
cp -r .github/ /path/to/your-repo/.github/

# 複製 wiki/ 骨架目錄
cp -r wiki/ /path/to/your-repo/wiki/
```

> 如果你的 repo 已有 `.github/` 目錄，請手動合併 `agents/`、`prompts/`、`hooks/`、`skills/` 等子目錄。

在 VS Code 中開啟你的 repo，確認以下設定已啟用：

- **GitHub Copilot Chat** 擴充套件已安裝並登入
- Copilot Chat 的 **Agent 模式**已開啟（Chat 視窗中可切換 Agent 下拉選單）

開啟 Copilot Chat，點選 Agent 下拉選單，應可看到：

- `wiki-keeper`
- `wiki-ingest`
- `wiki-query`
- `wiki-lint`
- `wiki-archaeologist`

若看不到這些 Agent，請確認 `.github/agents/` 目錄下的 `.agent.md` 檔案存在。

### OpenAI Codex 版

```bash
# 複製 Codex 專用指令檔到目標 repo 根目錄
cp AGENTS.md /path/to/your-repo/AGENTS.md

# 複製 wiki/ 骨架目錄
cp -r wiki/ /path/to/your-repo/wiki/

# 可選：若想沿用頁面模板與 Python 輔助腳本，複製共用 skill 資料夾
mkdir -p /path/to/your-repo/.github/skills/
cp -r .github/skills/codebase-wiki/ /path/to/your-repo/.github/skills/codebase-wiki/
```

Codex 會讀取 repo 內的 `AGENTS.md` 作為專案操作規則。開始任務時直接用自然語言描述需求即可，不需要切換 agent 或輸入 slash prompt。

---

## 快速開始

**Copilot 版**：開啟 Copilot Chat 並切換到 **`wiki-keeper`** agent，然後：

```
把 src/auth/ 模組加進 wiki
```

**Codex 版**：在 Codex CLI、IDE extension、Codex app 或 cloud task 中直接輸入：

```
請依照 Codebase LLM Wiki 的 ingest 流程，把 src/auth/ 模組加進 wiki
```

就這樣。Copilot 版會由 `wiki-keeper` 自動分析意圖並呼叫適合的子 agent；Codex 版會依照 `AGENTS.md` 中的意圖路由與工作流程行動，並在 `wiki/` 目錄下建立結構化的文件頁面。

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

### Codex 自然語言工作流

Codex 版沒有 Copilot 的 `.agent.md` manifest 與 slash prompt；所有路由邏輯都寫在 `AGENTS.md`，因此直接描述任務即可。

**攝入程式碼：**
```
請以 Codebase LLM Wiki 的 ingest 流程，分析 src/auth/ 並更新 wiki。
```

**查詢知識：**
```
請先查 wiki，再必要時回溯 sources，解釋 OrderService 的退款邏輯。
```

**健康檢查：**
```
請依 AGENTS.md 的 lint 流程檢查 wiki 健康狀態，列出 critical 和 warning。
```

**程式碼考古：**
```
請用 code archaeology 流程追蹤 discount_code 欄位的 git history，並把有價值的結論存進 wiki。
```

---

### Slash Prompt 指令

此區為 **GitHub Copilot 版專用**。在 Copilot Chat 輸入 `/` 可叫出 Prompt 指令：

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

位於 `.github/skills/codebase-wiki/scripts/`，可獨立在終端機執行。Copilot 版的 agents 與 Codex 版的 `AGENTS.md` 都會在需要時引用這些腳本（若已複製到目標 repo）：

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

Copilot 版包含 5 個專業 agent，各司其職：

| Agent                | 檔案                          | 職責                                                                                                                                                       |
| -------------------- | ----------------------------- | ---------------------------------------------------------------------------------------------------------------------------------------------------------- |
| `wiki-keeper`        | `wiki-keeper.agent.md`        | **路由器**。分析使用者意圖，派發到正確的子 agent。所有入口從這裡開始                                                                                       |
| `wiki-ingest`        | `wiki-ingest.agent.md`        | **攝入專家**。讀取原始碼，以互動或批次模式產出結構化 wiki 頁面                                                                                             |
| `wiki-query`         | `wiki-query.agent.md`         | **知識導航員**。搜尋 wiki 回答問題，可追溯到原始碼；重要分析可存入 synthesis。支援 **Hand-Off** 自動交接：建議行動經使用者確認後，自動委派給對應子代理執行 |
| `wiki-lint`          | `wiki-lint.agent.md`          | **品質審計員**。執行 8 項健康檢查：陳舊頁面、孤島頁面、斷裂連結、缺失 frontmatter 等                                                                       |
| `wiki-archaeologist` | `wiki-archaeologist.agent.md` | **程式碼考古師**。透過 git log 追蹤歷史、揭露隱含邏輯、分析技術債成因                                                                                      |

這些 agent manifest 的 `tools` 欄位採用 inline array 寫法（例如 `tools: [read, edit, search]`），方便快速比較各代理的能力邊界；只有確實需要的能力才會加入，例如 `execute`、`agent` 與 `vscode/askQuestions`。

agent 的協作與路由規則目前寫在各自的 Markdown 說明內容中，而不是依賴非官方 frontmatter 欄位；這樣能和現行 GitHub Copilot custom agents schema 保持一致。

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

Hooks 是 Copilot 版的自動觸發保護機制，在 repository 範圍內於 Copilot 執行工具前後自動運行：

| Hook 檔案                | 觸發時機       | 設定型式                                                                                     | 職責                                                                 |
| ------------------------ | -------------- | -------------------------------------------------------------------------------------------- | -------------------------------------------------------------------- |
| `wiki-write-guard.json`  | `preToolUse`   | `version: 1` + `type: command`，分別宣告 `bash` / `powershell`                              | 攔截寫入操作，拒絕對 `wiki/`、`.github/` 以外路徑的寫入（保護原始碼） |
| `wiki-log-reminder.json` | `postToolUse`  | `version: 1` + `type: command`，分別宣告 `bash` / `powershell`                              | 偵測到 `wiki/` 頁面被修改後，寫入 `.github/hooks/logs/wiki-log-reminder.jsonl` 稽核線索 |
| `wiki-session-init.json` | `sessionStart` | `version: 1` + `type: command`，分別宣告 `bash` / `powershell`                              | Session 開始時擷取 wiki 狀態摘要到 `.github/hooks/logs/wiki-session-state.md` |

> GitHub Copilot 的 hook 輸出目前不會把 `postToolUse` 或 `sessionStart` 的文字直接注入 agent context，所以這兩個 hook 會產生稽核工件，而不是回傳 `systemMessage`。

---

### Codex Instructions

Codex 版的入口是根目錄 `AGENTS.md`。它把 Copilot 版分散在 agents/prompts/instructions 裡的規則收斂成一份 Codex 可直接讀取的專案指令。

| 檔案 | 職責 |
| ---- | ---- |
| `AGENTS.md` | 定義 Codex 的 wiki 任務邊界、意圖路由、Ingest / Query / Lint / Archaeology / ADR 工作流程、frontmatter 規格與禁止事項 |
| `wiki/` | Codex 寫入與維護的 Markdown 知識庫 |
| `.github/skills/codebase-wiki/` | 可選的共用範本、reference 文件與 Python 輔助腳本；Codex 不會自動把它當成 skill 載入，但可依 `AGENTS.md` 指示讀取或執行 |

Codex 版不依賴 Copilot 的 custom agents、slash prompts 或 hooks；如果兩套檔案同時存在，Codex 會以 `AGENTS.md` 為主要入口。

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
type: module | entity | pattern | decision | dependency | guide | synthesis | overview | architecture | index | log
sources:
  - path/to/source/file.ts   # 必須是真實存在的路徑
  - path/to/another/file.py
last_updated: YYYY-MM-DD
tags: [tag1, tag2]
status: active | stale | placeholder
---
```

`index.md` 與 `log.md` 也屬於正式頁面類型，分別使用 `type: index`、`type: log`；若沒有直接對應的 raw source，需寫成 `sources: []`，而不是省略該欄位。

| 欄位           | 必填 | 說明                                                     |
| -------------- | ---- | -------------------------------------------------------- |
| `title`        | ✅    | 頁面標題                                                 |
| `type`         | ✅    | 頁面類型（影響 agent 的分類與 lint 行為）                |
| `sources`      | ✅    | 引用的原始碼路徑清單，必須真實存在                       |
| `last_updated` | ✅    | 最後更新日期（`YYYY-MM-DD`）                             |
| `tags`         | ✅    | 標籤清單，用於分類與搜尋                                 |
| `status`       | ✅    | `active`（現行）/ `stale`（過時）/ `placeholder`（待補） |

ADR 類型另有兩個專屬欄位：`decision_date` 與 `decision_status`。其中 `decision_status` 表示決策狀態（例如 `accepted`），`status` 仍只表示頁面生命週期。

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

Copilot 版：

```bash
# 1. 套用框架
cp -r .github/ your-repo/
cp -r wiki/ your-repo/

# 2. 在 Copilot Chat 中執行
/ingest-batch src/         # 批次掃描整個 src 目錄
/onboarding-guide          # 自動產生新人指南
/update-index              # 重建主索引
```

Codex 版：

```bash
# 1. 套用框架
cp AGENTS.md your-repo/AGENTS.md
cp -r wiki/ your-repo/
```

在 Codex 中描述任務：

```
請依照 AGENTS.md 的 batch ingest 流程掃描 src/，建立初始 wiki，最後更新 index 與 log。
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
| **LLM 永不修改原始碼** | wiki agents / Codex 在 wiki 任務中對 codebase 只讀不寫；Copilot 版的 `wiki-write-guard` hook 會攔截越界寫入 |
| **Log 為 append-only** | `log.md` 只能追加新條目，不得修改或刪除既有條目                          |
| **Sources 可追溯**     | 每個 wiki 頁面的 `frontmatter.sources` 必須指向真實存在的檔案路徑        |
| **Wiki 完整性**        | 新增或刪除 wiki 頁面後，必須同步更新 `wiki/index.md`                     |
| **增量建構**           | 不需要一次讀完整個 codebase，可按模組逐步累積知識                        |

---

## 目錄結構總覽

```
AGENTS.md                                — OpenAI Codex 版專案指令
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
│   ├── wiki-write-guard.json             — 寫入保護（preToolUse）
│   ├── wiki-log-reminder.json            — Log 稽核（postToolUse）
│   ├── wiki-session-init.json            — Session 初始化（sessionStart）
│   ├── logs/                             — Hook 執行期稽核輸出（git ignore）
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
            ├── frontmatter.py            — 內建 frontmatter parser
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
| **GitHub Copilot Chat** | ✅ 支援   | Copilot 版需要 VS Code 中的 GitHub Copilot Chat 擴充套件，啟用 Agent 模式 |
| **OpenAI Codex**        | ✅ 支援   | Codex 版使用 `AGENTS.md` 作為入口，可在 CLI、IDE extension、Codex app 或 cloud task 中使用 |
| **Obsidian**            | ✅ 相容   | `wiki/` 目錄可直接作為 Obsidian Vault 開啟，支援 Graph View 與雙向連結 |
| **Python 3.8+**         | ⚡ 選用   | 輔助腳本與 Hooks 的執行環境，純 Agent / `AGENTS.md` 使用不需要，且目前不依賴第三方 Python 套件 |
| **任意語言的 Codebase** | ✅ 通用   | 框架與語言無關，可套用到任何語言的 codebase                            |

---

## 變更紀錄

詳見 [ChangeLog.md](ChangeLog.md)。
