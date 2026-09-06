# 技術規劃：分離大型 Knowledge benchmark 的 BDD 與效能責任

- 狀態與核准證據：見 `handoff.json.approval`
- Candidate revision：`plan-v2-20260906`
- 日期：2026-09-06
- 來源規格：`docs/work/work-20260905-knowledge-benchmark-flake-40135f48/requirements-4.md`
- 範圍：安全承接 generation 1 已驗證產品 bytes，新增 controlled／observed measurement-mode 契約，讓 deterministic owner BDD 與三個真實 performance gates 各自 fail closed。
- Planning baseline：repo `3a6b11d008ffd5ef15f38f901249bf99b363ea4742fe8c587add45cd96949ab9`、delivery base `71e7d0289ff04ebb45eb0f09e7e14052cb9f4cd1`、status SHA-256 `8b48f5404eda0e8d2ae9632b0664c1da4369a6f2756ee25b1aeb26d6641ccd92`
- Primary／handoff：`docs/work/work-20260905-knowledge-benchmark-flake-40135f48/plan-2/plan.md`／`docs/work/work-20260905-knowledge-benchmark-flake-40135f48/plan-2/handoff.json`

## 1. 成果、範圍與限制

本計畫以 generation 2 的 exact-postimage manifest 承接既有三樣本與 local-manual 治理實作，再讓完整 50k/5k BDD 使用 controlled timing、三個 standalone commands 使用 observed wall-clock；report v3 明示 measurement_mode，任何 non-pass 均保留並停止。

範圍內包括 benchmark producer、full-scale `BDD-016`、synthetic report helper、portability comparator、matching unit／behavior tests、Project Knowledge local-manual 說明與 validator、`ChangeLog.md`、framework Wiki／index／append-only log，以及 generation 2 的精確 carry-forward。範圍外仍是一般 query 演算法重寫、host／防毒／scheduler 調校、GitHub workflow YAML、Linux 報告偽造、已知 link renderer BUG 與 NotebookLM export。

| ID | Required／Observed 限制 | SRC-* |
|---|---|---|
| `CON-001` | Required：固定 50,000 files／5,000 pages／39,998 sources、五組 cold＋warm query、index Candidate、三樣本、`2.0s` 與既定 functional SHA 不變。 | `SRC-REQ-001`、`SRC-GEN1-001` |
| `CON-002` | Observed：generation 1 已正確實作 report v2、三樣本 classifier、create-only output 與 local-manual governance；舊 run 因 seq99 回 upstream，不得原地續跑。 | `SRC-GEN1-001`、`SRC-PLAN-V1-001`、`SRC-SEQ99-001` |
| `CON-003` | Required：controlled evidence 只能供 contract BDD；CLI completion 與 portability comparator 只能接受 observed evidence，缺 mode／舊 schema／未知 mode 全部拒絕。 | `SRC-REQ-001`、`SRC-BUG-001` |
| `CON-004` | Required：三個 observed commands 各執行一次、create-only、strict-clean、固定順序；第一個 non-pass 保留後立即停止，不得第四次或替代 run。 | `SRC-REQ-001`、`SRC-SEQ99-001` |
| `CON-005` | Required：generation 2 從 delivery base 建立，只以 manifest 從 commit `1289f106e0dad48908449689e2ed244c21ff913f` 承接 17 個產品 postimages；不 cherry-pick 舊 Work／Knowledge artifacts。 | `SRC-GEN1-001`、`SRC-RESEARCH-001` |
| `CON-006` | Required：repository 維持 local-manual、沒有 workflow YAML、`.knowledge-test-tmp/` 單一 ignore，framework maintenance checks 與一筆新的 Wiki log update。 | `SRC-REQ-001`、`SRC-GOV-001` |
| `CON-007` | Required：既有 `bug-knowledge-index-relative-links` 只能作精確殘留，不可遮蔽任何新 failure；Linux portability 未有實機 report 時保持未完成。 | `SRC-REQ-001`、`SRC-RESEARCH-001` |

## 2. 證據與變更影響

