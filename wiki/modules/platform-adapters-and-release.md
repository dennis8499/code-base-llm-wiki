---
title: 平台 Adapter 與 GitHub Release
type: module
summary: 以 contract v6、單一 Skill 分流索引、Copilot 薄 adapters、Codex recipes、本機 parity 與 surface-specific GitHub Release packages 維持雙平台框架，並提供共用 Concise 輸出、source-first 靜態健檢及受限來源探索
notebooklm_group: function-platform-release
notebooklm_role: traceability
sources:
  - .agents/skills/codebase-wiki/SKILL.md
  - .agents/skills/codebase-wiki/references/intent-routing.md
  - .agents/skills/codebase-wiki/assets/target-agents-block.md
  - AGENTS.md
  - .github/copilot-instructions.md
  - .agents/skills/codebase-wiki/capabilities.json
  - .agents/skills/codebase-wiki/scripts/parity-check.py
  - tests/contracts/test_contracts.py
  - tests/contracts/test_code_audit.py
  - tests/installer/test_install_framework.py
  - tests/fixtures/code-audit/README.md
  - tests/fixtures/code-audit/expected-findings.md
  - tests/contracts/test_code_audit_validator.py
  - tests/fixtures/code-audit/history/README.md
  - tests/fixtures/code-audit/history/expected-findings.md
  - tools/release.py
  - tools/validate_release.py
  - tools/prepare_release.py
  - tests/release/test_prepare_release.py
  - scripts/release_ci.py
  - scripts/test_release_ci.py
  - tests/release/test_validation.py
  - docs/operations/releases/README.md
  - docs/operations/validation/README.md
  - LICENSE
  - .github/workflows/release.yml
  - .agents/skills/codebase-wiki/scripts/install-framework.py
  - tests/release/test_github_release_workflow.py
  - tests/release/features/github-release.feature
  - tests/release/scenario_runner.py
  - tests/release/test_release.py
  - .agents/skills/codebase-wiki/scripts/tgrep-search.py
  - .agents/skills/codebase-wiki/bin/tgrep-manifest.json
  - tests/tgrep/test_tgrep_search.py
  - .agents/skills/codebase-wiki/references/code-audit-workflow.md
  - .agents/skills/codebase-wiki/assets/code-audit-template.md
  - .agents/skills/codebase-wiki/scripts/validate-code-audit.py
  - .github/prompts/code-audit.prompt.md
  - Codex.md
source_digest: "sha256:3629720525c8e7dabff59c855a4b29d2da3c3ff6f2ded79e2103126a7cc01e13"
derived_from: ["[[system-architecture]]"]
last_updated: 2026-10-16
tags: [module, adapters, validation, release, parity]
status: active
---

# 平台 Adapter 與 GitHub Release

## Skill 分流與完成條件

Skill 入口保留共用邊界、輸出及完成條件；十四個意圖的 workflow 與授權路由統一由
`references/intent-routing.md` 維護，只載入目前分支的參考文件。Query 先查 Wiki；
功能探索、Codebase audit、開發規格與 NotebookLM 依各自 source-first 流程讀取目前來源。
明確的合併／上版分支審查保持其原流程，不轉成 Wiki 健檢。

查詢後的具體預覽只需一次範圍授權；完整 Ingest／探索／audit 保留逐檔及入口覆蓋、
未讀項與漂移缺口。精簡入口不改變 capability schema、靜態審查邊界或 index/log 耦合。

## 共用輸出風格

Codex、Copilot 與安裝後入口共用 `.agents/skills/codebase-wiki/SKILL.md` 的
Concise 規則，涵蓋進度、問答及新增或更新文件。首句直接給答案或目前結果，省略開場、
逐步旁白及收尾重述；簡單問答預設一至三句，要求詳解時完整說明。

正式文件在既有摘要或首個敘述段落交代重點，不限制句數。必要章節、識別碼、問題、
覆蓋缺口、限制、錯誤、失敗測試輸出及原始證據完整保留。既有授權與工作流契約維持原規則。

## 職責

- `development_spec` 的獨立規格、逐題釐清與 draft／ready 邊界見 [[development-specification]]；
  此路由透過 Codex／Copilot 共用同一模板和驗證器。

- 維持 Copilot prompts/hooks 與 Codex recipes/hooks 的共同 intent、
  authorization 與 completion contract。
