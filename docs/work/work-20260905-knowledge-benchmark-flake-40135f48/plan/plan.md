# 技術規劃：穩定大型 Knowledge benchmark baseline

- 狀態與核准證據：見 `handoff.json.approval`
- Candidate revision：`plan-v1-20260905`
- 日期：2026-09-05
- Work ID：`work-20260905-knowledge-benchmark-flake-40135f48`
- 來源規格：`docs/work/work-20260905-knowledge-benchmark-flake-40135f48/requirements-2.md`
- Primary BUG：`bug-knowledge-benchmark-baseline-flake` assessment revision 2
- Planning baseline：repo_id `3a6b11d008ffd5ef15f38f901249bf99b363ea4742fe8c587add45cd96949ab9`；HEAD `71e7d0289ff04ebb45eb0f09e7e14052cb9f4cd1`；status `8b48f5404eda0e8d2ae9632b0664c1da4369a6f2756ee25b1aeb26d6641ccd92`
- Primary／handoff：`docs/work/work-20260905-knowledge-benchmark-flake-40135f48/plan/plan.md`／`docs/work/work-20260905-knowledge-benchmark-flake-40135f48/plan/handoff.json`

## 1. 成果、範圍與限制

此 Ready 計畫以每個 operation 三個固定樣本、全域單一 isolated-outlier 預算與 fail-closed report v2 穩定 50k/5k benchmark，並維持 2.0 秒門檻及本機手動 Windows／Linux portability 治理。

交付後，使用者可由一次 machine-readable outcome 區分正常通過、帶一個孤立 outlier 的通過、持續效能違規、不確定 timing、功能違規與環境故障；跨平台核准仍要求兩台實際 Windows／Linux 主機各自在相同 clean source revision 產生報告，再離線比較。

- 範圍內：benchmark timing decision、report/error/CLI、portability comparator、BDD-016/019/020/021、matching unit/integration tests、Project Knowledge governance validator、Skill、`.gitignore`、公開驗證文件、ChangeLog 與 framework Wiki。
- 範圍外：50k/5k fixture／functional oracle／2.0 秒門檻調整、GitHub workflow、link renderer BUG、Windows Git `Access denied`、NotebookLM BA／SA export、host／防毒／CPU 調校、production dependency。
- 成功不允許 blanket retry。三次真實 run 中任一非 pass 都先保存並停止；只有新診斷或 upstream reapproval 才可改變修法。

| ID | Required／Observed 限制 | SRC-* |
|---|---|---|
| CON-001 | workload 固定 50,000 files／5,000 pages／39,998 source files，五個 cold、五個 warm 與一個 index operation 均保留 | SRC-REQ-001、SRC-BENCH-001 |
| CON-002 | threshold 固定 `2.0s`；不能以提高門檻、縮小 fixture、sleep 或挑選成功 run 取得 green | SRC-REQ-001、SRC-BUG-001 |
| CON-003 | v1 的 fixture、host、functional、digest 與單一第一樣本 evidence 不遺失或被重新解釋 | SRC-REQ-001、SRC-BENCH-001、SRC-COMPARE-001 |
| CON-004 | invalid timing、functional drift、process／timeout／cleanup 與 legacy report 全部 fail closed | SRC-REQ-001、SRC-BUG-001、SRC-BENCH-001 |
| CON-005 | repository 維持 local-manual policy 且 workflow YAML 數量為零；`.gitignore` 只新增 `.knowledge-test-tmp/` | SRC-REQ-001、SRC-VALIDATOR-001、SRC-REPO-POLICY-001 |
| CON-006 | framework maintenance 同步 tests、公開文件、ChangeLog、Wiki/index 與一筆 append-only log | SRC-REQ-001、SRC-GOV-001 |

## 2. 證據與變更影響