| SRC ID | Kind／location／revision | 事實 | Plan refs | 直接 WP refs |
|---|---|---|---|---|
| `SRC-REQ-001` | spec／`requirements-4.md`／`requirements-v4-20260906` | Required：controlled BDD、observed gates、mode boundary、generation 2、stop-on-first-non-pass。 | `CON-001..007`、`TD-001..005`、`BDD-016/019/020/021`、`TEST-001..004` | `WP-001..003` |
| `SRC-BUG-001` | bug／assessment 3 | Confirmed intermittent；root cause hypothesized／medium；contract-level duplication supported，底層 latency 未確認。 | `TD-002..004`、`BDD-016/019/020`、`TEST-001..003` | `WP-001..003` |
| `SRC-GEN1-001` | supporting／`generation-1-baseline.json` | 17 個 generation 1 產品檔、commit／tree／逐檔 SHA-256 的 exact carry-forward 邊界。 | `CON-002/005`、`TD-001`、`MOD-001..004` | `WP-001..003` |
| `SRC-PLAN-V1-001` | supporting／Git object `1289f106e0dad48908449689e2ed244c21ff913f` | 前一 Ready Plan 的三樣本、四態 classifier、local-manual 與完整 verification 設計已實作並有舊 Ledger。 | `TD-001`、`BDD-FWK-001`、`WP-001..003` | `WP-001..003` |
| `SRC-SEQ99-001` | supporting／implementation seq99／`23924a268c6b1a625269d08e404458ef97cf243489cd7d00e5bc7b4fe6a247c9` | 三個 standalone observed reports 先通過；後續 `BDD-016` 在同一 snapshot 以另一 timing window 得到 mixed／inconclusive。 | `CON-002/004`、`TD-002..004`、`BDD-016/019` | `WP-001..003` |
| `SRC-GOV-001` | governance／framework-maintenance／`71e7d0289ff04ebb45eb0f09e7e14052cb9f4cd1` | Framework 行為變更需 tests、parity、frontmatter、stale、log、stats、lint、index、ChangeLog 與 Wiki 同步。 | `CON-006`、`TD-005`、`BDD-021`、`TEST-004` | `WP-003` |
| `SRC-RESEARCH-001` | supporting／`research.md`／`research-v2-20260906` | current symbols、absence probes、generation rule、替代方案與驗證順序。 | 全部 `TD/MOD/SEAM/BDD/TEST/CMD/WP` | `WP-001..003` |

### Current → target

| 影響 ID | 能力／Module | New／Modified／Preserved | 來源要求 |
|---|---|---|---|
| `IMP-001` | generation baseline | New：generation 2 建立後先從 Git object 逐檔取回 manifest postimage並重算 SHA；舊 run／seq99只讀保留。 | `TR-004`、`TP-003` |
| `IMP-002` | `knowledge_benchmark.run_benchmark` | Modified：增加僅供 in-process contract tests 的 optional controlled sample seam；省略時仍以 `time.perf_counter` observed。 | `FR-001..005`、`FR-008`、`NFR-001/002/004/006` |
| `IMP-003` | portability report | Modified：升級為 `knowledge-portability-report/v3`，新增 closed `measurement_mode=observed|controlled`；timing contract v1、raw samples、digests與 duration projection保留。 | `FR-002..004`、`FR-008`、`TR-001` |
| `IMP-004` | `BDD-016` | Modified：移除 persisted observed-report捷徑，完整建立 50k/5k fixture並執行全部真實功能 calls，但 operation durations由固定 controlled samples決定。 | `FR-001/004/008`、`NFR-002/003/006`、`AC-007` |
| `IMP-005` | comparator／synthetic consumers | Modified：只有 report v3 observed 可形成 portability pass；controlled、v2、missing或unknown mode fail closed。 | `FR-004/006/008`、`TR-001` |
| `IMP-006` | standalone completion gate | Preserved＋strengthened：三個固定 CLI commands 保持 observed default、create-only、2.0s、三樣本與 strict-clean identity。 | `FR-009`、`AC-010/011` |
| `IMP-007` | governance／docs／Wiki | Modified：說明 mode 分責與禁止 controlled portability；保留 no-workflow policy並追加一筆新 Wiki update。 | `BR-002`、`CR-001` |

