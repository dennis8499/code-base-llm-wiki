# 需求分析：穩定大型 Knowledge benchmark baseline

- Work ID：`work-20260905-knowledge-benchmark-flake-40135f48`
- Revision：`requirements-v4-20260906`
- 文件狀態：Ready（本 postimage 僅在完整 Candidate 核准並套用後成為 current）
- 日期：2026-09-06
- 文件範圍：修正 project-knowledge 50,000-file／5,000-page benchmark 的間歇性 timing verdict，分離 deterministic owner-suite contract 與真實 wall-clock performance gate，並使 portability 治理契約符合本 repository 已核准的本機手動驗證政策。
- 需求來源：workspace user 對本次 upstream revision 方向的確認、`bug-knowledge-benchmark-baseline-flake` assessment revision 3 Candidate、implementation run `d9141c19feac3dfe2b921ce705b1feaaa1f0967173a415cafd5f9910b36409f6` 的 seq99 fail-closed evidence、現行 benchmark／BDD／comparator，以及 repository 的 local-manual validation contract。
- 確認者：`workspace-user`（待本 exact Candidate 核准）
- 預定核准證據：`conversation:bug-benchmark-requirements-v4`
- Revision 關係：本 revision 核准後取代 `docs/work/work-20260905-knowledge-benchmark-flake-40135f48/requirements-3.md` 作為 current Requirements；v3 exact postimages 與 receipt 保留為已核准但未完成 Delivery binding 的歷史，舊失敗 evidence 亦不改寫或重新解讀。

## 1. 執行摘要

### 問題或機會

原始大型 repository benchmark 在固定 50k/5k workload 下，以每個操作的一次 wall-clock 值直接決定整體 pass／fail。相同 source SHA、fixture shape 與功能雜湊曾因單一 `index_candidate` 樣本超過 `2.0s` 而失敗，也曾在相鄰抽樣全部通過；因此無關 delivery 可能被不穩定 baseline 阻擋，且結果無法說明是真實回歸、量測 outlier 或環境錯誤。

核准的 v2 Requirements／Plan 已把每個 operation 改為三個樣本，並正確讓 mixed timing fail closed 為 `inconclusive`。實作後三個獨立、strict-clean 的 50k/5k benchmark 均通過；但 preliminary review 後的 owner full suite 於 `BDD-016` 再執行同一真實 wall-clock workload 時，`cold_query_1` 出現 2/3 超限、`cold_query_2` 出現 1/3 超限，功能 digest 仍正確，因而正確輸出 `MIXED_OPERATION_EVIDENCE`／`inconclusive` 並使 suite 失敗。現行契約同時要求 BDD 的真實 wall-clock 必須 pass、又要求 inconclusive 不得被視為 pass，形成無法靠現有範圍可靠完成的驗收矛盾。

此外，Planning 已確認 portability 治理契約的既有矛盾：repository 的公開文件與 regression 要求本機驗證、手動發版且 `.github/workflows/` 不含 YAML，但 project-knowledge Skill／validator 曾要求不存在的 `.github/workflows/knowledge-portability.yml`，並要求會忽略一般 `docs/` 的規則。該部分仍依 v2 已確認範圍對齊 local-manual policy。

Requirements v3 的 exact postimages 已依使用者核准套用且 Knowledge lint 通過；但 Delivery transition 仍要求每個新 BUG Requirements approval create-only 綁定未曾使用的 assessment revision。v3 明確禁止建立 revision 3，因而不能在不違反其中一項核准契約的情況下推進。v4 只修正這個治理 binding，產品範圍、行為、門檻與驗收均維持 v3。

### 為何現在做

Seq99 是在相同 implementation snapshot 上、依核准的「遇到第一個 non-pass 即停止並保存」規則取得的實際反例；它證明問題不是 classifier 偷放行，而是 owner BDD 與 dedicated performance gate 重複依賴不可控制的 host wall-clock。若不先修訂 Requirements 與 Plan，後續只能違反 fail-closed 語意、採 retry-until-green，或擴張到一般 query 效能重寫，三者都超出既有核准。

### 預期成果

- `BG-001`：大型 Knowledge benchmark 在不降低 workload、功能正確性、樣本數或效能門檻下，以 deterministic contract gate 與獨立真實 performance gate 提供可重複、可解釋且可稽核的 completion verdict。
- `BG-002`：Project Knowledge 的 portability 說明、validator 與實際 repository 政策一致，以本機手動方式取得兩平台真實報告，不引入被產品契約禁止的 GitHub workflow。

Requirements v4 將完整 50k/5k 的功能／契約 BDD 與三個獨立真實 wall-clock 效能閘門分責，兩者都維持三樣本、2.0 秒與 fail-closed 語意，並以 create-only assessment revision 3 滿足同一 BUG approval binding。

## 2. 利害關係人與角色

| 角色 ID | 角色 | 需求／責任 | 決策或權限邊界 |
|---|---|---|---|
| `ACT-001` | Framework maintainer | 維護 benchmark、BDD、report、comparator、validator 與公開驗證說明 | 可修改 framework、tests、docs、`.gitignore` 與 Wiki；不得提高門檻、縮小 fixture、新增 GitHub workflow YAML，或把 controlled evidence 冒充實際效能 |
| `ACT-002` | Delivery executor | 以 owner suite 與獨立 performance commands 判斷能否開始或完成實作 | 可依 machine-readable verdict 行動；不得把未分類的重跑成功覆蓋先前 non-pass |
| `ACT-003` | Portability verifier | 在 Windows／Linux 各自產生真實報告並離線比較 | 只有兩份報告都符合相同版本、workload、功能 digest、量測模式與判定規則時可核准 portability |
| `ACT-004` | Repository maintainer | 維持 local-manual validation／release policy | 不接受 `.github/workflows/` 下的 `.yml`／`.yaml`；平台執行與報告搬移由人員或 repository 外部系統負責 |

## 3. 範圍與優先順序

### 範圍內

