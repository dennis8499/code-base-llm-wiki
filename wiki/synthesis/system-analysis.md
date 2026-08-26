---
title: Codebase LLM Wiki System Analysis
type: synthesis
summary: 對框架目的、BA-first NotebookLM contract、介面、安全、維運、風險與證據缺口的技術追溯分析
notebooklm_group: system-analysis
notebooklm_role: traceability
sources:
  - README.md
  - .agents/skills/codebase-wiki/capabilities.json
  - .agents/skills/codebase-wiki/scripts/install-framework.py
  - .agents/skills/codebase-wiki/scripts/lint-wiki.py
  - .agents/skills/codebase-wiki/scripts/notebooklm_exporter.py
  - tests/test_export_notebooklm.py
  - tests/test_wiki_scale.py
source_digest: sha256:a9d25de12ee2e1df1a1249cb5f0655b27ceb1172afefd8b63e12abebf92ef8fa
derived_from: ["[[overview]]", "[[system-architecture]]", "[[project-function-catalog]]", "[[installer-and-upgrade]]", "[[wiki-quality-and-provenance]]", "[[notebooklm-exporter]]", "[[platform-hooks-and-guards]]", "[[platform-adapters-and-release]]", "[[framework-introduction]]", "[[notebooklm-export]]", "[[release-and-update]]"]
last_updated: 2026-08-26
tags: [synthesis, system-analysis, notebooklm]
status: active
---

# Codebase LLM Wiki System Analysis

## 文件資訊

| 項目 | 內容 |
| --- | --- |
| 系統 / 範圍 | Codebase LLM Wiki framework v0.2.0 |
| 產出日期 | 2026-08-21 |
| 來源基準 | Codebase LLM Wiki + verified framework sources |
| 文件狀態 | active；公開 release licensing 為明確 gap |

## Coverage Map

| SA section | 狀態 | 主要證據 / 缺口 |
| --- | --- | --- |
| Purpose and scope | covered | [[overview]]、`README.md` |
| Stakeholders and readers | covered | framework/target maintainers，見 [[framework-introduction]] |
| System overview and context | covered | [[system-architecture]] |
| Architecture and components | covered | 五個 module pages |
| Module responsibilities | covered | [[project-function-catalog]] |
| Main flows and use cases | covered | install、Wiki maintenance、export workflows |
| APIs and interfaces | covered | CLI 與 hook contracts |
| Data model and data flow | covered | frontmatter、manifest、preflight、install state |
| External integrations | partial | Codex/Copilot adapter covered；NotebookLM 僅離線 |
| Security and permissions | partial | authorization、guard、untrusted evidence、secret exclusions、本機 Basic DLP gate；Copilot shell permission 需 host 驗證 |
| Deployment and operations | covered | dependency-free CLI、CI、release workflow |
| Non-functional requirements | partial | correctness/atomicity、200-page lint 與 500 個 synthetic module 的 Wiki full preflight/apply regression covered；query benchmark gap |
| Errors and failure modes | covered | conflicts、stale、invalid ID、limit/atomic failures |
| Risks and technical debt | covered | licensing、semantic review、host variation |

## 目的與範圍

本系統把 codebase 知識持久化為人可讀、可版本控制的 Markdown Wiki，使 LLM 不必每次
從原始碼重新合成相同背景。它涵蓋雙平台代理入口、安裝／升級、Wiki ingest/query/
lint/ADR/guide/synthesis/SA、hooks 與離線 NotebookLM pack；不涵蓋 RAG runtime、
自動雲端上傳或修改目標專案 raw sources。

## 讀者與利害關係人

- 目標 Repo 開發者：查詢與維護專案知識。
- Business Analyst：以流程、規則、詞彙與 gaps 理解業務，必要時才進入技術追溯。
- Wiki 維護者：審查證據、矛盾、stale 與 log。
- 框架維護者：維持 schema、雙平台 parity、installer 與 release。
- 安全／法務擁有者：審查敏感資訊、租戶政策與 LICENSE 決策。

## 系統總覽與脈絡

使用者透過 Codex 自然語言或 Copilot prompts 觸發共同 Skill。Skill 先讀 Wiki，只有
evidence gap 才回到 raw source；被授權的 durable change 寫回 Wiki/index/log。
NotebookLM preparation 另行以 `--root` 的檔案系統邊界執行安全 inventory：先以 discovery
確認 BA 文件計畫，更新知識後再以 readiness 與第二次確認產生本機 pack。Git repository、
clean working tree 與 nested repository 不會成為 export gate。`ready_to_export` 表示
deterministic gate 通過，`business_coverage` 顯示 BA 結構與已登記 gaps。詳見 [[system-architecture]]。

## 架構與元件