## 3. 設計與決策

| Context | Observed／Required | Proposed | SRC／TD |
|---|---|---|---|
| Runtime／依賴 | Python stdlib、Git、ripgrep；離線且無新 dependency。 | 沿用現況；controlled seam只接受既有 Python mapping/list。 | `SRC-GEN1-001`／`TD-002` |
| 資料／相容性 | report v2沒有 mode，silent default會讓舊／controlled evidence冒充 observed。 | breaking schema migration至 v3並要求 closed mode欄位；v2明示 incompatible。 | `SRC-REQ-001`／`TD-003` |
| Delivery | later generation只 materialize approved upstream，不複製產品 diff。 | 以 exact manifest重播 17 個 postimages；新行為才建立新 red／green。 | `SRC-RESEARCH-001`／`TD-001` |
| 營運／效能 | 真實效能需要 host wall-clock；owner BDD需要 deterministic。 | BDD與completion兩條 evidence lane並存，互不替代。 | `SRC-SEQ99-001`／`TD-004` |

### `TD-001` — 以逐檔 manifest 承接 generation 1，不 cherry-pick 整個 commit

- 需求／證據：`CON-002`、`CON-005`、`TR-004`、`SRC-GEN1-001`。
- 選定方案與理由：generation 2 建立後，先驗證 `1289f106e0dad48908449689e2ed244c21ff913f` 的 parent／tree；對 manifest 每個 path 使用 `git show <commit>:<path>` 取得 raw bytes並核對 SHA-256，再只寫入這 17 個產品檔，寫後重算全部 hash。這可精確保留已驗證 classifier／governance，又不匯入舊 Requirements、assessment、plan、promotion或其他 `docs/knowledge/**` bytes。
- 真實替代方案／拒絕原因：整體 cherry-pick會混入過期 upstream／Knowledge artifacts並與新 plan materialization衝突；從零重寫會丟失已完成行為與舊 red／green lineage；讓 generation 2 直接以 implementation commit當 base違反 delivery approved-base契約。
- Interface、資料、相容性、測試與營運影響：manifest是只讀 supporting artifact；任一 Git object／path／hash不符即在產品 edit 前 Blocked。舊 run保持 `Awaiting upstream reapproval`，carry-forward只能標示 `Satisfied by existing implementation`，不可改寫舊 Ledger。

### `TD-002` — 在最高既有 seam 注入 controlled operation samples

- 需求／證據：`FR-001..005`、`FR-008`、`NFR-002/006`、`SRC-SEQ99-001`。
- 選定方案與理由：`run_benchmark(..., controlled_operation_samples=None)` 為唯一新增 caller-facing參數。`None`使用現行 `_timed`／`time.perf_counter`；非 `None` 必須在 fixture write前驗證 operation順序、11×3 finite non-negative值，再讓每個真實 operation照常執行三次，但以對應 controlled值形成 classification。Fixture setup仍可保留 observed diagnostic，永不進 operation verdict。
- 真實替代方案／拒絕原因：mock全域 clock會同時污染 fixture setup與subprocess時序；只直接組 synthetic report無法證明完整 50k/5k功能路徑；縮小 fixture、提高threshold或retry會違反 Requirements。
- Interface、資料、相容性、測試與營運影響：controlled參數不暴露為 CLI flag；invalid shape在任何 fixture mutation前以 contract error fail closed；functional digest、result hashes、cleanup與三次真實 calls仍照常驗證。

### `TD-003` — Report v3 以 closed measurement mode 防止證據越權

