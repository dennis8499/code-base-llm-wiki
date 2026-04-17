# Codebase LLM Wiki

> 讓 GitHub Copilot 為任意 codebase 增量建構並維護結構化知識庫。

---

## 這是什麼？

Codebase LLM Wiki 是一套 **GitHub Copilot 自訂化框架**，透過自訂 Agent、Prompt、Hook 與 Skill，讓 Copilot 扮演技術文件架構師的角色，持續為你的 codebase 建立、更新並維護一座結構化的 Markdown wiki。

這**不是 RAG**（每次重新檢索原始碼）。而是**持久累積的知識庫**——讀過的模組被記錄成頁面，交叉引用持續建立，矛盾會被標記，綜合分析反映所有已讀內容。

---

## 三層架構

```
┌─────────────────────────────────────────────┐
│ Raw Sources  ← 唯讀。codebase 原始碼與設定檔  │
├─────────────────────────────────────────────┤
│ Wiki         ← LLM 產生並維護的 Markdown 知識庫 │
│              wiki/ 目錄（index、modules、ADR 等）│
├─────────────────────────────────────────────┤
│ Schema       ← 驅動 LLM 行為的 Copilot 元件   │
│              .github/ 底下的 agents/prompts/   │
│              hooks/skills                     │
└─────────────────────────────────────────────┘
```

| 層 | 位置 | 職責 |
|---|---|---|
| **Raw Sources** | codebase 本身 | 唯讀。LLM 只讀取，**永不修改** |
| **Wiki** | `wiki/` | LLM 產出的 Markdown 知識庫 |
| **Schema** | `.github/` | 規則、工作流、範本 |

---

## 快速開始

### 將框架套用到你的 codebase

1. **複製 `.github/` 目錄**到你的 repo 根目錄
2. **複製 `wiki/` 骨架目錄**到你的 repo 根目錄
3. 在 VS Code 中開啟該 repo，確認 GitHub Copilot Chat 已啟用
4. 在 Copilot Chat 中切換到 `wiki-keeper` agent（或直接使用 prompt）

> 不需要修改任何 `.github/` 的設定，框架是**通用設計**，開箱即用。

---

## 使用方式

### Agent 對話（推薦）

在 Copilot Chat 選擇 **`wiki-keeper`** agent 後直接以自然語言描述需求：

```
把 src/auth/ 模組加進 wiki
```
```
解釋一下 OrderService 的退款邏輯
```
```
幫我檢查 wiki 有沒有品質問題
```
```
我要記錄一個架構決策：為什麼選 PostgreSQL
```

`wiki-keeper` 會自動判斷意圖並路由到對應的專業 agent。

---

### Prompt 指令

| Prompt | 用途 | 輸入參數 |
|--------|------|---------|
| `/ingest-module` | 互動式攝入單一模組 | `modulePath`（模組路徑） |
| `/ingest-batch` | 批次掃描整個目錄 | `targetPath`（目標路徑） |
| `/query-wiki` | 向 wiki 提問 | `question`（問題） |
| `/lint-wiki` | 執行 wiki 健康檢查 | — |
| `/new-adr` | 建立 Architecture Decision Record | `decisionTitle`（決策標題） |
| `/onboarding-guide` | 自動產生新人 Onboarding 指南 | — |
| `/update-index` | 重建 wiki 主索引 | — |

**範例：**
```
/ingest-module src/payment/
/new-adr 選擇 gRPC 取代 REST 作為 service-to-service 通訊協定
/query-wiki 用戶登入流程的整個呼叫鏈是什麼？
```

---

## 元件一覽

### Agents（5 個）

| Agent | 職責 |
|-------|------|
| `wiki-keeper` | 路由器，分析意圖並派發到正確 agent |
| `wiki-ingest` | 讀取原始碼，產出結構化 wiki 頁面 |
| `wiki-query` | 搜尋 wiki 回答問題，可追溯到原始碼 |
| `wiki-lint` | 健康檢查：陳舊頁面、孤島頁面、斷裂連結等 8 項 |
| `wiki-archaeologist` | 程式碼考古：透過 git log 追蹤歷史、揭露隱含邏輯 |

### Skill

| Skill | 職責 |
|-------|------|
| `codebase-wiki` | 主方法論。包含頁面類型規格、工作流程、lint 清單、frontmatter 規格、6 個頁面範本與 3 個輔助腳本 |

### Hooks（保護機制）

| Hook | 類型 | 職責 |
|------|------|------|
| `wiki-write-guard` | `preToolUse` | 攔截寫入操作，防止 agent 意外修改 `wiki/` 以外的檔案 |
| `wiki-log-reminder` | `postToolUse` | 修改 wiki 頁面後提醒 agent 更新 `log.md` |

