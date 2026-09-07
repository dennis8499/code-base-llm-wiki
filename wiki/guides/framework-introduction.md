---
title: Codebase LLM Wiki — 使用指南
type: guide
summary: 從安裝、Wiki-first 操作到驗證與升級的框架使用路線
sources:
  - README.md
  - Codex.md
  - docs/setup/README.md
  - docs/workflows/README.md
  - docs/validation/README.md
source_digest: sha256:9447d81adbc410e642c273e1abf72215531a80ae2069b620eca41191170f815c
derived_from: ["[[overview]]", "[[installer-and-upgrade]]", "[[platform-hooks-and-guards]]"]
last_updated: 2026-09-07
tags: [guide, onboarding, framework, copilot, codex]
status: active
notebooklm_group: project-guides
notebooklm_role: traceability
---

# Codebase LLM Wiki — 使用指南

> 本頁是既有 `type: guide` 的 legacy 相容資料，仍可查詢、驗證與匯出；v5 不再
> 提供新 Guide 建立流程。以下內容提供框架使用者最短的安裝、操作與驗收路線。
> 架構背景請先閱讀 [[overview]]。

## 適用讀者

- 想把 Codebase LLM Wiki 安裝到既有 Repo 的維護者；
- 使用 GitHub Copilot 或 OpenAI Codex 維護 codebase 知識的人；
- 需要驗證雙入口能力、安全邊界或 Wiki 品質的框架貢獻者。
- 想把本地 Wiki 以可追蹤、可增量更新的方式交付給 NotebookLM Enterprise 使用者的人。

## 前置需求

- Git（版本控制與部分 Wiki freshness/history 功能需要；NotebookLM export 不要求）；
- Python 3.11+；
- GitHub Copilot Chat 或 OpenAI Codex，依選用入口決定；
- 對目標 Repo 的讀取權限，以及對框架 schema/Wiki 的必要寫入權限。

框架不需要向量資料庫、Node.js、MCP 搜尋服務、PyYAML 或其他第三方 Python 套件。

## 1. 選擇入口

| 需求 | 建議入口 | 安裝內容 |
| --- | --- | --- |
| VS Code Copilot prompts、hooks | Copilot surface | `AGENTS.md`、`codebase-wiki` Skill、`.github/`、`wiki/` |
| 其他 GitHub Copilot hosts | Copilot surface 的共用 Skill | 以自然語言使用 `.agents/skills/codebase-wiki/`；不依賴 VS Code prompt files |
| Codex CLI、IDE、App、Cloud task | Codex surface | `AGENTS.md`、`Codex.md`、`codebase-wiki` Skill、`.codex/`、`wiki/` |
| 同一 Repo 同時支援兩者 | 分別評估並合併兩種 surface | 共用 `.agents/` 與 `wiki/` |

雙入口的能力相同，但平台 adapter 不相同。Codex 不使用 project-level slash prompts；
Copilot prompt files 也不會被假裝成非 VS Code host 功能。Copilot 驗收標示為
`static-compatible / runtime-unverified`；Codex v6 也完成本機契約與 deterministic
驗證，但尚未重跑 host runtime UAT。2026-09-03 的 v4 Codex evidence 只作歷史基線。

## 2. 先 Dry-run 再安裝

```powershell
python .agents\skills\codebase-wiki\scripts\install-framework.py install --target C:\path\to\target --surface codex --guard-mode wiki-only --format json
python .agents\skills\codebase-wiki\scripts\install-framework.py install --target C:\path\to\target --surface codex --guard-mode wiki-only --apply --format json
```

將 `codex` 換成 `copilot` 即可安裝另一入口。Installer allowlist 只包含
`codebase-wiki` Skill。`install` 建立乾淨 starter；`upgrade` 保留既有
Wiki。只有沒有 `conflicts` 時才 apply，且不會自動刪除 legacy
`.codebase-wiki/`。

## 版本與下載

框架版號由根目錄 `VERSION` 唯一管理，使用穩定 `X.Y.Z`，Git tag 使用
`vX.Y.Z`。安裝或升級後，可在目標 Repo 的
`.agents/skills/codebase-wiki/VERSION` 查看已安裝版本。

手動建立的 GitHub Release 提供 ZIP、TAR.GZ、`SHA256SUMS` 與
`update-manifest.json`。未來
Extension 可比較本地版本與 manifest 版本，驗證 checksum 後呼叫 `upgrade`；
目前 Extension updater 尚未包含在框架內。完整 tag、發佈與 manifest 契約請看
`docs/releases/README.md`。

## 3. 第一次 Ingest

先選擇明確範圍，要求 Agent 摘要後再寫入：