- 需求／證據：`FR-004/006/008`、`TR-001`。
- 選定方案與理由：top-level `measurement_mode` 只允許 `observed` 或 `controlled`，schema升至 `knowledge-portability-report/v3`。CLI production path固定 observed；BDD-016只接受 controlled；portability comparator只接受 observed，且先檢查 schema／mode再重播raw samples。
- 真實替代方案／拒絕原因：在 v2新增 optional欄位會使缺欄舊報告被默認；用host metadata推斷 mode無法證明duration來源；另建第二套classifier會造成consumer drift。
- Interface、資料、相容性、測試與營運影響：`knowledge-timing-contract/v1`與四態precedence不變；v2、missing、unknown、controlled portability reports均輸出明確diagnostic與non-pass。

### `TD-004` — 固定兩條 gate 與 stop-on-first-non-pass 順序

- 需求／證據：`FR-009`、`NFR-006`、`AC-010/011`。
- 選定方案與理由：先完成 controlled owner／full suites；取得另行明示的 implementation commit授權後驗證 strict-clean；再只依序執行 `CMD-BENCHMARK-VERIFY-001..003`各一次。每份report獨立create-only；任一exit非0或mode／oracle／cleanup／identity不符，保存該份並停止後續performance sequence及fresh review。
- 真實替代方案／拒絕原因：把 observed benchmark放回 owner suite重現seq99矛盾；事後挑三份pass是retry-until-green；controlled report不能代表host performance。
- Interface、資料、相容性、測試與營運影響：3/3 observed pass才完成Windows local performance gate；沒有實際Linux report仍不得宣稱portability pass。

### `TD-005` — 沿用 local-manual governance並同步 framework knowledge

- 需求／證據：`BR-002`、`CR-001`、`SRC-GOV-001`。
- 選定方案與理由：Skill、validator與validation docs明示 producer只輸出 observed report，comparator拒絕controlled；保留no-workflow與單一temp ignore。行為更新同步ChangeLog與現有Wiki pages，刷新source digest／index並只追加一筆本revision update log。
- 真實替代方案／拒絕原因：新增GitHub workflow違反repository policy；只改程式不改使用說明會讓controlled evidence被誤用。
- Interface、資料、相容性、測試與營運影響：無網路、帳號或CI dependency；兩個OS由人員各自產生實際observed report再離線比較。

| MOD ID | 責任 | Caller-facing contract | SEAM／Adapter | 隱藏內容 | 要求 |
|---|---|---|---|---|---|
| `MOD-001` | benchmark producer與mode標記 | `run_benchmark`回report v3；CLI永遠observed；controlled mapping只供in-process tests | `SEAM-001`、`SEAM-002` | fixture build、cold subprocess、warm cache、timing capture | `FR-001..005/008` |
| `MOD-002` | behavior oracle與synthetic fixture | BDD-016要求controlled full fixture；BDD-019/020驗證mode與分類 | `SEAM-001`、`SEAM-003` | unittest harness、fixture cleanup | `AC-002..005/007` |
| `MOD-003` | portability comparator | exactly two v3 observed reports；recompute timing／functional／producer identity | `SEAM-003` | diagnostics aggregation | `FR-004/006/008` |
| `MOD-004` | governance與documentation | local-manual/no-workflow、mode guidance、framework maintenance evidence | `SEAM-004` | prose layout與Wiki navigation | `BR-002`、`CR-001` |

主要流程：generation 2 → manifest source/hash red／green → producer BDD/TDD red／green → consumer BDD/TDD red／green → docs/governance red／green → full commands → explicit commit authorization → strict-clean → observed gate 1 → 2 → 3 → fresh review。任何 non-pass 沿原 evidence 停止，不回頭替換。

## 4. 測試策略

### BUG diagnosis與verification target

