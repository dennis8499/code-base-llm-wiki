---
title: Codebase LLM Wiki System Analysis
type: synthesis
summary: 對框架目的、元件、流程、介面、安全、維運、風險與證據缺口的整體可追溯分析
notebooklm_group: system-analysis
sources:
  - README.md
  - .agents/skills/codebase-wiki/capabilities.json
  - .agents/skills/codebase-wiki/scripts/install-framework.py
  - .agents/skills/codebase-wiki/scripts/lint-wiki.py
  - .agents/skills/codebase-wiki/scripts/notebooklm_exporter.py
source_digest: sha256:262c00b2fd9e02da1b11a9a65074d31c74f1e8506629ba14fffe6e9ab1748bab
derived_from: ["[[overview]]", "[[system-architecture]]", "[[project-function-catalog]]", "[[installer-and-upgrade]]", "[[wiki-quality-and-provenance]]", "[[notebooklm-exporter]]", "[[platform-hooks-and-guards]]", "[[platform-adapters-and-release]]", "[[framework-introduction]]", "[[notebooklm-export]]", "[[release-and-update]]"]
last_updated: 2026-08-21
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
| Security and permissions | covered | authorization、guard、untrusted evidence、secret exclusions |
| Deployment and operations | covered | dependency-free CLI、CI、release workflow |
| Non-functional requirements | partial | correctness/atomicity 與 200-page lint regression covered；500+ pages benchmark gap |
| Errors and failure modes | covered | conflicts、stale、invalid ID、limit/atomic failures |
| Risks and technical debt | covered | licensing、semantic review、host variation |

## 目的與範圍

本系統把 codebase 知識持久化為人可讀、可版本控制的 Markdown Wiki，使 LLM 不必每次
從原始碼重新合成相同背景。它涵蓋雙平台代理入口、安裝／升級、Wiki ingest/query/
lint/ADR/guide/synthesis/SA、hooks 與離線 NotebookLM pack；不涵蓋 RAG runtime、
自動雲端上傳或修改目標專案 raw sources。

## 讀者與利害關係人

- 目標 Repo 開發者：查詢與維護專案知識。
- Wiki 維護者：審查證據、矛盾、stale 與 log。
- 框架維護者：維持 schema、雙平台 parity、installer 與 release。
- 安全／法務擁有者：審查敏感資訊、租戶政策與 LICENSE 決策。

## 系統總覽與脈絡

使用者透過 Codex 自然語言或 Copilot prompts 觸發共同 Skill。Skill 先讀 Wiki，只有
evidence gap 才回到 raw source；被授權的 durable change 寫回 Wiki/index/log。
NotebookLM preparation 另行執行安全全量 inventory，並在 preflight 與人工確認後產生
本機靜態 pack；`ready_to_export` 與 `coverage.status` 分別表示 gate readiness 與 Wiki
source coverage。詳見 [[system-architecture]]。

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
- 步驟：safe scan → function/document coverage → confirmation → required docs → apply rescan → pack。
- 失敗：ID mismatch、required docs、Critical lint、source limit 或 atomic write error 均不替換舊 pack。

## API / 介面

| 介面 | 方法 / 事件 | 用途 | 來源 |
| --- | --- | --- | --- |
| Installer CLI | install、upgrade、apply | 部署 framework surface | [[installer-and-upgrade]] |
| Wiki CLIs | validate、stale、lint、index、log | deterministic validation | [[wiki-quality-and-provenance]] |
| Hook contract | SessionStart、PreToolUse、PostToolUse | context、guard、audit | [[platform-hooks-and-guards]] |
| Export CLI | preflight、apply | 產生離線 source pack | [[notebooklm-exporter]] |
| Release CLI | validate、build | tag/asset/readiness | [[platform-adapters-and-release]] |

## 資料模型與資料流