| SRC ID | Kind／location／revision | 事實 | Plan refs | 直接 WP refs |
|---|---|---|---|---|
| SRC-REQ-001 | spec／`requirements-2.md`／requirements-v2-20260905 | 核准四態 timing、fail-closed consumer、local-manual governance 與 9 個 AC | CON-001..006、TD-001..005、BDD-016/019/020/021、TEST-001..004 | WP-001..003 |
| SRC-BUG-001 | bug／`assessment-2.json`／2 | 單樣本 verdict boundary 已支持；底層 outlier 來源仍 hypothesized／medium | TD-001、BDD-016/019/020、TEST-001..003 | WP-001..003 |
| SRC-GOV-001 | governance／`framework-maintenance.md`／71e7d028… | matching regression、公開文件、ChangeLog、Wiki/index/log 是完成條件 | CON-006、BDD-021、TEST-004 | WP-003 |
| SRC-BENCH-001 | project／`knowledge_benchmark.py`／71e7d028… | 現況 11 個單樣本直接決定 v1 outcome；可載入 runner／timing seams | TD-001/002、MOD-001/002、BDD-016/019/020、TEST-001/002 | WP-001..002 |
| SRC-COMPARE-001 | contract／`compare_portability_reports.py`／71e7d028… | 現況 comparator 只接受 v1 且任一單值超限即失敗 | TD-003、MOD-003、BDD-019/016、TEST-003 | WP-002 |
| SRC-VALIDATOR-001 | project／Project Knowledge `validate_contracts.py`／71e7d028… | 穩定產生 11 個 workflow／ignore findings，與 repo policy 衝突 | TD-004、MOD-004、BDD-021、TEST-004 | WP-003 |
| SRC-REPO-POLICY-001 | contract／`tests/test_contracts.py`／71e7d028… | 既有 regression 要求 `.github/workflows` 零 YAML 與本機手動驗證 | TD-004/005、BDD-021、TEST-004 | WP-003 |
| SRC-RESEARCH-001 | supporting／`plan/research.md`／research-v1-20260905 | 保存完整 probes、alternatives、migration、known failure 與 source hashes | TD-001..005、BDD-016/019/020/021、TEST-001..004 | WP-001..003 |

### Current → target

| 影響 ID | 能力／Module | New／Modified／Preserved | 來源要求 |
|---|---|---|---|
| IMP-001 | timing observations | Modified：每個 11 operations 由 1 樣本改為固定 3 樣本，順序不變且保存全部 raw evidence | FR-002、NFR-002/003 |
| IMP-002 | timing decision | New：0/1/2/3 breach 四態與全域單一 outlier budget | FR-003、NFR-001/002 |
| IMP-003 | report/error contract | Modified：report/error v2、明確 verdict／reason、cleanup、producer identity；legacy evidence preserved | FR-004/005、TR-001 |
| IMP-004 | functional repetition | New：每次 timing sample 保存 normalized result hash，任一 drift 為 functional failure | FR-001/002、AC-001/004 |
| IMP-005 | CLI evidence persistence | New：選配 create-only UTF-8/LF `--output`，stdout 與既有 exit 0/1、environment exit 4 保持 | FR-005/006、NFR-004 |
| IMP-006 | portability comparator | Modified：v2 重算 samples／decisions／projection，要求 clean identical source與兩個 OS | FR-004/006、TR-001 |
| IMP-007 | behavior/unit coverage | Modified：BDD-016/020；New：BDD-019/021；matching unit/integration tests | AC-001..007/009 |
| IMP-008 | local-manual governance | Modified：移除 workflow／docs-ignore 錯誤要求，新增 no-workflow、manual commands與 temp-root contract | FR-006/007、NFR-005 |
| IMP-009 | framework docs/Wiki | Modified：Skill、validation README、ChangeLog、`[[platform-adapters-and-release]]`、index/log | CR-001、AC-008 |

## 3. 設計與決策

### TD-001 — 固定三樣本與保守四態規則

每個 timing-sensitive operation 連續取得三個正式樣本，threshold 比較固定為 `duration > 2.0` 才算 breach。Operation decision 是 0/3 `within-threshold`、1/3 `isolated-outlier`、2/3 `mixed-inconclusive`、3/3 `sustained-violation`；median 只作診斷，不取代 breach-count rule。（FR-002/003、NFR-001/002）

整體 timing precedence 為 sustained → inconclusive → isolated／within：任一 3/3 是 performance failure；否則任一 2/3 是 inconclusive；否則全體超過一個 breach 仍是 inconclusive；只有零 breach 或全體唯一一個 breach 可通過。這避免把分散在多個 operation 的 host instability誤稱為成功，也不把 mixed 2/3 evidence 冒充已確認的持續產品回歸。

