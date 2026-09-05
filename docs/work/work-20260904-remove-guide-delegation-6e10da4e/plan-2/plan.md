# 技術規劃：移除 Durable Guide 與 Explicit Delegation

- 狀態與核准證據：見 `handoff.json.approval`
- Candidate revision：`plan-v2-20260904`
- 日期：2026-09-04
- 來源規格：`docs/work/work-20260904-remove-guide-delegation-6e10da4e/requirements.md`
- 範圍：移除兩項 active framework capabilities 及其平台入口，保留 legacy Guide 資料與安全升級相容性。
- Planning baseline：repo_id `3a6b11d008ffd5ef15f38f901249bf99b363ea4742fe8c587add45cd96949ab9`；HEAD `ab50a6c4090ac48a1ccf2dd483a7db2e70f0306d`；status `3077f105b951c565a6fb5fe6bada0503003012054a4b11accdc5aa37d68923d9`
- Primary／handoff：`docs/work/work-20260904-remove-guide-delegation-6e10da4e/plan-2/plan.md`／`docs/work/work-20260904-remove-guide-delegation-6e10da4e/plan-2/handoff.json`

## Plan v2 修訂說明

- `SRC-CONTRACT-001.revision` 改為精確 base commit `ab50a6c4090ac48a1ccf2dd483a7db2e70f0306d`，讓 consumer 必定從 planning baseline 讀取原始 v4 blob。
- 新 revision 使用完整 `plan-2/` bundle；產品決策、需求、BDD/TDD、命令與 WP DAG 均不變。
- 此來源綁定修正屬 global baseline；核准後必須建立新的 delivery generation 與 implementation run，重新執行 WP-001 至 WP-003。

## 1. 成果、範圍與限制

交付後，capability contract 與 Copilot/Codex adapter 都不再提供 Durable Guide 或 Explicit Delegation；fresh install 不再複製其檔案，upgrade 只回報舊受管檔為 obsolete，不自動刪除。既有 `type: guide` 頁面、`guide` log operation、Guides index 與 exporter mapping 繼續可讀、可驗證與可匯出。

- 範圍內：manifest v5、Skill routing/authorization、Guide workflow/template/prompts、兩平台 Wiki custom agents、Codex fan-out 設定、剩餘 Copilot prompt metadata、installer regression、公開文件、ChangeLog、framework Wiki 與 coverage ledger。
- 範圍外：平台產品本身的 custom-agent/subagent 功能、既有 `wiki/guides/` 內容、歷史 `wiki/log.md` 與 `ChangeLog.md` 條目、目標 Repo raw sources、自動刪除 obsolete 檔案。

| ID | Required／Observed 限制 | SRC-* |
|---|---|---|
| CON-001 | active operations 與 intent groups 均收斂為 11，雙平台不得引用刪除資源 | SRC-REQ-001、SRC-CONTRACT-001 |
| CON-002 | legacy Guide 是資料相容層，不得被當成 active 建立能力一併刪除 | SRC-REQ-001、SRC-RESEARCH-001 |
| CON-003 | installer 不自動刪除；舊非 Wiki managed paths 只能進 `obsolete_paths` | SRC-REQ-001、SRC-INSTALL-001 |
| CON-004 | framework maintenance 必須同步文件、Wiki/index/log/ChangeLog 並完成規定 checks | SRC-GOV-001、SRC-COVERAGE-001 |

## 2. 證據與變更影響

