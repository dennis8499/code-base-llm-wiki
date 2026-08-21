# Frontmatter 欄位完整規格

本檔是 wiki page frontmatter 的權威規格。頂層 instruction、agent prompt
與文件可以摘要必填欄位，但 allowed values、type-specific 欄位與驗證規則
以本檔為準。

## 共用欄位（所有頁面類型必填）

| 欄位           | 型別     | 必填 | 說明                               | 範例                            |
| -------------- | -------- | ---- | ---------------------------------- | ------------------------------- |
| `title`        | string   | ✅    | 頁面標題（人類可讀）               | `"User Authentication Service"` |
| `type`         | enum     | ✅    | 頁面類型                           | `module`                        |
| `sources`      | string[] | ✅    | 引用的原始碼路徑（相對 repo root） | `["src/auth/service.ts"]`       |
| `last_updated` | string   | ✅    | 最後更新日期（YYYY-MM-DD）         | `"2026-04-16"`                  |
| `tags`         | string[] | ✅    | 分類標籤                           | `["auth", "security"]`          |
| `status`       | enum     | ✅    | 頁面狀態                           | `active`                        |

### 證據與衍生欄位（選填、增量採用）

| 欄位 | 型別 | 規則 |
| --- | --- | --- |
| `summary` | string | 一句話結論；新增或重大更新的 evidence-backed 頁面必填。 |
| `derived_from` | string[] | Wiki 衍生證據，使用 `[[page-name]]`；不得放入 `sources`。 |
| `source_digest` | string | `sha256:<64 lowercase hex>`；新增或重大更新且 `sources` 非空的頁面必填。 |

`source_digest` 對排序後的 `repo-relative-path + NUL + file-sha256` records
再做 SHA-256。目錄來源展開 Git tracked 與 non-ignored untracked files，並排除
Wiki、dependency、generated、cache 與 export output。舊頁面缺少這些欄位時
Lint 先回報 Info，不作為 schema failure。

### NotebookLM 功能分組（選填）

| 欄位 | 型別 | 必填 | 說明 | 範例 |
| --- | --- | --- | --- | --- |
| `notebooklm_group` | string | NotebookLM preparation 建立或更新的頁面必填；其他頁面選填 | 穩定的功能文件群組，使用 kebab-case | `function-order-checkout` |

允許值必須符合 `^[a-z0-9]+(?:-[a-z0-9]+)*$`。同一功能域重跑時沿用既有值；
共用高階頁面使用 `project`、`architecture` 或 `system-analysis`。舊頁面沒有此欄位時，
exporter 會依 type/path 使用相容 fallback。

### `type` 允許值

| 值             | 對應目錄             | 說明                         |
| -------------- | -------------------- | ---------------------------- |
| `module`       | `wiki/modules/`      | 按模組/目錄的文件頁面        |
| `entity`       | `wiki/entities/`     | 類別、服務、API 端點、DB 表  |
| `pattern`      | `wiki/patterns/`     | 設計模式                     |
| `decision`     | `wiki/decisions/`    | Architecture Decision Record |
| `dependency`   | `wiki/dependencies/` | 外部相依套件                 |
| `guide`        | `wiki/guides/`       | 操作指南                     |
| `synthesis`    | `wiki/synthesis/`    | 綜合分析                     |
| `overview`     | `wiki/` (root)       | Codebase 高階總覽            |
| `architecture` | `wiki/architecture/` | 架構文件                     |
| `index`        | `wiki/` (root)       | 索引頁（僅 `index.md`）      |
| `log`          | `wiki/` (root)       | 活動日誌（僅 `log.md`）      |

### `type` 對應路徑規則

| `type` | 合法位置 |
| --- | --- |
| `module` | `wiki/modules/*.md` |
| `entity` | `wiki/entities/*.md` |
| `pattern` | `wiki/patterns/*.md` |
| `decision` | `wiki/decisions/*.md` |
| `dependency` | `wiki/dependencies/*.md` |
| `guide` | `wiki/guides/*.md` |
| `synthesis` | `wiki/synthesis/*.md` |
| `overview` | `wiki/overview.md` |
| `architecture` | `wiki/architecture/*.md` |
| `index` | `wiki/index.md` |
| `log` | `wiki/log.md` |

### `status` 允許值

