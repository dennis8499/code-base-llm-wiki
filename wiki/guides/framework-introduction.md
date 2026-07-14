---
title: Codebase LLM Wiki — 完整功能介紹
type: guide
sources:
  - README.md
  - AGENTS.md
  - Codex.md
  - llm-wiki.md
  - .github/copilot-instructions.md
  - .github/agents/wiki-keeper.agent.md
  - .github/agents/wiki-ingest.agent.md
  - .github/agents/wiki-query.agent.md
  - .github/agents/wiki-lint.agent.md
  - .github/agents/wiki-archaeologist.agent.md
  - .agents/skills/codebase-wiki/SKILL.md
  - .agents/skills/codebase-wiki/references/ingest-workflow.md
  - .agents/skills/codebase-wiki/capabilities.json
  - .codebase-wiki/runtime/codebase_wiki_runtime/storage.py
  - .codebase-wiki/runtime/codebase_wiki_runtime/structure.py
  - .codebase-wiki/runtime/codebase_wiki_runtime/cli.py
last_updated: 2026-07-14
tags: [guide, onboarding, framework, copilot, codex]
status: active
---

# Codebase LLM Wiki — 完整功能介紹

> 本指南詳細說明框架的所有功能、元件與使用方式。初次使用請先閱讀 [[overview]]。

---

## 目錄