五樣本 median 會把正式 operation calls 從 33 增到 55，沒有增加本需求必要的分類能力；2/3 直接 failure 則超過 assessment 的 root-cause certainty。單樣本 retry 明確拒絕。

### TD-002 — v2 report 保留 v1 evidence 原義

Producer 輸出 `knowledge-portability-report/v2`：top-level `outcome=passed|failed` 與 `verdict=pass|functional-failure|performance-failure|inconclusive`；每個 operation 保存 raw samples、result hashes、median、breach count 與 classification。Closed decision contract 固定 sample count、threshold、operation order、rules、global budget與 canonical SHA-256。（FR-001/002/004、TR-001）

既有 `functional`／expected digest、fixture shape、host、cold／warm hashes均保留；`durations_seconds` 保持「每個 operation 第一個正式樣本＋fixture setup」的 v1 原義。新 consumer 只由 raw arrays 重算 verdict，並驗證 legacy projection，不會把舊單值重新解釋成代表性 statistic。

每次 timed call 另保存 normalized result hash；同 operation 三個 hashes、cold/warm 對應 hashes與既有 canonical payload 任一不等即 `functional-failure`，其 precedence 高於 timing 結論。

CLI 保留 stdout；選配 `--output` 以 exclusive-create 寫入 UTF-8/LF，不覆寫 evidence。Report pass 回傳 0，其餘正常 report 回傳 1；environment error 保留 4。`knowledge-portability-error/v2` 只輸出 stable category／code、cleanup status與 recovery，不洩漏 raw stderr、absolute path、環境值或 exception message。（FR-005/006、NFR-004）

### TD-003 — Comparator 重算且綁定 clean producer identity

`compare_reports` 使用 producer 擁有的純 decision functions重新驗證 exact operation order、三個 finite/nonnegative/non-bool samples、contract digest、asserted classifications、top-level verdict、result hashes、legacy projection與所有 raw sample max。舊 v1、任何 default 補值或宣告／重算 drift 都是 incompatible failure。（FR-004/006、TR-001）

Report 的 producer identity 包含根 `VERSION`、producer Git HEAD、worktree-clean flag與 benchmark script SHA-256。`knowledge-portability-comparison/v2` 只有在恰有一份 Windows、一份 Linux、兩者 strict-clean、identity／contract／functional oracle相同且 verdict=pass、cleanup=removed 時通過；單一 isolated outlier report 可依共同規則通過，但 inconclusive／performance／functional／environment evidence 一律不能。（AC-004/006）

### TD-004 — 對齊 local-manual portability，零 workflow YAML

Project Knowledge validator 移除不存在 workflow 與四個 docs ignore required fragments；改驗證 producer/comparator、Skill與 validation README 的實際 Python commands、根 `.gitignore` 精確含 `.knowledge-test-tmp/` 且不含四個禁用 patterns，以及 `.github/workflows` 不含任何 `.yml|.yaml`。Root contract test 對同一規則做 mutation-sensitive assertion。（FR-006/007、NFR-005）

公開流程要求兩個 clean hosts各自使用 producer保存 report，人工搬到只含兩份檔案的 ignored directory，再執行 comparator。這是 local-manual evidence，不是 CI 或自動 release；本機 synthetic OS metadata只驗證 contract，不宣稱 Linux performance。（AC-006/009）

### TD-005 — Verified BUG evidence 與既有 link failure 隔離

Original delivery-group command在修改前是 intermittent，在修改後與 BDD-016/019/020、TEST-001..003 一起重跑。Implementation commit 後 strict-clean Windows host連續執行三個獨立 50k/5k runs；3/3 均須 report v2 `verdict=pass`、functional oracle相符、cleanup removed，不能以替代 run覆蓋非 pass。（AC-007、TR-003）

Root suite 仍完整執行；唯一可接受殘留是 `bug-knowledge-index-relative-links` 在 `test_active_docs_and_framework_knowledge_match_removed_surface` 與 `test_local_markdown_links_resolve` 對三個精確 targets造成的四個 failures：`docs/knowledge/topics/work-20260904-remove-guide-delegation-6e10da4e-implementation.md`、`docs/knowledge/topics/work-20260905-knowledge-benchmark-flake-40135f48-requirements.md`、`docs/knowledge/decisions/work-20260905-knowledge-benchmark-flake-40135f48-planning.md`。任何新 method／diagnostic／target都阻擋，不修改 renderer 或該 BUG tests。（TR-002）