| 值            | 語意                     | 何時使用                  |
| ------------- | ------------------------ | ------------------------- |
| `active`      | 內容準確且最新           | 剛 ingest 或驗證過的頁面  |
| `stale`       | 內容可能過時             | source 已變更但頁面未更新 |
| `placeholder` | 佔位符，尚未填入實質內容 | 已知需要但尚未 ingest     |

### 日期格式

所有日期欄位必須使用 `YYYY-MM-DD`，且必須是有效日期，例如
`2026-07-01`。不得使用相對日期、時間戳、民國年、或含時間的 ISO 字串。

---

## 類型特定欄位

### `type: decision`（ADR 專用）

| 欄位              | 型別   | 必填 | 說明                                          | 範例                 |
| ----------------- | ------ | ---- | --------------------------------------------- | -------------------- |
| `decision_date`   | string | ✅    | 決策日期（YYYY-MM-DD）                        | `"2026-04-16"`       |
| `decision_status` | enum   | ✅    | proposed / accepted / deprecated / superseded | `"accepted"`         |
| `superseded_by`   | string | ❌    | 取代此 ADR 的頁面名                           | `"adr-005-new-auth"` |

`decision_status` 只描述決策生命週期；共用欄位 `status` 仍描述 wiki 頁面
狀態，只能使用 `active` / `stale` / `placeholder`。

### `type: entity`（Entity 專用）

| 欄位            | 型別   | 必填 | 說明                                            | 範例            |
| --------------- | ------ | ---- | ----------------------------------------------- | --------------- |
| `entity_type`   | enum   | 建議 | class / service / api-endpoint / database-table | `"service"`     |
| `parent_module` | string | 建議 | 所屬模組的 wiki 頁面名                          | `"auth-module"` |

### `type: dependency`（Dependency 專用）

| 欄位           | 型別   | 必填 | 說明                       | 範例             |
| -------------- | ------ | ---- | -------------------------- | ---------------- |
| `package_name` | string | ✅    | 套件全名（含 scope）       | `"@nestjs/core"` |
| `version`      | string | ✅    | 目前使用版本               | `"^10.3.0"`      |
| `registry`     | string | 建議 | npm / pypi / maven / nuget | `"npm"`          |

### `type: index` 與 `type: log`

| 頁面 | 必填值 |
| --- | --- |
| `wiki/index.md` | `type: index`、`sources: []`、`tags: [index]` |
| `wiki/log.md` | `type: log`、`sources: []`、`tags: [log]` |

`wiki/log.md` 的內容區塊為 append-only；可更新 frontmatter 的
`last_updated`，但不得刪除或改寫既有 log entries。

---

## Templates

Frontmatter examples live only in the exact assets selected by
`page-types.md`. This file remains the schema source of truth; assets remain the
page-shape source of truth.

---

## sources 填寫規範

1. 路徑相對於 repo root，且只引用 raw repository evidence；Wiki 頁面改用 `derived_from`
2. 指向目錄時以 `/` 結尾：`src/modules/auth/`
3. 指向檔案時不加 `/`：`src/modules/auth/service.ts`
4. 只列出最核心的 1-5 個 source，不需窮舉
5. **禁止填入不存在的路徑**——Lint 會檢查
6. sources 可為空陣列 `[]`（如 guide、synthesis 可能無直接 raw source）

---

## 驗證規則

`validate-frontmatter.py` 依此規格執行 deterministic validation：

1. 所有 wiki markdown 檔必須有 YAML frontmatter。
2. 共用必填欄位不得缺漏。
3. `title` 必須是非空字串。
4. `type` 必須是本檔列出的允許值。
5. `sources` 必須是陣列；可為空陣列。
6. `last_updated` 必須是有效 `YYYY-MM-DD` 日期。
7. `tags` 必須是陣列。
8. `status` 必須是 `active` / `stale` / `placeholder`。
9. `type: decision` 必須有有效 `decision_date` 與 `decision_status`。
10. `type: dependency` 必須有非空 `package_name` 與 `version`。
11. `type: index` / `type: log` 必須位於指定 root 檔名。
12. `notebooklm_group` 若存在，必須是非空 kebab-case 字串。
13. `summary` 若存在，必須是非空字串。
14. `derived_from` 若存在，必須是由 `[[wikilink]]` 組成的陣列。
15. `source_digest` 若存在，必須符合 `sha256:<64 lowercase hex>`。
