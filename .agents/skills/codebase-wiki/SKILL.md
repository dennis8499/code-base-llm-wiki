---
name: codebase-wiki
description: >
  Builds and maintains a persistent, structured wiki for any codebase using
  incremental LLM-driven knowledge extraction. Use this skill whenever the user
  wants to understand, document, or explore a codebase — including ingesting
  modules into the wiki, querying the knowledge base, running wiki health checks,
  creating Architecture Decision Records, generating onboarding guides, or
  performing code archaeology on legacy systems. Invoke even when the user
  mentions "文件化" "知識庫" "wiki" "ingest" "onboarding" "程式碼考古"
  "技術債" "ADR" or asks to understand how a module works, trace a feature's
  history, or get an overview of the project structure.
---

# Codebase Wiki — LLM 驅動的 Codebase 知識庫

讓 LLM 為任意 codebase 增量建構並維護結構化知識庫。
不是 RAG（每次重新檢索），而是**持久累積的 wiki 產物**——交叉引用已建立、矛盾已標記、綜合分析已反映所有已讀內容。

---

## 三層架構

| 層 | 對應 | 職責 |
|---|---|---|
| **Raw Sources** | codebase 本身 | 唯讀。LLM 讀取但**永不修改** |
| **Wiki** | `wiki/` 目錄 | LLM 產生並維護的 markdown 知識庫 |
| **Schema** | `AGENTS.md`、`.codex/`、`.agents/skills/codebase-wiki/` | 驅動 Codex 行為的規則、範本與工作流 |

---

## 適用範圍

**適用：**
- 為 codebase 建立結構化知識庫（新人 Onboarding、持續文件維護）
- 記錄架構決策（ADR）
- 追蹤遺留系統的隱含邏輯（程式碼考古）
- 跨團隊知識共享
- Wiki 健康檢查與品質維護

**不適用：**
- 修改原始碼（wiki agents 只讀不改 codebase）
- 即時程式除錯（用預設 agent）
- 測試撰寫（用專門的測試 agent）

---

## 三大操作

### 1. Ingest（知識攝入）

讀取 codebase 原始碼 → 產出結構化 wiki 頁面 → 更新 index 與 log。

兩種模式：
- **Interactive**：逐模組處理，LLM 先摘要讓使用者確認後再寫入 wiki
- **Batch**：掃描整個目錄 / glob，按依賴順序批次產出頁面

> 載入 `references/ingest-workflow.md` 取得完整 Ingest 流程步驟與判斷邏輯。

### 2. Query（知識查詢）

讀取 wiki index → 定位相關頁面 → 綜合回答 → 引用 wiki 頁面。
有價值的分析結果應存入 `wiki/synthesis/` 目錄，讓探索成果持續累積。

### 3. Lint（健康檢查）

定期檢查 wiki 品質：
- 陳舊頁面（source 已刪除/搬移）
- 孤島頁面（無 inbound link）
- 矛盾（頁面間不一致描述）
- 缺失頁面（重要模組無 wiki 頁面）
- 缺少 cross-references

> 載入 `references/lint-checklist.md` 取得完整健康檢查清單。

---

## Wiki 目錄結構

```
wiki/
├── index.md          — 主索引（LLM 自動維護）
├── log.md            — 時序活動紀錄（append-only）
├── overview.md       — codebase 高階總覽
├── architecture/     — 架構文件
├── modules/          — 按模組/目錄的文件頁面
├── entities/         — 關鍵實體（類別、服務、API 端點）
├── patterns/         — 使用到的設計模式
├── decisions/        — Architecture Decision Records (ADR)
├── dependencies/     — 相依性分析
├── guides/           — Onboarding、除錯、貢獻指南
└── synthesis/        — 綜合分析（技術債、風險區域、改善建議）
```

---

## 頁面類型與 Frontmatter

每個 wiki 頁面必須包含標準 YAML frontmatter：

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

> 載入 `references/frontmatter-spec.md` 取得各 type 的完整欄位定義。
> 載入 `references/page-types.md` 取得各頁面類型的結構範例。

---

## Cross-Referencing 規則

- 跨 wiki 頁面引用：使用 `[[page-name]]` wikilink（Obsidian 相容）
- 引用原始碼檔案：使用反引號路徑 `` `src/services/auth.ts` ``
- 每頁至少一個 outbound `[[wikilink]]`
- index.md 必須列出所有頁面

---

## 品質判斷準則

一個 wiki 頁面的品質由以下指標衡量：

1. **可追溯性**：每個事實陳述都能追溯到 `sources` 中列出的檔案
2. **連結完整性**：所有 `[[wikilink]]` 指向真實存在的頁面
3. **時效性**：`status` 反映頁面當前狀態；`last_updated` 在每次修改後更新
4. **cross-reference 密度**：關鍵概念都有對應的 wikilink
5. **結構一致性**：頁面遵循對應 type 的結構模板

---

## 禁止事項

- **不得修改 raw sources**：只能讀取 codebase，絕不修改
- **不得刪除 log 條目**：log.md 為 append-only
- **不得偽造 sources**：frontmatter.sources 必須指向真實存在的檔案
- **不得跳過 index 更新**：新增/刪除頁面後必須同步 index.md
- **不得跳過 log 記錄**：ingest / lint / 重大更新後必須追加 log 條目

---

## 快速路由

| 需要了解 | 載入 |
|---------|------|
| 各頁面類型的完整結構與範例 | `references/page-types.md` |
| Ingest 完整流程與判斷邏輯 | `references/ingest-workflow.md` |
| 健康檢查完整清單 | `references/lint-checklist.md` |
| Frontmatter 欄位完整規格 | `references/frontmatter-spec.md` |
| 頁面模板（即貼即用） | `assets/` 目錄下的各類模板 |
| 自動化工具 | `scripts/` 目錄下的 Python 腳本 |
