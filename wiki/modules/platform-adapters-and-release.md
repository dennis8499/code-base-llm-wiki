---
title: 平台 Adapter 與手動 Release
type: module
summary: 以 contract v5、Copilot 薄 adapters、本機 parity、mode 分責的三樣本 benchmark 與手動發版維持雙平台框架
notebooklm_group: function-platform-release
notebooklm_role: traceability
sources:
  - .agents/skills/codebase-wiki/capabilities.json
  - .agents/skills/codebase-wiki/scripts/parity-check.py
  - .agents/skills/project-knowledge/SKILL.md
  - .agents/skills/project-knowledge/scripts/knowledge_benchmark.py
  - .agents/skills/project-knowledge/scripts/compare_portability_reports.py
  - .agents/skills/project-knowledge/scripts/validate_contracts.py
  - tests/test_contracts.py
  - tools/release.py
  - docs/validation/README.md
  - docs/releases/README.md
source_digest: sha256:f996719b0d3f2233ab304389036a2a24d02c22f3d6c483d4e1858dc43728f2ed
derived_from: ["[[system-architecture]]"]
last_updated: 2026-09-06
tags: [module, adapters, validation, release, parity]
status: active
---

# 平台 Adapter 與手動 Release

## 職責

- 維持 Copilot prompts/hooks 與 Codex recipes/hooks 的共同 intent、
  authorization 與 completion contract。
- 以 `capabilities.json` contract version 5 描述十一個 operations／十一個 intent groups；
  BA／SA／SD 與既有操作的
  名稱與 authorization policy 不因平台 adapter 改變。
- 將 Copilot `.github/prompts/` 限定為 VS Code 本機 Agent 入口；其他 Copilot
  hosts 直接使用 `.agents/skills/codebase-wiki/`。
- 所有保留的 Copilot prompts 使用 built-in `agent` metadata；框架不發佈
  Repo-local Wiki agent profiles。
- 共用 Query workflow 與雙平台代理只接受 Wiki／Repo source evidence；即時資料庫存取、
  資料庫工具及 fallback 由 parity 與 contract regression 明確禁止。
- Copilot 與 Codex v5 只宣告本機 contract/deterministic 驗證結果；host runtime UAT
  尚未重跑。2026-09-03 的 Codex v4 evidence 是歷史基線，不外推到 v5。
- 以根 `VERSION` 作為產品版號唯一來源；本機建置後由維護者明列四個 assets，
  手動執行 `gh release create`。
- 大型 Knowledge portability benchmark 固定 50,000 files／5,000 pages，十一個
  timing-sensitive operations 各取三個正式樣本；單一 isolated outlier 可依共同規則
  通過，mixed、sustained、functional drift 或環境錯誤一律不能成為跨平台通過證據。
- 完整 owner BDD 仍執行 50k/5k 真實功能 calls，但以 `measurement_mode=controlled`
  固定 operation timing；CLI 則只產生 `measurement_mode=observed` 的 v3 report。
- Windows／Linux 必須在同一 `strict-clean` revision 的實際主機各自產生一份 observed
  v3 report，再由本機 comparator 重算 raw samples、result hashes、legacy projection、
  producer identity 與 functional oracle；controlled report 不具 portability 證據資格，
  Repo 也不以 workflow YAML 模擬雙平台證據。
- 在專案擁有者選定 LICENSE 前阻擋公開 release；本次維護不改版號、不發版。

## Evidence

- `parity-check.py` 驗證 contract 5、十一項 operation mapping、prompt coupling、built-in
  prompt metadata、已移除資源保持不存在、即時資料庫能力保持移除、Codex
  root-resolved hooks，並要求 Repo 不含 GitHub workflow YAML。
- Copilot prompts（含新增 BA／SD 與保留 SA 入口）是連結 authoritative workflow 的薄
  adapter，不複製完整規則；
  Interactive/Batch authorization 與 Query/Lint/Archaeology completion coupling
  都由 `tests/test_contracts.py` 固定。
- Codex v4 的 18 個歷史 Task Tracker fixture runs 保存 JSONL tool events、前後 hashes、
  Git 狀態、情境 assertions 與 deterministic outputs；受修復影響的情境皆捨棄首輪
  結果後重新取得完整 3/3，證據只留在隔離且不提交的本機驗收目錄。
- 本機驗證以 Python 3.11 與 3.14 執行 unit、compile、parity、frontmatter、stale、
  log、stats、lint 與 index check；lint 的兩項語意檢查另由人工完成。
- `knowledge_benchmark.py` 以 report v3／error v2 保存 33 個 raw timing samples、
  normalized result hashes、四態 decision、measurement mode、cleanup 與 producer identity；
  `compare_portability_reports.py` fail closed 拒絕 controlled、v2、缺少／未知 mode、
  缺樣本、宣告漂移、dirty source、OS 缺漏及跨主機 identity／functional 不一致。
- `docs/validation/README.md` 保存 Windows 與 Linux producer 命令、create-only report
  搬移方式及 comparator 命令；`.knowledge-test-tmp/` 是唯一新增的 ignored evidence root。
- `tools/release.py` 在 validate/build 時呼叫 readiness gate，驗證版本、tag、LICENSE、
  repository name、資產邊界與 checksum。
- Release builder 排除 cache、hook/NotebookLM state、transaction artifacts 與敏感
  paths，並拒絕非排除路徑的 symlink/reparse source 或不安全 output entry。

## Contradictions

- `VERSION=0.2.0` 代表目前產品版號，不代表已取得 LICENSE 或已有可公開的
  `v0.2.0` 資產。
- 靜態 contract 相容不能當作 host runtime 驗收；v4 歷史結果也不能外推為 v5 或
  未測 host/version 的保證。
- Synthetic OS metadata 與單一 Windows run 只能驗證 contract／本機路徑，不能宣稱
  已完成 Windows/Linux portability。

## Inferences

- 移除 hosted automation 後，發版責任明確落在執行本機矩陣、檢查 assets、推送
  tag 與呼叫 GitHub CLI 的維護者；deterministic scripts 仍提供相同可稽核 gate。
- 三樣本四態規則把一次 host jitter 與持續 regression 分開；comparator 仍要求兩份
  observed pass report，避免把 controlled 或 inconclusive evidence 推論成成功。

## Gaps

- Copilot host runtime 尚未執行，因此維持 `runtime-unverified`。
- 本次只在 Windows 執行大型 benchmark；實際 Linux strict-clean report 與雙平台
  comparator 結果仍是 release／portability follow-up，不由 synthetic test 代替。
- LICENSE、公開發佈日期、套件簽章、SBOM 與 provenance attestation 仍待擁有者決策。

## 相關頁面

- [[release-and-update]]
- [[platform-hooks-and-guards]]
- [[wiki-quality-and-provenance]]
- [[business-analysis]]
- [[system-analysis]]
- [[system-design]]