- 50,000 tracked files／5,000 Knowledge pages benchmark 的 timing 取樣、分類與 verdict 語意。
- `BDD-016` 在完整 50k/5k fixture 上的 deterministic 功能、schema、producer、cleanup、三樣本與分類契約驗證責任。
- 三個獨立、strict-clean、真實 wall-clock 50k/5k benchmark commands 的 completion-gate 責任。
- Benchmark CLI、portability report／comparator 與 matching unit／behavior regression coverage。
- 可機器區分的正常通過、持續效能違規、孤立 outlier、不確定結果、功能違規與 benchmark 環境故障。
- Raw samples、量測模式、決策依據、fixture shape、功能 digest 與 cleanup evidence 的可觀察輸出。
- Project Knowledge Skill、governance validator 與本機驗證文件的 portability 說明對齊。
- 根 `.gitignore` 只新增 benchmark temporary root `.knowledge-test-tmp/`，使中斷後的 bounded fixture 不污染 Git inventory。
- Framework maintenance 所需的公開文件、`ChangeLog.md`、Wiki/index 與 append-only log 同步。

### 範圍外

- 一般 `knowledge_query.py` 演算法、索引、cache、資料模型或效能重寫；若實測證明產品效能持續違規，另行診斷與規劃。
- 新增任何 `.github/workflows/*.yml` 或 `.yaml`、CI service、scheduled job 或自動 release。
- 把 `docs/*`、`!docs/work/**`、`!docs/bugs/**`、`!docs/knowledge/**` 加入 framework repository 的 `.gitignore`。
- `test_security_fault_matrix_rolls_back_and_requires_recovery` 曾遇到的 Windows Git `Access denied`；隔離抽樣沒有共享根因證據。
- `bug-knowledge-index-relative-links` 的 renderer／href 修復，以及 NotebookLM BA／SA export 功能。
- 作業系統、即時防毒、filesystem filter、CPU 排程器或 hosted runner 的管理與調校。

### 非目標

- 不提高 `2.0s` 門檻、不減少每個 operation 的三個樣本、不減少 50k/5k fixture、不移除 cold／warm query 或功能 digest oracle。
- 不採用 retry-until-green、任意 sleep、忽略 failed／inconclusive sample、替換失敗報告或 full-suite blanket retry 作為成功條件。
- 不把 controlled timing evidence 宣稱為主機效能或 Windows／Linux portability evidence。
- 不把 seq99 的 `inconclusive` 重新標示為 pass，也不刪除、覆寫或省略其 evidence。
- 不新增外部 runtime dependency、網路依賴或雲端帳號要求。
- 不藉由分離 gate 移除真實的 benchmark、functional、schema、cleanup、2.0 秒或 portability checks。

### 優先順序

Must：真實回歸敏感度、固定規模、每 operation 三樣本、`2.0s` 門檻、fail-closed 分類、controlled／observed evidence 不混用、local-manual policy 與 non-pass 保留均不可犧牲。Should：避免 owner suite 重複支付真實 performance gate 的 host-noise 風險，並維持所有單一命令在既有 timeout 內。

## 4. 使用者與業務旅程

### `J-001` — 執行可重複的 owner contract baseline

- 主要角色：`ACT-001`、`ACT-002`
- 觸發與前置條件：同一 source revision 的支援環境可使用 Python、Git 與 ripgrep，fixture root 可安全建立與清理。
- 主要流程：owner suite 建立固定 50k/5k fixture；以 controlled timing evidence 驗證每個 operation 三樣本、四態分類、functional digest、cold／warm 等價、report schema、producer identity 與 cleanup；輸出可重複結果。
- 替代、例外與復原：功能、schema、分類、fixture、dependency、process 或 cleanup 不符仍 fail closed；BDD 的 controlled timing 不提供主機效能結論，也不得被 comparator 接受為 portability report。
- 完成結果：相同 source 與受控 evidence 的 owner suite 可重複判定產品契約是否正確，不因無法事前控制的主機延遲隨機切換。
- 相關需求：`BR-001`、`FR-001`、`FR-003`～`FR-005`、`FR-008`、`NFR-002`、`NFR-003`、`NFR-006`
- 驗收：`AC-002`～`AC-005`、`AC-007`、`AC-009`

### `J-002` — 手動取得並比較 Windows／Linux portability evidence

- 主要角色：`ACT-003`、`ACT-004`
- 觸發與前置條件：相同 source SHA 與工具版本可分別在 Windows、Linux 支援主機執行；repository 內不建立 GitHub workflow。
- 主要流程：每個平台依公開命令執行真實 benchmark；保存未改寫且標示 observed wall-clock 模式的 JSON report；將兩份 report 放入 bounded comparison directory；離線執行 comparator。
- 替代、例外與復原：缺少任一平台、controlled report、schema／decision contract 漂移、功能 digest drift、environment／inconclusive report 或 performance failure 均不得產生 portability pass；外部報告傳輸與主機管理不由本 framework 自動化。
- 完成結果：跨平台通過只代表兩份實際平台報告均符合相同功能與效能判定契約；單一平台結果明確保持 local-only evidence。
- 相關需求：`BR-002`、`FR-004`、`FR-006`～`FR-008`、`NFR-001`、`NFR-003`、`NFR-005`、`TR-001`
- 驗收：`AC-004`、`AC-006`、`AC-009`

### `J-003` — 以真實 performance gate 完成 delivery

- 主要角色：`ACT-001`、`ACT-002`
- 觸發與前置條件：候選 implementation 已 commit，worktree strict-clean，owner functional／contract suites 已通過。
- 主要流程：依固定順序各執行一次三個獨立 50k/5k benchmark command；每份 report 均使用 observed wall-clock、完整三樣本與 `2.0s` 規則；逐份保存結果。
- 替代、例外與復原：任一 command 為 performance failure、inconclusive、functional failure 或 environment error 時，立即保存該 non-pass、停止後續 performance sequence，並回 upstream／diagnosis；不得以替代 run 覆蓋。
- 完成結果：只有原定三份真實報告 3/3 pass，且來源、功能、模式與 cleanup 均相符時，performance completion gate 才通過。
- 相關需求：`BR-001`、`FR-001`～`FR-005`、`FR-008`、`FR-009`、`NFR-001`、`NFR-004`、`TR-003`、`TR-004`
- 驗收：`AC-001`、`AC-005`、`AC-010`、`AC-011`

