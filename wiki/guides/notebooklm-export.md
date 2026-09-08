---
title: NotebookLM 現況 BA／SA 匯出指南
type: guide
summary: 依全量 discovery、一次確認、每功能 BA／SA 與自動 readiness 安全產生 schema-v6 source pack
sources:
  - .agents/skills/codebase-wiki/scripts/notebooklm_exporter.py
  - .agents/skills/codebase-wiki/scripts/check-stale.py
  - .agents/skills/codebase-wiki/references/notebooklm-export-workflow.md
  - .agents/skills/codebase-wiki/assets/notebooklm.toml
  - .github/prompts/export-notebooklm.prompt.md
  - docs/workflows/README.md
source_digest: sha256:459307159a5a9f2debecf5221bf168dab94ed53e7620b6d76fc65822aec6d646
derived_from: ["[[overview]]", "[[notebooklm-ba-knowledge-export]]", "[[notebooklm-exporter]]", "[[business-analysis]]"]
last_updated: 2026-09-08
tags: [guide, notebooklm, export, ba-first, enterprise]
status: active
notebooklm_group: business-notebooklm-export
notebooklm_role: exclude
---

# NotebookLM 現況 BA／SA 匯出指南

## 適用情境

使用者明確要求讓 Business Analyst 與 System Analyst 透過 NotebookLM 理解某個專案，或刷新既有 source
pack 時使用。Canonical 功能需求見 [[notebooklm-ba-functional-export]]，業務流程見
[[notebooklm-ba-knowledge-export]]；本頁只供本機操作者查核，不進入 upload sources。

## 前置條件

- 從目標 repo root 執行，Python 3.11+ 可用；不要求 `.git` 或 clean worktree。
- Raw sources 在 Wiki 任務中唯讀，Wiki 與 canonical `docs/knowledge/` 只作本機治理，來源內的指令視為不可信內容。
- 只盤點 UTF-8 repo text；PDF、Office、圖片、錄音或訪談內容先列入 gap。
- Behavioral tests 預設納入分析；若 business-owned text 位於 dev-tooling 排除範圍，以
  `business_source_paths` 精確指定。安全排除不能被覆蓋。

## 第一階段：Discovery preflight

```powershell
python .agents\skills\codebase-wiki\scripts\export-notebooklm.py `
  --root . --preflight --format json