## 4. Module、Interface 與資料流

| MOD ID | 責任 | Caller-facing contract | SEAM／Adapter | 隱藏內容 | 要求 |
|---|---|---|---|---|---|
| MOD-001 | timing observation／decision | `classify_operation(samples)` 與 `evaluate_timing_evidence(operation_samples)` 回傳 deterministic closed decision | SEAM-001 `knowledge_benchmark` pure functions | perf counter、median、breach aggregation | FR-002/003、NFR-001/002 |
| MOD-002 | benchmark report／CLI／cleanup | `run_benchmark(...) -> report/v2`；CLI stdout／optional output／exit contract | SEAM-002 `run_benchmark`、`main`、typed environment error | warm-up、fixture lifecycle、safe diagnostics | FR-001/004/005、NFR-004 |
| MOD-003 | Windows/Linux comparison | `compare_reports(iterable) -> comparison/v2`，完全重算 report evidence | SEAM-003 `compare_reports`／CLI root scan | report parsing、diagnostic accumulation | FR-004/006、TR-001 |
| MOD-004 | repository governance | governance validator、behavior/root contract與人工文件一致 | SEAM-004 `governance_errors`、BDD-021、root contract | fragment inventory與doc rendering | FR-007、NFR-005、CR-001 |

### SEAM-001 timing contract

- Input：依 fixed `operation_order` 的 11 個 entries；每個恰有三個 samples與三個 result hashes。
- Valid sample：`int|float` 但非 `bool`、`math.isfinite`、`>=0`；threshold只取 producer constant 2.0。
- Output：per-operation median／breach count／classification，以及 overall `timing_status`、total breach count、reason code與 contract digest。
- Invalid input：typed measurement-contract environment error；不回傳 partial pass。

### SEAM-002 report／錯誤 precedence

1. 建立／驗證 fixed fixture並分離 fixture setup duration。
2. 完成既有 warm-up；以 operation-major、sample-minor 固定順序執行 15 cold processes、15 warm calls、3 Candidate calls。
3. 驗證所有 repeated functional hashes與既有 functional oracle。
4. 由 SEAM-001 評估 timing；functional drift先形成 `functional-failure`，否則 timing status映射 pass／inconclusive／performance-failure。
5. 在 return前完成 cleanup並把 `removed|retained-by-request` 寫入 report；cleanup failure取代任何產品結論為 environment error。
6. `--output` 只在完整 report形成後 create-only materialize；output failure 回傳 environment error且不破壞既有檔。

### SEAM-003 comparator contract

Comparator 不相信 `outcome`、`verdict`、median、breach count、classification、contract hash或 max 的任何 asserted value；全部從 raw／canonical constants重算後要求完全相等。`durations_seconds` 只驗證為第一樣本 projection。Input directory只讀 `knowledge-portability-report-*.json`，恰好一個 Windows與一個 Linux；comparison output不會被再次當成 input。

### 版本化 shape

| Shape | 必要狀態／欄位 | Fail-closed 邊界 |
|---|---|---|
| `knowledge-portability-report/v2` | outcome、verdict、producer、host、fixture/functional digests、legacy durations、timing decision、cleanup | v1／unknown key semantics不升級；缺 raw／hash／identity拒絕 |
| `knowledge-timing-decision/v1` | closed contract＋digest、ordered operations、samples/result hashes、median/breaches/classification、overall status/reason | 任一 invalid number、count/order/rule drift拒絕 |
| `knowledge-portability-error/v2` | outcome failed、verdict environment-error、stable category/code、cleanup、recovery | 不含原始 exception／stderr／absolute path |
| `knowledge-portability-comparison/v2` | outcome、oses、producer/contract/functional identity、max raw duration、diagnostics | 缺／重複 OS、dirty/different source、任何 non-pass report拒絕 |

## 5. 測試策略

