---
title: Codebase LLM Wiki — 專案總覽
type: overview
summary: 以 Wiki-first、唯讀原始證據與共享雙平台規格持續累積可追溯 codebase 知識
sources:
  - README.md
  - AGENTS.md
  - .agents/skills/codebase-wiki/capabilities.json
  - .agents/skills/codebase-wiki/scripts/install-framework.py
  - .agents/skills/codebase-wiki/scripts/notebooklm_exporter.py
source_digest: sha256:fb106e6ab6b12d8af27748f03177382364669b8ce18005f409811791dbca3d61
derived_from: []
last_updated: 2026-08-26
tags: [framework, llm, wiki, copilot, codex]
status: active
notebooklm_group: project
---

# Codebase LLM Wiki — 專案總覽

> 讓 GitHub Copilot 或 OpenAI Codex 為任意 codebase 增量建構並維護可追溯的 Markdown 知識庫。

## 核心定位

Codebase LLM Wiki 是面向 coding agents 的持久知識框架。Agent 將已理解的模組、實體、模式、決策與操作經驗保存到 `wiki/`；後續問題先讀 Wiki，只有內容不足、過時或矛盾時才回溯 raw sources。

**這不是 RAG。** 框架不建立向量資料庫、本機 source index 或完整原始碼副本。知識直接以可閱讀、可版本控制、可交叉引用的 Markdown 累積。

## 三層模型

| 層 | 位置 | 責任 |
| --- | --- | --- |
| Raw Sources | 目標專案的原始碼、設定與既有文件 | Wiki 任務中唯讀 |
| Wiki | `wiki/` | 持久知識、主索引、活動紀錄 |
| Schema | `AGENTS.md`、`.agents/`、`.github/`、`.codex/` | 意圖、工作流、模板、scripts、hooks 與平台入口 |

NotebookLM delivery pack 是由 Schema/Workflow 產生的可審查交付物，不是第四個
知識層：Agent 每次以明確 `--root` 的檔案系統目錄為邊界安全掃描全專案，依功能補齊
Wiki，再將完整文件與精選 evidence 寫入 `.notebooklm/`。掃描不要求 Git repository、
clean working tree 或 root `.git`；nested repository 的專案檔案照常納入，`.git` metadata
仍排除。Pack 只供手動上傳，包含 `query-index`、`project-map`、Markdown
sources、manifest 與增量 upload plan，預設不進 Git，也不會自動連線 NotebookLM。
Exporter 在 canonicalize output path 前拒絕 output root 或其 parent components
透過 symlink/reparse point 到達，避免 pack boundary 被繞過。

```text
Schema instructions + Skill
            │
            ▼
     Copilot / Codex
       │           │
       │ Wiki-first│ evidence gap
       ▼           ▼
     wiki/      Raw Sources
       ▲           │
       └───────────┘
       evidence-backed updates
```

## Repo 產品結構

```text
code-base-llm-wiki/
├── .agents/skills/codebase-wiki/  — 雙平台共用 Skill、規格、模板與 scripts
├── .github/                        — Copilot agents、prompts、hooks、instructions
├── .codex/                         — Codex hooks、設定與 optional agents
├── docs/                           — 架構、安裝、工作流、驗證與歷史文件
├── tools/release.py                — 版號驗證、Release assets 與更新 manifest
├── samples/task-tracker/           — 無第三方依賴的 E2E 驗證 codebase
├── tests/                          — Deterministic regression tests
├── wiki/                           — 本 Repo 的持久知識庫
├── .notebooklm/                    — 本機產生、預設忽略的 NotebookLM source pack
├── AGENTS.md                       — Codex 專案規則
├── Codex.md                        — 可隨 Codex surface 安裝的操作手冊
├── VERSION                         — 唯一產品版號來源
├── ChangeLog.md                    — 重要變更
└── README.md                       — 公開導覽與快速開始
```

`docs/`、`samples/`、`tests/` 是框架 Repo 的產品文件與驗證資產，不會被 installer 複製到目標專案。框架自己的 `wiki/` 也不會外洩到目標；installer 由 `.agents/skills/codebase-wiki/assets/wiki-starter/` 建立乾淨 Wiki 骨架。原始方法論與早期 prompt 保留於 `docs/history/`。

## 版本與發佈

根目錄 `VERSION` 是唯一產品版號來源，採穩定 `X.Y.Z`，並以 `vX.Y.Z` 作為
Git tag。GitHub Release workflow 會先驗證 tag 與版號，再產生 ZIP/TAR.GZ、
`SHA256SUMS` 與 `update-manifest.json`。Installer 將相同版號保存至目標 Repo
的 `.agents/skills/codebase-wiki/VERSION`；`contract_version: 3` 則維持獨立，
代表 installer contract 而非產品版號。

公開 Release 另有 LICENSE readiness gate；目前版號已進入 0.2.0，但在專案
擁有者選定授權前不會產生公開資產。