## 5. 證據與 BUG context

### Primary timing BUG

- BUG ID：`bug-knowledge-benchmark-baseline-flake`
- Assessment Markdown：`docs/bugs/bug-knowledge-benchmark-baseline-flake/assessment-3.md`，SHA-256 `d83535f5f465f7c667dfa352aeb1c0a900b9ef71cc99c224fdc5c60f2159bff4`
- Assessment JSON：`docs/bugs/bug-knowledge-benchmark-baseline-flake/assessment-3.json`，SHA-256 `072bb3eaab41b2f948090cf6d4cdfd4343d6eeb7d0ddb6243e5af31cf46d0ec9`
- Verdict／reproduction：`confirmed`／`intermittent`
- Observed：相同 base SHA、50k/5k fixture 與正確功能 digest 下，留存 failure 的 `index_candidate=3.470925499976147s`，而留存 pass 與五個受控樣本通過；受控範圍為 `0.7987834999803454–0.9807830000063404s`。
- Root cause status／confidence：`hypothesized`／`medium`。已支持單一 wall-clock sample 直接控制 verdict 的失真邊界；底層 outlier 來源仍未確認。

### Implementation upstream-reapproval evidence

- Run ID：`d9141c19feac3dfe2b921ce705b1feaaa1f0967173a415cafd5f9910b36409f6`；product snapshot `75a191a25a198f535f3eb5e6678cda4db3279cd2cbdbd5cf2796400031848447`；implementation commit `1289f106e0dad48908449689e2ed244c21ff913f`。
- 三個獨立 strict-clean reports 在相同 snapshot 均為 pass，最大單樣本分別為 `1.1978953999932855s`、`1.6081831000046805s`、`1.45902730000671s`，功能 digest 皆為預期值且 cleanup 完成。
- Seq99 owner full suite 於 BDD-016 的真實 run 取得：`cold_query_1=[1.3286805999814533, 2.0839867999893613, 2.394746900012251]`（2 breaches）、`cold_query_2=[2.055227900040336, 1.2933956000488251, 1.1293651000014506]`（1 breach）、總 breaches 3；functional SHA-256 仍為 `bae0d3eee98a4ba39967ca26e3b60fd1d2f5f1d781b7dca8e00b8d385c615f83`。
- Classifier 依核准規則輸出 `timing.status=inconclusive`、`reason_code=MIXED_OPERATION_EVIDENCE`，owner command exit 1；這是正確 fail-closed 行為，不是 classifier regression。
- Fixture setup 為 `49.119367600011174s`，先前三次 pass 為約 `26.18s`、`31.26s`、`35.11s`；沒有同時量得的 host-load evidence 足以把差異歸因為 filesystem filter、scheduler 或產品 query path，因此底層原因保持 `inconclusive`。
- Upstream evidence：`implementation:runs/d9141c19feac3dfe2b921ce705b1feaaa1f0967173a415cafd5f9910b36409f6/evidence/raw/preliminary-round-1-reverify-timing-inconclusive.json`，SHA-256 `23924a268c6b1a625269d08e404458ef97cf243489cd7d00e5bc7b4fe6a247c9`；seq99 record SHA-256 `e3ae13e09379dd287f502dd8de49df60ae3b1488a49c3c752292324713a661a4`；stderr SHA-256 `dd71453168472f14360dd7737cd2799ea42e3cea902fe239be3d162eaccf52e0`。
- 現行 BDD 在 `.agents/skills/project-knowledge/scripts/test_behavior.py:2547-2609` 直接呼叫真實 `run_benchmark` 並要求 report pass；classifier 與實際量測位於 `.agents/skills/project-knowledge/scripts/knowledge_benchmark.py:84-150,554-740`。Ready Plan 又同時要求 BDD-016 真實 pass 與三份獨立真實報告（`docs/work/work-20260905-knowledge-benchmark-flake-40135f48/plan/plan.md:92,146`）。

### Planning 發現的治理契約矛盾

- `tests/test_contracts.py:473-477` 穩定要求 `.github/workflows/` 沒有 YAML；focused regression 實跑通過。
- `ChangeLog.md:39-40`、`docs/validation/README.md:55` 與 `wiki/modules/platform-adapters-and-release.md:45` 均把本機驗證／手動 release、repository 不含 workflow YAML 定為 current policy。
- V2 baseline 的 Project Knowledge Skill／validator 曾要求不存在的 workflow 與四個未被 repository policy 支持的 `docs` patterns；implementation 已依核准方向對齊，revision 3 不撤銷該範圍。
- Workspace user 已再次明確選擇：保留 `2.0s`、每 operation 三樣本及三個真實 performance gates；讓 BDD-016 使用 controlled timing 驗證完整 50k/5k 功能／契約，且不採縮小 workload、弱化 fail-closed 或 retry-until-green。

Assessment revision 3 與本次需求修訂維持 primary BUG 的 `hypothesized`／`medium` root-cause 狀態，不把 owner-suite contract gap 冒充原始 latency 的底層根因；它只納入 seq99 反例與 create-only approval binding，產品 WHAT 不因治理修正而擴張。

## 6. 領域詞彙

| 詞彙 ID | 詞彙 | 定義 |
|---|---|---|
| `TERM-001` | 固定 workload | 50,000 tracked files、5,000 Knowledge pages、39,998 source files、五個既定 query tokens 與既定 functional digest 的完整 benchmark 輸入 |
| `TERM-002` | 孤立 outlier | 在功能與環境前置有效時，少數 timing 觀測偏離相鄰樣本，且不足以依核准規則證明持續效能違規 |
| `TERM-003` | 持續效能回歸 | 依核准的三樣本規則，operation 的三個真實 wall-clock 觀測全數超過既有 `2.0s` 門檻的產品違規 |
| `TERM-004` | 環境故障 | dependency、process launch、timeout、fixture、permission 或 cleanup 使 benchmark 無法取得有效產品效能結論的非通過狀態 |
| `TERM-005` | 不確定結果 | 已取得部分合法 timing evidence，但既不能依規則判定 pass，也不能證明持續效能回歸的明示非通過狀態 |
| `TERM-006` | 本機手動 portability | Windows／Linux 各由人員在 repository 內使用同一公開命令產生真實 report，再離線交由 comparator 驗證；repository 不負責 CI orchestration |
| `TERM-007` | Controlled contract evidence | 由測試事前指定、固定且可重播的三樣本序列，只證明分類、schema 與 consumer 語意，不代表任何主機實際速度 |
| `TERM-008` | Observed performance evidence | 在支援主機對完整 workload 實際量得的 wall-clock 三樣本與 host／producer metadata，可作 local performance 或兩平台 portability gate evidence |