| BDD-FWK ID | Framework／版本 | Test-only／安裝邊界 | Feature／fixture | Discovery／zero-skip |
|---|---|---|---|---|
| BDD-FWK-001 | Observed Python 3.14.6 stdlib `unittest` custom scenario runner | 無新增依賴或安裝 | `test_behavior.py`；synthetic decisions、250/20 reduced fixture、50k/5k full fixture、real repo governance | CMD-BDD-DISCOVERY-001；target inventory=21、run=0、skip=0；所有 focused/full run skip=0 |

`BOOT-*` 不適用：`run_benchmark`、`compare_reports`、`governance_errors`、behavior `_run` 與 unittest fixtures在 baseline 均可載入。新純 decision interface可由 BDD 使用 `getattr` assertion先形成正常 oracle red，不需要 load error、sentinel或 production wiring bootstrap。

| BDD ID | Scenario／fixture／oracle | 正確 red | Focused CMD | WP／order |
|---|---|---|---|---|
| BDD-020 | Modified：250/20 真實 fixture產生 11×3 ordered samples、result hashes、v2 pass、legacy projection、functional equality、cleanup removed | 先更新 oracle；baseline 回傳 v1與單樣本而 assertion mismatch | CMD-BDD-FOCUSED-001 | WP-001／1 |
| BDD-019 | New：四組 controlled sequences各重算十次；runner decision、CLI mapping與 comparator對 pass/isolated/inconclusive/sustained一致，兩個分散 outliers為 inconclusive，v1/incomplete drift拒絕 | `getattr` assertion顯示 decision seam不存在；baseline comparator拒絕目標 v2 pass fixture | CMD-BDD-FOCUSED-002 | WP-002／1 |
| BDD-016 | Modified：完整 50k/5k report v2，全部 operations三樣本、功能／producer／cleanup evidence完整且 verdict pass | baseline即使 timing pass仍因 schema v1缺 decision evidence而 assertion mismatch | CMD-BDD-FOCUSED-003、CMD-BUG-REPRO-001 | WP-002／2 |
| BDD-021 | New：no-workflow、單一 temp ignore、Skill/docs manual producer/comparator與 project validator一致 | baseline `governance_errors()` 穩定回傳 11 findings | CMD-BDD-FOCUSED-004 | WP-003／1 |

| TEST ID | BDD／風險 | 層級／SEAM／oracle | Focused／related CMD |
|---|---|---|---|
| TEST-001 | BDD-020/019／classifier 放寬或 nondeterministic | unit／SEAM-001：0/1/2/3 breaches、global budget各 10 次 exact；bool/NaN/inf/negative/wrong count拒絕 | CMD-TDD-FOCUSED-001、CMD-RELATED-001 |
| TEST-002 | BDD-020/016／repeated functional、cleanup、secret leakage、output overwrite | integration／SEAM-002：reduced fixture call counts/order/hash/projection；dependency/process/timeout/fixture/cleanup/output injections與 exit 0/1/4 | CMD-TDD-FOCUSED-001、CMD-RELATED-001 |
| TEST-003 | BDD-019/016／consumer trust或跨平台誤判 | unit/integration／SEAM-003：四 verdict fixtures、raw recomputation、v1/shape/assertion/source/clean/OS drift、max all samples | CMD-TDD-FOCUSED-001/002、CMD-RELATED-001 |
| TEST-004 | BDD-021／治理再次要求 hosted workflow或忽略 docs | contract／SEAM-004：validator=0；root method固定 commands、no YAML、temp ignore presence與四個禁用 patterns absence | CMD-TDD-FOCUSED-002/003、CMD-GOVERNANCE-001/002 |

執行順序：每個 WP 先建立對應 BDD 的 assertion red，再讓映射 TEST red → minimal green → refactor-with-green；focused BDD、TDD、related 全綠後才能進下一包。最後 fresh 執行 owner full suite、root full suite、framework governance與三次真實 benchmark。未核准的 retry、skip或 threshold/workload變更一律不是完成證據。

## 6. 工作包

### WP-001 — 多樣本 runner、report v2 與安全 CLI

