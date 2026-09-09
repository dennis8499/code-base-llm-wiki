---
title: 平台 Adapter 與手動 Release
type: module
summary: 以 contract v6、Copilot 薄 adapters、Codex recipes、本機 parity 與手動發版維持雙平台框架，並以 pinned tgrep bundle 擴充 Ingest／Archaeology 來源探索
notebooklm_group: function-platform-release
notebooklm_role: traceability
sources:
  - .agents/skills/codebase-wiki/capabilities.json
  - .agents/skills/codebase-wiki/scripts/parity-check.py
  - tests/contracts/test_contracts.py
  - tools/release.py
  - docs/operations/releases/README.md
  - .agents/skills/codebase-wiki/scripts/tgrep-search.py
  - .agents/skills/codebase-wiki/bin/tgrep-manifest.json
  - tests/tgrep/test_tgrep_search.py
source_digest: sha256:62d428771b00c001e09dfcc121014496182bf601495c4802b90bb7c3eb670b76
derived_from: ["[[system-architecture]]"]
last_updated: 2026-09-09
tags: [module, adapters, validation, release, parity]
status: active
---

# 平台 Adapter 與手動 Release

## 職責

- 維持 Copilot prompts/hooks 與 Codex recipes/hooks 的共同 intent、
  authorization 與 completion contract。
- 以 `capabilities.json` contract version 6 描述 manifest-declared operations／intent groups；
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
- Copilot 與 Codex v6 只宣告本機 contract/deterministic 驗證結果；host runtime UAT
  尚未重跑。2026-09-03 的 Codex v4 evidence 是歷史基線，不外推到目前 contract。
- 以根 `VERSION` 作為產品版號唯一來源；本機建置後由維護者明列四個 assets，
  手動執行 `gh release create`。
- 在專案擁有者選定 LICENSE 前阻擋公開 release；本次維護不改版號、不發版。

## Evidence

- `parity-check.py` 驗證 contract 6、operation mapping、prompt coupling、built-in
  prompt metadata、已移除資源保持不存在、即時資料庫能力保持移除、Codex
  root-resolved hooks，並要求 Repo 不含 GitHub workflow YAML。
- Copilot prompts（含新增 BA／SD 與保留 SA 入口）是連結 authoritative workflow 的薄
  adapter，不複製完整規則；
  Interactive/Batch authorization 與 Query/Lint/Archaeology completion coupling
  都由 `tests/contracts/test_contracts.py` 固定。
- `tests/tgrep/test_tgrep_search.py` 固定 bundled tgrep 的版本／digest、allowlisted
  flags、shell 禁用、path containment、exit codes 與不建立 index 的唯讀邊界。
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
  與 binary；這不是額外 asset，也不改變四項手動 Release asset 契約。

## Contradictions

- `VERSION=0.2.0` 代表目前產品版號，不代表已取得 LICENSE 或已有可公開的
  `v0.2.0` 資產。
- 靜態 contract 相容不能當作 host runtime 驗收；v4 歷史結果也不能外推為 v6 或
  未測 host/version 的保證。

## Inferences

- 移除 hosted automation 後，發版責任明確落在執行本機矩陣、檢查 assets、推送
  tag 與呼叫 GitHub CLI 的維護者；deterministic scripts 仍提供相同可稽核 gate。

## Gaps

- Copilot host runtime 尚未執行，因此維持 `runtime-unverified`。
- LICENSE、公開發佈日期、套件簽章、SBOM 與 provenance attestation 仍待擁有者決策。

## 相關頁面

- [[release-and-update]]
- [[platform-hooks-and-guards]]
- [[wiki-quality-and-provenance]]
- [[business-analysis]]
- [[system-analysis]]
- [[system-design]]