- Assessment：`docs/bugs/bug-knowledge-benchmark-baseline-flake/assessment-3.json` SHA-256 `072bb3eaab41b2f948090cf6d4cdfd4343d6eeb7d0ddb6243e5af31cf46d0ec9`；Markdown SHA-256 `d83535f5f465f7c667dfa352aeb1c0a900b9ef71cc99c224fdc5c60f2159bff4`。
- Reproduction／root cause：`intermittent`；`hypothesized`／`medium`。最小 causal change只改BDD operation timing evidence ownership與report mode boundary，不宣稱修復底層Windows latency。
- Target：`verified`。Original command為 `CMD-BUG-REPRO-001`；regression BDD為 `BDD-016/019/020`，TEST為 `TEST-001/002/003`。修正前在exact carry-forward後，新的 mode/seam assertion產生正確red；修正後focused command以完整controlled fixture證明原duplicate responsibility已消失，三個observed commands另證明真實performance。
- Partial safeguards：不適用；若完整 BDD不能建立、原contract red被推翻或三個observed gates任一non-pass，結果不是partial success，而是Fixing／Blocked／upstream reapproval。

| BDD-FWK ID | Observed framework、版本與一手來源 | Test-only／安裝邊界 | Feature／binding／fixture | Discovery／report／zero-skip／CI |
|---|---|---|---|---|
| `BDD-FWK-001` | Existing Python 3.14.6 stdlib `unittest` scenario registry；`test_behavior.py --list-scenarios`實測21個。 | 不安裝dependency；repository內既有runner。 | `test_behavior.py`、完整／reduced `.knowledge-test-tmp` fixtures。 | `CMD-BDD-DISCOVERY-001`固定21；focused/full JSON必須run=discovered、failed=0、skipped=0；無hosted CI。 |

| SEAM ID | 可觀察 Interface | 替身策略 | 測試層 |
|---|---|---|---|
| `SEAM-001` | `run_benchmark(..., controlled_operation_samples=None)`與11×3 operation execution | controlled mapping替代operation duration來源，不替代功能operation | BDD＋unit/integration |
| `SEAM-002` | report v3 `measurement_mode`、timing、functional、producer、cleanup | full/reduced真實fixture；invalid mapping | contract＋integration |
| `SEAM-003` | `compare_reports(reports)` | synthetic Windows/Linux v3 reports，mode/schema mutations | BDD＋unit＋integration |
| `SEAM-004` | Skill/docs/validator/Wiki文字與repository policy | exact fragments、no YAML、single ignore、Wiki validators | contract＋governance |

`BOOT-*`：不適用。`run_benchmark`、`compare_reports`、scenario registry、CLI與governance seams均可從 `SRC-GEN1-001` 對應commit載入；generation 2只做exact carry-forward，不建立新entrypoint。

| BDD ID | 要求／scenario | SEAM／fixture | Oracle／正確 red | Feature／binding | Focused CMD | WP／order |
|---|---|---|---|---|---|---|
| `BDD-020` | Reduced 250/20 producer同時證明observed default、controlled injection、11×3 calls、report v3、digests與cleanup。 | `SEAM-001/002`；真實reduced fixture＋fixed mapping | carry-forward report仍為v2且signature缺controlled參數，target schema/mode assertion mismatch | `test_behavior.py` | `CMD-BDD-FOCUSED-001` | `WP-001／1` |
| `BDD-019` | 四態各10次一致；observed雙平台可通過；controlled、v2、missing、unknown mode拒絕。 | `SEAM-002/003`；synthetic reports | carry-forward synthetic reports無mode，comparator也未拒絕controlled | `test_behavior.py` | `CMD-BDD-FOCUSED-001` | `WP-002／1` |
| `BDD-016` | 完整50k/5k真實功能calls＋固定controlled 11×3 samples；schema／producer／digest／cleanup完整且不受host operation clock裁決。 | `SEAM-001/002`；full fixture | 先assert signature含controlled seam；carry-forward缺該參數，形成assertion red而非load/error | `test_behavior.py` | `CMD-BUG-REPRO-001` | `WP-002／2` |
| `BDD-021` | Skill/docs/validator一致描述observed producer、controlled禁用、local-manual/no-workflow與單一ignore。 | `SEAM-004` | carry-forward文字缺mode boundary fragment | `test_behavior.py` | `CMD-BDD-FOCUSED-002` | `WP-003／1` |

