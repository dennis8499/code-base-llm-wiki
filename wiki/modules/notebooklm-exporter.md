---
title: NotebookLM BA-first 離線匯出器
type: module
summary: 以 schema v4、BA 結構閘門、必要 business evidence 與獨立 traceability 建立可審查的 NotebookLM source pack
notebooklm_group: business-notebooklm-export
notebooklm_role: traceability
sources:
  - .agents/skills/codebase-wiki/scripts/notebooklm_exporter.py
  - .agents/skills/codebase-wiki/scripts/check-stale.py
  - .agents/skills/codebase-wiki/references/notebooklm-export-workflow.md
  - .agents/skills/codebase-wiki/assets/notebooklm.toml
  - .github/prompts/export-notebooklm.prompt.md
  - tests/test_export_notebooklm.py
source_digest: sha256:f3be2f613acfdc3042bedc6821307e30fd4d36c43e2695b7f3609ca165d94ef0
derived_from: ["[[notebooklm-ba-knowledge-export]]", "[[system-architecture]]", "[[wiki-quality-and-provenance]]"]
last_updated: 2026-08-26
tags: [module, notebooklm, exporter, ba-first, traceability]
status: active
---

# NotebookLM BA-first 離線匯出器

## 職責

`notebooklm_exporter.py` 把已確認的 BA Wiki 與安全 repo text 編排成離線 source pack。
固定 audience 是 `business-analyst`，knowledge contract 是 `business-knowledge-v1`，
retrieval contract 是 `business-first-ba-v1`。它不呼叫 NotebookLM API、不修改 raw sources，
也不把技術頁混入 BA 主文件。

## 輸入分類

| 類別 | 來源 | Pack 優先序 |
| --- | --- | --- |
| BA documents | `notebooklm_role: business` 的 overview、catalogs、glossary、gaps、process/rule pages | 必要 |
| Business evidence | `business_source_paths` 指定且通過安全政策的 UTF-8 text | 必要 |
| Technical traceability | `notebooklm_role: traceability` 的 Wiki 與其餘安全實作來源 | 可選、最後配置 |
| Excluded | `notebooklm_role: exclude`、sensitive、binary/generated/dependency、CI/IaC、Wiki/output 等 | 不匯出 |

`business_source_paths` 只可覆蓋 tests/dev-tooling 的 scope 分類，不能覆蓋 sensitive、
generated/dependency、CI/IaC、configured exclusion、Wiki/output 或 symlink/reparse boundary。
未指定角色的舊 Wiki 頁不會自動成為 BA source，preflight 會列出 warning。

## BA 結構閘門

Preflight 的 `business_coverage` 驗證：

- overview、business process catalog、business rule catalog、glossary 與 gaps 都存在、active，
  且是 `notebooklm_role: business`；
- 至少一個 active `business-process`，每個 process/rule ID 唯一；
- process 與 rule catalogs 實際連到對應頁；
- 每條 rule 的 `applies_to` 指向存在的 process；
- business page 有穩定 `notebooklm_group` 與非空 `notebooklm_terms`；
- 規則證據狀態只使用 `business-confirmed`、`implementation-observed`、`inference` 或 `gap`。

已登記 gap 可以存在；缺少結構、dangling knowledge 或 required-document stale 則
`ready_to_export=false`。

## Preflight identity 與兩次確認

Discovery 與 readiness 使用同一個唯讀命令，但扮演不同業務階段。ID 綁定 Wiki、safe
inventory、設定、DLP summary、source policy 與 retrieval contract。第一次文件更新後必然
失效；第二次結果必須展示並取得確認，apply 又會完整重算，任何漂移都 fail closed。

```text
export-notebooklm.py --root . --preflight --format json
export-notebooklm.py --root . --apply --preflight-id sha256:... --output .notebooklm
```

## 打包與路由

固定 logical source IDs：

- `query-index`：BA 問題類型與最多五個業務群組的 router；
- `project-map`：流程、規則、coverage、source roles 與 gaps 導覽；
- `docs:<group>`：完整 BA Wiki 文件；
- `business-evidence:<group>`：指定業務文字證據；
- `trace:<group>`：技術追溯；
- slot 壓力下才使用 `*:combined`，安全分割時加 `#part-###`。

選源順序永遠是 query/map → BA documents → business evidence → traceability。
`include_traceability=false` 可完全停用技術附錄；deprecated `include_evidence` 只作 alias，
若兩個 key 衝突就拒絕設定。必要 BA 內容不能因 `source_budget` 靜默消失。

## Schema v4 與 migration

Manifest 記錄 audience、knowledge/retrieval contract、business coverage、source policy、
roles、inventory、input/output hashes、limits、DLP、omissions 與 upload diff。Exporter 可讀
schema v1–v3 previous manifest，但非 `business-first-ba-v1` contract 一律設定
`migration.requires_full_rebuild=true`，要求先移除舊 static sources，避免技術優先與 BA
優先內容共存。

## 安全、容量與原子性

- Top-down walker 在進入排除樹前剪枝，只回報 bounded metadata summary，不讀取其內容。
- 只解析 UTF-8 text；非 UTF-8 或 malformed config/manifest/journal 回傳受控錯誤。
- 本機 `notebooklm-enterprise-basic` DLP 檢查高信心金融、GCP credential/API key 與明文
  password patterns；finding report 不保存命中值。
- 預設 Enterprise hard limits 為 300 sources、200 MB、500,000 words；safety limits 為
  180 MB、450,000 words，字數採 `han_characters_plus_non_han_tokens`。
- Output 使用 containment checks、transaction lock、journal、stage/backup 與 `os.replace()`；
  失敗或程序中止時保留／恢復上一份有效 pack。

## 驗證證據

- `tests/test_export_notebooklm.py` 覆蓋 schema v4、BA 必備文件、business source override、
  dangling `applies_to`、legacy alias conflict、full-rebuild migration、DLP、容量、path safety、
  process-kill recovery、並行 writer 與 500-page compaction。
- `tests/test_contracts.py::test_framework_notebooklm_preflight_is_ready` 固定本框架 Wiki 本身
  必須通過 BA readiness gate。
- 固定答案品質驗收見 `docs/validation/notebooklm-ba-uat.md`；這是手動 tenant UAT，不由
  exporter 假裝驗證生成式回答。

## 相關頁面

- [[notebooklm-ba-knowledge-export]]
- [[ba-knowledge-precedes-traceability]]
- [[readiness-preflight-required]]
- [[notebooklm-export]]
- [[business-knowledge-gaps]]
