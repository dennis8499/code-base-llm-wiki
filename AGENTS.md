# AGENTS.md — Codebase LLM Wiki for Codex

本檔案是 **OpenAI Codex 版**的 Codebase LLM Wiki 操作指令。當使用者要求建立、查詢、維護或健康檢查 `wiki/` 時，Codex 應依照本檔案行動。

若目前正在維護的是 **Codebase LLM Wiki 框架本身**，且使用者明確要求修改框架文件或範本，則可以依請求修改 `README.md`、`ChangeLog.md`、`.github/`、`AGENTS.md` 等框架檔案；下方「不得修改 raw sources」規則主要適用於把本框架套用到目標 codebase 時的 wiki 維護工作。

## 核心模型

Codebase LLM Wiki 不是每次查詢都重新檢索原始碼的 RAG；它是一個由 LLM 持續維護、可累積的 Markdown 知識庫。

| 層 | 位置 | 職責 |
| --- | --- | --- |
| Raw Sources | 目標 codebase 的原始碼、設定檔、既有文件 | 唯讀。wiki 任務中只讀取、不修改 |
| Wiki | `wiki/` | Codex 產生並維護的結構化知識庫 |
| Schema | `AGENTS.md` 與可選的 `.github/skills/codebase-wiki/` | 驅動 Codex 行為的規則、範本、輔助腳本 |

## 意圖路由

先判斷使用者要做哪一類 wiki 任務，再選擇工作流程：

| 意圖 | 常見訊號 | 工作流程 |
| --- | --- | --- |
| Ingest | 「讀取」「分析」「文件化」「加入 wiki」「ingest」 | 讀 raw sources，建立或更新 wiki 頁面 |
| Query | 「怎麼做」「在哪裡」「解釋」「查詢」「找」 | 先查 wiki，必要時回溯 sources |
| Lint | 「檢查」「健康」「品質」「陳舊」「lint」 | 檢查 stale pages、broken links、frontmatter、index |
| Archaeology | 「歷史」「為什麼這樣寫」「legacy」「考古」 | 使用 git history 與原始碼追蹤設計脈絡 |
| ADR | 「決策」「ADR」「架構選擇」 | 建立 `wiki/decisions/` 架構決策紀錄 |
| Synthesis / Guide | 「整理成指南」「存起來」「onboarding」「綜合分析」 | 產出 `wiki/guides/` 或 `wiki/synthesis/` |

## 全域規則

- Wiki 任務中，raw sources 只能讀取，不能修改。
- Codex 可以建立或更新 `wiki/` 內的頁面、`wiki/index.md`、`wiki/log.md`。
- `wiki/log.md` 是 append-only，只能追加新條目，不得刪改既有條目。
- 新增、刪除、改名 wiki 頁面後，必須同步更新 `wiki/index.md`。
- 每個 wiki 頁面的 `frontmatter.sources` 必須指向真實存在的 repo 相對路徑；沒有直接 source 時使用 `sources: []`。
- 提到其他 wiki 頁面時使用 `[[page-name]]` wikilink，不使用相對路徑連結。
- 事實陳述需可追溯到 sources 或 git history；推測必須明確標記為推測。
- 保留使用者既有補充內容，不要用重新產生的文字整段覆蓋人工維護段落。

## Wiki 結構

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

## Frontmatter 規格

每個 wiki 頁面必須包含：

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

`wiki/index.md` 使用 `type: index`，`wiki/log.md` 使用 `type: log`。兩者若沒有直接 raw source，仍需寫 `sources: []` 與 `tags`。

ADR 頁面另需加入：

```yaml
decision_date: YYYY-MM-DD
decision_status: proposed | accepted | deprecated | superseded
```

## Ingest 流程

1. 先讀 `wiki/index.md` 與 `wiki/log.md`，理解目前 wiki 狀態。
2. 探索目標路徑：優先找 README、入口點、export/import、路由、service、model、設定檔。
3. 摘要發現：核心職責、主要類別或函式、相依關係、設計模式、特殊邏輯、潛在風險。
4. 建立或更新頁面：
   - 模組頁：`wiki/modules/{slug}.md`
   - 重要類別、服務、API、資料表：`wiki/entities/{slug}.md`
   - 重複出現的設計結構：`wiki/patterns/{slug}.md`
   - 重要外部相依：`wiki/dependencies/{slug}.md`
5. 補上 cross-references，確保相關頁面互相連結。
6. 更新 `wiki/index.md`。
7. 追加 `wiki/log.md` 條目：`## [YYYY-MM-DD] ingest | {subject}`。

若 `.github/skills/codebase-wiki/assets/` 存在，優先沿用其中模板。若不存在，仍依照本檔案規格產生頁面。

## Query 流程

1. 先讀 `wiki/index.md` 定位相關頁面。
2. 讀取 1-5 個最相關的 wiki 頁面。
3. 若 wiki 資訊不足或疑似過時，依 `sources` 回溯 raw source 驗證。
4. 回答時列出引用來源，例如 `[[auth-module]]` 與 `src/auth/service.ts`。
5. 若回答具有長期價值，建議存入 `wiki/synthesis/`；未經使用者確認，不主動寫入 query 結果。

## Lint 流程

檢查項目：

- stale sources：frontmatter `sources` 是否仍存在
- orphan pages：是否缺少 inbound wikilink
- broken links：`[[wikilink]]` 目標是否存在
- missing pages：重要模組是否尚未文件化
- frontmatter validation：必填欄位與 enum 是否正確
- contradictions：多頁描述是否互相矛盾
- index completeness：實際頁面是否都列入 `index.md`
- coverage report：頁面數、類型分佈、近期更新狀態

可用輔助腳本（若存在）：

```bash
python .github/skills/codebase-wiki/scripts/check-stale.py wiki/
python .github/skills/codebase-wiki/scripts/wiki-stats.py wiki/
python .github/skills/codebase-wiki/scripts/rebuild-index.py wiki/
```

大範圍自動修復前，先輸出健康報告與建議行動；使用者確認後再修改 wiki。

## Archaeology 流程

1. 找功能入口點：路由、CLI command、event handler、public API、關鍵函式。
2. 沿呼叫鏈追蹤輸入、處理、輸出與特殊分支。
3. 使用非破壞性 git 指令取得歷史證據：

```bash
git log --oneline -- path/to/file
git blame -L start,end path/to/file
git show <commit>
```

4. 產出考古報告或更新相關 wiki 頁面，清楚區分「證據支持」與「推測」。
5. 更新 `wiki/index.md` 並追加 `wiki/log.md`。

## ADR 流程

建立 `wiki/decisions/{slug}.md`，內容包含：

- 背景與問題
- 決策
- 替代方案
- 影響與取捨
- 後續追蹤

ADR frontmatter 必須包含 `decision_date`、`decision_status`、標準 `sources`、`tags`、`status`。

## 回覆格式

完成 wiki 任務後，簡短回報：

- 建立或更新了哪些 wiki 頁面
- 是否更新 `wiki/index.md`
- 是否追加 `wiki/log.md`
- 有哪些未驗證、需使用者確認或值得後續 ingest 的地方

若沒有修改檔案，明確說明只做了查詢或健康檢查。
