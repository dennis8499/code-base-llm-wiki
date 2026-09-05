# 研究證據：移除 Durable Guide 與 Explicit Delegation

- 日期：2026-09-04
- Work ID：`work-20260904-remove-guide-delegation-6e10da4e`
- Planning baseline：`ab50a6c4090ac48a1ccf2dd483a7db2e70f0306d`；status SHA-256 `3077f105b951c565a6fb5fe6bada0503003012054a4b11accdc5aa37d68923d9`
- 用途：固定 repository probes、官方平台契約與 baseline test 結果。
- 此文件是 supporting source；coverage 缺口不升格為 primary BUG plan，`handoff.json` 省略 `bug_context`。

## Plan v2 來源綁定修正

- `SRC-CONTRACT-001.revision` 使用精確 base commit `ab50a6c4090ac48a1ccf2dd483a7db2e70f0306d`，其 SHA-256 仍綁定同一份 v4 baseline bytes。
- 本 supporting artifact 搬入 `plan-2/` 完整 revision bundle，因此更新為 `research-v2-20260904`。
- 產品決策與驗收範圍不變；上述兩個 source 變更均按 global baseline 處理，三個 WP 必須在新 delivery generation／implementation run 全量重跑。

## 1. Repository 現況

- `capabilities.json` 為 v4，含 13 active intents、12 groups；`guide`/`delegation` 都是 operation。
- Guide creator surface 有 4 檔：`guide-workflow.md`、`guide-template.md`、`save-guide.prompt.md`、`onboarding-guide.prompt.md`。
- Wiki custom-agent surface 有 10 profiles：`.github/agents/`、`.codex/agents/` 各 5；`.codex/config.toml` 另有 `[agents]`。
- 13 個 Copilot prompts 刪 2 個 Guide prompts 後保留 11 個。
- installer 遞迴列 source surface；舊 install-state 與新 manifest 差集形成 `obsolete_paths`，apply 不自動刪除此清單。
- Guide tokens 也存在 validators、index、lint/exporter 與既有 Wiki；這些是 legacy data seams。
- `tests/test_capability_removal.py` 不存在（`Test-Path` = False）；新 BDD commands 因此是 Proposed。既有 seams 可載入，不需 BOOT 或新依賴。

## 2. 平台契約

GitHub 官方「Your first prompt file」（2026-09-04 讀取，https://docs.github.com/en/copilot/tutorials/customization-library/prompt-files/your-first-prompt-file）示範 built-in `agent: 'agent'`，並說明 prompt 會切至 agent mode。因此保留的 11 prompts 改為 `agent: "agent"`，不引用 deleted named profiles。這是官方契約推論，不冒充 runtime UAT。

Codex 下架範圍限於 repo-owned `.codex/agents/*.toml`、`.codex/config.toml` Wiki delegation 設定與 `Codex.md` recipes；不移除 Codex 產品本身的 subagent 功能。

## 3. Baseline probes

| Probe | 結果 |
|---|---|
| `python --version` | Python 3.14.6 |
| `py -0p`／3.11 lookup | 有 3.12/3.13/3.14；無 3.11 |
| `python -X utf8 -B -m unittest tests.test_install_framework -q` | 22 tests OK；2 個既有 Windows symlink skips |
| `python -X utf8 -B -m unittest tests.test_contracts -v` | 18 tests；唯一 failure 是 framework NotebookLM preflight |
| `python .agents/skills/codebase-wiki/scripts/parity-check.py` | exit 0 |
| `Test-Path tests/test_capability_removal.py` | False |

## 4. Coverage failure 分診

`ContractTests.test_framework_notebooklm_preflight_is_ready` 回傳 `ready_to_export=false`、coverage `partial`、`uncovered_count=77`。77 paths 全在同一 baseline 新增的 peer skill bundles：`bug-diagnosis`、`delivery-orchestrator`、`implementation-execution`、`project-knowledge`、`requirements-discovery`、`technical-planning`、`writing-great-skills`。

`wiki/synthesis/codebase-functional-coverage.md` 只以 `.agents/skills/codebase-wiki/` 覆蓋 framework skill。唯讀 controlled probe 在記憶體副本新增：

`| .agents/skills/ | supporting-technical | [[notebooklm-ba-functional-export]], [[business-analysis-document]], [[system-analysis-document]], [[system-design-document]] |`

結果從 `uncovered=77/partial/ready=false` 變為 `uncovered=0/complete/ready=true`。根因是 ledger 漏列既有 peer skills；最小修正是一個 supporting-technical prefix，不改 exporter runtime，且位於 FR-004/NFR-001 範圍。

## 5. 選項

| 決策 | 選定 | 未選理由 |
|---|---|---|
| contract | v5 | v4 無法表達 breaking removal |
| Guide | 保留 legacy parsers | 全刪破壞內容與 append-only 歷史 |
| Copilot | built-in `agent` | named profiles 違反下架；省略欄位不等價 |
| upgrade | `obsolete_paths` + preservation regression | auto-delete 超出授權 |
| coverage | `.agents/skills/` prefix | 77 個逐檔 rows 易漂移 |
| BDD | stdlib `unittest` | 無需新 dependency |

## 6. Source bindings

- Requirements：`4342fd35a69d129e1f897b318bda55abe1472fddc2c24b15196c0341ac8a0a08`
- Governance：`bbe3f935e423e8cb1dc709f1c5545683964e4788719237b8fe0238985931799d`
- Capability manifest：`b6654657c9051b73d9e2c1924cdf0440c67b14db9ed6e2b2b39e3e9a41cf8224`
- Installer：`e93873a69bdf9153a0c80b819ff4e7e365f7ed544670be05dedd1df7ef110c8a`
- Coverage ledger：`63d6bfc97a2b40b1618b9fcd0fa295d886f5caa11a3ac682ef7b0fc8a95759d3`
- 本 artifact hash 由 `handoff.json` 固定，避免自我遞迴。