| TEST ID | BDD／風險 | 層級／SEAM／fixture | Oracle／red | Focused／related CMD |
|---|---|---|---|---|
| `TEST-001` | `BDD-020/016`；invalid controlled input或host clock洩漏 | unit＋integration／`SEAM-001` | 11×3 closed shape在write前驗證；controlled時每個operation仍執行三次且分類只等於provided values；缺seam先red | `CMD-TDD-FOCUSED-001`、`CMD-RELATED-001` |
| `TEST-002` | `BDD-020`；CLI或legacy report誤標 | unit／`SEAM-002` | CLI無controlled flag且default report為v3 observed；create-only/error contract保留；current v2 assertion red | `CMD-TDD-FOCUSED-001` |
| `TEST-003` | `BDD-019`；controlled evidence通過portability | unit＋integration／`SEAM-003` | only two strict-clean observed v3 pass；controlled/missing/unknown/v2均diagnostic non-pass | `CMD-TDD-FOCUSED-001/002` |
| `TEST-004` | `BDD-021`；治理／文件漂移 | contract／`SEAM-004` | exact mode/manual fragments、no YAML、single temp ignore、Wiki consistency | `CMD-TDD-FOCUSED-003`、`CMD-GOVERNANCE-001..008` |

| CMD ID | Purpose | Observed／Proposed | 摘要；完整 contract在handoff.json |
|---|---|---|---|
| `CMD-BASELINE-VERIFY-001` | related | Proposed | manifest path目前不存在；generation 2 carry-forward前後逐檔驗證source與working-tree SHA。 |
| `CMD-BUG-REPRO-001` | bug-reproduction | Observed command／Proposed oracle | focused full-scale BDD-016；red後green。 |
| `CMD-BDD-DISCOVERY-001` | bdd-discovery | Observed | exactly 21 scenarios。 |
| `CMD-BDD-FOCUSED-001/002` | bdd-focused | Observed commands／Modified assertions | performance與governance groups。 |
| `CMD-BDD-FULL-001` | bdd-full | Observed | 21/21、zero skip；BDD-016 controlled。 |
| `CMD-TDD-FOCUSED-001..003` | tdd-focused | Observed commands／Modified cases | producer/comparator/integration/repository policy。 |
| `CMD-RELATED-001` | related | Observed | Project Knowledge related owner checks。 |
| `CMD-BUILD-FULL-001` | build-full | Observed | 全部Git-eligible Python／schema parse。 |
| `CMD-TEST-FULL-001/002` | test-full | Observed | owner all＋repository tests；只有精確registered link BUG可殘留。 |
| `CMD-GOVERNANCE-001..008` | governance | Observed | project validator＋framework parity/frontmatter/stale/log/stats/lint/index。 |
| `CMD-STRICT-CLEAN-001` | governance | Observed | explicit commit授權後要求zero output。 |
| `CMD-BENCHMARK-VERIFY-001..003` | governance | Observed commands／Modified v3 oracle | 三個create-only observed reports；第一個non-pass即停止。 |

順序：generation 2 materialize → `CMD-BASELINE-VERIFY-001` carry-forward red／green → 每個WP的BDD assertion red → mapped TEST red／minimal green／refactor-with-green → focused／related green。全部WP後fresh跑build、owner full、repository full與governance；再取得獨立commit授權、跑strict-clean與三個observed gates。任何非預期 failure不以retry、skip、threshold或workload變更處理。

## 5. 工作包

### `WP-001` — Exact carry-forward 與 mode-aware producer

- 要求／結果／impact：`FR-001..005/008`、`NFR-001/002/004`、`TR-001/004`、`AC-001..005/011`；`IMP-001..003`。
- Blocked by：None。
- Consumes／produces：consumes `SRC-GEN1-001`與Git object；produces verified carry-forward、`SEAM-001/002`、report v3與producer tests。
- Intent：先只搬移manifest列出的17個postimages並逐檔核對；既有部分記為`Satisfied by existing implementation`。接著更新BDD-020 target取得red，加入prevalidated controlled mapping與closed mode，保留observed default及全部functional calls。
- Slice order：baseline source verification → exact carry-forward → `BDD-020` red → `TEST-001` red/green → `TEST-002` red/green → BDD／related green。
- Commands／完成證據：`CMD-BASELINE-VERIFY-001` source/worktree mismatches=0；`CMD-BDD-FOCUSED-001`、`CMD-TDD-FOCUSED-001`、`CMD-RELATED-001`通過。