## 7. 需求

### `BR-001` — Baseline verdict 必須可信

- 需求：大型 repository baseline 必須以固定、事前可知且可重複驗證的規則區分通過、持續效能回歸、孤立 outlier／不確定結果與環境故障，並把 deterministic contract correctness 與實際主機 performance 分別判定。
- 理由與來源：`BG-001`、`J-001`、`J-003`、confirmed intermittent assessment、seq99 upstream evidence。
- 優先順序：Must。
- 驗收：`AC-001`～`AC-005`、`AC-007`、`AC-010`、`AC-011`

### `BR-002` — Portability 治理必須符合 repository policy

- 需求：Project Knowledge 的 Skill、validator、測試與公開驗證說明必須一致採用本機手動 portability，不得要求或新增 repository 已禁止的 GitHub workflow YAML。
- 理由與來源：`BG-002`、`J-002`、Planning governance evidence、workspace user scope decision。
- 優先順序：Must。
- 驗收：`AC-006`、`AC-009`

### `FR-001` — 固定功能與規模 oracle

- 需求：所有 full-scale contract 與 performance 驗證必須維持 `50,000` tracked files、`5,000` pages、`39,998` source files、cold／warm query 等價與既定 `EXPECTED_FUNCTIONAL_SHA256`；任一不符都不得通過。
- 理由與來源：`BR-001`、`.agents/skills/project-knowledge/scripts/knowledge_benchmark.py:35-42,554-740`。
- 優先順序：Must。
- 驗收：`AC-001`、`AC-004`、`AC-006`、`AC-007`、`AC-010`

### `FR-002` — 真實 Timing 判定必須使用可重複觀測

- 需求：每個 timing-sensitive operation 的 observed performance verdict 必須由事前宣告、順序固定的三個有效 wall-clock 觀測值產生；report 必須保存所有 raw durations、門檻、決策統計與判定理由。
- 理由與來源：`BR-001`、`TERM-008`、assessment `H-001`、`.agents/skills/project-knowledge/scripts/knowledge_benchmark.py:38-63,84-150`。
- 優先順序：Must。
- 驗收：`AC-001`、`AC-003`、`AC-004`、`AC-010`

### `FR-003` — 孤立 outlier、混合樣本與持續違規必須有不同結果

- 需求：功能 oracle 正確且 timing 只有全域一個孤立超限觀測時，不得宣告持續產品回歸；任一 operation 3/3 超過 `2.0s` 時必須輸出 performance failure；2/3 超限或全域超過一個分散 breach 必須輸出 machine-distinguishable inconclusive。
- 理由與來源：`BR-001`、`TERM-002`、`TERM-003`、`TERM-005`、seq99 evidence。
- 優先順序：Must。
- 驗收：`AC-002`、`AC-003`、`AC-004`

### `FR-004` — 所有 report consumer 必須使用同一分類語意

- 需求：Benchmark CLI、controlled BDD oracle、portability comparator 與 matching tests 必須對相同三樣本 evidence 產生相同四態分類與 precedence；schema、分類或 required timing evidence 不完整時一律 fail closed。
- 理由與來源：`J-001`、`J-002`、`.agents/skills/project-knowledge/scripts/test_behavior.py:2547-2609`、`.agents/skills/project-knowledge/scripts/compare_portability_reports.py`。
- 優先順序：Must。
- 驗收：`AC-002`～`AC-004`、`AC-006`

### `FR-005` — 環境與 cleanup failure 必須 fail closed

- 需求：dependency、subprocess、permission、timeout、fixture integrity 或 cleanup failure 必須輸出與 performance regression 可區分的 environment error，保留安全診斷且 exit code 非零；不得產生效能通過聲明，fixture 最終必須移除或明示 recovery requirement。
- 理由與來源：`J-001`、`J-003`、`TERM-004`、現行 `BENCHMARK_ENVIRONMENT` 與 safe fixture cleanup boundary。
- 優先順序：Must。
- 驗收：`AC-005`、`AC-011`

### `FR-006` — 兩平台報告以本機手動流程產生與比較

- 需求：公開驗證說明與 Project Knowledge Skill 必須提供同一組離線命令，讓 Windows／Linux 各自產生 observed performance report 並由 comparator 比較；單一 OS 或 controlled report 不得標示為 cross-platform passed，缺任一平台必須 fail closed。
- 理由與來源：`BR-002`、`TERM-006`～`TERM-008`、現行 local-manual policy 與 comparator contract。
- 優先順序：Must。
- 驗收：`AC-006`、`AC-009`

### `FR-007` — Governance validator 與 temporary fixture 規則必須對齊

- 需求：Project Knowledge governance validator 必須驗證 local-manual 命令、report producer、comparator 與「無 GitHub workflow YAML」契約；不得要求不存在的 workflow 或四個未核准 `docs` ignore patterns。根 `.gitignore` 必須新增且僅就本 scope 新增 `.knowledge-test-tmp/`。
- 理由與來源：Planning governance evidence、workspace user scope decision、`NFR-004`。
- 優先順序：Must。
- 驗收：`AC-007`、`AC-009`

### `FR-008` — Report 必須標示並限制量測模式

- 需求：每份 timing report 必須以 machine-readable evidence 明確區分 controlled contract evidence 與 observed performance evidence；BDD、completion gate 與 comparator 必須拒絕不符合各自責任的模式，且不得以 controlled report 滿足真實效能或 portability gate。
- 理由與來源：`TERM-007`、`TERM-008`、seq99 所揭露的 oracle responsibility conflict。
- 優先順序：Must。
- 驗收：`AC-004`、`AC-006`、`AC-007`、`AC-010`