| SRC ID | Kind／location／revision | 事實 | Plan refs | 直接 WP refs |
|---|---|---|---|---|
| SRC-REQ-001 | spec／核准 requirements／requirements-v2 | 要求兩項功能都移除，保留 legacy Guide 與 non-deleting upgrade | FR-001..004、TR-001..002、NFR-001、AC-001..006 | WP-001..003 |
| SRC-GOV-001 | governance／`framework-maintenance.md`／ab50a6c4090ac48a1ccf2dd483a7db2e70f0306d | matching tests、parity、ChangeLog、Wiki index/log 與 checks 是完成條件 | CON-004、BDD-004、TEST-004 | WP-001..003 |
| SRC-CONTRACT-001 | contract／`capabilities.json`／`ab50a6c4090ac48a1ccf2dd483a7db2e70f0306d` | planning baseline 的 v4 現況為 13 operations、12 groups，含 guide/delegation | TD-001、BDD-001、TEST-001 | WP-001 |
| SRC-INSTALL-001 | project／`install-framework.py`／ab50a6c4090ac48a1ccf2dd483a7db2e70f0306d | surface 遞迴安裝；install-state 差集回報 obsolete，未自動刪除 | TD-004、BDD-002、TEST-002 | WP-002 |
| SRC-COVERAGE-001 | project／`codebase-functional-coverage.md`／ab50a6c4090ac48a1ccf2dd483a7db2e70f0306d | peer skills 尚未由 coverage prefix 分類，造成 77 個 uncovered paths | TD-005、BDD-004、TEST-004 | WP-003 |
| SRC-RESEARCH-001 | supporting／`docs/work/work-20260904-remove-guide-delegation-6e10da4e/plan-2/research.md`／research-v2-20260904 | 固定平台 metadata、baseline tests、controlled probe、來源綁定修正與取捨 | TD-001..005、BDD-001..004、TEST-001..004 | WP-001..003 |

規劃決策：以 capability contract v5 移除兩項 active operations 與所有 Wiki custom-agent／Guide 建立入口，保留 legacy Guide 資料解析，並以 installer obsolete-path 與完整驗證守住升級相容性。

### Current → target

| 影響 ID | 能力／Module | New／Modified／Removed／Preserved | 來源要求 |
|---|---|---|---|
| IMP-001 | capability SSOT/parity | Modified：v4 13/12 → v5 11/11；移除 guide/delegation | FR-001、AC-001 |
| IMP-002 | Guide active resources | Removed：workflow、template、2 prompts、recipes、save-guide follow-up | FR-002、AC-002 |
| IMP-003 | Wiki custom-agent surfaces | Removed：5 Copilot profiles、5 Codex profiles、fan-out config與active policy | FR-003、AC-003 |
| IMP-004 | 剩餘 Copilot prompts | Modified：11 個 prompt 使用 built-in `agent` metadata | FR-003、AC-003 |
| IMP-005 | installer lifecycle | Modified tests around existing contract；fresh omit、upgrade obsolete/preserve | TR-001、AC-005 |
| IMP-006 | legacy Guide data | Preserved：frontmatter/log/index/lint/export parser tokens與既有 pages | TR-002、AC-006 |
| IMP-007 | docs/release/framework knowledge | Modified：active claims、ChangeLog、Wiki/index/log、coverage ledger | FR-004、NFR-001 |
| IMP-008 | outside-in behavior suite | New：`tests/test_capability_removal.py` 四個零 skip scenarios | NFR-001、AC-001..006 |

## 3. 設計與決策

### TD-001 — Capability contract 升為 v5

移除兩個公開 operations 是 breaking change；manifest、parity/test expected operations、groups、entrypoints 與錯誤訊息同步為 v5/11/11。維持 v4 會讓 consumers 無法辨識 breaking removal；installer state schema 不需跟著改版。（FR-001、SRC-CONTRACT-001）

### TD-002 — 將 legacy Guide 資料層與 active workflow 分離

刪除 `guide-workflow.md`、`guide-template.md`、兩個 prompt、Codex recipe 與 follow-up；`page-types.md` 的 Guide 列改為 legacy/read-only compatibility 且不再指向 template。保留 validators、rebuild-index、lint、exporter 與歷史資料。全刪 `guide` tokens 會破壞使用者內容與 append-only log。（TR-002）

### TD-003 — Copilot prompts 使用 built-in agent mode

