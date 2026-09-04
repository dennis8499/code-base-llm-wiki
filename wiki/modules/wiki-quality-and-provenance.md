---
title: Wiki 品質與證據追溯
type: module
summary: 以安全來源解析、內容摘要、受管索引與 append-only log 建立可稽核的 Markdown 知識層
notebooklm_group: function-wiki-quality
notebooklm_role: exclude
sources:
  - .agents/skills/codebase-wiki/scripts/validate-frontmatter.py
  - .agents/skills/codebase-wiki/scripts/check-stale.py
  - .agents/skills/codebase-wiki/scripts/validate-log.py
  - tests/test_stale.py
  - tests/test_wiki_lint.py
source_digest: sha256:eed24d3f759ab9d252cab64034bf08b4cf7589d0aba574dc4e3cbefb1d7061cb
derived_from: ["[[system-architecture]]"]
last_updated: 2026-09-03
tags: [module, lint, provenance, frontmatter, freshness]
status: active
---

# Wiki 品質與證據追溯

## 職責

- 驗證頁面 type、路徑、日期、status 與型別特定 frontmatter；`business-requirement` 驗證
  `requirement_id`、`capability_id`、`applies_to`、evidence state、`## 驗收條件` 與 stable
  `AC-*`，`business-process` 驗證 process/actors/coverage，`business-rule` 驗證 rule/applies_to。
- 驗證 NotebookLM `business|traceability|exclude` roles、穩定 group，並要求 business pages
  提供非空 `notebooklm_terms`。
- 分離 raw `sources` 與 Wiki `derived_from`，並以 `source_digest` 偵測內容變更。
- 檢查 missing/stale sources、broken/ambiguous wikilinks、真正 orphan 與 index completeness。
- 檢查 `sources` 的實際解析路徑仍位於 repo root 內，拒絕 drive-qualified path 或逃逸到
  repo 外的 symlink。
- Repo 內 raw-source symlink 允許作為 evidence，digest 使用 resolved target；逃逸
  Repo 的 symlink/reparse source 必須拒絕。這不同於 installer 對 framework source
  symlink/reparse 的全面拒絕。
- 維護 index 的 managed region，保留 marker 外的人工內容。
- 驗證 log operation、日期、affected pages、Git baseline 與 append-only 契約；lint API
  可在 NotebookLM preflight 使用 filesystem-only 模式，略過 Git baseline。

## 狀態契約

`lint-wiki.py` 分別輸出 `deterministic_status`、`semantic_status` 與
`overall_status`。舊 `ok` 只表示 deterministic Critical/Warning 為零；
`missing_module_coverage` 與 `semantic_contradictions` 在無法機械證明時維持
`agent_review_required`。

Orphan inbound 不計 `index.md`、`log.md` 或自我連結。`source_digest` 相符時，
其內容證據優先於 Git commit date 與 dirty-path heuristic；摘要不符則同日變更也會
報 stale。
`overview.md` 只免除 orphan warning，仍必須出現在 index；orphan 與 index
completeness 是兩個獨立判定。持久化 archaeology page 還必須由相關內容頁建立
語意 inbound wikilink，index/log 不算內容關係。

## Evidence

- `validate-frontmatter.py` 驗證 `summary`、`derived_from`、digest、BA page types 與
  NotebookLM role/term 契約。
- `check-stale.py` 對排序後 path/file hash records 建立 aggregate SHA-256。
- `check-stale.py` 在 existence/digest 判定前驗證 source symlink containment。
- Filesystem fallback 在做 repo-relative 比較前，同時 resolve root 與 candidate，避免
  Windows 8.3 路徑和完整路徑指向同一位置卻被誤判為越界。
- `check-stale.py`、`validate-frontmatter.py` 與 `wiki-stats.py` 都提供標準
  `--help` CLI；source directory 在沒有 Git metadata 時 fallback 到 filesystem scan，
  並可由 lint API 明確停用 Git freshness/history lookup。
- `check-stale.py` 與 digest resolver 對 repo-relative source 正規化 `/` 與 `\\`
  separators，讓同一 Wiki source 在 Windows/Linux host 維持一致。
- `validate-log.py` 對新 contract marker 後的 entry 執行嚴格檢查，舊 entry 僅警告。
- `validate-log.py` 也會在讀取前驗證 log parent tree 與 repo containment，直接 CLI
  invocation 遇到 symlink/reparse 或 repo 外 path 會 fail closed。
- CLI 會保留 lexical log path 到 validator 完成 regular-tree 檢查，避免 `resolve()`
  先行隱藏 symlink/reparse parent。
- `rebuild-index.py` 在讀取或寫入 managed index 前拒絕 Wiki tree 中的 symlink 或
  Windows reparse point，避免 index write escape。
- `frontmatter.py` 的 shared regular-tree guard 讓 stale、frontmatter、lint 與 stats
  在讀取 Wiki pages 前拒絕 symlink/reparse tree，避免 health tools 跟隨外部頁面。
- `lint-wiki.py` CLI 也在 `resolve()` 前驗證 caller-provided Wiki root，避免 CLI
  canonicalization 繞過同一 regular-tree boundary。
- `tests/test_stale.py` 與 `tests/test_wiki_lint.py` 也驗證 quality CLI 的成功、warning、
  invalid input 與 unsafe-tree exit contracts，避免只測 library path 而漏掉使用者入口。
- `tests/test_stale.py` 明確建立 Repo 外 escape target；另固定 Repo 內 symlink 的 resolved
  digest 必須隨 target 內容變化。無建立 symlink 權限的平台會 skip fixture，而 Linux
  clean-run 必須執行該契約。
- `tests/test_wiki_lint.py` 固定 overview 缺 index 時回報 `index_missing`，同時不把
  overview 誤報為 orphan。

## Contradictions

- 舊 orphan 演算法把 index 與 self-link 算入 inbound，導致已列索引的頁面永遠不會
  成為 orphan；目前已排除。
- 舊 rebuild 會覆寫整份 index；目前只替換 managed region。

## Inferences

- Aggregate digest 是 page-level freshness，不等於逐 claim provenance；body 仍需以
  路徑與 symbol 對重要事實定位。

## Gaps

- 語意矛盾與模組重要性仍需要 agent review。
- 未提供 claim-level AST mapping 或外部資料庫證據的自動 fingerprint。

## 相關頁面

- [[system-analysis]]
- [[notebooklm-exporter]]
- [[framework-introduction]]