### `FR-009` — Delivery performance gate 必須獨立且不可替代

- 需求：Implementation completion 必須取得預先固定的三個獨立、strict-clean、observed wall-clock 50k/5k reports，且原定三份均為 pass；owner-suite controlled BDD、先前 run 或 non-pass 後的替代 run 均不得取代任何一份。
- 理由與來源：`J-003`、workspace user revision decision、三份既有 pass 與 seq99 non-pass evidence。
- 優先順序：Must。
- 驗收：`AC-010`、`AC-011`

### `NFR-001` — 2.0 秒效能門檻不得弱化

- 需求：Observed performance evidence 中，每個 operation 只有符合核准三樣本分類且 `max_operation_seconds=2.0` 才能通過；不得提高門檻、縮小 workload 或排除原本受測的 cold queries、warm queries、index Candidate。
- 理由與來源：`FR-001`～`FR-003`、`.agents/skills/project-knowledge/scripts/knowledge_benchmark.py:38-63,84-150`。
- 優先順序：Must。
- 驗收：`AC-001`、`AC-003`、`AC-006`、`AC-010`

### `NFR-002` — Controlled 判定重複性

- 需求：固定 source、fixture、functional output 與 controlled timing sequence 下，重複十次的 BDD／consumer machine verdict 必須一致，且不得讀取該次 host wall-clock 來決定預期分類。
- 理由與來源：`BG-001`、`TERM-007`、seq99 contract contradiction。
- 優先順序：Must。
- 驗收：`AC-002`、`AC-003`、`AC-007`

### `NFR-003` — Deterministic 與跨平台 evidence

- 需求：除 observed timing 與 host metadata 外，相同輸入的 functional payload、digests、sample ordering、decision metadata 與 JSON key semantics 必須 deterministic；Windows／Linux 必須使用相同門檻、模式契約與判定規則。
- 理由與來源：`J-002`、現行 portability contract。
- 優先順序：Must。
- 驗收：`AC-004`、`AC-006`、`AC-007`

### `NFR-004` — 執行成本、離線與 bounded write

- 需求：新增量測不得需要網路或外部 dependency；每個完整 benchmark command 必須維持在現行 `900s` timeout 內，report 分離 fixture setup 與受評估 operation timing，所有 temporary writes 限於 `.knowledge-test-tmp/` 並於正常或錯誤路徑安全清理。
- 理由與來源：現行 full-suite timeout、離線 Project Knowledge 架構與可比較性需求。
- 優先順序：Must。
- 驗收：`AC-001`、`AC-005`、`AC-007`、`AC-010`

### `NFR-005` — 不新增 repository CI surface

- 需求：實作後 `.github/workflows/` 必須仍不含 `.yml` 或 `.yaml`，且公開文件不得把本機手動命令描述成自動 CI 或自動 release。
- 理由與來源：`BR-002`、`tests/test_contracts.py:473-477`、`docs/validation/README.md:55`。
- 優先順序：Must。
- 驗收：`AC-009`

### `NFR-006` — Owner suite 的 BDD-016 不得重複依賴不可控制的效能 oracle

- 需求：Owner full suite 中 BDD-016 的 pass／fail 必須由可重播的 contract／functional evidence 決定；真實 host wall-clock 只由 `FR-009` 的 dedicated commands 判定，兩者任一失敗都保持獨立 fail-closed，不互相覆蓋。
- 理由與來源：`BG-001`、seq99 upstream evidence、workspace user revision decision。
- 優先順序：Must。
- 驗收：`AC-007`、`AC-010`、`AC-011`

### `TR-001` — Report 與 automation consumer 相容

- 需求：現行 `knowledge-portability-report/v2` 的 fixture、host、functional、digest、三樣本與 duration evidence 不得遺失或改變既有意義；若量測模式需要新增欄位或 schema version，CLI、BDD、comparator、tests、Skill 與本機驗證文件必須同時遷移，舊報告不得被靜默誤判為符合新契約。
- 理由與來源：`ACT-002`、`ACT-003`、`FR-004`、`FR-006`、`FR-008`。
- 優先順序：Must。
- 驗收：`AC-004`、`AC-006`

### `TR-002` — 與已知連結 BUG 的過渡邊界

- 需求：本 BUG verification 必須完整報告 `bug-knowledge-index-relative-links` 造成的既有 repository-link failure，且只允許該精確已登錄 failure 作為外部殘留；不得修改其 renderer／tests，也不得讓任何新增 failure 被該例外掩蓋。
- 理由與來源：獨立 delivery 決策與 `work-20260905-knowledge-index-links-80dd5c6f` blocked record。
- 優先順序：Must。
- 驗收：`AC-007`

### `TR-003` — Primary BUG 與治理／contract integration scope 保持可辨識

- 需求：BUG verification 必須把 timing symptom／regression evidence、治理契約對齊與 BDD responsibility revision evidence 分別列出；後兩者不得提高 assessment 的 root-cause confidence，也不得宣稱解決 Windows Git launch、host latency 或 link renderer BUG。
- 理由與來源：assessment revision 3、Planning gap decision、seq99 upstream evidence。
- 優先順序：Must。
- 驗收：`AC-007`、`AC-009`～`AC-011`

### `TR-004` — 舊 implementation run 不得原地重開

- 需求：Run `d9141c19feac3dfe2b921ce705b1feaaa1f0967173a415cafd5f9910b36409f6` 必須保留 `Awaiting upstream reapproval` 與 seq99 evidence；Requirements／Plan 重新核准後，global baseline revision 必須由新的 delivery generation 與新的 implementation run 執行，不得改寫舊 Ledger 或假裝舊 run Complete。
- 理由與來源：implementation-execution global-baseline revision contract、delivery stage-routing contract、seq99 evidence。
- 優先順序：Must。
- 驗收：`AC-011`

### `CR-001` — Framework maintenance 同步

- 需求：行為修正必須具備 matching regressions、公開驗證說明、`ChangeLog.md` 更新、framework Wiki/index 同步，以及一筆有效且 append-only 的 `wiki/log.md` update operation。
- 理由與來源：`.agents/skills/codebase-wiki/references/framework-maintenance.md`。
- 優先順序：Must。
- 驗收：`AC-008`