刪除 repo custom agents 後，11 個保留 prompt 的 frontmatter 統一為 `agent: "agent"`；官方 prompt-file 範例使用此 built-in value。保留 named profiles 不符合下架，省略 metadata 則會改變啟動模式且缺乏同等一手契約。本機只驗證 metadata/parity，不冒充 runtime UAT。（FR-003、SRC-RESEARCH-001）

### TD-004 — 沿用 obsolete_paths 的非破壞升級

source files 刪除後，fresh install 自然省略；舊 install-state 的 14 個非 Wiki managed paths（4 Guide resources、10 custom-agent profiles）由既有差集列為 obsolete，原 bytes 保留。自動刪除可能抹除使用者修改，也超出授權。（TR-001、SRC-INSTALL-001）

### TD-005 — 修復 framework coverage ledger 的 peer-skill 缺口

coverage ledger 加一條 `.agents/skills/` supporting-technical prefix，覆蓋既有 peer SDLC skills；controlled probe 從 uncovered=77/partial 轉為 uncovered=0/complete。逐檔列 77 筆易漂移，忽略 failure 則無法完成 NFR-001。（FR-004、NFR-001）

| MOD ID | 責任 | Caller-facing contract | SEAM／Adapter | 隱藏內容 | 要求 |
|---|---|---|---|---|---|
| MOD-001 | capability SSOT/platform adapters | v5；11 operations/groups；無刪除路徑 | SEAM-001 manifest + parity | enumeration/assertion details | FR-001..003 |
| MOD-002 | installer lifecycle | `files`、`obsolete_paths`、conflicts；不刪 obsolete | SEAM-002 `plan_install`／`apply_install` | state diff/hash mechanics | TR-001 |
| MOD-003 | legacy Guide compatibility | `type: guide`/`guide` log 可驗證、索引、lint、export | SEAM-003 validators/index/exporter | active creator resources | TR-002 |
| MOD-004 | docs/release/framework knowledge | active docs 無宣傳；ChangeLog Removed；Wiki一致 | SEAM-004 repo scan + governance CLIs | 歷史文字/user-authored Wiki | FR-004、NFR-001 |

主要流程：manifest/adapter removal → installer fresh/upgrade checks → legacy Guide compatibility → docs/Wiki/coverage sync → full build/test/BDD/governance。失敗時保留證據，不 commit、merge、發布或清理目標 Repo。

## 4. 測試策略

| BDD-FWK ID | Framework／版本 | Test-only／安裝邊界 | Feature／fixture | Discovery／zero-skip |
|---|---|---|---|---|
| BDD-FWK-001 | Observed Python 3.14.6 stdlib `unittest`；binding Proposed | 無新增依賴 | `tests/test_capability_removal.py`；repo tree + temp target/legacy fixture | CMD-BDD-DISCOVERY-001、CMD-BDD-FULL-001；inventory=4、skip=0 |

| SEAM ID | 可觀察 Interface | 替身策略 | 測試層 |
|---|---|---|---|
| SEAM-001 | manifest、prompt frontmatter、path existence、parity exit | 真實 repo files | outside-in + contract |
| SEAM-002 | installer dry-run/apply JSON 與 target bytes | temporary target + synthetic install-state | outside-in + integration |
| SEAM-003 | validation/index/export CLI results | temporary legacy Guide Wiki | outside-in + unit/integration |
| SEAM-004 | active-doc allowlist、Wiki index/log、preflight JSON | 真實 repo tree | outside-in + governance |

`BOOT-*` 不適用：`unittest` harness、manifest loader、installer functions、validators 與 exporter seams 已可載入；只缺新 behavior binding file。