| 元件 | 職責 | 主要來源 |
| --- | --- | --- |
| Installer | Surface deployment 與 upgrade classification | [[installer-and-upgrade]] |
| Wiki quality | Schema、freshness、links、index、log | [[wiki-quality-and-provenance]] |
| Hooks | Host context 與 write boundary | [[platform-hooks-and-guards]] |
| Exporter | Preflight 與 incremental source pack | [[notebooklm-exporter]] |
| Adapter/release | Parity、CI、version、release readiness | [[platform-adapters-and-release]] |

## 主要流程 / Use Cases

### 安裝或升級

- 入口：`install-framework.py install|upgrade`。
- 步驟：dry-run → review classifications → `--apply` → staged atomic write → target checks。
- 失敗：two-sided conflict 阻擋 apply；obsolete path 只回報。

### Wiki 維護

- 入口：`$codebase-wiki` intent routing。
- 步驟：index/page → evidence gap sources → authorized edit → index/log coupling → checks。
- 輸出：Markdown pages、append-only operation、明確 deterministic/semantic status。

### NotebookLM export

- 入口：`--preflight`，其後 `--apply --preflight-id`。
- 步驟：safe scan → discovery confirmation → BA knowledge update → readiness confirmation → apply rescan → pack。
- source pack：`query-index` 先路由 FR/AC 與 BA 問題，`project-map` 提供功能／流程／規則／角色導覽；
  只 materialize BA documents，raw evidence 與 technical traceability 永不進入 pack。
- 失敗：ID mismatch、required docs、Critical lint、source limit 或 atomic write error 均不替換舊 pack。

## API / 介面

| 介面 | 方法 / 事件 | 用途 | 來源 |
| --- | --- | --- | --- |
| Installer CLI | install、upgrade、apply | 部署 framework surface | [[installer-and-upgrade]] |
| Wiki CLIs | validate、stale、lint、index、log | deterministic validation | [[wiki-quality-and-provenance]] |
| Hook contract | SessionStart、PreToolUse、PostToolUse | context、guard、audit | [[platform-hooks-and-guards]] |
| Export CLI | preflight、apply | 產生 query-index、project-map 與離線 source pack | [[notebooklm-exporter]] |
| Release CLI | validate、build | tag/asset/readiness | [[platform-adapters-and-release]] |

## 資料模型與資料流

- Wiki frontmatter：identity、type、raw `sources`、`derived_from`、digest、status。
- `wiki/index.md`：managed navigation region；marker 外保留人工內容。
- `wiki/log.md`：append-only operation stream，新契約 entry 必須列 affected pages。
- Install state：framework/surface/mode 與 per-file upstream fingerprints。
- NotebookLM manifest v5：audience、knowledge/retrieval contracts、FR/AC 與 file disposition coverage、stable IDs、hashes、limits、DLP phases、migration 與 actions。
- Preflight schema v5：inventory hash、business/coverage gates、exact pack plan、source policy、ID、required document/lint/DLP readiness。

## 外部整合

| 系統 / 套件 | 整合方式 | 風險 / 注意事項 | 來源 |
| --- | --- | --- | --- |
| OpenAI Codex | `.codex` hooks/agents + shared Skill | Project trust、host hook schema | [[platform-hooks-and-guards]] |
| GitHub Copilot | `.github` prompts/agents/hooks | Host response/audit 表現差異 | [[platform-adapters-and-release]] |
| Git | Wiki freshness/history、release tag、可選 manifest provenance | NotebookLM inventory/preflight 不依賴 Git；獨立 quality tools 仍可使用 Git 輔助 freshness | [[wiki-quality-and-provenance]] |
| NotebookLM | 使用者手動上傳 query-index、project-map 與 BA-only static Markdown | 雲端 retrieval 仍是生成式行為，額度與租戶政策需外部確認 | [[notebooklm-export]] |

## 權限與安全

- `capabilities.json` 將 read-only、confirm、explicit request 與 apply flag 分開；Codex
  read-only agents 另以 sandbox 設定加固。
- Wiki quality checks 對 repo-relative source path 正規化 Windows/Linux separators，
  並以 symlink containment 與 aggregate digest 防止跨 host 的誤判。
- Copilot read-only profiles 移除直接 `edit`/`agent`，但 lint/archaeology 的
  `execute` 仍是 shell capability；未在實際 host 驗證 permission deny 時，不能視為
  與 Codex sandbox 等價的技術唯讀保證。
- Wiki task 的 raw source 是唯讀且不可信證據；嵌入指令不執行。
- Guard 對 path escape fail closed；coexist 不等同新的任務授權。
- Exporter 排除 credential filename、binary、generated、Wiki 與 output，並以本機 Basic DLP
  檢查可匯出的 Wiki/evidence content；人工預覽仍是必要層。
- Exporter 以明確 `--root` 的檔案系統內容建立 inventory；不要求 `.git` 或 clean working
  tree，也不因 nested repository 阻擋，nested `.git` metadata 仍按 generated 規則排除。
