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
source_digest: sha256:6561fb4f6b348b8d7bbe0a7b25bc96882fcbdc622570cc15bcc08801623887e2
derived_from: ["[[overview]]", "[[installer-and-upgrade]]", "[[platform-hooks-and-guards]]"]
last_updated: 2026-08-21
tags: [guide, onboarding, framework, copilot, codex]
status: active
notebooklm_group: project-guides
---

# Codebase LLM Wiki — 使用指南

> 本指南提供框架使用者最短的安裝、操作與驗收路線。架構背景請先閱讀 [[overview]]。

## 適用讀者

- 想把 Codebase LLM Wiki 安裝到既有 Repo 的維護者；
- 使用 GitHub Copilot 或 OpenAI Codex 維護 codebase 知識的人；
- 需要驗證雙入口能力、安全邊界或 Wiki 品質的框架貢獻者。
- 想把本地 Wiki 以可追蹤、可增量更新的方式交付給 NotebookLM Enterprise 使用者的人。

## 前置需求

- Git；
- Python 3.11+；
- GitHub Copilot Chat 或 OpenAI Codex，依選用入口決定；
- 對目標 Repo 的讀取權限，以及對框架 schema/Wiki 的必要寫入權限。

框架不需要向量資料庫、Node.js、MCP 搜尋服務、PyYAML 或其他第三方 Python 套件。

## 1. 選擇入口

| 需求 | 建議入口 | 安裝內容 |
| --- | --- | --- |
| VS Code Copilot agents、prompts、hooks | Copilot surface | `AGENTS.md`、`codebase-wiki` Skill、`.github/`、`wiki/` |
| Codex CLI、IDE、App、Cloud task | Codex surface | `AGENTS.md`、`Codex.md`、`codebase-wiki` Skill、`.codex/`、`wiki/` |
| 同一 Repo 同時支援兩者 | 分別評估並合併兩種 surface | 共用 `.agents/` 與 `wiki/` |

雙入口的能力相同，但平台 adapter 不相同。Codex 不使用 project-level slash prompts；Copilot prompts 也不會被假裝成 Codex 功能。

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

GitHub Release 提供 ZIP、TAR.GZ、`SHA256SUMS` 與 `update-manifest.json`。未來
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
| Guide | 保存 setup/runbook/onboarding | guide + index + log |
| System Analysis / SA | 系統級文件與 gaps | synthesis + index + log |
| NotebookLM export | 全專案掃描並依功能補齊 Wiki，組成可手動上傳的 source pack | 功能文件、`.notebooklm/`、manifest、upload plan；不自動上傳 |
| Delegation | 使用者明確要求專業代理 | 不擴張原任務權限 |

完整提示詞與輸出契約位於 `docs/workflows/README.md`。

## NotebookLM Enterprise export

使用 `/export-notebooklm` 或 Codex 的自然語言 recipe。每次執行都重新掃描 Git
tracked 與 non-ignored untracked files，納入可分享的 runtime source、必要
config/manifests、schema/migrations 與既有文件；tests、CI/CD、IaC、build/dev
tooling、dependencies、generated、binary、secrets、framework adapters 與輸出目錄
預設排除。既有 Wiki 是增量知識基線，不是掃描邊界。

先執行唯讀 preflight，取得納入/排除 inventory、Wiki coverage、缺失文件、容量與
來源數估計、warnings 和未驗證事項：

```powershell
python .agents\skills\codebase-wiki\scripts\export-notebooklm.py `
  --root . --preflight --format json
```

Agent 依功能批次閱讀所有 included files，預覽預計建立或重大更新的頁面。即使沒有
stale、placeholder 或容量警告，也要等待使用者確認。確認後以繁體中文補齊專案總覽、
功能目錄、系統架構、各功能 module/entity pages 與系統分析，填入真實
`frontmatter.sources`、`notebooklm_group`、wikilinks，並同步 index、只追加一筆
`ingest` log，最後才執行 exporter：

```powershell
python .agents\skills\codebase-wiki\scripts\export-notebooklm.py `
  --root . --apply --preflight-id <id> --output .notebooklm --format json
```