### 輔助腳本

| 腳本 | 用途 |
|------|------|
| `rebuild-index.py` | 掃描 `wiki/` 重建 `index.md` |
| `check-stale.py` | 驗證 `frontmatter.sources` 中的路徑是否仍存在 |
| `wiki-stats.py` | 統計頁面數量、類型分佈、wikilink 密度、覆蓋率 |

---

## Wiki 目錄結構

```
wiki/
├── index.md          — 主索引（LLM 自動維護）
├── log.md            — 時序活動紀錄（append-only）
├── overview.md       — codebase 高階總覽
├── architecture/     — 系統架構、部署架構、資料流
├── modules/          — 按模組/目錄的文件頁面
├── entities/         — 關鍵類別、服務、API 端點
├── patterns/         — 使用到的設計模式
├── decisions/        — Architecture Decision Records (ADR)
├── dependencies/     — 相依性分析
├── guides/           — Onboarding、除錯、貢獻指南
└── synthesis/        — 技術債、風險區域、改善建議
```

每個 wiki 頁面都有標準 YAML frontmatter：

```yaml
---
title: 頁面標題
type: module | entity | pattern | decision | dependency | guide | synthesis | overview | architecture
sources:
  - path/to/source/file.ts
last_updated: YYYY-MM-DD
tags: [tag1, tag2]
status: active | stale | placeholder
---
```

跨頁引用使用 **Wikilink 語法** `[[page-name]]`（與 Obsidian 相容）。

---

## 典型工作流程

### 初始化新專案 wiki

```
1. 複製框架到 repo
2. /ingest-batch src/         ← 批次掃描整個 src 目錄
3. /onboarding-guide          ← 自動產生新人指南
4. /update-index              ← 重建主索引
```

### 持續維護

```
# 新模組上線後
/ingest-module src/new-feature/

# 做出重要架構決策後
/new-adr 為什麼採用 Event Sourcing

# 定期健康檢查
/lint-wiki
```

### 知識查詢

```
# 理解某段邏輯
/query-wiki PaymentService 如何處理退款？

# 深挖歷史（切換到 wiki-archaeologist agent）
為什麼這段重試邏輯要用指數退避而不是固定間隔？
```

---

## 框架設計原則

- **LLM 永不修改原始碼** — wiki agents 對 codebase 只讀不寫
- **Log 為 append-only** — `log.md` 只能追加，不得修改或刪除條目
- **Sources 可追溯** — 每個 wiki 頁面的 `sources` 必須指向真實存在的檔案
- **Wiki 完整性** — 新增或刪除頁面後必須同步更新 `index.md`
- **增量建構** — 不需要一次讀完整個 codebase，可按模組逐步累積

---

## 相容性

- **GitHub Copilot** — 需要 VS Code 中的 GitHub Copilot Chat 擴充套件
- **Obsidian** — `wiki/` 目錄可直接作為 Obsidian Vault 開啟，支援 Graph View
- **Python** — 輔助腳本需要 Python 3.8+（非必要，僅輔助用）

---

## 目錄結構總覽

```
.github/
├── copilot-instructions.md          — 全域規則（wiki 慣例、禁止事項）
├── instructions/
│   └── wiki-pages.instructions.md  — 套用至 wiki/**/*.md 的頁面規則
├── agents/
│   ├── wiki-keeper.agent.md
│   ├── wiki-ingest.agent.md
│   ├── wiki-query.agent.md
│   ├── wiki-lint.agent.md
│   └── wiki-archaeologist.agent.md
├── prompts/
│   ├── ingest-module.prompt.md
│   ├── ingest-batch.prompt.md
│   ├── query-wiki.prompt.md
│   ├── lint-wiki.prompt.md
│   ├── new-adr.prompt.md
│   ├── onboarding-guide.prompt.md
│   └── update-index.prompt.md
├── hooks/
│   ├── wiki-write-guard.json
│   ├── wiki-log-reminder.json
│   └── scripts/
│       ├── wiki-write-guard.py
│       └── wiki-log-reminder.py
└── skills/
    └── codebase-wiki/
        ├── SKILL.md
        ├── references/
        │   ├── page-types.md
        │   ├── ingest-workflow.md
        │   ├── lint-checklist.md
        │   └── frontmatter-spec.md
        ├── assets/
        │   └── (6 個頁面範本)
        └── scripts/
            ├── rebuild-index.py
            ├── check-stale.py
            └── wiki-stats.py
wiki/
├── index.md
├── log.md
├── overview.md
└── (8 個子目錄)
```