## 8. 驗收情境

### `AC-001` — 真實正常 workload 通過且 evidence 完整

- Given：ACT-002 在支援主機取得固定 50k/5k fixture、正確 functional digest、可用 dependencies，且 observed cold／warm／index 三樣本均在 `2.0s` 內。
- When：執行一個正式 standalone benchmark command。
- Then：exit code 0、verdict pass；report 標示 observed performance mode，含完整 raw samples、decision statistic、threshold、fixture counts、host、producer、cold／warm digests 與 cleanup 結果。
- 驗證需求：FR-001、FR-002、NFR-001、NFR-004

### `AC-002` — 單一 timing outlier 不冒充持續回歸

- Given：ACT-001 準備固定功能結果與一組 controlled timing sequence，只有全域一個觀測超過 `2.0s`，其餘符合門檻。
- When：同一 sequence 經 benchmark decision、BDD oracle、CLI mapping 與 comparator regression 各重複判定十次。
- Then：所有 machine verdict 完全一致，均不宣告 sustained performance regression；report 保留超限 raw sample 與 isolated-outlier 理由。
- 驗證需求：FR-003、FR-004、NFR-002

### `AC-003` — 持續超限與 mixed evidence 必須穩定 fail closed

- Given：ACT-001 準備一組 operation 3/3 超限的 controlled sequence，以及另一組 2/3 或多 operation 分散 breaches 的 controlled sequence。
- When：每組各重複判定十次。
- Then：前者十次均為 performance failure，後者十次均為 inconclusive，exit code／consumer disposition 均非成功；diagnostic 指出 operation、threshold、classification 與 raw samples。
- 驗證需求：FR-003、FR-004、NFR-001、NFR-002

### `AC-004` — BDD、CLI 與 comparator 分類與模式語意一致

- Given：ACT-001 準備 within-threshold、isolated outlier、inconclusive、sustained violation、controlled mode、observed mode 與 mode 缺失的合法／非法 report evidence。
- When：分別交給 benchmark decision／CLI、BDD oracle 與 portability comparator 的 matching regressions。
- Then：所有 consumer 對同一 samples 的四態分類一致；BDD 接受 controlled contract evidence，completion／portability 只接受 observed performance evidence；錯誤模式、schema 或 required evidence 缺失時 fail closed。
- 驗證需求：FR-004、FR-008、TR-001

### `AC-005` — 環境故障不產生產品結論

- Given：ACT-001 注入 dependency unavailable、subprocess launch failure、timeout、fixture drift 或 cleanup failure 之一。
- When：執行 benchmark 或 BDD contract producer。
- Then：輸出 machine-distinguishable environment error 與非零 exit code，不宣告 pass 或 performance regression；敏感資料不出現在 diagnostic，fixture 已安全清理或提供 recovery requirement。
- 驗證需求：FR-005、NFR-004

### `AC-006` — Windows／Linux 手動 portability 契約保持

- Given：ACT-003 取得 Windows 與 Linux 各一份由相同 source SHA、report version、workload、observed mode 與 decision contract 產生的實際 report。
- When：依公開 local-manual 流程執行 comparator。
- Then：只有兩份均通過 functional digest、cold／warm 等價、2.0 秒 decision 與完整 evidence 時才通過；任一平台缺失、controlled mode、performance failure、environment／inconclusive 或 contract drift 都明確失敗；單一平台不產生 cross-platform pass。
- 驗證需求：FR-006、FR-008、NFR-001、NFR-003、TR-001

### `AC-007` — Owner suite 在完整 fixture 上 deterministic

- Given：ACT-001 使用修正後的同一 source revision、完整 50k/5k fixture 與固定 controlled timing sequences。
- When：Focused contract test 對相同 controlled sequences 各重複判定十次，BDD-016 在 owner suite 執行一次完整 fixture，並執行 Project Knowledge governance／owner／behavior suites 與 repository full verification。
- Then：Focused verdict 10/10 一致；BDD-016 驗證相同三樣本、四態 decision、functional digest、schema、producer 與 cleanup contract，且不由該次 host wall-clock 決定預期 verdict；所有本 scope suites 通過，full verification 除精確映射至 `bug-knowledge-index-relative-links` 的既有 failure 外不得有其他 failure。
- 驗證需求：FR-001、FR-004、FR-007、NFR-002、NFR-003、NFR-006、TR-002

### `AC-008` — Framework 文件與 Wiki 同步

- Given：ACT-001 已完成本次 framework 行為變更。
- When：檢查公開驗證文件、ChangeLog、Wiki index、log integrity、frontmatter、staleness、parity 與 lint。
- Then：文件描述 timing decision、controlled／observed 分責、local-manual portability 與限制；`wiki/index.md` 同步；一筆新 update operation 追加至 `wiki/log.md`；所有適用治理檢查通過。
- 驗證需求：CR-001

### `AC-009` — 治理 validator 與 no-workflow policy 一致

- Given：ACT-004 確認 repository 保持沒有 GitHub workflow YAML，根 `.gitignore` 只新增 `.knowledge-test-tmp/`，Project Knowledge production scripts／manual commands 均存在。
- When：執行 focused local-manual policy regression、Project Knowledge `validate_contracts.py --governance` 與 repository contract suite。
- Then：三者均通過；validator 不要求不存在的 workflow 或四個 `docs` ignore patterns；Skill 與 validation docs 指示在兩個 OS 手動產生 observed report 再比較，且不宣稱本機單一 OS 或 controlled report 即為 portability pass。
- 驗證需求：BR-002、FR-006、FR-007、NFR-005

### `AC-010` — 三個獨立真實 performance gates 全數通過

- Given：ACT-002 已確認 owner contract suites 通過、implementation commit 已建立、worktree strict-clean，且三個固定 output paths 均尚不存在。
- When：依核准順序各執行一次三個 standalone 50k/5k benchmark commands。
- Then：原定三份 report 均為 observed mode、functional oracle 相符、cleanup removed、verdict pass 與 exit code 0；每份 hash／path 分別保存，3/3 才使 performance completion gate 通過。
- 驗證需求：FR-001、FR-002、FR-008、FR-009、NFR-001、NFR-004、NFR-006