```text
請分析 src/orders。先摘要主要職責、公開介面、相依性、特殊分支、風險與 gaps；
確認證據足夠後建立或更新 wiki，補上 wikilinks、wiki/index.md 與 wiki/log.md。
```

驗收重點：

- 頁面只陳述 sources 能支持的事實；
- source paths 真實存在且相對 Repo root；
- 新頁面能從 `wiki/index.md` 導覽；
- `wiki/log.md` 只在尾端追加 `ingest` 條目；
- raw sources 沒有被修改。

## 4. Wiki-first Query

```text
請先查 wiki，再必要時回溯 sources，說明訂單取消流程與失敗條件。
```

Agent 應先讀 `wiki/index.md` 與少量相關頁面。只有內容不足、stale 或矛盾時才讀 raw sources；Query 預設不寫檔。若結果具有長期價值、暴露 Wiki gap 或發現品質問題，會依 `.agents/skills/codebase-wiki/references/follow-up-actions.md` 提供最多三個後續選項與「暫不處理」；選項不會自動執行。

## 5. 常用工作流

| 工作流 | 使用時機 | 必要維護 |
| --- | --- | --- |
| Interactive / Batch Ingest | 新模組、第一次初始化 | pages + index + `ingest` log |
| Query | 找行為、位置、原因；必要時提供保存、更新或 Lint 選項 | 預設唯讀 |
| Lint | Wiki 品質與 coverage；報告後提供受 findings 支持的選項 | 先報告；修復後 `lint` log |
| Archaeology | Legacy、異常分支、歷史原因 | 預設唯讀 |
| ADR | 保存架構選擇 | decision + index + `adr` log |
| Synthesis | 保存跨模組分析 | synthesis + index + log |
| Business Analysis / BA | 業務問題、現況／目標、能力、流程、規則、成功指標與 change impact | synthesis + index + log |
| System Analysis / SA | solution-neutral 邊界、needs、SR/NFR/IF 與 verification needs | synthesis + index + log |
| System Design / SD | concerns/viewpoints、決策、元件、runtime、資料、介面、部署、安全與品質策略 | synthesis + index + log |
| NotebookLM export | 全量盤點當下 Codebase 並重建每功能現況 BA／SA | `.notebooklm/` documents、upload sources、schema v6、governance；不自動上傳 |

完整提示詞與輸出契約位於 `docs/workflows/README.md`。

## NotebookLM Enterprise export

使用 `/export-notebooklm` 或 Codex 自然語言 recipe。每次以 `--root` 為 filesystem
boundary 掃描安全 UTF-8 repo text（behavioral tests 預設包含）；非文字業務證據列為 gap。
`business_source_paths` 可精確指定 dev-tooling 下的業務文字，但不能繞過敏感、產物、
CI/IaC、Wiki/output 等安全排除。

Discovery preflight 取得 inventory、capabilities、BA／SA coverage、文件計畫、DLP、容量與 gaps：

```powershell
python .agents\skills\codebase-wiki\scripts\export-notebooklm.py `
  --root . --preflight --format json
```

使用者檢視完整預覽並確認一次後，全量更新 catalogs、knowledge gaps、coverage ledger，
並為每個 active `cap-*` 建立互連的繁中 `{cap}-ba.md` 與 `{cap}-sa.md`。BA／SA 使用專用
current-state profiles、真實 sources 與 `path:line` locators；同步 index 與一筆 log，將
confirmed discovery ID 寫入 ledger。系統接著自動重跑 readiness，取得最新 ID 後 apply：

```powershell
python .agents\skills\codebase-wiki\scripts\export-notebooklm.py `
  --root . --apply --discovery-id <confirmed-discovery-id> `
  --preflight-id <readiness-id> --output .notebooklm --format json
