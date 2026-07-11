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
- [Codex 版完整使用範例](#codex-版完整使用範例)
- [Codex Workflow 功能範例（逐項）](#codex-workflow-功能範例逐項)
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

| 文件                         | 用途                                                 |
| ---------------------------- | ---------------------------------------------------- |
| [README.md](README.md)       | 專案總覽，說明 Copilot 與 Codex 兩種入口的定位與結構 |
| [Codex.md](Codex.md)         | 給框架使用者的 Codex 專用安裝、操作、排錯手冊        |
| [AGENTS.md](AGENTS.md)       | 給 Codex 讀取的機器指令，定義 wiki 邊界、流程與規則  |
| [ChangeLog.md](ChangeLog.md) | 框架版本變更紀錄                                     |
| [llm-wiki.md](llm-wiki.md)   | 這套方法論的原始概念說明                             |
| [prompt.txt](prompt.txt)     | 早期設計此框架時使用的提示草稿                       |

如果你是第一次接觸這個 repo，建議先讀 `README.md`；如果你要把這套框架套到自己的 repo 並用 Codex 操作，接著讀 [Codex.md](Codex.md)。

---

## 三層模型

| 層              | 位置                                                      | 職責                                        |
| --------------- | --------------------------------------------------------- | ------------------------------------------- |
| **Raw Sources** | 目標 codebase 的原始碼、設定檔、既有文件                  | 唯讀。wiki 任務中只讀取、不修改             |
| **Wiki**        | `wiki/`                                                   | LLM 產生並維護的 Markdown 知識庫            |
| **Schema**      | `.github/` 或 `AGENTS.md` + `.codex/` + `.agents/skills/` | 驅動 agent 行為的規則、模板、腳本與工作流程 |

---

## 支援入口

| 入口                  | 主要檔案                                                                                                      | 適合情境                                                                                                                                                     |
| --------------------- | ------------------------------------------------------------------------------------------------------------- | ------------------------------------------------------------------------------------------------------------------------------------------------------------ |
| **GitHub Copilot 版** | `.github/copilot-instructions.md`、`.github/agents/`、`.github/prompts/`、`.github/hooks/`、`.github/skills/` | 你想在 VS Code Copilot Chat 中使用自訂 agent、slash prompt、hook，並讓 `wiki-query` 在可用時透過 VS Code MSSQL tools 取得唯讀資料庫證據                      |
| **OpenAI Codex 版**   | `AGENTS.md`、`.codex/config.toml`、`.codex/hooks.json`、`.codex/agents/`、`.agents/skills/codebase-wiki/`     | 你想讓 Codex CLI、IDE extension、Codex app 或 cloud task 直接讀取專案規則與 repo-local skill；Codex query 流程會同步遵守 SQL Server live evidence 的唯讀規則 |
| **共用 Wiki 骨架**    | `wiki/`                                                                                                       | 兩種版本共用的知識庫輸出位置                                                                                                                                 |

你可以只選其中一條路線，也可以讓兩套檔案共存於同一個 repo。本框架採 **雙入口同權維護**：Copilot 與 Codex 共享同一組 wiki 能力、邊界、安全規則與驗收結果，但各自使用平台原生入口。

### Copilot ↔ Codex 功能對照

| 能力          | GitHub Copilot                              | OpenAI Codex                    |
| ------------- | ------------------------------------------- | ------------------------------- |
| 全域規則      | `.github/copilot-instructions.md`           | `AGENTS.md`                     |
| 專業代理      | `.github/agents/*.agent.md`                 | `.codex/agents/*.toml`          |
| 使用者入口    | `.github/prompts/*.prompt.md` slash prompts | `Codex.md` 內的自然語言 recipe  |
| Workflow 細節 | `.github/skills/codebase-wiki/`             | `.agents/skills/codebase-wiki/` |
| Hooks         | `.github/hooks/*.json`                      | `.codex/hooks.json`             |
| 輸出          | `wiki/`                                     | `wiki/`                         |

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
- `.github/hooks/logs/`：Copilot hooks 的稽核輸出位置。
- `.github-hook-logs/`：若 `.github/hooks/logs/` 無法寫入，Copilot hooks 會退到這個 root-level ignored 目錄。

---

## 安裝與設定

### GitHub Copilot 版

```bash
cp -r .github/ /path/to/your-repo/.github/
cp -r wiki/ /path/to/your-repo/wiki/
```

安裝到目標 codebase 後，請將 `.github/hooks/config.toml` 的
`[wiki_guard] mode` 設為 `"target"`。只有維護本框架 repo 時才使用
`"framework"`。

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

安裝到目標 codebase 後，請將 `.codex/config.toml` 的
`[wiki_guard] mode` 設為 `"target"`。只有維護本框架 repo 時才使用
`"framework"`。

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
/save-guide 本機開發環境設定
/update-index
```

**Codex**

```text
請依照 AGENTS.md 的 batch ingest 流程掃描 src/，建立初始 wiki，最後更新 index 與 log。
請根據目前的 wiki 內容產出一份 onboarding guide，存到 wiki/guides/，並更新 index 與 log。
請把本機開發環境設定整理成 wiki/guides/ 指南，標示來源、gap 與可操作步驟，並更新 index 與 log。
```

更多 Codex 寫法可參考 [Codex.md](Codex.md)。

### 情境二：新功能上線後更新 wiki

**Copilot**

```text
/ingest-module src/features/checkout/
/new-adr 為什麼在結帳流程中採用 Saga Pattern
/save-synthesis 結帳流程跨服務依賴分析
/system-analysis-doc 結帳流程
```

**Codex**

```text
請依照 AGENTS.md 的 Interactive Ingest 流程，分析 src/features/checkout/，先摘要主要職責、相依關係與風險，再更新 wiki。

請建立一份 ADR，說明為什麼在結帳流程中採用 Saga Pattern，寫入 wiki/decisions/，並同步更新 index 與 log。

請把這次對結帳流程跨服務依賴的分析整理成 wiki/synthesis/ 頁面，保留來源並更新 index 與 log。

請基於目前 wiki 內容產出結帳流程的 SA 系統分析文件，寫入 wiki/synthesis/checkout-flow-system-analysis.md，標示 coverage gaps，並更新 index 與 log。
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
/code-archaeology discount_code
/save-synthesis 折扣碼設計演進分析
```

**Codex**

```text
請用 code archaeology 流程追蹤 discount_code 欄位的 git history，清楚區分證據與推測，最後更新 wiki。
請把這次分析整理成一份 synthesis 頁面，並更新 index 與 log。
```

## Codex 版完整使用範例

這一節示範一個團隊把 Codebase LLM Wiki 套到既有 repo 後，如何用 Codex 完成「初始化、查詢、沉澱、健康檢查、委派」的一輪實際操作。範例使用自然語言 prompt，不使用 Copilot slash prompt files。

### 範例 A：把框架安裝到目標 repo

**使用情境**

你有一個既有專案 `my-service/`，想讓 Codex 開始維護 `wiki/`，但不希望 wiki 任務誤改原始碼。

**複製 Codex 版必要元件**

```powershell
Copy-Item AGENTS.md C:\work\my-service\AGENTS.md
New-Item -ItemType Directory -Force C:\work\my-service\.agents\skills | Out-Null
Copy-Item -Recurse .agents\skills\codebase-wiki C:\work\my-service\.agents\skills\codebase-wiki
Copy-Item -Recurse .codex C:\work\my-service\.codex
Copy-Item -Recurse wiki C:\work\my-service\wiki
```

**在 Codex 中開啟目標 repo 後先確認**

```text
請確認目前 repo 已載入 AGENTS.md，並列出你看到的 Codebase LLM Wiki 邊界規則與可用的 $codebase-wiki skill。不要修改任何檔案。
```

**預期結果**

- Codex 會指出 raw sources 在 wiki 任務中唯讀。
- Codex 會辨識 `wiki/` 是輸出層。
- Codex 會知道長流程在 `.agents/skills/codebase-wiki/`。
- 若 `.codex/` hooks 尚未被信任，Codex 會仍可依 `AGENTS.md` 工作，但自動 guard/reminder 可能尚未啟用。

**驗收**

```powershell
Test-Path C:\work\my-service\AGENTS.md
Test-Path C:\work\my-service\.codex\hooks.json
Test-Path C:\work\my-service\.agents\skills\codebase-wiki\SKILL.md
Test-Path C:\work\my-service\wiki\index.md
Test-Path C:\work\my-service\wiki\log.md
```

### 範例 B：第一次初始化 wiki

**使用情境**

你剛把框架裝好，想讓 Codex 掃描 `src/`，建立初始 wiki。

**Prompt**

```text
請使用 $codebase-wiki，依照 AGENTS.md 的 batch ingest 流程掃描 src/。
先列出你會處理的主要模組與依賴順序，然後建立初始 wiki。
完成後請更新 wiki/index.md、追加 wiki/log.md，並回報建立與更新的頁面清單。
```

**預期 Codex 行為**

- 先讀 `wiki/index.md` 與 `wiki/log.md`。
- 掃描 `src/` 的入口點、README、export/import、路由、service、model、config。
- 依依賴關係或目錄結構排序。
- 建立或更新 `wiki/modules/`，必要時補 `wiki/entities/`、`wiki/patterns/`、`wiki/dependencies/`。
- 建立或更新 `wiki/overview.md` 與 `wiki/architecture/`，前提是 source evidence 足夠。
- 更新 `wiki/index.md` 並追加 `wiki/log.md`。

**驗收重點**

- 每個新增 wiki 頁面都有完整 frontmatter。
- `sources` 都是 repo 相對路徑且真實存在。
- `wiki/index.md` 能導覽到所有新增頁面。
- `wiki/log.md` 末尾有 `## [YYYY-MM-DD] ingest | ...` 條目。
- 原始碼目錄如 `src/` 沒有被修改。

### 範例 C：新功能上線後做增量維護

**使用情境**

`src/features/checkout/` 剛上線，你想把結帳流程的模組責任、跨服務依賴和設計取捨沉澱下來。

**Prompt 1：互動式 ingest**

```text
請使用 $codebase-wiki，對 src/features/checkout/ 執行 Interactive Ingest。
先只做探索與摘要，說明：
1. 模組核心職責
2. 主要入口點與公開介面
3. 依賴哪些模組、被誰依賴
4. 偵測到的設計模式
5. 需要我確認的風險或模糊點
在我確認前不要寫入 wiki。
```

**Prompt 2：確認後寫入**

```text
摘要方向正確。請建立或更新 checkout 相關 wiki 頁面，補上 cross-references，更新 wiki/index.md，並追加 wiki/log.md。
```

**Prompt 3：建立 ADR**

```text
請建立一份 ADR，記錄結帳流程採用 Saga Pattern 的原因。
內容需要包含背景、替代方案、決策、理由、後果與後續追蹤。
寫入 wiki/decisions/，並同步更新 index 與 log。
```

**預期產出**

- `wiki/modules/checkout.md` 或相近 slug 的 module page。
- 重要 service/controller/entity 的 `wiki/entities/*.md`。
- 若 Saga Pattern 有明確 source evidence，新增或更新 `wiki/patterns/saga-pattern.md`。
- 新增 `wiki/decisions/adr-*.md`。
- `wiki/index.md` 和 `wiki/log.md` 同步更新。

### 範例 D：wiki-first 查詢並保存長期分析

**使用情境**

你想理解退款流程，並把跨模組分析保存起來。

**Prompt 1：只查詢，不寫檔**

```text
請先查 wiki，再必要時回溯 sources，解釋 PaymentService 如何處理退款。
回答請列出 Wiki 引用與 source path。這一步不要修改檔案。
```

**Prompt 2：保存成 synthesis**

```text
這份分析有長期價值。請整理成 wiki/synthesis/payment-refund-flow.md。
請保留來源、補上相關 wikilink、更新 wiki/index.md，並追加 wiki/log.md。
```

**預期行為**

- Query 階段優先讀 `wiki/index.md` 與 1-5 個相關頁面。
- 只有 wiki 不足、過時或矛盾時，才依 `sources` 回溯原始碼。
- 保存 synthesis 前，Codex 會把分析整理成結構化頁面，而不是直接貼上聊天回答。

**驗收重點**

- 查詢回答明確列出 `[[wiki-page]]` 和 source path。
- `wiki/synthesis/payment-refund-flow.md` 的 `sources` 不偽造不存在路徑。
- synthesis 頁面至少連回相關 module/entity 頁面。

### 範例 E：使用 SQL Server live evidence

**使用情境**

你需要確認 wiki/source 對 Orders 資料表的描述是否和目前資料庫 schema 一致。

**Prompt**

```text
請先查 wiki，再判斷是否需要 SQL Server live evidence。
如果目前 Codex 環境有 MSSQL 工具，請只做 schema discovery、metadata lookup 或 bounded read-only SELECT。
說明 Orders 資料表和 PaymentService 退款流程的關係。
若沒有 MSSQL 工具，請先明確告知，不要猜測資料庫現況。
```

**預期回答**

- 有工具時：回答包含 wiki/source 引用與 DB evidence metadata。
- 無工具時：Codex 會說明目前無法取得 live evidence，並詢問是否改走 Copilot、MCP、CLI 或其他 fallback。

**DB evidence metadata 必須包含**

```text
connected_at
source_tool
server
database
query_scope
result_limit
row_count
freshness_note
```

**重要限制**

- 禁止 DML、DDL、`EXEC`、stored procedure execution。
- 禁止無限制全表掃描。
- DB evidence 不可寫入 wiki frontmatter `sources`；若要保存，只能放在正文 evidence block。

### 範例 F：健康檢查與安全修復

**使用情境**

一次 batch ingest 後，你想確認 wiki 沒有 stale source、broken link 或 index 漏列。

**Prompt**

```text
請依 AGENTS.md 的 lint 流程檢查 wiki 健康狀態。
請先產出報告，依 Critical、Warning、Info 分級。
在我確認前，不要做大範圍自動修復。
```

**可搭配的本機驗證**

```powershell
python .agents\skills\codebase-wiki\scripts\check-stale.py wiki\
python .agents\skills\codebase-wiki\scripts\validate-frontmatter.py wiki\
python .agents\skills\codebase-wiki\scripts\wiki-stats.py wiki\
python .agents\skills\codebase-wiki\scripts\check-dual-entry-sync.py
```

**確認後的修復 Prompt**

```text
請修復報告中的 Critical 問題：
1. 標記 sources 全部失效的頁面為 stale
2. 修正明確 broken wikilink
3. 重建 wiki/index.md
完成後追加 wiki/log.md。
```

**驗收重點**

- Codex 不刪除 wiki 頁面，只標記 stale 或提出人工處理建議。
- 修復後重新跑 `check-stale.py`、`validate-frontmatter.py` 和 `wiki-stats.py`。
- `wiki/log.md` 有 lint 條目。

### 範例 G：明確要求 custom agents 委派

**使用情境**

你有大型變更，希望同時做 ingest 與 lint，再由主 agent 整合。

**Prompt**

```text
請使用 Codex delegation，明確委派兩個子任務：
1. 使用 wiki-ingest 分析 src/features/checkout/
2. 使用 wiki-lint 檢查整個 wiki 的健康狀態
兩個任務都完成後，請回到主 agent 整合結果，列出應先處理的問題與建議下一步。
```

**預期行為**

- Codex 只有在這種明確要求下才使用 `.codex/agents/*.toml`。
- `wiki-ingest` 負責 source-backed wiki 更新。
- `wiki-lint` 負責 health report。
- 主 agent 負責整合與決策，不讓子代理無限制 fan-out。

**驗收重點**

- 子代理仍遵守 raw sources 唯讀。
- 若有 wiki 寫入，index/log 仍要同步。
- 若只是查詢或報告，不應產生不必要檔案變更。

### 範例 H：完整交付前檢查

在你準備提交 Codex 版 wiki 更新前，可以要求 Codex 做最後檢查：

```text
請檢查這次 wiki/schema 變更是否符合 AGENTS.md：
1. raw sources 是否保持唯讀
2. 新增 wiki 頁面的 frontmatter 是否完整
3. sources 是否真實存在
4. wikilink 是否指向存在頁面
5. wiki/index.md 是否同步
6. wiki/log.md 是否追加
7. 是否有任何推測沒有標記
請列出通過項目與仍需人工確認的項目。
```

也可以搭配：

```powershell
python .agents\skills\codebase-wiki\scripts\check-stale.py wiki\
python .agents\skills\codebase-wiki\scripts\validate-frontmatter.py wiki\
python .agents\skills\codebase-wiki\scripts\wiki-stats.py wiki\
```

如果你要逐項查看每個 Codex workflow 功能的「何時用、怎麼下 prompt、會產生什麼結果、如何驗收」，請看下一節。

## Codex Workflow 功能範例（逐項）

> 以下範例都假設你在 Codex CLI、IDE extension、Codex app 或 cloud task 中操作，並要求流程遵守 `AGENTS.md` 與 `$codebase-wiki` skill。

### 1. Interactive Ingest（單一模組）

**何時使用**
- 你剛修改了某個模組，想把該模組的責任、相依、風險增量寫入 wiki。

**Prompt（可直接貼上）**
```text
請依照 AGENTS.md 的 Interactive Ingest 流程，分析 src/auth/，先摘要主要職責、相依關係與風險，再更新 wiki。
```

**預期產出**
- 新增或更新 `wiki/modules/*.md`，必要時補 `wiki/entities/*.md`、`wiki/patterns/*.md`。
- 同步更新 `wiki/index.md`。
- 追加 `wiki/log.md`：`## [YYYY-MM-DD] ingest | src/auth/`。

**驗收重點**
- 新頁面 frontmatter 完整（`title/type/sources/last_updated/tags/status`）。
- `sources` 都是存在的 repo 相對路徑。
- 至少有一個有效 `[[wikilink]]` 連到相關頁面。

**注意事項**
- wiki 任務中 raw sources 唯讀，不可改 `src/` 原始碼。

### 2. Batch Ingest（目錄批次攝入）

**何時使用**
- 專案剛導入框架，或你要一次掃描一個大型目錄建立初始 wiki。

**Prompt（可直接貼上）**
```text
請依照 AGENTS.md 的 batch ingest 流程掃描 src/，建立初始 wiki，最後更新 index 與 log。
```

**預期產出**
- 批次建立/更新 modules、entities、patterns、dependencies 類頁面。
- `wiki/index.md` 收錄新頁面。
- `wiki/log.md` 追加一筆批次 ingest 紀錄。

**驗收重點**
- 新增頁面都可由 `wiki/index.md` 導航到。
- 無孤兒頁面（至少被 index 或其他頁面引用）。
- `sources` 無失效路徑。

**注意事項**
- 大範圍 ingest 先摘要再寫入，避免長任務 context drift。

### 3. Query（wiki-first）

**何時使用**
- 想知道某個功能怎麼運作，優先讀既有 wiki，必要時才回溯原始碼。

**Prompt（可直接貼上）**
```text
請先查 wiki，再必要時回溯 sources，解釋 PaymentService 如何處理退款。
```

**預期產出**
- 回答會先引用 `[[wiki-page]]`，不足處再補 source path 證據。
- 預設不改任何檔案。

**驗收重點**
- 回答中有明確來源（wikilink 或路徑）。
- 會指出 wiki 不足或過時處，而不是直接猜測。

**注意事項**
- 只有在你明確要求保存時，才應把 query 結果寫成 `wiki/synthesis/`。

### 4. Query + SQL Server Live Evidence（唯讀資料庫證據）

**何時使用**
- 需要確認「wiki/source 描述」和「資料庫現況」是否一致。

**Prompt（可直接貼上）**
```text
請先查 wiki，再必要時使用可用的 SQL Server 工具取得唯讀 live evidence，說明 Orders 資料表和 PaymentService 的退款流程有什麼關係。
```

**預期產出**
- 回答包含 wiki/source 引用，並附 DB evidence metadata：`connected_at`、`source_tool`、`server`、`database`、`query_scope`、`result_limit`、`row_count`、`freshness_note`。
- 若當前環境沒有 MSSQL 工具，會先明確告知並詢問是否改走 Copilot、MCP、CLI 或其他 fallback。

**驗收重點**
- 查詢操作保持唯讀（僅 schema/metadata/bounded SELECT）。
- 回答內沒有把 DB 證據寫成 frontmatter `sources`。

**注意事項**
- 禁止 DML、DDL、`EXEC`、stored procedure execution 與無限制全表掃描。

### 5. Lint（wiki 健康檢查）

**何時使用**
- 要做交付前健康檢查，或懷疑 wiki 有斷鏈、過時來源、frontmatter 異常。

**Prompt（可直接貼上）**
```text
請依 AGENTS.md 的 lint 流程檢查 wiki 健康狀態，列出 critical 和 warning。
```

**預期產出**
- 回傳健康報告：stale sources、broken links、orphan pages、index completeness 等。
- 先給修復建議，不會直接大範圍改檔。

**驗收重點**
- finding 有分級（Critical/Warning/Info）。
- 大修前會先確認，不會直接自動重寫大量頁面。

**注意事項**
- lint 不應改動 raw sources。

### 6. Archaeology（程式碼考古）

**何時使用**
- 你想追「為什麼這樣寫」或「某欄位何時加入、設計脈絡是什麼」。

**Prompt（可直接貼上）**
```text
請用 code archaeology 流程追蹤 discount_code 欄位的 git history，清楚區分證據與推測，最後更新 wiki。
```

Copilot 可使用：

```text
/code-archaeology discount_code
```

**預期產出**
- 以入口點 + 呼叫鏈 + git history 證據形成解釋。
- 若要求持久化，更新對應 wiki 頁面並同步 index/log。

**驗收重點**
- 內容清楚區分 evidence-supported 與 speculation。
- 使用非破壞性 git 指令（例如 `git log`、`git blame`、`git show`）。

**注意事項**
- 不可使用破壞性 git 指令（`reset`、`checkout`、`clean`、`rebase`）。

### 7. ADR（架構決策紀錄）

**何時使用**
- 功能有明確設計取捨，需要可追溯決策文件。

**Prompt（可直接貼上）**
```text
請建立一份 ADR，說明為什麼在結帳流程中採用 Saga Pattern，寫入 wiki/decisions/，並同步更新 index 與 log。
```

**預期產出**
- 新增 `wiki/decisions/{slug}.md`。
- ADR frontmatter 包含 `decision_date` 與 `decision_status`。
- `wiki/index.md` 與 `wiki/log.md` 同步更新。

**驗收重點**
- ADR 內容至少包含背景、決策、替代方案、影響與取捨、後續追蹤。
- `decision_status` 使用有效值（`proposed/accepted/deprecated/superseded`）。

**注意事項**
- 沒有直接 raw source 時，frontmatter `sources` 應使用 `[]`。

### 8. Synthesis（長期知識沉澱）

**何時使用**
- 查詢或分析結果具有長期價值，適合沉澱成跨頁整合知識。

**Prompt（可直接貼上）**
```text
請把這次對結帳流程跨服務依賴的分析整理成 wiki/synthesis/ 頁面，保留來源並更新 index 與 log。
```

**預期產出**
- 新增或更新 `wiki/synthesis/*.md`。
- 補齊 cross-references，並更新 index/log。

**驗收重點**
- 內容有清楚來源（wiki pages / source paths / evidence blocks）。
- 不是重複貼上 query 回答，而是有整理後的結構化知識。

**注意事項**
- DB-derived evidence 若需保留，放正文 evidence block，不進 frontmatter `sources`。

### 9. Guide（Onboarding / 操作指南）

**何時使用**
- 要給新人或跨團隊讀者一份可直接上手的導覽。

**Prompt（可直接貼上）**
```text
請根據目前 wiki 內容產出一份 onboarding guide，存到 wiki/guides/，並更新 index 與 log。
```

通用 guide 可使用：

```text
請把本機開發環境設定整理成 wiki/guides/ 指南，標示來源、gap 與可操作步驟，並更新 index 與 log。
```

Copilot 可使用 `/onboarding-guide` 或 `/save-guide {topic}`；前者保留給新人導覽，後者用於除錯、操作、runbook、維運或其他 durable guide。

**預期產出**
- 新增 `wiki/guides/*.md`，涵蓋核心模組、閱讀順序、常見流程。
- `wiki/index.md` 與 `wiki/log.md` 更新。

**驗收重點**
- 指南可獨立閱讀，不依賴讀者先知道內部脈絡。
- 關鍵術語與流程都有對應 wikilink。

**注意事項**
- 指南內容需可追溯來源，避免生成不可驗證結論。

### 10. System Analysis / SA（系統分析文件）

**何時使用**
- 要把既有 wiki 知識整理成可交付的 SA 系統分析文件。

**Prompt（可直接貼上）**
```text
請基於目前 wiki 內容產出整體系統的 SA 系統分析文件，寫入 wiki/synthesis/system-analysis.md，標示 coverage gaps，並更新 index 與 log。
```

**預期產出**
- 新增或更新 `wiki/synthesis/system-analysis.md`，指定範圍時使用 `wiki/synthesis/{kebab-scope}-system-analysis.md`。
- frontmatter 使用 `type: synthesis` 與 `tags: [synthesis, system-analysis]`。
- 文件涵蓋目的與範圍、系統總覽、架構與元件、模組職責、主要流程、API/介面、資料流、外部整合、權限安全、設定維運、非功能需求、錯誤模式、風險與待確認事項。

**驗收重點**
- 來源優先使用 wiki，只有在不足、過時或矛盾時才回溯 raw sources。
- 沒有可靠證據的章節標示 `待補` / `Gap`，並列出建議後續 ingest 目標。
- `wiki/index.md` 與 `wiki/log.md` 同步更新。

**注意事項**
- 預設只輸出 Markdown；Word/PDF 匯出屬於後續獨立任務。
- 不新增 `wiki/sa/` 目錄，也不新增 `type: sa`。

### 11. Delegation（明確要求才用 Custom Agents）

**何時使用**
- 你明確要求 spawn / 委派 / subagents / parallel agent work。

**Prompt（可直接貼上）**
```text
請使用 delegation，把這次工作拆成兩條平行子任務：
1) 委派 wiki-ingest 分析 src/features/checkout/
2) 委派 wiki-lint 做全站健康檢查
最後整合結果並提出修復優先順序。
```

**預期產出**
- 主 agent 委派 `.codex/agents/*.toml` 專業代理執行子任務。
- 回傳整合後摘要與下一步建議。

**驗收重點**
- 沒有明確委派需求時，維持主 agent + `$codebase-wiki` skill，避免不必要 token 成本。
- 委派結果仍遵守 `AGENTS.md` 邊界（raw sources 唯讀、index/log 規則）。

**注意事項**
- custom agents 是「可委派元件」，不是日常必切換入口。

### 最小驗收清單（Codex 版）

```text
1) 任一 ingest/ADR/synthesis/guide/system-analysis 任務後，wiki/index.md 與 wiki/log.md 是否同步更新？
2) 新頁面 frontmatter 是否完整且 sources 真實存在（或合理使用 sources: []）？
3) query 是否先用 wiki，再必要時才回溯 sources？
4) 涉及 SQL Server 時是否保持唯讀，且回答附 evidence metadata？
5) 未明確要求 delegation 時，是否避免不必要 spawn custom agents？
```

---

## 資料庫 Live Evidence

`wiki-query` 現在支援在查詢流程中納入 SQL Server live evidence，用來回答「wiki / source 描述」和「目前資料庫 schema 或資料」之間的關係。

| 入口           | 行為                                                                                                                                                         |
| -------------- | ------------------------------------------------------------------------------------------------------------------------------------------------------------ |
| GitHub Copilot | `.github/agents/wiki-query.agent.md` 宣告 VS Code Microsoft SQL Server extension tools；當工具可用時，可查 schema、metadata 與有界線的唯讀 `SELECT`          |
| OpenAI Codex   | `AGENTS.md` 與 `.codex/agents/wiki-query.toml` 同步定義相同行為；當 Codex 環境沒有 MSSQL tool 時，必須先詢問使用者是否改走 Copilot、MCP、CLI 或其他 fallback |

共同規則：

共同規則以 `references/mssql-evidence-rules.md` 為準。摘要：只允許 schema discovery、metadata lookup、connection details 與 bounded read-only `SELECT`；禁止 DML、DDL、`EXEC`、stored procedure execution、無限制全表掃描與任何會改變資料庫狀態的操作；DB-derived 回答必須標註 reference 規定的 metadata，且 DB 證據不得寫入 wiki frontmatter `sources`。

---

## 元件一覽

### Copilot 版

| 元件    | 位置                            | 用途                                                                                                                                               |
| ------- | ------------------------------- | -------------------------------------------------------------------------------------------------------------------------------------------------- |
| Agents  | `.github/agents/`               | `wiki-keeper` 等 5 個專業 agent，負責路由、ingest、query、lint、archaeology；`wiki-query` 可在 VS Code MSSQL tools 可用時取得唯讀 DB live evidence |
| Prompts | `.github/prompts/`              | `/ingest-module`、`/lint-wiki`、`/code-archaeology`、`/save-guide`、`/save-synthesis`、`/system-analysis-doc` 等對話入口                           |
| Hooks   | `.github/hooks/`                | 寫入保護、稽核提醒與 `config.toml` guard mode                                                                                                      |
| Skill   | `.github/skills/codebase-wiki/` | 共用模板、reference 文件與 `validate-frontmatter.py` / `check-dual-entry-sync.py` 等腳本                                                           |

### Codex 版

| 元件              | 位置                                                               | 用途                                                                                                                                                  |
| ----------------- | ------------------------------------------------------------------ | ----------------------------------------------------------------------------------------------------------------------------------------------------- |
| Root instructions | `AGENTS.md`                                                        | Codex 讀取的主要規則、流程與禁止事項                                                                                                                  |
| Repo-local skill  | `.agents/skills/codebase-wiki/`                                    | 模板、reference 文件與輔助腳本                                                                                                                        |
| Hooks             | `.codex/config.toml`、`.codex/hooks.json`、`.codex/hooks/scripts/` | SessionStart 狀態摘要、寫入保護、log reminder；`config.toml` 內設定 guard mode                                                                        |
| Custom agents     | `.codex/agents/`                                                   | 可委派的 specialized agents；只在明確要求 delegation 或 parallel agent work 時使用；`wiki-query` 內建 SQL Server live evidence 的唯讀與 fallback 規則 |

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

完整規格以 `references/frontmatter-spec.md` 為準。每個 wiki 頁面都應包含：

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

ADR、Dependency、Index、Log 的類型專屬欄位以 `frontmatter-spec.md` 為準。ADR 頁面另外需要：

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

| 工具                | 支援狀態 | 說明                                                    |
| ------------------- | -------- | ------------------------------------------------------- |
| GitHub Copilot Chat | ✅ 支援   | 使用 `.github/` 內的 agents、prompts、hooks、skills     |
| OpenAI Codex        | ✅ 支援   | 使用 `AGENTS.md`、`.codex/`、`.agents/skills/` 作為入口 |
| VS Code             | ✅ 支援   | Copilot 與 Codex IDE extension 都可使用                 |
| Python 3.8+         | ⚡ 選用   | hooks 與輔助腳本需要；純自然語言流程不一定需要          |
| Obsidian            | ✅ 相容   | `wiki/` 可直接當作 Vault 使用                           |
| 任意語言的 codebase | ✅ 通用   | 框架不依賴特定程式語言                                  |

---

## 變更紀錄

詳見 [ChangeLog.md](ChangeLog.md)。