### `AC-011` — Non-pass 保留並停止，不以重跑覆蓋

- Given：ACT-002 觀察到 owner suite、三個 standalone gates 或後續 full verification 的任一 command 產生 performance failure、inconclusive、functional failure 或 environment error。
- When：execution runner 處理該結果。
- Then：保存原始 stdout／stderr、report／record、source snapshot 與分類，立即停止相依序列並進入適用的 Fixing、Blocked 或 upstream reapproval；不得刪除、覆寫、重標為 pass，或用未預先核准的替代 run 滿足同一 gate。
- 驗證需求：FR-005、FR-009、NFR-006、TR-003、TR-004

## 9. 成功指標

| 指標 ID | 對應成果 | 指標與計算方式 | 基準 | 目標 | 來源 |
|---|---|---|---|---|---|
| `KPI-001` | `BG-001` | 固定 isolated-outlier sequence 十次判定中，錯誤宣告 sustained regression 的次數 | 現行單樣本曾直接失敗 | `0/10` | deterministic focused regression |
| `KPI-002` | `BG-001` | 固定 sustained／mixed sequences 十次判定中，分類或 fail-closed disposition 錯誤次數 | v2 已有四態 classifier | `0/20` | deterministic focused regression |
| `KPI-003` | `BG-001` | 原定三個 standalone observed performance reports 的 pass 數／替代報告數 | implementation snapshot 曾有 `3/3` pass，後續 BDD 另有 1 inconclusive | `3/3` pass、`0` 替代 | BUG verification |
| `KPI-004` | `BG-001` | Fixture count、functional digest、cold／warm digest、三樣本或 2.0s threshold drift 數 | `0` | `0` | BDD／comparator assertions |
| `KPI-005` | `BG-002` | Project Knowledge governance findings 中 workflow／unsupported `.gitignore` contract findings | v2 baseline 有 `11` 個總 findings | `0` | `validate_contracts.py --governance` |
| `KPI-006` | `BG-002` | `.github/workflows/` 下的 `.yml`／`.yaml` 數 | `0` | `0` | repository contract regression |
| `KPI-007` | 兩項成果 | 除已登錄 link BUG 外的 owner／full verification failure 數 | seq99 有 1 個本 scope contract failure | `0` | final verification |
| `KPI-008` | `BG-001` | 相同 controlled evidence 的 focused 判定十次差異數，以及完整 BDD-016 owner run 結果 | 真實 wall-clock BDD 可出現 inconclusive | `0/10` 差異、BDD-016 pass | focused／owner regression |
| `KPI-009` | `BG-001`、`BG-002` | Controlled report 被 completion gate 或 portability comparator 接受的次數 | 尚無明示 mode boundary | `0` | negative contract tests |

## 10. 追溯矩陣

| 業務成果 | 旅程 | 需求 | 驗收情境 | 成功指標 |
|---|---|---|---|---|
| `BG-001` | `J-001` | `BR-001`、`FR-003`、`FR-004`、`NFR-002`、`NFR-006` | `AC-002`～`AC-004`、`AC-007` | `KPI-001`、`KPI-002`、`KPI-008` |
| `BG-001` | `J-001`、`J-003` | `FR-001`、`FR-002`、`FR-005`、`NFR-001`、`NFR-004` | `AC-001`、`AC-005`、`AC-010`、`AC-011` | `KPI-003`、`KPI-004`、`KPI-007` |
| `BG-001`、`BG-002` | `J-001`～`J-003` | `FR-008`、`TR-001` | `AC-004`、`AC-006`、`AC-007`、`AC-010` | `KPI-004`、`KPI-009` |
| `BG-001` | `J-003` | `FR-009`、`TR-003`、`TR-004` | `AC-010`、`AC-011` | `KPI-003`、`KPI-007` |
| `BG-002` | `J-002` | `BR-002`、`FR-006`、`FR-007`、`NFR-003`、`NFR-005` | `AC-006`、`AC-009` | `KPI-005`、`KPI-006`、`KPI-009` |
| `BG-001` | `J-001`、`J-003` | `TR-002` | `AC-007` | `KPI-007` |
| `BG-001`、`BG-002` | `J-001`～`J-003` | `CR-001` | `AC-008` | `KPI-007` |

## 11. 已確認決策、假設與依賴

### 已確認決策

- `D-001`：以獨立 primary BUG delivery 修正 timing baseline，不在 link 或 NotebookLM worktree 中改動；決策者為 workspace user。
- `D-002`：保留 50k/5k workload、functional digest、cold／warm coverage、每 operation 三樣本與 `2.0s` threshold；不以弱化門檻達成 green。
- `D-003`：Windows Git `Access denied`、host 管理與 link renderer BUG 不納入產品變更；前兩者無共享根因 evidence，後者已有獨立 Work ID。
- `D-004`：Inconclusive 或 environment 狀態不得宣稱 pass 或 performance regression；machine consumer 必須辨識其狀態。
- `D-005`：維持 repository local-manual validation／release policy，不建立 GitHub workflow；兩平台 evidence 由各平台手動 observed commands 與 comparator 組成。
- `D-006`：保留 v2 governance alignment；Project Knowledge validator 不要求 workflow 與四個 `docs` ignore patterns，根 `.gitignore` 只新增 `.knowledge-test-tmp/`。
- `D-007`：完整 50k/5k BDD 使用 controlled timing 驗證功能與決策契約；三個獨立 commands 使用 observed wall-clock 驗證真實效能。決策者為 workspace user，依據為 seq99 反例與本輪明確同意。
- `D-008`：Seq99 的 inconclusive 是正確且必須保留的 non-pass evidence；不得重跑至綠或反向修改 classifier 讓它通過。
- `D-009`：本修訂改變 global BDD／command baseline；舊 implementation run 保持 terminal，Requirements 與 Plan 完整重新核准後另開新 generation／run。
- `D-010`：Requirements v3 保留為核准歷史但不繞過 Delivery create-only BUG binding；assessment revision 3 只刷新 current evidence 與 approval path，verdict、severity、disposition及 root-cause certainty 不提高。

