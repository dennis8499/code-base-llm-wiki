---
title: NotebookLM BA-only 功能需求匯出器
type: module
summary: 以 schema v5、完整 codebase disposition、DLP masking 與 BA-only materialization 建立功能需求 source pack
notebooklm_group: business-notebooklm-export
notebooklm_role: exclude
sources:
  - .agents/skills/codebase-wiki/scripts/notebooklm_exporter.py
  - .agents/skills/codebase-wiki/scripts/check-stale.py
  - .agents/skills/codebase-wiki/references/notebooklm-export-workflow.md
  - .agents/skills/codebase-wiki/assets/notebooklm.toml
  - .github/prompts/export-notebooklm.prompt.md
  - tests/test_export_notebooklm.py
source_digest: sha256:401dcbb56ac95186b789ab37b3eb0ddb9521545ed04cae30a18d9dd8c405b95a
derived_from: ["[[notebooklm-ba-knowledge-export]]", "[[system-architecture]]", "[[wiki-quality-and-provenance]]"]
last_updated: 2026-08-26
tags: [module, notebooklm, exporter, ba-first, traceability]
status: active
---

# NotebookLM BA-only 功能需求匯出器

## 職責

`notebooklm_exporter.py` 讀取完整安全 repo scope 驗證 coverage，再把已確認的 BA Wiki 編排成
離線 source pack。固定 audience 是 `business-analyst`，knowledge contract 是
`business-functional-requirements-v2`，retrieval contract 是 `business-only-ba-v2`。它不呼叫
NotebookLM API、不修改 raw sources，也不 materialize raw evidence 或技術頁。

## 輸入分類

| 類別 | 來源 | Pack 行為 |
| --- | --- | --- |
| BA documents | `notebooklm_role: business` 的 overview、requirement/process/rule catalogs、glossary、gaps 與 FR/BP/BR pages | 唯一可 materialize 的知識 |
| Analysis inputs | Safe runtime source/config/schema/docs/tests、`business_source_paths`、`extra_paths` | 本機讀取、DLP masking、coverage 驗證；不匯出 |
| Local governance | coverage ledger 與 `notebooklm_role: exclude` pages | readiness evidence；不匯出 |
| Safety exclusions | sensitive、binary/generated/dependency、CI/IaC、Wiki/output 等 | 不讀內容或不匯出 |

`business_source_paths` 只可覆蓋 dev-tooling 的 scope 分類，不能覆蓋 sensitive、
generated/dependency、CI/IaC、configured exclusion、Wiki/output 或 symlink/reparse boundary。
未指定角色的舊 Wiki 頁不會自動成為 BA source，preflight 會列出 warning。

## BA 結構閘門

Preflight 的 `business_coverage` 驗證：

- overview、functional requirement catalog、business process/rule catalogs、glossary、gaps 與
  local coverage ledger 都存在、active；前六份 BA documents 是 `notebooklm_role: business`；
- coverage ledger 固定 `notebooklm_role: exclude`；
- 至少一個 active requirement/process，每個 requirement/process/rule ID 唯一；
- requirement/process/rule catalogs 實際連到對應頁；
- requirement 與 rule 的 `applies_to` 指向存在的 process；
- 每個 requirement 有 `## 驗收條件` 與至少一個 stable `AC-*`；
- business page 有穩定 `notebooklm_group` 與非空 `notebooklm_terms`；
- 規則證據狀態只使用 `business-confirmed`、`implementation-observed`、`inference` 或 `gap`。

每個 safe included file 另由 ledger 分成 `functional-evidence`、`supporting-technical`、
`no-observable-behavior` 或 `analysis-gap`。Uncovered、analysis-gap、dangling requirement、
缺少結構或 required-document stale 都使
`ready_to_export=false`。

## Preflight identity 與兩次確認

Discovery 與 readiness 使用同一個唯讀命令，但扮演不同業務階段。ID 綁定 Wiki、safe
inventory、設定、coverage、三階段 DLP summary、exact pack plan 與 retrieval contract。第一次文件更新後必然
失效；第二次結果必須展示並取得確認，apply 又會完整重算，任何漂移都 fail closed。

```text
export-notebooklm.py --root . --preflight --format json
export-notebooklm.py --root . --apply --preflight-id sha256:... --output .notebooklm
```

## 打包與路由

固定 logical source IDs：

- `query-index`：BA 問題類型與最多五個業務群組的 router；
- `project-map`：功能需求、流程、規則、coverage 與 gaps 導覽；
- `docs:<group>`：完整 BA Wiki 文件；
- slot 壓力下才使用 `docs:combined`，安全分割時加 `#part-###`。

選源只有 query/map → BA documents。Schema v5 拒絕 `include_traceability`、
`include_evidence` 與 `dlp_allowlist`。必要 BA 內容不能因 `source_budget` 靜默消失。

## Schema v5 與 migration

Manifest 記錄 audience、knowledge/retrieval contract、functional/business coverage、file
dispositions、source policy、input/output hashes、limits、DLP phases 與 upload diff。Exporter
可讀 schema v1–v4 previous manifest，但非 `business-only-ba-v2` contract 一律設定
`migration.requires_full_rebuild=true`，要求先移除同一本 Notebook 的舊 static sources。

## 安全、容量與原子性

- Top-down walker 在進入排除樹前剪枝，只回報 bounded metadata summary，不讀取其內容。
- 只解析 UTF-8 text；非 UTF-8 或 malformed config/manifest/journal 回傳受控錯誤。
- 本機 `notebooklm-enterprise-ba-mask-v1` 在 analysis copy、managed Wiki 與 final payload
  檢查高信心金融、GCP credential/API key 與明文 password patterns；先遮罩，final residual
  才阻擋，report 不保存命中值。
- 預設 Enterprise hard limits 為 300 sources、500 MB、500,000 words；safety limits 為
  450 MB、450,000 words，字數採 `han_characters_plus_non_han_tokens`。
- Output 使用 containment checks、transaction lock、journal、stage/backup 與 `os.replace()`；
  失敗或程序中止時保留／恢復上一份有效 pack。

## 驗證證據

- `tests/test_export_notebooklm.py` 覆蓋 schema v5、FR/AC 與完整 disposition gates、BA-only
  materialization、legacy key rejection、full-rebuild migration、DLP masking、容量、path safety、
  process-kill recovery、並行 writer 與 500-page compaction。
- `tests/test_contracts.py::test_framework_notebooklm_preflight_is_ready` 固定本框架 Wiki 本身
  必須通過 BA readiness gate。
- 固定答案品質驗收見 `docs/validation/notebooklm-ba-uat.md`；這是手動 tenant UAT，不由
  exporter 假裝驗證生成式回答。

## 相關頁面

- [[notebooklm-ba-knowledge-export]]
- [[notebooklm-ba-functional-export]]
- [[functional-requirement-catalog]]
- [[ba-knowledge-precedes-traceability]]
- [[readiness-preflight-required]]
- [[notebooklm-export]]
- [[business-knowledge-gaps]]