- Wiki frontmatter：identity、type、raw `sources`、`derived_from`、digest、status。
- `wiki/index.md`：managed navigation region；marker 外保留人工內容。
- `wiki/log.md`：append-only operation stream，新契約 entry 必須列 affected pages。
- Install state：framework/surface/mode 與 per-file upstream fingerprints。
- NotebookLM manifest v2：stable logical source IDs、input/output hashes、coverage、limits、actions。
- Preflight contract v1：inventory hash、ID、required document/lint readiness。

## 外部整合

| 系統 / 套件 | 整合方式 | 風險 / 注意事項 | 來源 |
| --- | --- | --- | --- |
| OpenAI Codex | `.codex` hooks/agents + shared Skill | Project trust、host hook schema | [[platform-hooks-and-guards]] |
| GitHub Copilot | `.github` prompts/agents/hooks | Host response/audit 表現差異 | [[platform-adapters-and-release]] |
| Git | inventory、dirty paths、history、release tag | 無 Git 時部分工具使用 filesystem fallback | [[wiki-quality-and-provenance]] |
| NotebookLM | 使用者手動上傳 static Markdown | 額度與租戶政策需外部確認 | [[notebooklm-export]] |

## 權限與安全

- `capabilities.json` 將 read-only、confirm、explicit request 與 apply flag 分開；Codex
  read-only agents 另以 sandbox 設定加固。
- Wiki task 的 raw source 是唯讀且不可信證據；嵌入指令不執行。
- Guard 對 path escape fail closed；coexist 不等同新的任務授權。
- Exporter 排除 credential filename、binary、generated、Wiki 與 output，人工預覽仍是必要層。
- SQL Server live evidence 僅允許有界唯讀 SELECT，且不進 frontmatter sources。

## 設定 / 部署 / 維運

系統使用 Python 標準函式庫，沒有資料庫 migration 或 daemon。Repo-local TOML 控制
guard 與 NotebookLM profile。CI 驗證 Linux 3.11/3.14 與 Windows 3.11 full suite；
release workflow 另外要求 tag/version 相符及明確 LICENSE。

## 非功能需求

| 類別 | 目前證據 | 缺口 |
| --- | --- | --- |
| 正確性 | deterministic checks、68 unit scenarios | 語意矛盾仍需 agent review |
| 安全性 | raw read-only、guard、secret exclusion、two-phase export | host/sandbox 與租戶政策在框架外 |
| 可恢復性 | installer/exporter stage + rollback | 未做 process-kill fault injection |
| 可維護性 | single canonical Skill/scripts、parity、managed docs | ChangeLog 歷史仍偏大 |
| 效能 | 無常駐服務與第三方 runtime；200-page lint regression | 尚無 500+ Wiki pages lint/query/export benchmark |

## 錯誤與失敗模式

- 不合法 frontmatter/path/link/log → deterministic Critical。
- source missing/digest mismatch/orphan → Warning；semantic review 狀態另列。
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
| Large Wiki scale | 200-page lint regression 已覆蓋；更大規模查詢可能變慢 | 先完成 500+ pages benchmark，再以證據評估分層 index 或 optional adapter |

## Evidence

本文件的可驗證事實由 frontmatter raw sources 與所有 `derived_from` Wiki 頁面支援；
功能缺口維持 partial/gap，不以推測補齊。

## Contradictions

- 歷史文件與 v0.1 指令的直接 export、target guard、contract v2 敘述已由 v0.2
  public contract 取代，舊名稱只在明確相容層保留。

## Inferences

- 目前架構足以服務小至中型 codebase；超大型 Repo 的容量與查詢效能仍需要實測後
  才能決定是否加入 optional search adapter。

## 待確認事項

- [ ] 專案擁有者選定 LICENSE，解除公開 release gate。
- [ ] 在真實或合成 500+ pages Wiki 執行 lint/query/export benchmark。
- [ ] 在實際 Codex/Copilot host 驗證 coexist audit context 呈現。

## 來源附錄

- Wiki：[[overview]]、[[system-architecture]]、[[project-function-catalog]]
- Source：`README.md`、`.agents/skills/codebase-wiki/capabilities.json`
