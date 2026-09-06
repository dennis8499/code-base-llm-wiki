# 規劃研究：穩定大型 Knowledge benchmark baseline

- 日期：2026-09-05
- Work ID：`work-20260905-knowledge-benchmark-flake-40135f48`
- Planning baseline：HEAD `71e7d0289ff04ebb45eb0f09e7e14052cb9f4cd1`；porcelain v1 `-z` SHA-256 `8b48f5404eda0e8d2ae9632b0664c1da4369a6f2756ee25b1aeb26d6641ccd92`
- 執行環境：Windows、Python 3.14.6；所有網路存取均未使用。
- 用途：保存 timing、report consumer、治理矛盾、測試 seam 與 known-failure baseline，供 Ready plan consumer 獨立重查。

## 1. Primary BUG 與固定事實

- 核准 assessment revision 2 維持 `confirmed`／`intermittent`；root cause 是 `hypothesized`／`medium`。已支持的 causal boundary 是「單一 wall-clock 樣本直接控制整體 verdict」，底層 latency outlier 來源仍未確認。
- 留存 failure 的 `index_candidate` 為 `3.470925499976147s`；相同 source SHA、50,000-file／5,000-page fixture 與相同 functional digest 的相鄰／受控樣本可通過，五個受控值為 `0.7987834999803454–0.9807830000063404s`。
- `knowledge_benchmark.py` 的固定契約為 `FILE_COUNT = 50_000`、`PAGE_COUNT = 5_000`、`MAX_SECONDS = 2.0` 與既定 `EXPECTED_FUNCTIONAL_SHA256`。現況只對五個 cold queries、五個 warm queries 與一個 index Candidate 各量一次，再用 `all(value <= MAX_SECONDS)` 直接決定 pass／fail。
- Cold path 在正式樣本前只 warm up 第一個 query 的 process/tool readiness；warm path 先 warm up 五個 queries 與 Candidate。這些 warm-up 不列入受評估 timing，fixture setup 另列。
- 現行 functional payload、cold／warm hashes 與 Candidate operation hashes已能穩定驗證結果等價；多次 timing 觀測不得改變這份既有 functional payload 或其 expected digest。

## 2. 現行 report 與 consumer

- Producer 輸出 `knowledge-portability-report/v1`，`outcome` 只有 `passed|failed`；`durations_seconds` 保存每個 operation 的唯一樣本與獨立 fixture setup。
- CLI 對 report pass 回傳 0、一般 report failure 回傳 1；任何 exception 以 `knowledge-portability-error/v1`／`BENCHMARK_ENVIRONMENT` 回傳 4，但現況會把原始 exception text 直接放入 message。
- `compare_portability_reports.py` 只接受一份 Windows 與一份 Linux v1 report，固定檢查 50k/5k、tracked shape、functional oracle、cold／warm hash，再以任一單值大於 2.0 秒直接失敗。
- Comparator 現況不綁定 producer Git SHA、framework version、cleanliness 或 decision-contract digest；也沒有足夠 raw evidence 重算多樣本判定。
- `BDD-016` 直接要求 v1 `outcome=passed` 與單值 `<=2.0`；`BDD-020` 以 250-file／20-page fixture 鎖定五個 cold／warm 單樣本。`BDD-019` 尚未使用。
- `knowledge_benchmark.py --help` 只有 `--fixture-root`、`--reuse-fixture`、`--keep-fixture`；沒有可跨 shell 保存 exact UTF-8/LF JSON 的 `--output`。

## 3. 可用測試 seam 與 baseline probes

| Probe | Baseline 結果 |
|---|---|
| `test_behavior.py --list-scenarios` | exit 0；19 scenarios；ID 001–018 與 020，無 019；run=0、failed=0、skipped=0 |
| `test_behavior.py --group performance` | 在解除 workspace sandbox 對專用 worktree 的寫入限制後，BDD-018／BDD-020 2/2 通過、0 skip；初次 PermissionError 是 tool sandbox，不是產品 failure |
| focused local-manual repository contract | `test_validation_and_release_are_local_manual_workflows` 1/1 通過 |
| Project Knowledge governance validator | exit 1；11 findings：缺不存在的 workflow、四個未核准 docs ignore patterns、缺 `.knowledge-test-tmp/`，以及五個 workflow fragment |
| Wiki lint | exit 0；0 critical、0 warning、2 info；兩項 semantic review 保持人工檢查 |
| root unittest discovery | 175 tests；3 failures、8 skips；所有 failure 都由同一已登錄 relative-link BUG 造成 |

現有 `run_benchmark`、`compare_reports`、`governance_errors`、custom behavior runner 與 unittest fixtures 都可載入；不需要 BOOT seam、新 test framework、網路或 production dependency。

### 已登錄 relative-link baseline

Root suite 的精確 failure surface 是：