```

只手動上傳 `.notebooklm/sources/*.md`。Schema v6 `manifest.json` 記錄 discovery/readiness、
BA／SA documents、source mapping、coverage、DLP、migration 與 stable IDs；`governance.md`
區分本機檢查與待管理員驗證的雲端控制。Raw evidence 不直接進入 pack；舊 schema v1–v5
或 retrieval contract 必須在同一本 Notebook full rebuild。預設 pack 使用 450 MB /
450,000 words safety limits，且不超過 Enterprise 的 300 sources、500 MB /
500,000 words hard limits；不同 Workspace tier 請在 `notebooklm.toml` 下調。

Exporter 在 analysis copy、documents 與 sources 執行 `notebooklm-enterprise-ba-sa-mask-v1`
DLP；finding 先遮罩，final payload 有殘留才阻擋 apply，報告只顯示安全 metadata。詳細
步驟與 BA／SA UAT 見 [[notebooklm-export]]。

## 6. Guard modes

- **wiki-only**：安裝預設，只允許寫入 `wiki/`；舊 `target` 名稱映射至此模式。
- **coexist**：一般 coding 與 Wiki 共存的工作階段，允許 Repo 內明確編輯並對非 Wiki
  路徑提供 audit context；不會擴張任務授權。
- **framework**：只用於本框架 Repo，可更新核准入口、schema、adapters、docs、
  samples、tests、tools 與 Wiki。

Guard 是 deterministic 防呆層，不取代 sandbox。若需求是修改目標專案程式碼，請改成一般 coding task，不要透過 Wiki 任務繞過限制。

Codex 的 `SessionStart`、`PreToolUse` 與 `PostToolUse` 以 session cwd 執行。
`.codex/hooks.json` 的 POSIX command 先以 `git rev-parse --show-toplevel` 找 Git root，
Windows `commandWindows` 則使用 PowerShell wrapper；兩者在非 Git target root 才回退
目前目錄。若看到 hook failure，先確認是從 Git tree 或非 Git 安裝 root 啟動，並檢查
canonical `.agents/skills/codebase-wiki/scripts/hooks/` 是否存在，不要先停用 guard/audit。

## 7. Deterministic checks

```powershell
python -m unittest discover -s tests -v
python .agents\skills\codebase-wiki\scripts\parity-check.py
python .agents\skills\codebase-wiki\scripts\validate-frontmatter.py wiki
python .agents\skills\codebase-wiki\scripts\check-stale.py wiki
python .agents\skills\codebase-wiki\scripts\validate-log.py wiki\log.md --repo-root .
python .agents\skills\codebase-wiki\scripts\wiki-stats.py wiki
python .agents\skills\codebase-wiki\scripts\lint-wiki.py wiki
python .agents\skills\codebase-wiki\scripts\rebuild-index.py wiki --check
python .agents\skills\codebase-wiki\scripts\export-notebooklm.py --root . --preflight --format json
python .agents\skills\codebase-wiki\scripts\export-notebooklm.py --root . --apply --discovery-id DISCOVERY_ID --preflight-id PREFLIGHT_ID --output .notebooklm --format json
```

三個 path-based quality CLI 都接受標準 `--help`；獨立執行時 `check-stale.py` 的
directory source 在沒有 Git metadata 時會 fallback 到 filesystem scan，NotebookLM
preflight 則直接使用 filesystem-only Wiki lint mode。

Frontmatter 或 stale check 失敗時，先修復實際 path/schema 問題；不要以虛構 sources 或刪除 log 歷史規避檢查。

## 8. E2E 樣例

`samples/task-tracker/` 包含 `TaskItem`、Repository pattern、設定載入、狀態轉換、錯誤分支與 injected clock。依 `samples/README.md` 複製到暫存目錄後，可對五個 active 情境執行隔離驗收。

驗收不比較 Agent 文字是否完全相同，而是確認：

- 關鍵 domain behavior 有 Wiki/source evidence；
- index、wikilinks、frontmatter 與 append-only log 正確；
- Lint 沒有 Critical；
- raw source hashes 維持不變。
- 自然語言可不同，但每次 process invariants 相同。

## 9. 常見陷阱

- **直接對版本化 sample 執行 `--apply`**：先複製到暫存目錄。
- **把 Query 當成全文 source scan**：必須先查 Wiki。
- **要求 Query 連線即時資料庫**：Query 只讀 Wiki 與 Repo sources；需要目前資料庫狀態時標示 gap，不呼叫資料庫工具或 fallback。
- **遇到 conflicts 使用覆寫**：Installer 沒有 force；應人工合併。
- **把既有 Wiki 當成 NotebookLM 掃描邊界**：export 每次都要重掃安全的全專案範圍，才能發現新增、刪除與未被 Wiki 覆蓋的功能。
- **把 NotebookLM 當成自動同步服務**：本流程只產生本機 pack 與 diff plan，必須由使用者手動更新 NotebookLM。
- **修正 log 時重寫歷史**：`wiki/log.md` 永遠只能追加。

## 進一步閱讀

- 文件總覽：`docs/README.md`
- 架構與資料流：`docs/architecture/README.md`
- 安裝、升級與排錯：`docs/setup/README.md`
- 12 個操作情境：`docs/workflows/README.md`
- 本機 deterministic checks 與手動驗收：`docs/validation/README.md`
- Codex 獨立手冊：`Codex.md`

## 相關頁面

- [[overview]] — 框架定位、產品結構與核心設計
- [[installer-and-upgrade]] — v6 managed blocks、manifest 與 atomic apply
- [[platform-hooks-and-guards]] — 三種 guard mode 與跨平台 hook contract
- [[business-analysis]] — 業務分析與 BA traceability
- [[system-analysis]] — solution-neutral 系統分析與 verification needs
- [[system-design]] — 架構與設計 views、決策及品質策略
