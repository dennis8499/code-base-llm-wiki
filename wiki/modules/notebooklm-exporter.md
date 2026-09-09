---
title: NotebookLM 現況 BA／SA 匯出器
type: module
summary: 以 schema v6、discovery/readiness identity、BA／SA 配對、DLP 與原子輸出建立單一 Notebook source pack
notebooklm_group: business-notebooklm-export
notebooklm_role: exclude
sources:
  - .agents/skills/codebase-wiki/scripts/notebooklm_exporter.py
  - .agents/skills/codebase-wiki/scripts/check-stale.py
  - .agents/skills/codebase-wiki/references/notebooklm-export-workflow.md
  - .agents/skills/codebase-wiki/assets/notebooklm.toml
  - .github/prompts/export-notebooklm.prompt.md
  - tests/notebooklm/test_export_notebooklm.py
source_digest: sha256:940487342b9f3fc6226a473638b161141dd5ef4412db2f31931f4e77e234a1ab
derived_from: ["[[notebooklm-ba-knowledge-export]]", "[[system-architecture]]", "[[wiki-quality-and-provenance]]", "[[business-analysis]]"]
last_updated: 2026-09-09
tags: [module, notebooklm, exporter, ba-first, traceability]
status: active
---

# NotebookLM 現況 BA／SA 匯出器

## 職責

`notebooklm_exporter.py` 讀取完整安全 repo scope 驗證 coverage，再把已確認的每功能 BA／SA 編排成
離線 source pack。Audience 是 `business-and-system-analyst`，knowledge contract 是
`codebase-ba-sa-v1`，retrieval contract 是 `codebase-ba-sa-retrieval-v1`。它不呼叫
NotebookLM API、不修改 raw sources，也不 materialize raw evidence 或技術頁。

## 輸入分類

| 類別 | 來源 | Pack 行為 |
| --- | --- | --- |
| Capability documents | 專用 current-state profiles、`notebooklm_document: ba/sa`、相同 capability/group 的 pair | 產生本機 documents 與 upload sources |
| Analysis inputs | Safe runtime source/config/schema/docs/tests、`business_source_paths`、`extra_paths` | 本機讀取、DLP masking、coverage 驗證；不匯出 |
| Local governance | coverage ledger 與 `notebooklm_role: exclude` pages | readiness evidence；不匯出 |
| Safety exclusions | sensitive、binary/generated/dependency、CI/IaC、Wiki/output 等 | 不讀內容或不匯出 |

`business_source_paths` 只可覆蓋 dev-tooling 的 scope 分類，不能覆蓋 sensitive、
generated/dependency、CI/IaC、configured exclusion、Wiki/output 或 symlink/reparse boundary。
未指定角色的舊 Wiki 頁不會自動成為 source，preflight 會列出 warning。Standalone
[[business-analysis]]、[[system-analysis]] 與 [[system-design]] 維持各自 profiles，均不會
因 role 自動進入 schema-v6 上傳內容。

## BA／SA 結構閘門

Preflight 的 `business_coverage` 驗證：

- overview、functional requirement catalog、business process/rule catalogs、glossary、gaps 與
  local coverage ledger 都存在、active；前六份 BA documents 是 `notebooklm_role: business`；
- coverage ledger 固定 `notebooklm_role: exclude`；
- 每個 active `cap-*` 必須有固定 path 的唯一 BA／SA、專用 profiles、相同 group、互連與 locators；
- 至少一個 active requirement/process，每個 requirement/process/rule ID 唯一；
- requirement/process/rule catalogs 實際連到對應頁；
- requirement 與 rule 的 `applies_to` 指向存在的 process；
- 每個 requirement 有 `## 驗收條件` 與至少一個 stable `AC-*`；
- business page 有穩定 `notebooklm_group` 與非空 `notebooklm_terms`；
- 規則證據狀態只使用 `business-confirmed`、`implementation-observed`、`inference` 或 `gap`。
- active process 另有 `analysis_status` 與 `gap_classification`；`analysis-gap`／`untraced` 會阻擋，
  `evidence-gap` 與 `business-confirmation` 分開列出且保留已知實作行為；嚴格頁面必須有具體
  逐步條件、資料／狀態、結果、例外與定位，四步摘要不算完成。

每個 safe included file 另由 ledger 分成 `functional-evidence`、`supporting-technical`、
`no-observable-behavior` 或 `analysis-gap`。Uncovered、analysis-gap、dangling requirement、
缺少結構或 required-document stale 都使
`ready_to_export=false`。