### `WP-002` — Controlled full-scale BDD 與 observed-only consumers

- 要求／結果／impact：`FR-003/004/006/008/009`、`NFR-002/003/006`、`TR-001/003/004`、`AC-002..007/010/011`；`IMP-004..006`。
- Blocked by：`WP-001`。
- Consumes／produces：consumes report v3／mode constants；produces BDD-019 mode matrix、BDD-016 controlled full fixture、comparator observed-only contract。
- Intent：先讓BDD-019以mode mutations取得red，完成comparator與synthetic helper；再讓BDD-016以signature assertion取得red，移除persisted observed report捷徑並對完整fixture注入固定11×3 samples。不得改classifier、threshold或functional oracle。
- Slice order：`BDD-019` red → `TEST-003` red/green → `BDD-019` green → `BDD-016` red → `TEST-001/002` related green → `BDD-016` green。
- Commands／完成證據：`CMD-BUG-REPRO-001`、`CMD-BDD-FOCUSED-001`、`CMD-TDD-FOCUSED-001/002`與`CMD-BDD-FULL-001`全部通過；controlled report交comparator必敗。

### `WP-003` — Governance、文件與不可替代的 observed completion gate

- 要求／結果／impact：`BR-002`、`FR-006..009`、`NFR-003..006`、`TR-002..004`、`CR-001`、`AC-006..011`；`IMP-007`。
- Blocked by：`WP-002`。
- Consumes／produces：consumes mode contract與local-manual policy；produces同步Skill/docs/tests/ChangeLog/Wiki與完整verification evidence。
- Intent：BDD-021先固定mode/manual文字取得red，再同步validator與framework knowledge。主代理完成所有full/governance commands；只有取得另行commit授權且strict-clean後，才執行三個observed commands。任一non-pass保留並終止序列。
- Slice order：`BDD-021` red → `TEST-004` red/green → focused governance green → full verification → commit authorization boundary → strict-clean → observed gates 1/2/3 → fresh reviews。
- Commands／完成證據：`CMD-BDD-FOCUSED-002`、`CMD-TDD-FOCUSED-003`、full與`CMD-GOVERNANCE-001..008`通過；`CMD-STRICT-CLEAN-001`零輸出；三份v3 observed report 3/3 pass、各自path/hash保存、無替代run。

## 6. 風險與追溯

### 風險與取捨

| Risk ID | 觸發條件 | 影響 | Mitigation／驗證 | Owner／決策點 |
|---|---|---|---|---|
| `RISK-001` | generation 1 Git object缺失或manifest hash漂移 | 無法可信承接既有功能 | 在任何產品write前停止；保留source mismatch evidence，回Blocked，不手工猜測 | `WP-001` |
| `RISK-002` | controlled mapping繞過功能calls或讀host duration裁決 | BDD假綠或仍flaky | call/result hash計數、clock-independent unit oracle與full BDD；fixture setup不進verdict | `WP-001/002` |
| `RISK-003` | v2／missing mode被默認observed | controlled evidence可冒充performance | schema v3 breaking boundary與negative comparator/CLI tests | `WP-002` |
| `RISK-004` | 任一observed gate出現mixed／failure／environment | 無法完成本地performance結論 | 保存首個non-pass並停止；不跑替代report；回Fixing／Blocked／upstream | `WP-003` |
| `RISK-005` | full tests出現link BUG以外failure | 已知例外吞掉新回歸 | 只允許兩個具名method／三個具名Knowledge target；其餘一律Fail | `WP-003` |
| `RISK-006` | 沒有Linux實機report | 無法宣稱cross-platform pass | 明示Windows local-only；Linux由後續實機manual gate提供 | release owner |
| `RISK-007` | 未取得commit授權便執行strict-clean gates | producer identity為dirty或越權commit | 在full green後停於明示授權邊界；未授權不執行三個completion gates | workspace user／`WP-003` |

