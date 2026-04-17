# Frontmatter 欄位完整規格

## 共用欄位（所有頁面類型必填）

| 欄位 | 型別 | 必填 | 說明 | 範例 |
|------|------|------|------|------|
| `title` | string | ✅ | 頁面標題（人類可讀） | `"User Authentication Service"` |
| `type` | enum | ✅ | 頁面類型 | `module` |
| `sources` | string[] | ✅ | 引用的原始碼路徑（相對 repo root） | `["src/auth/service.ts"]` |
| `last_updated` | string | ✅ | 最後更新日期（YYYY-MM-DD） | `"2026-04-16"` |
| `tags` | string[] | ✅ | 分類標籤 | `["auth", "security"]` |
| `status` | enum | ✅ | 頁面狀態 | `active` |

### `type` 允許值

| 值 | 對應目錄 | 說明 |
|---|---|---|
| `module` | `wiki/modules/` | 按模組/目錄的文件頁面 |
| `entity` | `wiki/entities/` | 類別、服務、API 端點、DB 表 |
| `pattern` | `wiki/patterns/` | 設計模式 |
| `decision` | `wiki/decisions/` | Architecture Decision Record |
| `dependency` | `wiki/dependencies/` | 外部相依套件 |
| `guide` | `wiki/guides/` | 操作指南 |
| `synthesis` | `wiki/synthesis/` | 綜合分析 |
| `overview` | `wiki/` (root) | Codebase 高階總覽 |
| `architecture` | `wiki/architecture/` | 架構文件 |
| `index` | `wiki/` (root) | 索引頁（僅 `index.md`） |
| `log` | `wiki/` (root) | 活動日誌（僅 `log.md`） |

### `status` 允許值

| 值 | 語意 | 何時使用 |
|---|---|---|
| `active` | 內容準確且最新 | 剛 ingest 或驗證過的頁面 |
| `stale` | 內容可能過時 | source 已變更但頁面未更新 |
| `placeholder` | 佔位符，尚未填入實質內容 | 已知需要但尚未 ingest |

---

## 類型特定欄位

### `type: decision`（ADR 專用）

| 欄位 | 型別 | 必填 | 說明 | 範例 |
|------|------|------|------|------|
| `decision_date` | string | ✅ | 決策日期（YYYY-MM-DD） | `"2026-04-16"` |
| `decision_status` | enum | ✅ | proposed / accepted / deprecated / superseded | `"accepted"` |
| `superseded_by` | string | ❌ | 取代此 ADR 的頁面名 | `"adr-005-new-auth"` |

### `type: entity`（Entity 專用）

| 欄位 | 型別 | 必填 | 說明 | 範例 |
|------|------|------|------|------|
| `entity_type` | enum | 建議 | class / service / api-endpoint / database-table | `"service"` |
| `parent_module` | string | 建議 | 所屬模組的 wiki 頁面名 | `"auth-module"` |

### `type: dependency`（Dependency 專用）

| 欄位 | 型別 | 必填 | 說明 | 範例 |
|------|------|------|------|------|
| `package_name` | string | ✅ | 套件全名（含 scope） | `"@nestjs/core"` |
| `version` | string | ✅ | 目前使用版本 | `"^10.3.0"` |
| `registry` | string | 建議 | npm / pypi / maven / nuget | `"npm"` |

---

## 完整範例

### Module 頁面

```yaml
---
title: Authentication Module
type: module
sources:
  - src/modules/auth/
  - src/modules/auth/auth.service.ts
  - src/modules/auth/auth.controller.ts
last_updated: 2026-04-16
tags: [auth, security, core]
status: active
---
```

### ADR 頁面

```yaml
---
title: "ADR-001: 選用 JWT 作為 Session 管理方案"
type: decision
decision_date: 2026-03-15
decision_status: accepted
sources:
  - src/modules/auth/jwt.strategy.ts
  - src/config/auth.config.ts
last_updated: 2026-04-16
tags: [adr, auth, jwt]
status: active
---
```

### Entity 頁面

```yaml
---
title: UserService
type: entity
entity_type: service
parent_module: auth-module
sources:
  - src/modules/auth/user.service.ts
last_updated: 2026-04-16
tags: [auth, user, service]
status: active
---
```

### Dependency 頁面

```yaml
---
title: Express.js
type: dependency
package_name: express
version: "^4.18.2"
registry: npm
sources:
  - package.json
  - src/main.ts
last_updated: 2026-04-16
tags: [dependency, framework, http]
status: active
---
```

---

## sources 填寫規範

1. 路徑相對於 repo root
2. 指向目錄時以 `/` 結尾：`src/modules/auth/`
3. 指向檔案時不加 `/`：`src/modules/auth/service.ts`
4. 只列出最核心的 1-5 個 source，不需窮舉
5. **禁止填入不存在的路徑**——Lint 會檢查
6. sources 可為空陣列 `[]`（如 guide、synthesis 可能無直接 source）