## Discovery/readiness identity 與一次確認

Discovery 與 readiness 使用同一個唯讀命令，但有不同身分。`discovery_id` 綁定 safe raw
inventory、設定、排除與語意契約，不含 Wiki bytes；
`preflight_id` 另綁 Wiki、coverage、DLP 與 exact pack plan。使用者確認 discovery preview
一次後，Wiki 重建、knowledge promotion 與 readiness/apply 自動完成；raw/config/scope
drift 才需要新 preview。

```text
export-notebooklm.py --root . --preflight --format json
export-notebooklm.py --root . --apply --discovery-id sha256:... --preflight-id sha256:... --output .notebooklm
```

## 打包與路由

固定 logical source IDs：

- `query-index`：BA／SA 問題與最多五個 capability sources 的 router；
- `project-map`：capability 與 document/source mapping 導覽；
- `shared-business-context`：共用詞彙、流程目錄與 active 且具 sources／derived
  evidence 的跨功能流程，並嵌入適用 requirement／rule 正文供獨立閱讀；
- `capability:<cap>`：完整 BA／SA pair；
- slot 壓力下才使用 `capability:combined`，安全分割時加 `#part-###`。

輸出分成完整 `documents/{cap}-ba.md`／`-sa.md` 與只供上傳的 sources，manifest 保存雙向
mapping。Schema v6 拒絕 `ba_only`、`include_traceability`、`include_evidence` 與
`dlp_allowlist`。必要 BA／SA 內容不能因 `source_budget` 靜默消失。

在遮罩與安全分割後，`process_source_integrity` 會直接檢查即將寫入 `sources/*.md` 的 bytes：
每個 active evidence-backed process 的正文、具體步驟與適用規則正文都必須存在。這是內容與
追溯完整性檢查，不是 NotebookLM 生成式問答保證；實際 tenant 問答仍依固定 UAT 題組驗證。

## Schema v6 與 migration

Manifest 記錄 audience、knowledge/retrieval contract、functional/business coverage、file
dispositions、source policy、input/output hashes、limits、DLP phases 與 upload diff。Exporter
可讀 schema v1–v5 previous manifest，但非 `codebase-ba-sa-retrieval-v1` contract 一律設定
`migration.requires_full_rebuild=true`，要求先移除同一本 Notebook 的舊 static sources。

## 安全、容量與原子性

- Top-down walker 在進入排除樹前剪枝，只回報 bounded metadata summary，不讀取其內容。
- Wiki 是唯一持久知識層，明確排除且不進 raw discovery 或 upload source。
- Product requirements、歷史變更摘要與其他專案文件都是正常 documentation evidence；
  不再依賴已移除的工作紀錄或 delivery outcome 特殊路徑。
- 只解析 UTF-8 text；非 UTF-8 或 malformed config/manifest/journal 回傳受控錯誤。
- 本機 `notebooklm-enterprise-ba-sa-mask-v1` 在 analysis copy、documents 與 sources
  檢查高信心金融、GCP credential/API key 與明文 password patterns；先遮罩，final residual
  才阻擋，report 不保存命中值。
- 預設 Enterprise hard limits 為 300 sources、500 MB、500,000 words；safety limits 為
  450 MB、450,000 words，字數採 `han_characters_plus_non_han_tokens`。
- Output 使用 containment checks、transaction lock、journal、stage/backup 與 `os.replace()`；
  失敗或程序中止時保留／恢復上一份有效 pack。

## 驗證證據

- `tests/notebooklm/test_export_notebooklm.py` 與 acceptance/contract runner 覆蓋 schema v6、discovery、
  BA／SA pairing/mapping、完整 disposition、legacy migration、DLP、容量、path safety、
  process-kill recovery、並行 writer 與 500-page compaction。
- `tests/contracts/test_contracts.py::test_framework_notebooklm_preflight_is_ready` 固定本框架 Wiki 本身
  必須通過 BA readiness gate。
- 固定答案品質驗收見 `docs/operations/validation/notebooklm-ba-uat.md`；這是手動 tenant UAT，不由
  exporter 假裝驗證生成式回答。

## 相關頁面

- [[notebooklm-ba-knowledge-export]]
- [[notebooklm-ba-functional-export]]
- [[functional-requirement-catalog]]
- [[ba-knowledge-precedes-traceability]]
- [[readiness-preflight-required]]
- [[notebooklm-export]]
- [[business-knowledge-gaps]]
- [[business-analysis]]
- [[system-analysis]]
- [[system-design]]