1. `test_capability_removal.CapabilityRemovalBehaviorTests.test_active_docs_and_framework_knowledge_match_removed_surface` 的兩個 subtests，分別指向 `docs/knowledge/topics/work-20260904-remove-guide-delegation-6e10da4e-implementation.md` 與 `docs/knowledge/topics/work-20260905-knowledge-benchmark-flake-40135f48-requirements.md`。
2. `test_repository_format.RepositoryFormatTests.test_local_markdown_links_resolve` 聚合回報同兩個 targets。

Plan promotion 會再由同一 renderer 新增 `docs/knowledge/decisions/work-20260905-knowledge-benchmark-flake-40135f48-planning.md`，因此 implementation full verification 預期只可增加該 target 的同型 failure。任何不同 test method、不同 diagnostic 類型或非 `docs/knowledge/index.md` 產生的 target 都不是核准例外。

## 4. Sampling alternatives 與選擇

| 方案 | 優點 | 拒絕或選擇理由 |
|---|---|---|
| 維持單樣本並重跑 | 零程式變更 | 拒絕：讓執行者挑選成功 run，無法保存第一次 failure 的分類，也違反非目標 |
| 三樣本、2/3 超限即 performance failure | 成本有限，median 可直接分類 | 拒絕：兩快一慢與兩慢一快都是 mixed evidence；assessment 尚未確認底層 outlier 來源，把 2/3 直接宣稱 sustained 會提高診斷確定性 |
| 五樣本 median／trimmed statistic | 對 outlier 更平滑 | 拒絕：使 11 個 operations 的正式觀測增加到 55 次，未提供比三樣本四態分類更必要的本 scope 證據 |
| 三樣本、四態 operation decision，加全域 outlier budget | 最小新增成本；既保留真正 regression sensitivity，也把 mixed／host-wide variance 顯式化 | 選擇：0/3=`within-threshold`、1/3=`isolated-outlier`、2/3=`mixed-inconclusive`、3/3=`sustained-violation` |

整體 timing precedence 固定為：任一 3/3 → `sustained-violation`；否則任一 2/3 → `inconclusive`；否則全體 raw samples 若超過一個 breach → `inconclusive`；否則零 breach 為 `within-threshold`、唯一 breach 為 `isolated-outlier`。因此只有零或全體唯一一個 isolated breach 可形成 top-level pass，兩個分散 outliers 不會被當成成功。

三樣本採固定 operation-major、sample-minor 順序：五個 cold query（每個連續三次）、五個 warm query（每個連續三次）、index Candidate（三次）。每個 raw duration 必須是非 bool、finite、非負數字且數量精確為三；threshold 固定 2.0 秒。Median 保存為診斷統計，但 machine classification 由 breach count 與全域 budget 決定，不以浮點近似或動態 percentile 改變。

## 5. Report v2 migration

- 升級 producer 為 `knowledge-portability-report/v2`，新增 top-level `verdict`：`pass|functional-failure|performance-failure|inconclusive`；`outcome` 仍保持 `passed|failed`，只有 `verdict=pass` 可為 passed。
- 每個 timing operation 保存 deterministic `operation_id`、三個 `samples_seconds`、三個 `result_sha256`、`median_seconds`、`breach_count` 與 operation classification；report 保存 closed timing contract、contract SHA-256、固定 operation order、全域 breach count／timing status／reason code。
- `durations_seconds` 保留 v1 原義：每個 operation 的第一個正式樣本投影，加上未納入門檻的 fixture setup。Comparator 必須驗證此 legacy projection 等於 raw arrays 的第一個值，不可拿它重新決定 v2 verdict。
- 每次重複 query／Candidate 的 normalized result 都計算 hash；三個 result hashes 必須彼此一致，並對應既有 canonical functional payload。任何 drift 是 `functional-failure`，不得由 timing pass 覆蓋。
- Producer metadata 保存 framework `VERSION`、producer Git HEAD、worktree clean flag 與 benchmark script SHA-256。Benchmark 本身可在 dirty implementation worktree執行，但 Windows／Linux portability comparator 只接受 strict-clean 且上述 revision identity 完全相同的 reports。
- Comparator 升為 `knowledge-portability-comparison/v2`，重算 timing contract、所有 operation decisions、top-level verdict、legacy projection、functional sample hashes與 max observed seconds；v1、缺欄位、asserted decision drift、非 clean／不同 revision、重複或缺 OS 均 fail closed。
- Error 升為 `knowledge-portability-error/v2`，保留 exit 4 與 `BENCHMARK_ENVIRONMENT`，另以 bounded category／diagnostic code 區分 dependency、process、timeout、fixture、measurement、cleanup、report-output；不輸出 raw subprocess stderr、absolute path、environment value 或 injected exception text。
- 正常／一般非通過 report 的 CLI exit 維持 0／1；environment error 維持 4。選配 `--output` 使用 UTF-8、LF、create-only file，既有 stdout JSON 保持；既有檔案不覆寫。