| BDD ID | Scenario／oracle | Feature method | Focused CMD | WP／order |
|---|---|---|---|---|
| BDD-001 | active contract/adapters 無兩項能力；現況 v4/named agents 使 red | `test_active_contract_and_platform_adapters_drop_removed_capabilities` | CMD-BDD-FOCUSED-001 | WP-001／1 |
| BDD-002 | fresh omit；upgrade exact obsolete 且 bytes preserved；現況 source 仍存在使 red | `test_upgrade_marks_removed_managed_paths_obsolete_without_deletion` | CMD-BDD-FOCUSED-002 | WP-002／1 |
| BDD-003 | legacy Guide 可解析/索引/lint/export；誤刪 parser 即 red | `test_legacy_guide_data_remains_parseable` | CMD-BDD-FOCUSED-003 | WP-002／2 |
| BDD-004 | active docs/Wiki/coverage/preflight 一致；現況 active claims/uncovered=77 使 red | `test_active_docs_and_framework_knowledge_match_removed_surface` | CMD-BDD-FOCUSED-004 | WP-003／1 |

| TEST ID | BDD／風險 | 層級／oracle | Focused／related CMD |
|---|---|---|---|
| TEST-001 | BDD-001／contract drift | `test_contracts.py`：v5 11/11、無 deleted path/named agent | CMD-TDD-FOCUSED-001、CMD-RELATED-001 |
| TEST-002 | BDD-002／升級誤刪 | `test_install_framework.py`：exact obsolete、preserve、Wiki excluded | CMD-TDD-FOCUSED-002、CMD-RELATED-001 |
| TEST-003 | BDD-003／legacy regression | 既有 lint/export/write-guard focused tests 維持 green | CMD-TDD-FOCUSED-003、CMD-RELATED-001 |
| TEST-004 | BDD-004／docs/coverage drift | preflight ready、uncovered=0、單一 Wiki update log | CMD-TDD-FOCUSED-004、CMD-GOVERNANCE-001..008 |

| CMD ID | Purpose | 狀態 | 摘要 |
|---|---|---|---|
| CMD-BDD-DISCOVERY-001 | bdd-discovery | Proposed | AST inventory 4 scenarios |
| CMD-BDD-FOCUSED-001..004 | bdd-focused | Proposed | 每個 scenario 各跑一次 |
| CMD-BDD-FULL-001 | bdd-full | Proposed | behavior suite 4/4 |
| CMD-TDD-FOCUSED-001..004 | tdd-focused | Observed | contracts、installer、legacy、preflight |
| CMD-RELATED-001 | related | Observed | 五個受影響 suites |
| CMD-BUILD-FULL-001 | build-full | Observed | framework scripts/tools/tests 記憶體 compile |
| CMD-TEST-FULL-001 | test-full | Observed | 完整 unittest discovery |
| CMD-GOVERNANCE-001..008 | governance | Observed | parity、frontmatter、stale、log、stats、lint、index、preflight |

順序：各 WP 先跑 BDD 取得預期 red，再用映射 TEST 做 minimal green/refactor-with-green；focused BDD/related green 後才前進。最後 fresh 執行 full build/test/BDD/governance。BDD 零 skipped；完整 suite 只允許既有環境相依 skips。此環境無 Python 3.11，不能宣稱 3.11 coverage；本次在 Python 3.14.6 完成本地門檻並明列限制。

## 5. 工作包

### WP-001 — Active contract 與 platform adapters 下架

- 結果：FR-001..003、AC-001..004、IMP-001..004、IMP-008。
- Blocked by：None。
- Intent：建立 BDD-001 red；更新 manifest/routing/authorization/follow-up/Skill/Codex/Copilot/parity/tests；刪 Guide creator resources與 10 profiles；保留 prompts 改 built-in agent。
- 順序／證據：BDD-001 → TEST-001 → CMD-BDD-FOCUSED-001、CMD-TDD-FOCUSED-001、CMD-RELATED-001。

### WP-002 — Fresh install、safe upgrade 與 legacy Guide