- 結果：FR-001..005、NFR-001..004、TR-001、AC-001/004/005 的 producer half；IMP-001..005。
- Blocked by：None。
- Files：`knowledge_benchmark.py`、`test_behavior.py` 的 BDD-020、`test_query.py` producer/classifier tests。
- Intent：先把 BDD-020改為 v2三樣本 oracle取得 red；建立 SEAM-001 pure decisions與 SEAM-002 report/error/cleanup/output；每次 repeated call驗證 result hash；完成 TEST-001/002。
- 順序／證據：BDD-020 red → TEST-001 red/green → TEST-002 red/green → CMD-BDD-FOCUSED-001、CMD-TDD-FOCUSED-001、CMD-RELATED-001 green。

### WP-002 — Consumer 重算、source binding 與完整 BUG regression

- 結果：FR-004/006、NFR-002/003、TR-001/003、AC-002/003/004/006/007；IMP-006/007。
- Blocked by：WP-001。
- Files：`compare_portability_reports.py`、`test_behavior.py` 的 BDD-019/016與 performance group、`test_query.py`／`test_workflow.py` comparator tests。
- Intent：建立 BDD-019四態與十次 deterministic red；升級 comparator v2並重算所有 evidence；更新 BDD-016 full oracle；不把 synthetic OS fixtures冒充 actual portability。
- 順序／證據：BDD-019 red → TEST-003 red/green → BDD-019 focused green → BDD-016 schema red → full producer/comparator green → original reproduction green。

### WP-003 — Local-manual governance、framework knowledge 與 final verification

- 結果：BR-002、FR-006/007、NFR-005、TR-002/003、CR-001、AC-006..009；IMP-008/009。
- Blocked by：WP-002。
- Files：Project Knowledge `validate_contracts.py`／`SKILL.md`、`.gitignore`、`docs/validation/README.md`、`tests/test_contracts.py`、`test_behavior.py` 的 BDD-021、`ChangeLog.md`、`wiki/modules/platform-adapters-and-release.md`、`wiki/index.md`、`wiki/log.md`。
- Intent：BDD-021先固定 local-manual/no-workflow red；移除錯誤 workflow/docs-ignore expectations並加入正向／反向契約；同步使用文件與 Wiki provenance；append exactly one framework update log。
- Final evidence：owner full suite無本 scope failure；root full suite只留精確 link BUG；parity/frontmatter/stale/log/stats/lint/index通過；implementation commit後 strict-clean三個 Windows 50k/5k reports皆 pass。沒有實際 Linux report時明示 portability runtime未完成，不阻塞本機 BUG修復但不得宣稱 cross-platform passed。

## 7. Commands 摘要

完整 cwd、timeout、network、allowed writes、side effects、成功與完整性條件以 `handoff.json.commands` 為權威。命令族如下：

- BUG／BDD：CMD-BUG-REPRO-001、CMD-BDD-DISCOVERY-001、CMD-BDD-FOCUSED-001..004、CMD-BDD-FULL-001。
- Inner／related：CMD-TDD-FOCUSED-001..003、CMD-RELATED-001。
- Full：CMD-BUILD-FULL-001、CMD-TEST-FULL-001/002。
- Governance：CMD-GOVERNANCE-001..008、CMD-BENCHMARK-VERIFY-001..003。

實際雙平台 comparator invocation 由 `docs/validation/README.md` 保存為 release／portability follow-up；本機 completion 不建立假的 Linux report。其 recomputation 與 CLI input contract 由 BDD-019、TEST-003 及 owner full suite自動驗證。

三個 benchmark verify commands 使用新 `--output`，因此是 Proposed，且以 baseline `--help` 無該 option 作 absence evidence；其餘命令入口均已存在而標示 Observed。所有網路政策為 forbidden；唯一 repository writes 是 bounded `.knowledge-test-tmp/` 與已 ignore 的 `dist/knowledge-benchmark-verification/`。

## 8. 風險、失敗分支與 rollback