Cleanup evidence 固定為 `removed|retained-by-request|failed`。正式 portability 與三次 BUG verification 只接受 `removed`；`keep_fixture` 是明示 local diagnosis，comparator 不接受。Cleanup failure 覆蓋原本可能的 pass／performance 結論，改出 environment error 與 `.knowledge-test-tmp/` recovery instruction。

## 6. Local-manual governance alignment

- `tests/test_contracts.py`、`docs/validation/README.md`、`ChangeLog.md`、`wiki/modules/platform-adapters-and-release.md` 與 parity check 已一致要求 repository 不含 workflow YAML、本機驗證、手動 release。
- Project Knowledge Skill 與 validator 是孤立 drift：Skill 指向不存在的 `.github/workflows/knowledge-portability.yml`；validator同時要求該檔及四個會改變一般 docs tracking 的 ignore patterns。
- 修正方向是讓 validator 枚舉並拒絕 `.github/workflows/*.yml|*.yaml`，要求 producer／comparator／本機命令與 `.knowledge-test-tmp/`，並明確拒絕 `docs/*`、`!docs/work/**`、`!docs/bugs/**`、`!docs/knowledge/**`。不建立 workflow。
- 根 `.gitignore` 本 scope 唯一新增行為是 `.knowledge-test-tmp/`；`dist/` 已存在，足以保存不提交的 local reports。
- 驗證文件提供同一組 Python producer／comparator commands；Windows 與 Linux report 由各自 strict-clean host 產生並人工搬入 bounded comparison directory。單一 Windows result 只標示 local evidence，本 work 不宣稱實際 Linux portability pass。

## 7. 實作與驗證邊界

- 三次真實 50k/5k run 必須在本 delivery branch 的 implementation commit 後、strict-clean 狀態下依序執行，輸出到 ignored `dist/knowledge-benchmark-verification/`；每次都必須 `verdict=pass`、cleanup=`removed`、functional oracle相符。任何 inconclusive、performance、functional 或 environment 結果立即停止，不以替代 run 覆蓋。
- Synthetic Windows／Linux reports只驗證 comparator contract，不能算實際雙平台 performance evidence；實際 Linux report 是 release／portability follow-up。
- Root full suite 必須完整執行。Plan promotion 後唯一可接受的 nonzero baseline 是已登錄 relative-link BUG 對三個精確 Knowledge index targets形成的四個 unittest failures；其餘新增 failure、error 或 skip 都阻擋本 Work。
- Framework Wiki 更新 `[[platform-adapters-and-release]]`，同步 `wiki/index.md` summary 與 source digest，並只在 `wiki/log.md` 追加一筆 update；`ChangeLog.md` 在 Unreleased／Fixed 記錄 durable behavior。
- 完成本 Work 只解除 benchmark／governance prerequisite；不修改 link renderer，也不直接續接或宣稱完成 NotebookLM BA／SA export。

## 8. Source hashes

| Path | SHA-256 |
|---|---|
| `docs/work/work-20260905-knowledge-benchmark-flake-40135f48/requirements-2.md` | `8c6b0a0961687a69cb387088ca45718ca56516a3690fb7117c2e405c4c7641a3` |
| `docs/bugs/bug-knowledge-benchmark-baseline-flake/assessment-2.json` | `ed451ce286cba56fe002418b4c62c7e0ed56ba0445da47d4c33298e8e5b44e15` |
| `docs/bugs/bug-knowledge-benchmark-baseline-flake/assessment-2.md` | `a417a157ba4d57212a20cb0ec4cf5ace3b159d3525049837a6fb6e64849eb9c1` |
| `.agents/skills/codebase-wiki/references/framework-maintenance.md` | `bbe3f935e423e8cb1dc709f1c5545683964e4788719237b8fe0238985931799d` |
| `.agents/skills/project-knowledge/scripts/knowledge_benchmark.py` | `89db943c0841b4d046802c8c61779996aeb7bc43b02cf67bee2dc23d335bbc48` |
| `.agents/skills/project-knowledge/scripts/compare_portability_reports.py` | `ad9f673f63cf613c8a4e8fd135e440914fa6116c26fb44b65182765fd81e8af1` |
| `.agents/skills/project-knowledge/scripts/validate_contracts.py` | `ebbb9f7f8a0fe673f47df9c0fa13f7a974a307e24318e934e4dd1b018dd38533` |
| `tests/test_contracts.py` | `c179812a0d27193836c420131eed597b859713053f04ff7b1f42a81becc79d13` |
| `docs/validation/README.md` | `75a2655ac1f35ff1712503b72d5af21b376b308d68e4d9a0368dca3e0a7ff7a8` |
| `.agents/skills/project-knowledge/SKILL.md` | `eb0423743321c988385a06e8f0fe9421475d364901846fb4498041544b05c60f` |
| `.gitignore` | `fc8adceaa13f918a642e258a035c8986c5a3927bc9af7d19578060904c789cf4` |