- 結果：TR-001、TR-002、AC-005、AC-006、IMP-005..006。
- Blocked by：WP-001。
- Intent：以新/舊 targets 固定 14 個 prior managed non-Wiki paths 全列 obsolete 且不刪；Wiki 不進 obsolete；真實 legacy fixture 鎖定 parser/index/lint/export。
- 順序／證據：BDD-002 → TEST-002 → BDD-003 → TEST-003 → focused/related green。

### WP-003 — 文件、release、framework Wiki 與完整驗證

- 結果：FR-004、NFR-001、AC-004、AC-006、IMP-007。
- Blocked by：WP-002。
- Intent：更新 README/Codex/AGENTS/docs/samples/ChangeLog/Wiki；同步 `wiki/index.md`；只 append 一筆 `wiki/log.md` update；修 coverage prefix；清除 active claims但保留 history/legacy。
- 順序／證據：BDD-004 → TEST-004 → full build/test/BDD + CMD-GOVERNANCE-001..008。

## 6. 風險與追溯

| Risk ID | 觸發／影響 | Mitigation／驗證 |
|---|---|---|
| RISK-001 | legacy `guide` 被誤刪，舊 Wiki 失效 | BDD-003 + TEST-003 + explicit allowlist |
| RISK-002 | installer 漂移，舊檔漏報或誤刪 | BDD-002 exact set/byte preservation/Wiki exclusion |
| RISK-003 | Copilot metadata 推論與實機差異 | 官方文件 + metadata/parity；不宣稱 runtime UAT |
| RISK-004 | active-doc 搜尋誤傷歷史或漏宣傳 | active scope/legacy allowlist；logs append-only |
| RISK-005 | coverage prefix 過寬 | 僅 supporting-technical；preflight ledger issues=0；fresh review |
| RISK-006 | 無 Python 3.11 | 3.14.6 全驗證；發版前另跑 3.11 |

| SRC／要求 | TD／MOD／SEAM | BDD | TEST | WP | 證據 |
|---|---|---|---|---|---|
| FR-001..003／SRC-CONTRACT-001 | TD-001/003、MOD-001、SEAM-001 | BDD-001 | TEST-001 | WP-001 | focused + parity |
| TR-001／SRC-INSTALL-001 | TD-004、MOD-002、SEAM-002 | BDD-002 | TEST-002 | WP-002 | installer tests |
| TR-002／SRC-REQ-001 | TD-002、MOD-003、SEAM-003 | BDD-003 | TEST-003 | WP-002 | legacy tests |
| FR-004/NFR-001／SRC-GOV-001/COVERAGE-001 | TD-005、MOD-004、SEAM-004 | BDD-004 | TEST-004 | WP-003 | full/governance |
| SRC-RESEARCH-001／AC-001..006 | TD-001..005、MOD-001..004 | BDD-001..004 | TEST-001..004 | WP-001..003 | all commands |

Revision impact：`SRC-CONTRACT-001` 與 `SRC-RESEARCH-001` 的 Plan v2 修正都是 global baseline，影響全部三個 WP；核准後以新的 delivery generation 與 implementation run 全量重跑。

## 7. Artifacts 與 readiness

| Path | Role | 權威內容 |
|---|---|---|
| `plan-2/plan.md` | primary | 設計、BDD/TDD、DAG、風險與追溯 |
| `plan-2/research.md` | supporting | platform/baseline/controlled-probe evidence |
| `plan-2/handoff.json` | handoff | hashes、sources、contracts、commands、WP mappings |

- 缺口／未知：無阻塞性缺口；Python 3.11 與 Copilot runtime UAT 是明列的非本地驗證限制。
- BDD/BOOT/TDD/WP/commands：完整；BOOT 有不適用證據。
- `handoff.json` schema/cross-references：Candidate sealing 前機器驗證。
- 品質：通過；NotebookLM baseline failure 有可否證根因與最小修正。
- 寫入：使用者核准 promotion 前，所有 postimages 均不寫入工作樹。