1. [什麼是 Codebase LLM Wiki？](#1-什麼是-codebase-llm-wiki)
2. [核心概念：三層模型](#2-核心概念三層模型)
3. [五大 Agents](#3-五大-agents)
4. [核心操作與擴充流程](#4-核心操作與擴充流程)
5. [Hooks 自動保護機制](#5-hooks-自動保護機制)
6. [Wiki 頁面類型與規格](#6-wiki-頁面類型與規格)
7. [Slash Prompts（Copilot 版）](#7-slash-promptscopilot-版)
8. [輔助腳本](#8-輔助腳本)
9. [頁面模板](#9-頁面模板)
10. [安裝與設定](#10-安裝與設定)
11. [典型工作流程範例](#11-典型工作流程範例)
12. [相容性與整合](#12-相容性與整合)

---

## 1. 什麼是 Codebase LLM Wiki？

Codebase LLM Wiki 是一套讓 LLM（GitHub Copilot 或 OpenAI Codex）為任意 codebase 持續建構與維護結構化知識庫的框架。

### 核心思想

傳統 RAG（Retrieval Augmented Generation）每次查詢都重新從原始碼撈取片段，無法累積知識。本框架採用完全不同的方法：

**LLM 增量讀取 codebase → 轉化成結構化 Markdown wiki → 之後查詢先讀 wiki**

這使得：
- 交叉引用事先建立好，不再每次重新發現
- 矛盾與技術債已標記，不會被遺忘
- 綜合分析沉澱為持久頁面，探索成果不消失在聊天記錄裡
- LLM 做所有繁瑣的書記工作，人類負責導向與決策

### 設計靈感

源自 Vannevar Bush 的 Memex（1945）概念——私人、主動策展、文件間的連結與文件本身一樣有價值。Bush 無法解決的問題是：誰來維護？本框架的答案是：LLM。

---

## 2. 核心概念：三層模型

```
Schema 層（驅動規則）
    ↓ 讀取規則
Wiki 層（知識產物）
    ↑ 讀取 source，寫入 wiki
Raw Sources 層（唯讀原始碼）
```

| 層              | 位置                                              | 角色                                |
| --------------- | ------------------------------------------------- | ----------------------------------- |
| **Raw Sources** | 目標 codebase                                     | 唯讀。LLM 永不修改                  |
| **Wiki**        | `wiki/`                                           | LLM 產生並維護的 Markdown 知識庫    |
| **Schema**      | `.github/` / `AGENTS.md` + `.codex/` + `.agents/` | 驅動 agent 行為的規則、模板與工作流 |

---

## 3. 五大 Agents

框架提供五個專業化的 agent，各有明確職責：

### wiki-keeper — Wiki 總管

**角色**：理解使用者意圖，路由到正確的專業 agent。

**功能**：
- 接收模糊或複合請求，澄清後再路由
- 維護 wiki 整體品質與一致性
- 處理簡單查詢（無需委派）
- 建立 ADR（Architecture Decision Records）

**意圖路由表**：

| 使用者說...                             | 路由到                  |
| --------------------------------------- | ----------------------- |
| 「讀取」「分析」「文件化」「加入 wiki」 | wiki-ingest             |
| 「怎麼做」「在哪裡」「解釋」「查詢」    | wiki-query              |
| 「檢查」「健康」「品質」「陳舊」        | wiki-lint               |
| 「歷史」「為什麼這樣寫」「考古」        | wiki-archaeologist      |
| 「ADR」「決策」「架構選擇」             | wiki-keeper（自行處理） |

### wiki-ingest — 知識攝入代理

**角色**：讀取原始碼，產出結構化 wiki 頁面。

**兩種模式**：

| 模式        | 指令                    | 適用場景                           |
| ----------- | ----------------------- | ---------------------------------- |
| Interactive | `/ingest-module {path}` | 日常維護，逐模組深入，有使用者確認 |
| Batch       | `/ingest-batch {path}`  | 初始化，大範圍批次，自動執行       |

**Interactive 模式流程**：
1. 探索目錄結構與入口點
2. 向使用者報告發現（職責、相依、設計模式、風險）
3. **等待使用者確認後**才寫入
4. 建立 module / entity / pattern 頁面
5. 更新 index.md 與 log.md

**Batch 模式流程**：
1. 掃描所有子目錄，建立模組清單
2. 依賴排序（被依賴最多的先處理）
3. 逐模組批次寫入
4. 最後建立 overview.md 與 architecture/ 頁面

### wiki-query — 知識查詢代理

**角色**：先讀 wiki，再必要時回溯原始碼，回答問題。

**查詢流程**：
1. 讀 `wiki/index.md` 定位相關頁面
2. 讀取 1-5 個最相關 wiki 頁面
3. 若 wiki 不足或過時，回溯 `sources` 中列出的原始碼驗證
4. 回答時標注引用來源（`[[wikilink]]` + 檔案路徑）
5. 若分析有長期價值，提供儲存至 `wiki/synthesis/` 的選項

**Hand-Off（行動交接）功能**：
查詢完成後，若發現可跟進的問題，wiki-query 會提供行動清單：
- `save-synthesis`：儲存分析至 wiki/synthesis/
- `re-ingest`：對過時頁面重新攝入
- `lint-fix`：修復品質問題

### wiki-lint — 健康檢查代理

**角色**：定期審計 wiki 品質，找出問題並建議修復。

**8 大檢查項目**：

| #   | 項目                   | 說明                               |
| --- | ---------------------- | ---------------------------------- |
| 1   | Stale Pages            | frontmatter sources 路徑是否仍存在 |
| 2   | Orphan Pages           | 是否有頁面缺少 inbound wikilink    |
| 3   | Broken Links           | `[[wikilink]]` 目標是否存在        |
| 4   | Missing Pages          | 重要模組是否尚未文件化             |
| 5   | Frontmatter Validation | 必填欄位與 enum 是否正確           |
| 6   | Contradictions         | 多頁面描述同一實體時是否矛盾       |
| 7   | Index Completeness     | 實際頁面是否都列入 index.md        |
| 8   | Coverage Report        | wiki 覆蓋率統計                    |

**自動修復**（使用者確認後）：
- 將失效 sources 的頁面標記為 `stale`
- 修正明顯的 broken wikilinks
- 補齊 index.md 缺失條目

### wiki-archaeologist — 程式碼考古代理

**角色**：透過 git history 與程式碼追蹤，發現隱含業務規則與設計脈絡。

**適用場景**：
- 「為什麼這段程式碼這樣寫？」
- 追蹤某功能的演進歷史
- 發現 legacy code 的隱含假設
- 識別技術債的根源

**考古流程**：
1. 定位功能入口點（路由、event handler、CLI）
2. 沿呼叫鏈逐層追蹤
3. 使用 `git log`、`git blame`、`git show` 取得歷史證據
4. 清楚區分「證據支持」與「推測」
5. 產出考古報告，建立/更新相關 wiki 頁面

**輸出格式**：
- 功能路徑文件（`wiki/modules/` 或 `wiki/entities/`）
- 隱含業務規則（`wiki/patterns/` 或 `wiki/synthesis/`）
- 技術債標記（`wiki/synthesis/technical-debt-{area}.md`）
- Architecture Decision Records（`wiki/decisions/`）

---

## 4. 核心操作與擴充流程

### Ingest（知識攝入）

讀取原始碼，建立 wiki 頁面，是最核心的操作。每次 ingest 可能觸及 5-15 個頁面的建立或更新。

### Query（知識查詢）

先查 wiki 再回溯 sources。有價值的分析可存入 `wiki/synthesis/`，讓探索成果持續累積。

### Lint（健康檢查）

週期性審計。發現問題後先輸出報告，使用者確認後才執行自動修復。

### Archaeology（程式碼考古）

追蹤歷史脈絡。結合 git history 與程式碼分析，回答「為什麼」的問題。

### ADR（架構決策記錄）

建立 `wiki/decisions/` 下的決策文件，記錄背景、選擇、替代方案與影響。

### Synthesis / Guide（綜合分析與指南）

從已有 wiki 內容提煉：
- `wiki/synthesis/`：技術債分析、風險評估、架構總結
- `wiki/guides/`：Onboarding 指南、除錯指南、貢獻指南

### System Analysis / SA（系統分析）

基於既有 wiki 頁面產出結構化系統分析文件，寫入
`wiki/synthesis/`，並將 coverage gaps 明確標示為待補證據，不臆測缺失行為。

### Delegation（明確委派）

只有使用者明確要求 delegation、parallel 或 subagents 時，才使用
`.codex/agents/*.toml` 或對應的 Copilot agents；一般 wiki 工作由目前 agent
直接處理。

路由規則以 `intent-routing.md` 的 9 類使用者意圖為準；機器可讀的
`capabilities.json` 會將 Synthesis 與 Guide 分成兩個可寫入 capability，這是
執行契約的拆分，不是額外的路由類別。

---

## 5. Hooks 自動保護機制

框架提供三個自動化 Hook，在背景默默保護 wiki 品質：

### wiki-write-guard（寫入保護）

- **觸發時機**：任何寫入操作前（PreToolUse）
- **作用**：攔截超出 `wiki/` 邊界的寫入，防止誤改 raw sources
- **行為**：直接回傳 `permissionDecision`，拒絕違規寫入

### wiki-session-init（Session 初始化）

- **觸發時機**：每次 Session 啟動時（SessionStart）
- **作用**：摘要 `wiki/index.md` 與 `wiki/log.md` 的最新狀態
- **行為**：Copilot 產出稽核工件到 `.github/hooks/logs/wiki-session-state.md`；Codex 優先寫 `.codex/hooks/logs/wiki-session-state.md`，若 Windows ACL 擋住則退到 `.codex-hook-logs/wiki-session-state.md`

### wiki-log-reminder（Log 提醒）

- **觸發時機**：wiki 頁面被修改後（PostToolUse）
- **作用**：提醒補上 `wiki/log.md` 條目
- **行為**：Copilot 寫入 `.github/hooks/logs/wiki-log-reminder.jsonl`；Codex 優先寫 `.codex/hooks/logs/wiki-log-reminder.jsonl`，若 Windows ACL 擋住則退到 `.codex-hook-logs/wiki-log-reminder.jsonl`

**Copilot 版設定檔**：
- `wiki-write-guard.json`
- `wiki-session-init.json`
- `wiki-log-reminder.json`

**Codex 版設定檔**：
- `.codex/hooks.json`（三個 hook 集中管理）

---

## 6. Wiki 頁面類型與規格

### 頁面類型

| type           | 目錄                 | 說明                                |
| -------------- | -------------------- | ----------------------------------- |
| `module`       | `wiki/modules/`      | 對應 codebase 中的邏輯模組          |
| `entity`       | `wiki/entities/`     | 關鍵實體（類別、服務、API、資料表） |
| `pattern`      | `wiki/patterns/`     | 重複出現的設計結構                  |
| `decision`     | `wiki/decisions/`    | Architecture Decision Records       |
| `dependency`   | `wiki/dependencies/` | 重要外部相依性                      |
| `guide`        | `wiki/guides/`       | Onboarding / 除錯 / 貢獻指南        |
| `synthesis`    | `wiki/synthesis/`    | 綜合分析、技術債、風險評估          |
| `overview`     | `wiki/`              | 高階總覽                            |
| `architecture` | `wiki/architecture/` | 架構文件                            |
| `index`        | `wiki/`              | 主索引（`index.md`）                |
| `log`          | `wiki/`              | 活動紀錄（`log.md`）                |

### 標準 Frontmatter

```yaml
---
title: 頁面標題
type: module | entity | pattern | ...（見上表）
sources:
  - path/to/source/file.ts   # 必須是真實存在的路徑
last_updated: YYYY-MM-DD
tags: [tag1, tag2]
status: active | stale | placeholder
---
```

**ADR 額外欄位**：
```yaml
decision_date: YYYY-MM-DD
decision_status: proposed | accepted | deprecated | superseded
```

### Cross-Reference 規則

- 跨 wiki 頁面引用使用 `[[page-name]]` wikilink（Obsidian 相容）
- 引用原始碼使用反引號路徑 `` `src/services/auth.ts` ``
- 每頁至少一個 outbound wikilink
- `wiki/index.md` 必須列出所有頁面

---

## 7. Slash Prompts（Copilot 版）

Copilot 版提供 11 個 slash prompts，可在 VS Code Copilot Chat 中直接呼叫；Copilot CLI 使用 agents、skills 或自然語言：

| Prompt                    | 功能                           |
| ------------------------- | ------------------------------ |
| `/ingest-module {path}`   | Interactive 模式攝入單一模組   |
| `/ingest-batch {path}`    | Batch 模式批次攝入目錄         |
| `/query-wiki {question}`  | 查詢 wiki 知識庫               |
| `/lint-wiki`              | 執行完整 wiki 健康檢查         |
| `/new-adr {title}`        | 建立架構決策記錄               |
| `/onboarding-guide`       | 產出 Onboarding 指南           |
| `/save-synthesis {topic}` | 儲存綜合分析至 wiki/synthesis/ |
| `/save-guide {topic}`      | 儲存操作指南至 wiki/guides/      |
| `/code-archaeology {target}` | 追蹤目前行為與 Git history       |
| `/system-analysis-doc {scope}` | 產出 SA 系統分析文件          |
| `/update-index`           | 手動重建 wiki/index.md         |

Codex 版不偽造 project-level custom slash prompts。Codex IDE / CLI 的 slash commands 是平台控制命令；本框架在 Codex 端以自然語言 recipe 達成同等流程：

| Copilot prompt | Codex recipe |
| --- | --- |
| `/ingest-module {path}` | `請依照 AGENTS.md 的 Interactive Ingest 流程，分析 {path}，先摘要主要職責、相依關係與風險，再更新 wiki。` |
| `/ingest-batch {path}` | `請依照 AGENTS.md 的 batch ingest 流程掃描 {path}，建立初始 wiki，最後更新 index 與 log。` |
| `/query-wiki {question}` | `請先查 wiki，再必要時回溯 sources，回答：{question}` |
| `/lint-wiki` | `請依 AGENTS.md 的 lint 流程檢查 wiki 健康狀態，列出 critical 和 warning。` |
| `/new-adr {title}` | `請建立一份 ADR：{title}，寫入 wiki/decisions/，並同步更新 index 與 log。` |
| `/onboarding-guide` | `請根據目前 wiki 內容產出一份 onboarding guide，存到 wiki/guides/，並更新 index 與 log。` |
| `/save-synthesis {topic}` | `請把這次分析整理成 wiki/synthesis/{topic} 頁面，保留來源並更新 index 與 log。` |
| `/update-index` | `請重新掃描 wiki/ 目錄，依現有 frontmatter 重建 wiki/index.md，並追加 wiki/log.md。` |

---

## 8. 輔助腳本

位於 `.agents/skills/codebase-wiki/scripts/`，Copilot 與 Codex 共用同一份 helper scripts；搜尋 Runtime 位於 `.codebase-wiki/runtime/`，**無需全域安裝套件**：

| 腳本               | 功能                                              |
| ------------------ | ------------------------------------------------- |
| `check-stale.py`   | 批次檢查 frontmatter sources 是否仍存在           |
| `rebuild-index.py` | 重建 `wiki/index.md`                              |
| `wiki-stats.py`    | 產出 wiki 統計報告（頁面數、類型分佈、近期更新）  |
| `frontmatter.py`   | 無依賴的 frontmatter 解析函式庫（供其他腳本引用） |
| `parity-check.py`  | 驗證 Copilot/Codex capability 與路徑契約           |
| `structure-index.py` | 舊版 JSON 結構索引腳本（建議改用共用 CLI）          |
| `tree-sitter-preflight.py` | 舊版 grammar 檢查腳本（建議改用 `doctor`）      |

**使用方式**：
```bash
python .agents/skills/codebase-wiki/scripts/check-stale.py wiki/
python .agents/skills/codebase-wiki/scripts/wiki-stats.py wiki/
python .agents/skills/codebase-wiki/scripts/rebuild-index.py wiki/
```

---

## 9. 頁面模板

位於 `.agents/skills/codebase-wiki/assets/`，提供即用型頁面模板：

| 模板                  | 對應頁面類型 |
| --------------------- | ------------ |
| `module-template.md`  | Module 頁面  |
| `entity-template.md`  | Entity 頁面  |
| `pattern-template.md` | Pattern 頁面 |
| `adr-template.md`     | ADR 頁面     |
| `index-template.md`   | index.md     |
| `log-template.md`     | log.md       |

---

## 10. 安裝與設定

### GitHub Copilot 版（最小安裝）

```bash
cp -r .github/ /path/to/your-repo/.github/
cp -r wiki/ /path/to/your-repo/wiki/
```

前提條件：
- 已安裝並登入 GitHub Copilot Chat
- 已啟用 Agent 模式
- 可在 `.github/agents/` 看到五個 wiki agents

### OpenAI Codex 版（最小安裝）

```bash
cp AGENTS.md /path/to/your-repo/AGENTS.md
cp -r .codex/ /path/to/your-repo/.codex/
mkdir -p /path/to/your-repo/.agents/skills/
cp -r .agents/skills/codebase-wiki/ /path/to/your-repo/.agents/skills/codebase-wiki/
cp -r wiki/ /path/to/your-repo/wiki/
```

Codex 版必要元件：
- `AGENTS.md`（主要專案指令）
- `.codex/config.toml`（啟用 hooks）
- `.codex/hooks.json`（hook 事件設定）
- `.agents/skills/codebase-wiki/`（repo-local skill）
- `wiki/`（知識庫骨架）

### 驗收清單

- [ ] `AGENTS.md` 在 repo root
- [ ] `.codex/config.toml` 與 `.codex/hooks.json` 存在
- [ ] `.agents/skills/codebase-wiki/SKILL.md` 存在
- [ ] `wiki/index.md`、`wiki/log.md`、`wiki/overview.md` 存在
- [ ] 能成功用自然語言執行一次 ingest 或 query

---

## 11. 典型工作流程範例

### 情境一：初始化全新專案的 wiki

**Copilot**：
```text
/ingest-batch src/
```

**Codex**（自然語言，無需 slash prompt）：
```text
請依照 AGENTS.md 的 batch ingest 流程掃描 src/，建立初始 wiki，最後更新 index 與 log。
```

### 情境二：新功能上線後做增量更新

```text
請分析 src/features/checkout/，先摘要主要職責、相依關係與風險，再更新 wiki。
```

### 情境三：查詢特定功能

```text
請先查 wiki，再必要時回溯 sources，解釋 PaymentService 的退款流程。
```

### 情境四：週期性健康檢查

```text
請依 lint 流程檢查 wiki 健康狀態，列出 critical 和 warning。
```

### 情境五：追蹤 legacy 程式碼歷史

```text
請用 code archaeology 追蹤 discount_code 欄位的 git history，清楚區分證據與推測，最後更新 wiki。
```

### 情境六：記錄架構決策

```text
請建立一份 ADR，說明為什麼在結帳流程中採用 Saga Pattern，寫入 wiki/decisions/，並同步更新 index 與 log。
```

### 情境七：產出 Onboarding 指南

```text
請根據目前 wiki 內容產出一份 onboarding guide，存到 wiki/guides/，並更新 index 與 log。
```

---

## 12. 相容性與整合

| 平台                                 | 支援程度                                      |
| ------------------------------------ | --------------------------------------------- |
| GitHub Copilot（VS Code Agent 模式） | ✅ 完整支援（含 slash prompts、hooks、agents） |
| OpenAI Codex CLI                     | ✅ 完整支援（AGENTS.md + .codex/）             |
| OpenAI Codex IDE Extension           | ✅ 支援                                        |
| OpenAI Codex Cloud Tasks             | ✅ 支援                                        |
| Obsidian                             | ✅ wikilink 語法相容，graph view 可視化        |
| Marp                                 | ✅ 可從 wiki 內容產出 Markdown 簡報            |
| Obsidian Dataview                    | ✅ 可查詢頁面 frontmatter                      |
| Python                               | 需要 3.11+（Runtime 與輔助腳本的共同基線）     |

### Windows 相容性

所有 Python 輔助腳本已處理 Windows UTF-8 終端輸出問題（CP950 主控台相容性修正）。

---

## 相關頁面

- [[overview]] — 專案高階總覽