未來 Extension 可讀取最新 manifest，依本地版本做 SemVer 比較，驗證下載資產
後呼叫既有 conflict-safe `upgrade`；目前不包含 Extension updater。

## 雙平台入口

| 能力 | GitHub Copilot | OpenAI Codex |
| --- | --- | --- |
| 全域規則 | `.github/copilot-instructions.md` | `AGENTS.md` |
| 共用工作流 | `.agents/skills/codebase-wiki/` | `.agents/skills/codebase-wiki/` |
| 專業代理 | `.github/agents/*.agent.md` | `.codex/agents/*.toml` |
| 使用者入口 | `.github/prompts/*.prompt.md` | `Codex.md` recipes |
| Hooks | `.github/hooks/` | `.codex/hooks.json` |

兩個入口共用 contract version 3、十個使用者意圖群組、十一個 machine
operations、authorization policy、Wiki page schema、安全邊界與驗收標準。
Hook configuration 共同呼叫 `.agents/skills/codebase-wiki/scripts/hooks/`
的 canonical implementation。Codex 使用 workspace-relative command；Windows
`commandWindows` 遵循 `cmd.exe` 語法，不使用 PowerShell `$()` substitution 或
nested quoted paths。Delegation 只有使用者明確要求時啟用。

## 核心工作流

- **Install / setup**：Installer 只發佈 `codebase-wiki` Skill；install 建立
  starter，upgrade 保留既有 Wiki；`--apply` 且無 conflicts 才以 staging/rollback
  寫入，並保存 framework version 與 fingerprint manifest。
- **Ingest**：讀 source evidence，建立或更新 module、entity、pattern 等頁面。
- **Query**：先讀 `wiki/index.md` 與 1–5 個相關頁面，預設唯讀。
- **Lint**：唯讀聚合 frontmatter、digest freshness、orphan、broken link、index、
  append-only log 與 stats，並分開回報 deterministic/semantic status。
- **Follow-up actions**：高價值 Query 與 Lint findings 可提供有界的 Synthesis、Guide、重新 Ingest 或 Lint 選項；選項不會自動寫入或 Hand-Off。
- **Archaeology**：追蹤 call path 與非破壞性 Git history。
- **ADR / Synthesis / Guide / SA**：保存 durable decision、analysis 與操作知識。
- **NotebookLM export**：每次以 `--root` 進行檔案系統全量掃描，完成必要功能文件後取得
  `preflight_id`；apply 重新驗證相同輸入與本機 DLP gate，才產生含有
  `query-index`/`project-map` 的 documents-first source pack。Query index 將
  Wiki-first direct-lookup contract 帶入 NotebookLM，但不建立常駐搜尋服務；export
  preflight 不依賴 Git status、commit date 或 log baseline。
- **Delegation**：明確要求時才路由給專業代理。

## 安全與品質

- `frontmatter.sources` 只能列出真實 raw Repo-relative paths；Wiki 衍生證據使用
  `derived_from`，內容 freshness 使用 `source_digest`。
- Wiki pages 透過 `[[wikilink]]` 互相引用。
- `wiki/log.md` 只能追加，不能刪除或改寫既有條目。
- `wiki-only` 只允許 Wiki；`coexist` 支援正常 coding session；`framework` 才允許
  維護 schema、adapters、docs、samples、tests 與 release tooling。
- NotebookLM export 預設使用 300 sources、每 source 200 MB / 500,000 words 的 Enterprise hard limits，實際 pack 以 180 MB / 450,000 words safety limits 先行切分或失敗；文件優先保留，低優先 evidence 的省略會透明記錄，Workspace tier 可在 `notebooklm.toml` 再下調。
- Exporter 另以 `notebooklm-enterprise-basic` 在本機檢查信用卡、金融帳號、GCP credentials、GCP API key 與明文密碼；未 allowlist finding 會阻擋 apply，報告不保存敏感原文。
- SQL Server live evidence 只允許 bounded read-only 查詢，且不得放入 frontmatter sources。

## 驗證方式

框架提供 installer/contract/guard/format tests，以及 parity、frontmatter、
stale-source、唯讀 lint、index、append-only log check 與 Wiki stats scripts。
`samples/task-tracker/` 以三次重複情境驗證兩平台的 process invariants，
同時確認 raw source hashes 未變更。

## 相關頁面

- [[framework-introduction]] — 安裝、操作、驗收與常見陷阱指南
- [[notebooklm-export]] — 全專案功能文件化、documents-first NotebookLM Enterprise source pack 與增量上傳計畫
- [[release-and-update]] — 版本、GitHub Release、下載與 Extension manifest
- [[system-architecture]] — 元件、資料流、部署與已知 gap
- [[project-function-catalog]] — 五個產品功能域及 coverage
- [[system-analysis]] — 系統級介面、安全、失敗模式與風險