- 以 `capabilities.json` contract version 6 描述十四個 manifest-declared operations／intent groups；
  BA／SA／SD 與既有操作的
  名稱與 authorization policy 不因平台 adapter 改變。
- 將 Copilot `.github/prompts/` 限定為 VS Code 本機 Agent 入口；其他 Copilot
  hosts 直接使用 `.agents/skills/codebase-wiki/`。
- 所有保留的 Copilot prompts 使用 built-in `agent` metadata；框架不發佈
  Repo-local Wiki agent profiles。
- 共用 Query workflow 與雙平台代理只接受 Wiki／Repo source evidence；即時資料庫存取、
  資料庫工具及 fallback 由 parity 與 contract regression 明確禁止。
- tgrep source-discovery integration 只開放給 Interactive/Batch Ingest 與 Code Archaeology；
  Query 保持 Wiki-first，不呼叫 tgrep 或 CLI fallback。Windows x64 wrapper 只回傳候選
  locator，形成 evidence 前必須直接重讀目前 source。
- `code_audit` 先以唯讀原生搜尋從目前 Codebase 盤點入口，再交叉核對 transaction／side effects、
  設定引用、邏輯／狀態契約與變更完整性；只有遇到業務規則語意缺口才查 Wiki，之後定向使用
  `git log`／`git show`／`git blame` 讀取 commit 完整內文與 diff。不呼叫 tgrep、不執行目標程式或
  測試，並將 `BUG-*`、`RISK-*` 與 `BIZ-*` 分列。明確健檢要求預設保存 synthesis 報告，使用者
  指定只回報時維持零寫入，持久化後通過 `validate-code-audit.py`。
- Copilot 與 Codex v6 只宣告本機 contract/deterministic 驗證結果；host runtime UAT
  尚未重跑。2026-09-03 的 Codex v4 evidence 是歷史基線，不外推到目前 contract。
- 以根 `VERSION` 作為產品版號唯一來源；`.github/workflows/release.yml` 在 PR、main、手動及 reusable
  呼叫時以 Python 3.11／3.14 完成 validation；只有版本 tag push 可發布，明列
  `codebase-llm-wiki-codex.zip`、`codebase-llm-wiki-copilot.zip`、
  `update-manifest.json` 與 `SHA256SUMS` 四個 assets 建立 GitHub Release。
- 本 Repo 採用 MIT License；workflow 使用 job-level `contents: write` 發布，installer
  將 framework-only release workflow 排除在 target surface 之外。

## Evidence

- 查詢具體預覽的一次授權及全量 Ingest 逐檔完成性見 [[query-follow-ups-and-ingest]]；
  Codex 與 Copilot 共用相同 reference，原生套件保留通用規格，Megin 專屬匯出由下游擴充。
- `parity-check.py` 驗證 contract 6、十四個 operation mapping、Codebase audit 的四類檢查／Git history／
  validator contract、靜態邊界、prompt coupling、built-in
  prompt metadata、已移除資源保持不存在、即時資料庫能力保持移除、Codex
  root-resolved hooks，並驗證唯一 release workflow 的 trigger、權限、版本驗證、資產
  清單與 publish 命令；installer parity 同時保證它不流入 target。
- Copilot prompts（含新增 BA／SD 與保留 SA 入口）是連結 authoritative workflow 的薄
  adapter，不複製完整規則；
  Interactive/Batch authorization 與 Query/Lint/Archaeology completion coupling
  都由 `tests/contracts/test_contracts.py` 固定。
- `tests/tgrep/test_tgrep_search.py` 固定 bundled tgrep 的版本／digest、allowlisted
  flags、shell 禁用、path containment、exit codes 與不建立 index 的唯讀邊界。
- `test_code_audit.py` 與 `tests/fixtures/code-audit/` 固定 audit authorization、平台入口、靜態證據分類、
  共享根因、transaction／設定／介面變更、上游防護、技術風險、業務疑點與動態入口 coverage gap；
  `test_code_audit_validator.py` 另外以隔離 Git fixture 驗證刪除、commit 內文／diff、來源與報告計數；
  不執行 fixture 程式碼。
- Codex v4 的 18 個歷史 Task Tracker fixture runs 保存 JSONL tool events、前後 hashes、
  Git 狀態、情境 assertions 與 deterministic outputs；受修復影響的情境皆捨棄首輪
  結果後重新取得完整 3/3，證據只留在隔離且不提交的本機驗收目錄。
