---
title: 平台 Adapter 與手動 Release
type: module
summary: 以 Copilot 靜態契約、Codex 六流程 3/3 實機驗收、本機 parity 與手動發版維持雙平台框架
notebooklm_group: function-platform-release
notebooklm_role: traceability
sources:
  - .agents/skills/codebase-wiki/capabilities.json
  - .agents/skills/codebase-wiki/scripts/parity-check.py
  - tests/test_contracts.py
  - tools/release.py
  - docs/releases/README.md
source_digest: sha256:56e4f8c4103dfd71884f1ebe05fc81dcfdeba6e85ef09065c5311c04da7fc613
derived_from: ["[[system-architecture]]"]
last_updated: 2026-09-04
tags: [module, adapters, validation, release, parity]
status: active
---

# 平台 Adapter 與手動 Release

## 職責

- 維持 Copilot prompts/agents/hooks 與 Codex recipes/agents/hooks 的共同 intent、
  authorization 與 completion contract。
- 以 `capabilities.json` contract version 3 描述十一個 operations；六項核心流程的
  名稱與 authorization policy 不因平台 adapter 改變。
- 將 Copilot `.github/prompts/` 限定為 VS Code 本機 Agent 入口；其他 Copilot
  hosts 直接使用 `.agents/skills/codebase-wiki/`。
- Copilot custom agents 都是 `user-invocable: true`、
  `disable-model-invocation: true`，保留最小 tools，避免模型隱性委派。
- 共用 Query workflow 與雙平台代理只接受 Wiki／Repo source evidence；即時資料庫存取、
  資料庫工具及 fallback 由 parity 與 contract regression 明確禁止。
- Copilot 只宣告 `static-compatible / runtime-unverified`。Codex CLI 0.152.1 已於
  2026-09-03 完成六項情境各 3/3、raw hashes 不變且 deterministic gates 全通過，
  因此目前狀態為 `runtime-verified`。
- 以根 `VERSION` 作為產品版號唯一來源；本機建置後由維護者明列四個 assets，
  手動執行 `gh release create`。
- 在專案擁有者選定 LICENSE 前阻擋公開 release；本次維護不改版號、不發版。

## Evidence

- `parity-check.py` 驗證 contract 3、六項 prompt coupling、prompt metadata、agent
  reference、手動委派旗標、最小工具權限、即時資料庫能力保持移除、Codex
  root-resolved hooks，並要求 Repo 不含 GitHub workflow YAML。
- 六個 Copilot prompts 是連結 authoritative workflow 的薄 adapter，不複製完整規則；
  Interactive/Batch authorization 與 Query/Lint/Archaeology/Guide completion coupling
  都由 `tests/test_contracts.py` 固定。
- Codex 的 18 個有效 Task Tracker fixture runs 保存 JSONL tool events、前後 hashes、
  Git 狀態、情境 assertions 與 deterministic outputs；受修復影響的情境皆捨棄首輪
  結果後重新取得完整 3/3，證據只留在隔離且不提交的本機驗收目錄。
- 本機驗證以 Python 3.11 與 3.14 執行 unit、compile、parity、frontmatter、stale、
  log、stats、lint 與 index check；lint 的兩項語意檢查另由人工完成。
- `tools/release.py` 在 validate/build 時呼叫 readiness gate，驗證版本、tag、LICENSE、
  repository name、資產邊界與 checksum。
- Release builder 排除 cache、hook/NotebookLM state、transaction artifacts 與敏感
  paths，並拒絕非排除路徑的 symlink/reparse source 或不安全 output entry。

## Contradictions

- `VERSION=0.2.0` 代表目前產品版號，不代表已取得 LICENSE 或已有可公開的
  `v0.2.0` 資產。
- 靜態 contract 相容不能當作 Copilot runtime 驗收；Codex 的
  `runtime-verified` 也只適用於上述版本、日期與已保存的六項驗收矩陣，不能外推為
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
- [[system-analysis]]