只手動上傳 `.notebooklm/sources/*.md`。Schema v2 `manifest.json` 記錄 scan
inventory、coverage、omissions、input/output hash 與 stable `logical_source_id`；
`upload-plan.md` 將每次結果分成 `added`、`changed`、`deleted`、`unchanged`。變更
來源需先移除 NotebookLM 中的舊 static source 再上傳新檔，未變更來源不需重傳。
打包採 documents-first：先保留完整功能文件，再以剩餘 source/byte budget 加入
關鍵 evidence；`source_budget` 省略項目必須交付。預設 pack 使用 180 MB /
450,000 words safety limits，且不超過 Enterprise 的 300 sources、200 MB /
500,000 words hard limits；不同 Workspace tier 請在 `notebooklm.toml` 下調。

## 6. Guard modes

- **wiki-only**：安裝預設，只允許寫入 `wiki/`；舊 `target` 名稱映射至此模式。
- **coexist**：一般 coding 與 Wiki 共存的工作階段，允許 Repo 內明確編輯並對非 Wiki
  路徑提供 audit context；不會擴張任務授權。
- **framework**：只用於本框架 Repo，可更新核准入口、schema、adapters、docs、
  samples、tests、tools 與 Wiki。

Guard 是 deterministic 防呆層，不取代 sandbox。若需求是修改目標專案程式碼，請改成一般 coding task，不要透過 Wiki 任務繞過限制。

Codex 的 `SessionStart`、`PreToolUse` 與 `PostToolUse` 會以目前 workspace
作為 Hook 工作目錄，因此 `.codex/hooks.json` 使用相對腳本路徑。Windows
命令由 `cmd.exe` 執行，必須使用 `cmd.exe` 相容語法；若看到
`PostToolUse hook (failed)` 或 `hook exited with code 1`，先檢查是否誤用了
PowerShell `$()`、`git rev-parse` 或巢狀引號，不要先停用 audit reminder。

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
python .agents\skills\codebase-wiki\scripts\export-notebooklm.py --root . --apply --preflight-id ID --output .notebooklm --format json
```

Frontmatter 或 stale check 失敗時，先修復實際 path/schema 問題；不要以虛構 sources 或刪除 log 歷史規避檢查。

## 8. E2E 樣例

`samples/task-tracker/` 包含 `TaskItem`、Repository pattern、設定載入、狀態轉換、錯誤分支與 injected clock。依 `samples/README.md` 複製到暫存目錄後，兩平台各重複三次 Query、Interactive Ingest、Lint 與 Delegation 情境。

驗收不比較 Agent 文字是否完全相同，而是確認：

- 關鍵 domain behavior 有 Wiki/source evidence；
- index、wikilinks、frontmatter 與 append-only log 正確；
- Lint 沒有 Critical；
- raw source hashes 維持不變。
- 自然語言可不同，但每次 process invariants 相同。

## 9. 常見陷阱

- **直接對版本化 sample 執行 `--apply`**：先複製到暫存目錄。
- **把 Query 當成全文 source scan**：必須先查 Wiki。
- **把 DB evidence 放入 sources**：frontmatter sources 只接受 Repo paths。
- **遇到 conflicts 使用覆寫**：Installer 沒有 force；應人工合併。
- **未要求就啟用 delegation**：日常任務應由目前 Agent 完成。
- **把既有 Wiki 當成 NotebookLM 掃描邊界**：export 每次都要重掃安全的全專案範圍，才能發現新增、刪除與未被 Wiki 覆蓋的功能。
- **把 NotebookLM 當成自動同步服務**：本流程只產生本機 pack 與 diff plan，必須由使用者手動更新 NotebookLM。
- **修正 log 時重寫歷史**：`wiki/log.md` 永遠只能追加。

## 進一步閱讀

- 架構與資料流：`docs/architecture/README.md`
- 安裝、升級與排錯：`docs/setup/README.md`
- 12 個操作情境：`docs/workflows/README.md`
- 自動與手動驗證：`docs/validation/README.md`
- Codex 獨立手冊：`Codex.md`

## 相關頁面

- [[overview]] — 框架定位、產品結構與核心設計
- [[installer-and-upgrade]] — v3 managed blocks、manifest 與 atomic apply
- [[platform-hooks-and-guards]] — 三種 guard mode 與跨平台 hook contract
- [[system-analysis]] — 完整系統分析與 gap