### 已確認假設

- `A-001`：現行 50k/5k fixture 與固定 functional digest 仍是核准的規模／功能基準；來源為 benchmark、BDD 與 comparator assertions。
- `A-002`：本 scope 不涉及敏感資料、安全、隱私、法規、身分或外部服務；所有 fixture 都是 synthetic local data。
- `A-003`：實際 Linux performance 結果必須由 Linux 主機產生；Windows 本機只能驗證 deterministic contract 與 Windows observed report，不外推 Linux 數值。
- `A-004`：Controlled timing 只驗證分類邏輯與 consumer contract；其數值不具有 performance 或 portability 證據效力。

### 依賴與外部限制

- `DEP-001`：Generation 1 worktree、commit `1289f106e0dad48908449689e2ed244c21ff913f`、run `d914…09f6` 與全部 evidence 保留不動；本 revision 不授權新的產品 edit、commit、push、merge 或 cleanup。
- `DEP-002`：`work-20260905-knowledge-index-links-80dd5c6f` 保留 blocked evidence；本 work 完成並整合後，才可依 delivery contract 建立其新 generation／baseline。
- `DEP-003`：本機只有 Windows／Python 3.14.6 實跑 evidence；Linux performance／portability pass 必須等待實際 Linux report，不得以 synthetic metadata 或 controlled BDD 冒充。
- `DEP-004`：`wiki/log.md` 既有 entries 不可改寫，只能追加一筆合規 update。
- `DEP-005`：Assessment revision 3 Markdown／JSON、正式 Requirements v4、Knowledge postimages 與 receipt 必須由同一 exact approval create-only materialize／套用，並在同一 Delivery transition 綁定相同 evidence。
- `DEP-006`：Requirements v4 Ready 後必須先產出並再次核准新的完整 Ready Plan；第二道核准才授權 orchestrator 建立 global-baseline generation 2 與新的 implementation run。

### 延後至技術規劃的決策

- `TP-001`：選擇最小 controlled timing seam，使 BDD-016 仍建立完整 50k/5k fixture 並執行真實功能路徑，但預期 timing samples 可固定重播；不得修改 production CLI 的 observed default。
- `TP-002`：定義 report 的 measurement-mode contract、schema migration 與 comparator rejection rules，避免 controlled evidence 洩漏到 completion／portability gate。
- `TP-003`：定義 generation 2 如何安全承接已核准 generation 1 product bytes、形成新的 outside-in red／green，以及禁止改寫舊 run evidence的 binding。
- `TP-004`：定義 owner suites、三個 observed benchmark commands、repository full verification 與 fresh review 的固定順序、create-only outputs 及 stop-on-first-non-pass 規則。
- `TP-005`：定義 BUG verification 如何分開呈現原 timing symptom、governance alignment、BDD responsibility revision 與既有 link failure。

## 12. 邊界、錯誤與復原

- Timing samples 為空、bool、非數值、負值、非 finite、數量不是三、順序漂移或 decision metadata 缺失：contract failure，fail closed，對應 `FR-002`～`FR-004`。
- Functional digest、cold／warm digest、fixture counts 或 tracked shape 漂移：functional／fixture failure，不得由 controlled 或 observed timing pass 覆蓋，對應 `FR-001`。
- Controlled／observed mode 缺失、未知或被送往錯誤 consumer：contract failure；BDD 不可假裝量到主機效能，completion／comparator 不可接受 controlled report，對應 `FR-008`。
- 單一 outlier、持續超限與無法歸類的 mixed distribution：分別輸出 isolated-outlier evidence、performance failure 與 inconclusive，不共用含糊 failure，對應 `FR-003`。
- Process、permission、timeout 或 cleanup failure：environment error；安全 cleanup 或明示 recovery requirement 後才可啟動經重新核准的新 run，對應 `FR-005`。
- 三個 standalone commands 任一 non-pass：保存並停止；不能用第四次、重跑或 BDD controlled pass取代，對應 `FR-009`、`AC-011`。
- 舊 report 缺新 mode／decision evidence：明示 incompatible／legacy，不可由 default 值補成 pass，對應 `TR-001`。
- 只有一個 OS observed report：comparator 明示 missing OS 並失敗；不把 controlled metadata test 宣稱為實際雙平台效能通過，對應 `FR-006`、`DEP-003`。
- 任一 proposed change 產生 GitHub workflow YAML、加入四個 `docs` ignore patterns，或使 local-manual regression 失敗：scope violation，停止並回 upstream reapproval。
- Full verification 出現 link BUG 以外的新 failure：不得以已知例外吞掉；停止、保存 evidence 並依 relation 分流。
- 任一流程試圖恢復舊 implementation run、改寫 seq99 或沿用舊 Ready Plan 直接實作：global-baseline continuity violation，拒絕並要求新 generation，對應 `TR-004`。

## 13. 完整性與開放事項

- 阻塞性開放事項：無；workspace user 已選定 controlled BDD／三個 observed gates 的分責方向。
- 品質門檻：22 個 requirements 與 11 個 acceptance scenarios 均有來源、明確模式邊界、可觀察 pass／fail、正常／outlier／sustained／mixed／environment／manual portability／transition／文件驗收及完整追溯；逐項與整份品質檢查通過。
- Primary assessment：revision 3 Candidate 維持 `confirmed`／`medium` 與 root cause `hypothesized`／`medium`；只納入 seq99 與本次 binding evidence，底層 latency 原因仍為 inconclusive，不虛增 certainty。
- 高風險判定：不適用；本成果是 synthetic offline benchmark 與 repository-local governance，不處理安全、隱私、法規、醫療、金融、兒少或身分資料，也不宣稱 NotebookLM Enterprise 合規。
- Gate binding：`requirements-4.md`、`docs/bugs/bug-knowledge-benchmark-baseline-flake/assessment-3.md`、`docs/bugs/bug-knowledge-benchmark-baseline-flake/assessment-3.json` 與全部 required Knowledge postimages 必須以 `conversation:bug-benchmark-requirements-v4` 同一次核准 create-only 綁定；任一路徑碰撞、hash drift、validation 或 lint 失敗時整組不得推進；展示 Candidate 不等同核准。
