---
title: 平台 Adapter 與 GitHub Release
type: module
summary: 以 contract v6、Copilot 薄 adapters、Codex recipes、本機 parity 與 tag-triggered GitHub Release 維持雙平台框架，並提供 source-first Codebase 靜態健檢及受限 tgrep 來源探索
notebooklm_group: function-platform-release
notebooklm_role: traceability
sources:
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
source_digest: sha256:ed78b9e1637833660bfb4123317b8bbfe385ed7c40d015741f008c3cbbbf24bc
derived_from: ["[[system-architecture]]"]
last_updated: 2026-09-22
tags: [module, adapters, validation, release, parity]
status: active
---

# 平台 Adapter 與 GitHub Release

## 職責

- 維持 Copilot prompts/hooks 與 Codex recipes/hooks 的共同 intent、
  authorization 與 completion contract。
- 以 `capabilities.json` contract version 6 描述十二個 manifest-declared operations／intent groups；
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
- 以根 `VERSION` 作為產品版號唯一來源；`.github/workflows/release.yml` 只在
  `v*.*.*` tag push 時觸發，先以 Python 3.11／3.14 完成 validation，再明列 ZIP、
  TAR.GZ、`update-manifest.json` 與 `SHA256SUMS` 四個 assets 建立 GitHub Release。
- 本 Repo 採用 MIT License；workflow 使用 job-level `contents: write` 發布，installer
  將 framework-only release workflow 排除在 target surface 之外。

## Evidence

- `parity-check.py` 驗證 contract 6、十二個 operation mapping、Codebase audit 的四類檢查／Git history／
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
  log、stats、lint 與 index check；lint 的兩項語意檢查另由人工完成。
- `tools/release.py` 在 validate/build 時呼叫 readiness gate，驗證版本、tag、LICENSE、
  repository name、資產邊界與 checksum。
- Release builder 排除 cache、hook/NotebookLM state、transaction artifacts 與敏感
  paths，並拒絕非排除路徑的 symlink/reparse source 或不安全 output entry；它驗證
  `bundled_tools` 中 tgrep 1.0.5 的固定 path、platform 與 SHA-256，且排除 `.tgrep/`。
- `update-manifest.json` 以 `bundled_tools` 描述隨 ZIP/TAR.GZ 發佈的 wrapper、manifest
  與 binary；這不是額外 asset，也不改變四項 GitHub Release asset 契約。

## Contradictions

- `VERSION=0.2.0` 是目前產品版號；MIT License 已加入，但 `v0.2.0` tag 與 GitHub
  Release 仍須由合併後的 tag push workflow 建立。
- 靜態 contract 相容不能當作 host runtime 驗收；v4 歷史結果也不能外推為 v6 或
  未測 host/version 的保證。

## Inferences

- 發版責任分成兩層：維護者完成 review、合併並推送版本 tag；GitHub Actions 重新執行
  deterministic matrix、建置 assets 並呼叫 GitHub CLI 建立 Release。

## Gaps

- Copilot host runtime 尚未執行，因此維持 `runtime-unverified`。
- `v0.2.0` 的實際 tag push、workflow run、公開發佈日期、套件簽章、SBOM 與
  provenance attestation 仍待人工作業或後續決策。

## 相關頁面

- [[release-and-update]]
- [[platform-hooks-and-guards]]
- [[wiki-quality-and-provenance]]
- [[business-analysis]]
- [[system-analysis]]
- [[system-design]]