- 本機驗證以 Python 3.11 與 3.14 執行 unit、compile、parity、frontmatter、stale、
  log、stats、lint 與 index check；`tools/validate_release.py` 共用同次 component 結果，
  保留獨立 gate 的診斷與退出碼。Lint 的兩項語意檢查另由人工完成。
- 正式 tag 只重用七天內、可信 main push 或 main 手動執行、相同提交、完整矩陣與來源／環境／workflow／政策
  摘要相符的驗證證據；失效時重跑全矩陣。單一 cell 建置 assets，publish 核對後提升同份 bytes。
- `scripts/release_ci.py` 驗證固定提交及附件 SHA，重試時保留相同附件、補缺漏，
  拒絕同名不同內容，完成後重新下載正式資產核對；PR 驗證不能作為可信發布證據。
- 發版檢查與套件建置使用乾淨 Git checkout 的 canonical LF bytes；來源摘要與
  coverage discovery identity 必須對應相同來源。完整 deterministic gates 通過後
  可發佈標示 `runtime-unverified` 的版本，host runtime 保證另須取得 active UAT 3/3。
- `tools/release.py` 在 validate/build 時呼叫 readiness gate，驗證版本、tag、LICENSE、
  repository name、surface package allowlist、資產邊界與 checksum。
- `tools/prepare_release.py` 只對已完整分析且 preflight ready 的固定 HEAD 候選提交更新 release
  metadata 證據。VERSION／README 以外的來源變更、人工 Wiki 改動及新增檔案會阻擋；原有
  disposition 不增加，生成內容綁定候選提交及目標版本，部分完成或跨日重試仍須精確一致。
- Release builder 排除 cache、hook/NotebookLM state、transaction artifacts 與敏感
  paths，並拒絕非排除路徑的 symlink/reparse source 或不安全 output entry；它只從
  明確的共用 Skill、LICENSE、VERSION、target AGENTS template 與選定 adapter 收集檔案，
  驗證 `bundled_tools` 中 tgrep 1.0.5 的固定 path、platform 與 SHA-256，且排除 `.tgrep/`。
- `update-manifest.json` 使用 schema v2，以每個 asset 的 `surface` 分別描述兩個
  精簡 ZIP；`bundled_tools` 描述隨兩包發佈的 wrapper、manifest 與 binary。這不是額外
  asset，installer contract version 與目前實作一致為 6。

- 解壓後的精簡 package README 提供 install／upgrade 預覽與套用指令。Installer 會
  識別 package marker，在任何 target 寫入前檢查共用 Skill、Wiki starter 與所選 adapter
  的完整性；把 Copilot package 選成 Codex surface（或反向）會 fail closed。

## Contradictions

- `v0.3.0` Release 已公開；版本、附件及發版 CI 證據見下方現行發版紀錄。
- 靜態 contract 相容不能當作 host runtime 驗收；v4 歷史結果也不能外推為 v6 或
  未測 host/version 的保證。

### v0.3.0 現行發版紀錄

- [Codebase LLM Wiki v0.3.0](https://github.com/dennis8499/code-base-llm-wiki/releases/tag/v0.3.0) 於 2026-10-03 發布，tag 指向 commit `538712f553457d53b8e451d1733fe97a01c6aff6`。
- [發版 CI](https://github.com/dennis8499/code-base-llm-wiki/actions/runs/37133823578) 已成功，Python 3.11／3.14 deterministic checks 通過；v0.3.0 包含 Codex／Copilot ZIP、`SHA256SUMS` 與 `update-manifest.json`。
- Codex 與 Copilot host runtime UAT 尚未執行，狀態維持 `static-compatible / runtime-unverified`。

## Inferences

- 發版責任分成兩層：維護者完成 review、合併並推送版本 tag；GitHub Actions 選取符合
  固定來源及政策的完整證據，必要時重新驗證，再提升已驗證 assets 建立 Release。

## Gaps

- Copilot host runtime 尚未執行，因此維持 `runtime-unverified`。
- Codex v6 host runtime UAT 尚未執行，因此與 Copilot 相同，維持 `runtime-unverified`。

## 相關頁面

- [[release-and-update]]
- [[platform-hooks-and-guards]]
- [[wiki-quality-and-provenance]]
- [[business-analysis]]
- [[system-analysis]]
- [[system-design]]