| Risk ID | 觸發／影響 | Mitigation／驗證 |
|---|---|---|
| RISK-001 | 3/3 rule漏掉真實 intermittent regression | 2/3與多個 isolated仍非 pass；三次 full run；任何持續 3/3直接 fail；保留全部 raw samples |
| RISK-002 | 1/3 outlier policy被濫用到多 operations | 全域 breach budget=1；第二個 breach即 inconclusive；comparator重算 |
| RISK-003 | 多次 operation輸出功能漂移 | 每樣本 result hash＋既有 expected functional digest；functional failure precedence |
| RISK-004 | v1 automation silent pass | report/comparison/error升版；comparator明拒 v1；Skill/docs/tests同步 |
| RISK-005 | Environment detail洩漏本機 path／secret | stable category/code，不輸出 raw stderr/exception；注入 secret regression |
| RISK-006 | Cleanup或output覆寫證據 | cleanup-finally precedence、create-only output、exact temp root、recovery message |
| RISK-007 | Governance修正暗中加入 CI或忽略 docs | no-YAML枚舉、forbidden ignore assertions、root＋BDD-021雙層契約 |
| RISK-008 | Known link BUG掩蓋新增 failure | exact two methods＋three targets allowlist；任何其他 failure阻擋 |
| RISK-009 | 本機 Windows evidence被外推為 portability | producer metadata＋comparator要求實際兩 OS；文件明列 Linux follow-up |

Rollback 以 WP commits為界：WP-001/002 report schema必須一起回退，禁止只回退 comparator或 producer；WP-003治理／文件若回退也必須維持既有 no-workflow產品契約。若任何 BDD red顯示 assessment causal boundary錯誤、三次 full run出現 non-pass或修改需碰 link renderer／host設定，停止產品寫入，保存 evidence並回 upstream reapproval，不追加第二個猜測 patch。

## 9. 追溯矩陣

| 來源要求 | TD／MOD／SEAM | BDD | TEST | WP | 完成證據 |
|---|---|---|---|---|---|
| FR-001/002、NFR-001/004、AC-001 | TD-001/002、MOD-001/002、SEAM-001/002 | BDD-020、BDD-016 | TEST-001/002 | WP-001/002 | reduced＋full reports、functional hashes |
| FR-003、NFR-002、AC-002/003 | TD-001、MOD-001、SEAM-001 | BDD-019 | TEST-001 | WP-001/002 | 四 sequences各 10/10一致 |
| FR-004、TR-001、AC-004 | TD-002/003、MOD-002/003、SEAM-002/003 | BDD-019/020/016 | TEST-002/003 | WP-001/002 | v2 recomputation與legacy rejection |
| FR-005、AC-005 | TD-002、MOD-002、SEAM-002 | BDD-020 | TEST-002 | WP-001 | typed injections、cleanup/output evidence |
| FR-006、NFR-003/005、AC-006 | TD-003/004、MOD-003/004、SEAM-003/004 | BDD-019/021 | TEST-003/004 | synthetic contract＋manual actual-host procedure |
| FR-007、AC-009 | TD-004、MOD-004、SEAM-004 | BDD-021 | TEST-004 | governance=0、no YAML、exact ignore |
| TR-002/003、AC-007 | TD-005、SEAM-002/004 | BDD-016/021 | TEST-002/004 | original repro、3 reports、exact residual |
| CR-001、AC-008 | TD-004/005、MOD-004 | BDD-021 | TEST-004 | ChangeLog、Wiki/index、one log、checks |

## 10. Artifacts 與 readiness

| Path | Role | 權威內容 |
|---|---|---|
| `plan/plan.md` | primary | 設計、interfaces、BDD/TDD、DAG、風險、追溯與失敗分支 |
| `plan/research.md` | supporting | source hashes、baseline probes、alternatives、migration與 known failure |
| `plan/handoff.json` | handoff | approval、hashes、sources、bug context、commands、contracts與 WP mappings |

- 阻塞性開放事項：無。實際 Linux report是明列 release／portability follow-up，不冒充本機已取得的 evidence。
- 不確定性：底層 latency outlier來源維持 hypothesized／medium；修法只改已支持的 verdict boundary，不宣稱調校 host或改善 query本身速度。
- BDD／TDD／WP／commands：完整；BOOT有不適用 evidence；DAG 是 WP-001 → WP-002 → WP-003。
- BUG verification target：`verified`，因原症狀為 intermittent且有原始 reproduction command；partial safeguards不適用。
- `handoff.json` schema、cross references、payload digest、artifact/source hashes與 Knowledge co-promotion在 Candidate sealing 前機器驗證。
- 寫入：使用者確認完整 Plan／Knowledge Candidate 前，正式 `docs/work/.../plan/` 與 `docs/knowledge/` postimages均不寫入工作樹。