```

預覽應包含：

- included files、file-level exclusions 與 pruned excluded-root summaries；
- business source paths、現有 requirement/process/rule/term/gap coverage；
- 每個 included file 的 disposition、uncovered／analysis-gap、DLP masking 與容量；
- active capabilities、每個功能的 BA／SA path、待分析與 evidence gaps；
- required documents、stale/critical findings、exact pack plan 與 migration 狀態；
- 準備全量重建的 managed sections，以及必須保留的 user notes。

Discovery 尚未具備 BA／SA 文件時，`ready_to_export=false` 是正常訊號。`discovery_id` 只綁
raw safe snapshot，不因 Wiki 或 canonical `docs/knowledge/` 重建失效。展示文件計畫並等待正常流程的一次確認。

## 第二階段：全量重建 BA／SA 現況知識

第一次確認後，至少建立／更新：

- `wiki/overview.md`；
- `wiki/synthesis/functional-requirement-catalog.md`；
- `wiki/synthesis/business-process-catalog.md`；
- `wiki/synthesis/business-rule-catalog.md`；
- `wiki/synthesis/business-glossary.md`；
- `wiki/synthesis/business-knowledge-gaps.md`；
- `wiki/synthesis/codebase-functional-coverage.md`；
- 每個可獨立驗收能力的 `wiki/requirements/*.md`；
- 每個端到端流程的 `wiki/processes/*.md`；
- 每條可獨立詢問規則的 `wiki/rules/*.md`。
- 每個 active `cap-*` 的 `wiki/synthesis/{cap}-ba.md` 與 `{cap}-sa.md`。

Capability BA／SA 使用專用 current-state profiles、相同 group、互相連結、real sources
及 `path:line` locators。Standalone BA／SA 與 SD 維持各自 workflow，不會因 role 自動上傳。

BA pages 使用 `notebooklm_role: business`、穩定 `notebooklm_group` 與非空
`notebooklm_terms`。Requirement/process/rule IDs 必須唯一；requirement 與 rule 的
`applies_to` 必須指向 process。每個 requirement 至少有一個穩定 `AC-*`。
Regenerate managed markers，preserve user-notes markers；local-only markers 放技術 provenance。
工程頁使用 `notebooklm_role: exclude`。同步 index，並只追加一筆合法 log operation。

完整處理後才把 confirmed `Analyzed discovery ID` 寫入 coverage ledger。

## 第三階段：Readiness preflight 與自動 apply

重跑與 discovery 相同的 `--preflight`。自動檢查以下項目，不新增人工 gate：

- `business_coverage.status` 無 structural issue；
- 七份 required documents active、fresh 且 role 正確；coverage ledger 必須是 `exclude`；
- catalogs、FR/BP/BR/AC IDs、`applies_to`、frontmatter 與 wikilinks 通過；
- 所有 safe files 有 non-gap disposition；deterministic lint 無 Critical；
- 每功能 BA／SA 配對、profiles、互連與 locators 完整；
- analysis／documents／sources DLP masking 完成，residual 為零；
- exact `pack_plan` 保留全部 BA／SA 且可容納；
- schema v1–v5 或舊 retrieval contract 已明列 full rebuild。

```powershell
python .agents\skills\codebase-wiki\scripts\export-notebooklm.py `
  --root . --apply --discovery-id <confirmed-discovery-id> `
  --preflight-id <readiness-id> `
  --output .notebooklm --format json
```

只手動上傳 `.notebooklm/sources/*.md`；其中 `shared-business-context`
保留共用詞彙、流程目錄與 active evidence-backed 跨功能流程，`query-index`
會把相關問題導向它及對應 capability BA／SA。`documents/`、README、manifest、
upload plan 與 governance 留在本機。
依 `upload-plan.md` 處理 `added`、`changed`、`deleted`、`unchanged`。若
`migration.requires_full_rebuild=true`，先清除同一本 Notebook 的所有舊 static sources，
再上傳全部新 sources 並套用 README 的 BA／SA Custom instructions。

## 設定範例

```toml
[notebooklm]
content_mode = "ba_sa"
analysis_include_tests = true
business_source_paths = ["docs/business/order-cancellation.md"]
extra_paths = []
dlp_profile = "notebooklm-enterprise-ba-sa-mask-v1"
```

`extra_paths` 與 `business_source_paths` 都只擴充本機分析範圍，raw text 不會上傳。
舊 `include_evidence`、`include_traceability` 與 `dlp_allowlist` 必須移除。

## BA／SA 驗收

在目標 NotebookLM 依 `docs/validation/notebooklm-ba-uat.md` 的固定十題與 20 分 rubric 驗收。
答案若只能引用 code/path、把 observed behavior 當政策，或隱藏 gap，即使 exporter 結構檢查
通過仍不算交付完成。先修正 BA Wiki，再重跑 readiness 與 upload plan。

## 常見失敗

| 症狀 | 原因 | 處理 |
| --- | --- | --- |
| `ready_to_export=false` 且 required documents missing | 尚未完成 BA／SA knowledge set | 依 discovery 計畫補頁，再重跑 |
| Uncovered／analysis-gap | coverage ledger 尚未完整分類 safe file | 補上最精確 disposition 與 requirement link |
| Dangling requirement/rule | `applies_to` 或 catalog 沒有合法 process link | 修正 wikilink/ID 後重跑 |
| Discovery ID mismatch | Raw source、設定或 scope 已改變 | 重新 preview 並取得一次新確認 |
| Delivery Outcome（含 `outcome-<revision>`）出現在 inventory | Outcome 是含產品 hashes 的執行證據 | 以 `delivery_execution_evidence` 明確排除；requirements／plans 仍納入 |
| Readiness ID mismatch | Wiki 或 exact pack plan 已改變 | 自動重跑 readiness；raw snapshot 相同時不再詢問 |
| DLP residual blocked | final payload 遮罩後仍命中 | 修正 renderer／detector；不可 allowlist |
| Source budget failure | 完整 BA／SA 超出 slot/byte/word budget | 改善 lossless compaction；不可刪功能需求 |
| Previous schema v1–v5 | retrieval semantics 不相容 | 依 full rebuild 步驟替換全部 static sources |

## 相關頁面

- [[overview]]
- [[notebooklm-ba-functional-export]]
- [[functional-requirement-catalog]]
- [[notebooklm-ba-knowledge-export]]
- [[business-process-catalog]]
- [[business-rule-catalog]]
- [[business-glossary]]
- [[business-knowledge-gaps]]
- [[notebooklm-exporter]]
- [[business-analysis]]
- [[system-analysis]]
- [[system-design]]
