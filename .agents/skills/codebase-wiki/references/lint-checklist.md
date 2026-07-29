# Wiki 健康檢查清單

## 概述

Lint 操作對 wiki 進行全面健康檢查，找出品質問題並提供修復建議。
建議每次大規模 Ingest 後、以及每週定期執行一次。

---

## 檢查項目

### 1. Stale Pages（陳舊頁面）

**檢查方式：** 逐頁讀取 frontmatter 的 `sources` 欄位，驗證每個路徑是否仍存在於 codebase 中。

| 嚴重度     | 狀況                           | 處理方式                                     |
| ---------- | ------------------------------ | -------------------------------------------- |
| 🔴 Critical | sources 中所有檔案都已刪除     | 將頁面 status 標記為 `stale`，建議刪除或歸檔 |
| 🟡 Warning  | sources 中部分檔案已刪除或搬移 | 更新 sources 路徑，或標記需要重新 ingest     |
| 🟢 OK       | 所有 sources 檔案都存在        | 無需處理                                     |

**自動修復：** 可用 `scripts/check-stale.py` 批次檢查。

---

### 2. Orphan Pages（孤島頁面）

**檢查方式：** 掃描所有 wiki 頁面，建立 inbound link 圖。找出沒有任何其他頁面連結到的頁面。

**排除：** `index.md`、`log.md`、`overview.md` 不計入（它們是入口頁面）。

| 嚴重度    | 狀況                   | 處理方式                      |
| --------- | ---------------------- | ----------------------------- |
| 🟡 Warning | 頁面無 inbound link    | 在相關頁面加入 `[[wikilink]]` |
| 🟢 OK      | 至少 1 個 inbound link | 無需處理                      |

---

### 3. Broken Links（斷裂連結）

**檢查方式：** 掃描所有 `[[wikilink]]`，確認目標頁面存在。

| 嚴重度     | 狀況                             | 處理方式                              |
| ---------- | -------------------------------- | ------------------------------------- |
| 🔴 Critical | `[[page-name]]` 指向不存在的頁面 | 建立缺失頁面（placeholder）或修正連結 |

---

### 4. Missing Pages（缺失頁面）

**檢查方式：** 比對 codebase 的模組/目錄結構與 `wiki/modules/` 的頁面，找出未被文件化的模組。

| 嚴重度    | 狀況                                    | 處理方式        |
| --------- | --------------------------------------- | --------------- |
| 🟡 Warning | 重要模組（含 10+ 檔案）無對應 wiki 頁面 | 建議執行 Ingest |
| ℹ️ Info    | 小型模組/工具目錄無 wiki 頁面           | 列出但不強制    |

---

### 5. Frontmatter Validation（Frontmatter 驗證）

**檢查方式：** 驗證每頁的 YAML frontmatter 是否符合規格。

| 欄位           | 要求                                                                                                       |
| -------------- | ---------------------------------------------------------------------------------------------------------- |
| `title`        | 必填，非空字串                                                                                             |
| `type`         | 必填，值為 module / entity / pattern / decision / dependency / guide / synthesis / overview / architecture / index / log |
| `sources`      | 必填，陣列（可為空陣列 `[]`，但不可省略）                                                                  |
| `last_updated` | 必填，YYYY-MM-DD 格式                                                                                      |
| `tags`         | 必填，陣列                                                                                                 |
| `status`       | 必填，值為 active / stale / placeholder                                                                    |

---

### 6. Contradictions（矛盾偵測）

**檢查方式：** 語意層級檢查——當多個頁面描述同一實體或模組時，比對關鍵事實是否一致。

常見矛盾類型：
- 模組 A 頁面說「使用 PostgreSQL」，模組 B 頁面說「使用 MySQL」
- Entity 頁面的屬性列表與 Module 頁面的描述不一致
- 相依關係方向不一致（A 說依賴 B，但 B 的「被依賴」未列 A）

| 嚴重度    | 處理方式                         |
| --------- | -------------------------------- |
| 🟡 Warning | 標記矛盾位置，建議人工確認後修正 |

---

### 7. Index Completeness（索引完整性）

**檢查方式：** 比對 `wiki/` 目錄下實際存在的 `.md` 檔案與 `index.md` 中列出的頁面。

| 嚴重度     | 狀況                        | 處理方式                          |
| ---------- | --------------------------- | --------------------------------- |
| 🔴 Critical | wiki 頁面存在但未列入 index | 加入 index.md                     |
| 🟡 Warning  | index 列出但頁面不存在      | 移除 index 條目或建立 placeholder |

**自動修復：** 可用 `scripts/rebuild-index.py` 重建索引。

---

### 8. Coverage Report（覆蓋率報告）

**檢查方式：** 統計 wiki 對 codebase 的覆蓋程度。

報告內容：
- 總頁面數
- 各 type 頁面數量
- 已文件化 vs 未文件化的模組數量
- 最近 30 天未更新的頁面數量
- 平均每頁 source 數量

**自動化：** 可用 `scripts/wiki-stats.py` 產出統計報告。

---

## 健康報告輸出格式

```markdown
# Wiki 健康報告 — YYYY-MM-DD

## 摘要

| 指標            | 數值 |
| --------------- | ---- |
| 總頁面數        | N    |
| 🔴 Critical 問題 | N    |
| 🟡 Warning       | N    |
| 🟢 健康頁面      | N    |
| 覆蓋率          | N%   |

## Critical 問題

1. ...

## Warning

1. ...

## 建議行動

1. ...
```

## Completion Criterion

Lint is complete when all eight checks have a Critical, Warning, Info, OK, or
`agent_review_required` result. Deterministic checks cover frontmatter, sources,
wikilinks, orphans, index completeness, and statistics. Missing-module coverage
and semantic contradictions remain explicit agent-review items when they cannot
be proven deterministically. Repairs begin only after confirmation.
