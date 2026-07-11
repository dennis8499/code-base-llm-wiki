# Copilot Instructions — Codebase LLM Wiki

## 技術背景 (WHAT)

本倉庫是一套 **Codebase LLM Wiki 框架**——讓 LLM 為任意 codebase 增量建構並維護結構化知識庫。
框架由 `.github/` 底下的 Copilot 自訂化元件驅動，產出儲存於 `wiki/` 目錄。

### 三層架構

| 層 | 對應 | 職責 |
|---|---|---|
| Raw Sources | codebase 本身（原始碼、設定檔、既有文件） | 唯讀。LLM 讀取但**永不修改** |
| Wiki | `wiki/` 目錄 | LLM 產生並維護的 markdown 知識庫 |
| Schema | `.github/` 底下的 Copilot 元件 | 驅動 LLM 行為的規則與工作流 |

## Wiki 慣例 (HOW)

### 意圖路由

完整 9 類意圖以
`.github/skills/codebase-wiki/references/intent-routing.md` 為準：
Install / setup、Ingest、Query、Lint、ADR、Synthesis / Guide、
System Analysis / SA、Archaeology、Delegation。SQL Server live evidence 是
Query 子模式，不是獨立意圖。

### 命名與連結

- 頁面檔名使用 **kebab-case**：`user-auth-service.md`、`database-migration-pattern.md`
- 跨頁引用使用 **Wikilink 語法**：`[[page-name]]`（Obsidian 相容）
- 提到其他 wiki 頁面時**必須**使用 wikilink，不使用相對路徑連結

### 目錄結構

```
wiki/
├── index.md          — 主索引（LLM 自動維護）
├── log.md            — 時序活動紀錄（append-only）
├── overview.md       — codebase 高階總覽
├── architecture/     — 架構文件（系統架構、部署架構、資料流）
├── modules/          — 按模組/目錄的文件頁面
├── entities/         — 關鍵實體（類別、服務、API 端點）
├── patterns/         — 使用到的設計模式
├── decisions/        — Architecture Decision Records (ADR)
├── dependencies/     — 相依性分析
├── guides/           — Onboarding、除錯、貢獻指南
└── synthesis/        — 綜合分析（技術債、風險區域、改善建議、SA 系統分析文件）
```

### Frontmatter 標準

完整規格以 `.github/skills/codebase-wiki/references/frontmatter-spec.md`
為準。每個 wiki 頁面的 YAML frontmatter 至少必須包含：

```yaml
---
title: 頁面標題
type: module | entity | pattern | decision | dependency | guide | synthesis | overview | architecture | index | log
sources:
  - path/to/source/file.ts
  - path/to/another/file.py
last_updated: YYYY-MM-DD
tags: [tag1, tag2]
status: active | stale | placeholder
---
```

`wiki/index.md` 與 `wiki/log.md` 也必須包含上述欄位；若沒有直接 raw source，使用 `sources: []`。
ADR、Dependency、Index、Log 的類型專屬欄位與 allowed values 以
`frontmatter-spec.md` 為準。

### 品質標準

- 每頁必須在 `sources` 中標註引用的原始碼檔案路徑
- 每頁至少要有一個 inbound 或 outbound `[[wikilink]]`
- `status` 欄位必須反映頁面當前狀態
- 事實陳述必須可追溯到 sources 中列出的檔案

### Log 格式

`log.md` 為 append-only，每筆條目格式：

```markdown
## [YYYY-MM-DD] {operation} | {subject}

- 簡要描述變更內容
- 列出受影響的頁面
```

operation 以 `.github/skills/codebase-wiki/references/log-operations.md`
為準：`ingest|query|lint|update|init|adr|synthesis|guide|archaeology`。

## 禁止事項

禁止事項以 `.github/skills/codebase-wiki/SKILL.md` 的 **Core Rules** 為
準；本段是摘要。

- **不得修改 raw sources**：wiki agents 只能讀取 codebase 原始碼，不得以任何方式修改
- **不得刪除 log 條目**：`log.md` 為 append-only，只能追加，不得修改或刪除既有條目
- **不得偽造 sources**：`frontmatter.sources` 必須指向真實存在的檔案路徑
- **不得跳過 index 更新**：任何新增或刪除 wiki 頁面後，必須同步更新 `wiki/index.md`
- **不得跳過 log 記錄**：任何 ingest / lint / 重大更新操作後，必須在 `wiki/log.md` 追加條目