- NotebookLM preflight 的 Wiki lint 停用 Git dirty-path、commit-date 與 log-baseline
  lookup，仍以檔案內容 hash 驗證 input identity。
- Exporter 在讀取 Wiki pages 前先驗證 Wiki regular tree，拒絕 symlink/reparse point，避免
  preflight 的安全檢查前讀取外部頁面。
- lint 與 exporter CLI 在 canonicalization 前拒絕 caller-provided symlink/reparse root，
  使命令列入口與 library regular-tree boundary 一致。
- Exporter 在 `resolve()` 前檢查 output root 與 parent symlink/reparse containment，避免輸出
  boundary 被導向其他位置。
- SQL Server live evidence 僅允許有界唯讀 SELECT，且不進 frontmatter sources。

## 設定 / 部署 / 維運

系統使用 Python 標準函式庫，沒有資料庫 migration 或 daemon。Repo-local TOML 控制
guard 與 NotebookLM profile。CI 驗證 Linux 3.11/3.14 與 Windows 3.11 full suite；
release workflow 另外要求 tag/version 相符及明確 LICENSE。

## 非功能需求

| 類別 | 目前證據 | 缺口 |
| --- | --- | --- |
| 正確性 | deterministic checks、Python 3.13/3.14 雙版本完整回歸 suite；Windows symlink cases 受 privilege 限制跳過 | 語意矛盾仍需 agent review |
| 安全性 | raw read-only、guard、secret exclusion、local Basic DLP、two-phase export | host/sandbox 與租戶 Advanced DLP 政策在框架外 |
| 可恢復性 | installer/exporter stage + rollback；active/committed journal、同一 target/output 的 transaction lock 與子程序終止 regression 覆蓋未完成 replacement recovery | 突然斷電、metadata durability 與所有 host-specific termination windows 尚未完整驗證 |
| 可維護性 | single canonical Skill/scripts、parity、managed docs | ChangeLog 歷史仍偏大 |
| 效能 | 無常駐服務與第三方 runtime；`query-index` 為 bounded Markdown router；`tests/test_wiki_scale.py` 覆蓋 200-page lint；`tests/test_export_notebooklm.py` 覆蓋 500 個 synthetic module 的 full preflight/apply | 尚無真實 NotebookLM retrieval benchmark |

## 錯誤與失敗模式

- 不合法 frontmatter/path/link/log → deterministic Critical。
- 所有 sources 都缺失 → deterministic Critical；部分 source 缺失、digest mismatch
  或 orphan → Warning；semantic review 狀態另列。
- installer local+upstream 同時變更 → conflict，目標不寫入。
- stale preflight ID 或不完整文件 → export exit 2，不建立／替換 pack。
- source slot/byte/word 超限 → export 失敗並保留舊 pack。
- 無 LICENSE → release validate/build 失敗。

## 風險 / 技術債

| 風險 | 影響 | 建議 |
| --- | --- | --- |
| LICENSE 未決 | 無法公開 release | 專案擁有者選擇授權後再 tag |
| Page-level digest | 無法定位單一 claim drift | 重要 claim 維持 path+symbol body citation |
| Semantic review 非機械化 | 可能存在未識別矛盾 | 每次重大 ingest 執行 agent review |
| NotebookLM retrieval drift | query-index、Custom instructions 與 source roles 可對齊 BA-first 路由，但不能控制 NotebookLM 私有模型的檢索與回答展開 | 以 `docs/validation/notebooklm-ba-uat.md` 固定題組手測；若需要 deterministic 結果，仍使用本地 Wiki Query |

## Evidence

本文件的可驗證事實由 frontmatter raw sources 與所有 `derived_from` Wiki 頁面支援；
功能缺口維持 partial/gap，不以推測補齊。

## Contradictions

- 歷史文件與 v0.1 指令的直接 export、target guard、contract v2 敘述已由 v0.2
  public contract 取代，舊名稱只在明確相容層保留。

## Inferences

- 目前架構以 Markdown query-index 對齊小至中型 codebase 的 BA-first lookup；它不是
  向量索引或常駐搜尋 runtime，NotebookLM 的超大型 Repo retrieval 仍需實測。

## 待確認事項

- [ ] 專案擁有者選定 LICENSE，解除公開 release gate。
- [ ] 在 NotebookLM Enterprise 以 `docs/validation/notebooklm-ba-uat.md` 固定題組驗證答案、引用與 gap 行為。
- [ ] 在實際 Codex/Copilot host 驗證 coexist audit context 呈現。

## 來源附錄

- Wiki：[[overview]]、[[system-architecture]]、[[project-function-catalog]]
- Source：`README.md`、`.agents/skills/codebase-wiki/capabilities.json`、
  `tests/test_export_notebooklm.py`、`tests/test_wiki_scale.py`