Rollback以generation 2的WP product snapshots為界：report v3、producer、BDD與comparator必須同組回退，不能只回退mode consumer。carry-forward manifest與舊run永不修改。任何scope擴張、底層latency假說被推翻、non-pass或新failure都保存evidence後回upstream，不追加第二個猜測patch。

### 追溯矩陣

| SRC／要求 | TD／MOD／SEAM | BDD | TEST | WP | CMD／證據 |
|---|---|---|---|---|---|
| `SRC-GEN1-001`／`TR-004` | `TD-001` | `BDD-020` carry-forward baseline | `TEST-001/002` | `WP-001` | `CMD-BASELINE-VERIFY-001` |
| `FR-001/002/005`、`NFR-001/004` | `TD-002`／`MOD-001`／`SEAM-001/002` | `BDD-020/016` | `TEST-001/002` | `WP-001/002` | focused、build、full |
| `FR-003/004/008`、`NFR-002/006` | `TD-002/003`／`MOD-001..003`／`SEAM-001..003` | `BDD-019/016` | `TEST-001..003` | `WP-001/002` | bug repro、BDD/TDD/full |
| `FR-006`、`NFR-003`、`TR-001` | `TD-003/005`／`MOD-003/004`／`SEAM-003/004` | `BDD-019/021` | `TEST-003/004` | `WP-002/003` | comparator tests、governance |
| `FR-009`、`AC-010/011` | `TD-004`／`MOD-001`／`SEAM-002` | `BDD-016/019` | `TEST-002/003` | `WP-002/003` | strict-clean＋benchmark 1/2/3 |
| `BR-002`、`NFR-005`、`CR-001` | `TD-005`／`MOD-004`／`SEAM-004` | `BDD-021` | `TEST-004` | `WP-003` | governance 1..8 |
| `TR-002/003` | `TD-004/005` | `BDD-016/021` | `TEST-003/004` | `WP-002/003` | full tests＋BUG verification |

## 7. Artifacts 與 readiness

### Artifact manifest

完整role／approval_status／SHA-256以`handoff.json`為權威。

| Path | Role | 建立理由 | 權威內容 |
|---|---|---|---|
| `docs/work/work-20260905-knowledge-benchmark-flake-40135f48/plan-2/plan.md` | primary | 新global-baseline方案入口 | 設計、BDD/TDD、WP、風險與追溯 |
| `docs/work/work-20260905-knowledge-benchmark-flake-40135f48/plan-2/research.md` | supporting | current evidence與替代方案細節會妨礙主線 | probes、source facts、generation與mode研究 |
| `docs/work/work-20260905-knowledge-benchmark-flake-40135f48/plan-2/generation-1-baseline.json` | supporting | generation 2需獨立驗證既有產品bytes | commit/tree、17 paths與raw SHA-256 |
| `docs/work/work-20260905-knowledge-benchmark-flake-40135f48/plan-2/handoff.json` | handoff | versioned machine handoff | `ready-plan/v1`、commands、DAG、source與BUG binding |

### Readiness

- 缺口／未知／衝突：零；底層host latency保持非本scope的inconclusive，不影響責任分離設計。
- BDD framework：existing；BOOT不適用；`BDD-016/019/020/021`、`TEST-001..004`、三個WP與全部commands有雙向追溯。
- Generation 2：只有Plan核准後才由orchestrator建立；本Candidate不建立worktree、不修改產品、不commit。
- `handoff.json` Candidate／Ready normalization、schema、cross-references、artifact/source hashes與global revision impact：必須全部通過才展示。
- Required Knowledge overlay：同一approval將完整plan bundle與planned claim封為一個promotion；controlled不標成observed。
- 核准邊界：本次只核准技術計畫與knowledge diff；後續實作commit仍需另行明示授權，push／merge不在範圍。
