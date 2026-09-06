# 需求分析：穩定大型 Knowledge benchmark baseline

- Work ID：work-20260905-knowledge-benchmark-flake-40135f48
- 文件狀態：Ready
- 日期：2026-09-05
- 文件範圍：修正 project-knowledge 50,000-file／5,000-page 效能 baseline 的間歇性 verdict，使它可靠區分真實效能回歸、孤立計時 outlier 與環境故障。
- 需求來源：workspace user 對獨立 BUG delivery 的授權、`bug-knowledge-benchmark-baseline-flake` assessment、現行 benchmark／BDD／portability comparator 契約與 framework maintenance governance。
- 確認者：workspace-user
- 核准證據：conversation:bug-benchmark-requirements-v1

## 1. 執行摘要

### 問題或機會

現行大型 repository benchmark 在固定 50k/5k workload 下，以每個操作的一次 wall-clock 值直接決定整體 pass／fail。相同 source SHA、fixture shape 與功能雜湊曾因單一 `index_candidate` 樣本超過 `2.0s` 而失敗，也曾在相鄰抽樣全部通過；因此無關 delivery 可能被不穩定 baseline 阻擋，且結果無法說明是真實回歸、量測 outlier 或環境錯誤。

### 為何現在做

此症狀已阻擋 `work-20260905-knowledge-index-links-80dd5c6f` 的 implementation preflight；該工作又是 `work-20260905-notebooklm-ba-sa-export-8dd366d8` 的前置修復。若不先建立可信的效能判定，後續工作只能靠重跑碰運氣，無法形成可審核的 regression evidence。

### 預期成果

- BG-001：大型 Knowledge benchmark 在不降低 workload、功能正確性或效能門檻的前提下，對相同條件產生可重複且可解釋的 verdict，並持續攔截真正的效能回歸。

大型 Knowledge benchmark 必須在保留 50k/5k、功能雜湊與 2.0 秒門檻下，以可重複且能區分孤立 outlier、持續回歸與環境故障的量測契約產生判定。

## 2. 利害關係人與角色

| 角色 ID | 角色 | 需求／責任 | 決策或權限邊界 |
|---|---|---|---|
| ACT-001 | Framework maintainer | 維護 benchmark、BDD、portability report 與回歸證據 | 可修改 framework、tests、docs 與 Wiki；不得以提高門檻或縮小 fixture 隱藏問題 |
| ACT-002 | Delivery executor | 以 owner suite baseline 判斷是否可開始或完成實作 | 可依 machine-readable verdict 行動；不得把未分類的重跑成功冒充原失敗已解決 |
| ACT-003 | Portability verifier | 比較 Windows／Linux 報告與功能、效能契約 | 只能核准符合相同 workload、功能 digest 與量測規則的報告 |

## 3. 範圍與優先順序

### 範圍內

- 50,000 tracked files／5,000 Knowledge pages benchmark 的 timing 取樣與 verdict 語意。
- `BDD-016`、portability report／comparator 與 matching unit／behavior regression coverage。
- 可機器區分的正常通過、持續效能違規、孤立 outlier／不確定結果與 benchmark 環境故障。
- raw sample、決策依據、fixture shape、功能 digest 與 cleanup evidence 的可觀察輸出。
- Framework maintenance 所需的公開文件、`ChangeLog.md`、Wiki/index 與 append-only log 同步。

### 範圍外

- `test_security_fault_matrix_rolls_back_and_requires_recovery` 曾遇到的 Windows Git `Access denied`；隔離抽樣 5/5 通過且沒有共享根因證據，需另行診斷才可開案。
- `bug-knowledge-index-relative-links` 的 renderer／href 修復，以及 NotebookLM BA／SA export 功能。
- 作業系統、即時防毒、filesystem filter、CPU 排程器或 CI runner 的管理與調校。
- 一般 Knowledge query、promotion、recovery 或資料模型的功能改寫。

### 非目標

- 不提高 `2.0s` 門檻、不減少 50k/5k fixture、不移除 cold／warm query 或功能 digest oracle。
- 不採用「一直重跑直到成功」、任意 sleep、忽略 failed sample 或 full-suite blanket retry 作為成功條件。
- 不因本 BUG 宣稱所有 Windows subprocess failure 已修復。
- 不引入外部 runtime dependency 或需要網路的 benchmark。

### 優先順序

Must：真實回歸敏感度、孤立 outlier 可解釋性、既有功能／規模契約、fail-closed 環境分類與 deterministic evidence 均不可犧牲；Should：在不增加不合理執行時間下縮短診斷迴圈。

## 4. 使用者與業務旅程

### J-001 — 執行可信的大型 repository baseline

- 主要角色：ACT-001、ACT-002
- 觸發與前置條件：同一 source SHA 的支援環境可使用 Python、Git 與 ripgrep，fixture root 可安全建立與清理。
- 主要流程：runner 建立或驗證固定 50k/5k fixture；驗證 cold／warm 功能結果；依預先宣告且具多個觀測值的 timing 規則評估操作；輸出 verdict、原始樣本與決策理由；清理 fixture。
- 替代、例外與復原：孤立 delay 不得直接冒充持續產品回歸；樣本無法支持 pass 或 regression 時輸出可區分的不確定分類；dependency、process、timeout 或 cleanup 失敗輸出 environment error，且不得聲稱效能通過。
- 完成結果：executor 能以一次 machine-readable report 判斷 pass、performance regression 或非產品環境／不確定狀態，並追查每個判定所用的 evidence。
- 相關需求：BR-001、FR-001..005、NFR-001..004、TR-001
- 驗收情境：AC-001..007

### J-002 — 比較 Windows／Linux portability evidence

- 主要角色：ACT-003
- 觸發與前置條件：Windows 與 Linux 各提供一份符合目前契約的 benchmark report。
- 主要流程：comparator 驗證 OS、fixture、功能 digest、cold／warm 等價、timing evidence 與 verdict 語意；輸出跨平台結果及 diagnostics。
- 替代、例外與復原：缺少平台、schema／digest drift、持續超限、環境／不確定報告或不完整 timing evidence 均不得產生通過結論。
- 完成結果：跨平台通過只代表兩份報告均符合相同功能與效能判定契約。
- 相關需求：FR-001、FR-003、FR-004、NFR-001、NFR-003、TR-001
- 驗收情境：AC-004、AC-006

## 5. BUG diagnosis context

- BUG ID：`bug-knowledge-benchmark-baseline-flake`
- Assessment Markdown：`docs/bugs/bug-knowledge-benchmark-baseline-flake/assessment-1.md`，SHA-256 `f4ec3052d0aacf8c5ae784d29e365141b9663ad4bb87f72b71d756108490468e`
- Assessment JSON：`docs/bugs/bug-knowledge-benchmark-baseline-flake/assessment-1.json`，SHA-256 `e1777f5193812514a82c6705be205b077761e9b55af66ee9612b584809723571`
- Verdict／reproduction：`confirmed`／`intermittent`
- Observed：相同 base SHA、50k/5k fixture 與正確功能 digest 下，留存 failure 的 `index_candidate=3.470925499976147s`，而留存 pass 與本輪五個樣本通過；本輪範圍為 `0.7987834999803454–0.9807830000063404s`。
- Expected：固定 workload 的 gate 必須以可重複、可解釋規則判定，持續或具代表性的 `2.0s` 違規失敗，孤立 timing anomaly 不讓相同 baseline 隨機切換結果。
- Impact／severity／relation：阻斷所有依賴 project-knowledge full suite 的 delivery；`medium`；`intake`。
- Root cause status／confidence：`hypothesized`／`medium`。已支持單一 wall-clock sample 直接控制 verdict 的失真邊界；底層 outlier 來源仍待 Planning 以單一變因 probe 判定。

## 6. 領域詞彙

| 詞彙 ID | 詞彙 | 定義 |
|---|---|---|
| TERM-001 | 固定 workload | 50,000 tracked files、5,000 Knowledge pages、39,998 source files、五個既定 query tokens 與既定功能 digest 的完整 benchmark 輸入 |
| TERM-002 | 孤立 outlier | 在功能與環境前置仍有效時，少數 timing 觀測偏離其餘相鄰樣本，且不足以依核准規則證明持續效能違規 |
| TERM-003 | 持續效能回歸 | 依核准的多觀測量測規則，代表性 timing 超過既有 `2.0s` 門檻的可重現產品違規 |
| TERM-004 | 環境故障 | dependency、process launch、timeout、fixture、permission 或 cleanup 使 benchmark 無法取得有效產品效能結論的非通過狀態 |
| TERM-005 | 不確定結果 | 已取得部分 timing evidence，但既不能依規則判定 pass，也不能證明持續效能回歸的明示狀態 |

## 7. 需求

### BR-001 — Baseline verdict 必須可信

- 需求：大型 repository baseline 必須以固定、事前可知且可重複驗證的規則區分通過、持續效能回歸、孤立 outlier／不確定結果與環境故障。
- 理由與來源：BG-001、J-001、confirmed intermittent assessment。
- 優先順序：Must；這是解除無關 delivery 隨機阻塞而不放過真實回歸的核心成果。
- 驗收：AC-001、AC-002、AC-003、AC-005

### FR-001 — 固定功能與規模 oracle

- 需求：benchmark 必須維持 `50,000` tracked files、`5,000` pages、`39,998` source files、cold／warm query 等價與既定 `EXPECTED_FUNCTIONAL_SHA256`；任一不符都不得通過。
- 理由與來源：BR-001、`.agents/skills/project-knowledge/scripts/knowledge_benchmark.py:24-36,417-506`。
- 優先順序：Must。
- 驗收：AC-001、AC-004、AC-006

### FR-002 — Timing 判定必須使用可重複觀測

- 需求：每個 timing-sensitive operation 的 verdict 必須由預先宣告、具多個有效觀測值且順序固定的量測契約產生；report 必須保存所有 raw durations、門檻、所用決策統計與判定理由。
- 理由與來源：BR-001、TERM-002、assessment H-001、`.agents/skills/project-knowledge/scripts/knowledge_benchmark.py:431-506`。
- 優先順序：Must。
- 驗收：AC-001、AC-002、AC-003、AC-004

### FR-003 — 孤立 outlier 與持續違規必須有不同結果

- 需求：當功能 oracle 正確且受控 timing 中只有孤立 delay 時，benchmark 不得把它直接宣告為持續產品回歸；當受控 timing 持續超過 `2.0s` 時，benchmark 必須輸出 performance failure。不能可靠歸類的混合樣本必須輸出 machine-distinguishable 的不確定結果。
- 理由與來源：BR-001、TERM-002、TERM-003、TERM-005。
- 優先順序：Must。
- 驗收：AC-002、AC-003、AC-005

### FR-004 — 所有 consumer 必須使用同一 verdict 語意

- 需求：`BDD-016`、benchmark CLI 與 Windows／Linux portability comparator 必須驗證相同的 timing decision contract，不得一處依代表性判定、另一處仍以任一 raw outlier 直接失敗。
- 理由與來源：J-001、J-002、`.agents/skills/project-knowledge/scripts/test_behavior.py:2318-2355`、`.agents/skills/project-knowledge/scripts/compare_portability_reports.py:21-118`。
- 優先順序：Must。
- 驗收：AC-004、AC-006

### FR-005 — 環境與 cleanup failure 必須 fail closed

- 需求：dependency、subprocess、permission、timeout、fixture integrity 或 cleanup failure 必須輸出與 performance regression 可區分的 environment error，保留安全診斷且 exit code 非零；不得產生效能通過聲明，fixture 最終必須移除或明示 recovery requirement。
- 理由與來源：J-001、TERM-004、現行 `BENCHMARK_ENVIRONMENT` 與 safe fixture cleanup boundary。
- 優先順序：Must。
- 驗收：AC-005

### NFR-001 — 2.0 秒效能門檻不得弱化

- 需求：核准量測契約的代表性 operation timing 必須以 `<= 2.0s` 才能通過；不得提高門檻、縮小 workload 或排除原本受測的 cold queries、warm queries、index Candidate。
- 理由與來源：FR-001、FR-002、`.agents/skills/project-knowledge/scripts/knowledge_benchmark.py:24-26,497-506`。
- 優先順序：Must。
- 驗收：AC-001、AC-003、AC-006

### NFR-002 — 判定重複性

- 需求：在固定 source、fixture、功能輸出與受控 timing sequence 下，重複十次的 machine verdict 必須一致；同一支援主機的三次完整 50k/5k 驗證不得在沒有明示環境／不確定分類下交替產生 pass 與 performance failure。
- 理由與來源：BG-001、symptom oracle。
- 優先順序：Must。
- 驗收：AC-002、AC-003、AC-007

### NFR-003 — Deterministic 與跨平台 evidence

- 需求：除真實 timing 與 host metadata 外，相同輸入的功能 payload、digests、sample ordering、decision metadata 與 JSON key semantics 必須 deterministic；Windows／Linux 必須使用相同門檻與判定規則。
- 理由與來源：J-002、現行 portability contract。
- 優先順序：Must。
- 驗收：AC-004、AC-006

### NFR-004 — 執行成本與離線邊界

- 需求：新增量測不得需要網路或外部 dependency；完整 benchmark 必須維持在現行 `900s` command timeout 內，並在 report 中分離 fixture setup 與受評估 operation timing。
- 理由與來源：現行 full-suite timeout、離線 project-knowledge 架構與可比較性需求。
- 優先順序：Must。
- 驗收：AC-001、AC-005、AC-007

### TR-001 — Report 與 automation 相容

- 需求：現行 `knowledge-portability-report/v1` 的 fixture、host、functional、digest 與 duration evidence 不得遺失或改變既有意義；若為新判定增加欄位或版本，CLI、BDD、comparator、tests 與 workflow 必須同時遷移，舊報告不得被靜默誤判為符合新契約。
- 理由與來源：ACT-002、ACT-003、FR-004。
- 優先順序：Must。
- 驗收：AC-004、AC-006

### TR-002 — 與已知連結 BUG 的過渡邊界

- 需求：本 BUG 的 verification 必須完整報告 `bug-knowledge-index-relative-links` 造成的既有 repository-link failure，且只允許該精確已登錄 failure 作為外部殘留；不得修改其 renderer／tests，也不得讓任何新增 failure 被該例外掩蓋。
- 理由與來源：獨立 delivery 決策與 `work-20260905-knowledge-index-links-80dd5c6f` 的 blocked record。
- 優先順序：Must；避免循環依賴與 scope creep。
- 驗收：AC-007

### CR-001 — Framework maintenance 同步

- 需求：行為修正必須具備 matching regression tests、公開驗證說明、`ChangeLog.md` 更新、framework Wiki/index 同步，以及一筆有效且 append-only 的 `wiki/log.md` update operation。
- 理由與來源：`.agents/skills/codebase-wiki/references/framework-maintenance.md`。
- 優先順序：Must。
- 驗收：AC-008

## 8. 驗收情境

### AC-001 — 正常 workload 通過且 evidence 完整

- Given：固定 50k/5k fixture、正確 functional digest、可用 dependencies，且受控的代表性 cold／warm／index timing 均在 `2.0s` 內。
- When：執行正式 benchmark。
- Then：exit code 為 0、verdict 為 pass；report 含完整 raw samples、決策統計、threshold、fixture counts、host、cold／warm digests 與 cleanup 結果。
- 驗證需求：BR-001、FR-001、FR-002、NFR-001、NFR-004

### AC-002 — 單一 timing outlier 不冒充持續回歸

- Given：固定功能結果與一組受控 timing sequence，其中只有一個觀測因注入 delay 超過 `2.0s`，其餘觀測符合門檻且滿足核准的孤立 outlier 規則。
- When：同一 sequence 重複判定十次。
- Then：十次 machine verdict 完全相同，均不宣告持續 performance regression；report 保留超限 raw sample 與 outlier 判定理由。
- 驗證需求：BR-001、FR-002、FR-003、NFR-002

### AC-003 — 持續超限必須穩定失敗

- Given：固定功能結果與一組依核准規則代表持續違規的受控 timing sequence，其代表性 operation timing 超過 `2.0s`。
- When：同一 sequence 重複判定十次。
- Then：十次都輸出 performance failure、exit code 非零，diagnostic 指出 operation、threshold、decision statistic 與 raw samples；不得以任何單次快速樣本轉為 pass。
- 驗證需求：BR-001、FR-002、FR-003、NFR-001、NFR-002

### AC-004 — BDD、CLI 與 comparator 語意一致

- Given：pass、孤立 outlier、不確定與持續違規四組合法 report evidence。
- When：分別交給 benchmark CLI、`BDD-016` 與 portability comparator。
- Then：三個 consumer 對每組 evidence 的分類一致；schema／required timing evidence 不完整時 fail closed。
- 驗證需求：FR-001、FR-002、FR-004、NFR-003、TR-001

### AC-005 — 環境故障不產生產品結論

- Given：注入 dependency unavailable、subprocess launch failure、timeout、fixture drift 或 cleanup failure 之一。
- When：執行 benchmark。
- Then：輸出 machine-distinguishable environment error 與非零 exit code，不宣告 pass 或 performance regression；敏感資料不出現在 diagnostic，fixture 已安全清理或提供明確 recovery requirement。
- 驗證需求：BR-001、FR-003、FR-005、NFR-004

### AC-006 — Windows／Linux portability 契約保持

- Given：Windows 與 Linux 各一份由相同版本、workload 與判定規則產生的 report。
- When：執行 comparator。
- Then：只有兩份均通過功能 digest、cold／warm 等價、2.0 秒判定與完整 evidence 時才通過；任一平台缺失、違規、環境／不確定或契約漂移都明確失敗。
- 驗證需求：FR-001、FR-004、NFR-001、NFR-003、TR-001

### AC-007 — 真實重複驗證與已知 failure 隔離

- Given：修正後的同一 source SHA、strict-clean worktree 與支援 Windows host。
- When：連續三次執行完整 50k/5k benchmark，並執行 project-knowledge owner／behavior suites 與 repository full verification。
- Then：三次 benchmark 不在未分類情況下交替 pass／performance failure，owner／behavior suites 無本 BUG failure；full verification 除精確映射至 `bug-knowledge-index-relative-links` 的既有 failure 外不得有其他 failure，該殘留必須明列且本 work 不修改其產品或測試。
- 驗證需求：NFR-002、NFR-004、TR-002

### AC-008 — Framework 文件與 Wiki 同步

- Given：本次 framework 行為變更完成。
- When：檢查公開驗證文件、ChangeLog、Wiki index、log integrity、frontmatter、staleness、parity 與 lint。
- Then：文件描述新判定契約與限制，`wiki/index.md` 同步，一筆新 update operation 追加至 `wiki/log.md`，所有適用治理檢查通過。
- 驗證需求：CR-001

## 9. 成功指標

| 指標 ID | 對應成果 | 指標與計算方式 | 基準 | 目標 | 量測期間／資料來源 |
|---|---|---|---|---|---|
| KPI-001 | BG-001 | 固定孤立-outlier sequence 的十次判定中，錯誤宣告持續回歸的次數 | 現行單樣本語意可直接失敗 | 0/10 | Focused deterministic regression |
| KPI-002 | BG-001 | 固定持續超限 sequence 的十次判定中，未輸出 performance failure 的次數 | 尚無多觀測判定 coverage | 0/10 | Focused deterministic regression |
| KPI-003 | BG-001 | 同 SHA 三次完整 50k/5k run 中未分類的 verdict 轉換次數 | 留存 evidence 至少一 pass、一 fail | 0 | BUG verification run |
| KPI-004 | BG-001 | Fixture count、functional digest、cold／warm digest 或 `2.0s` threshold drift 數 | 0 | 0 | BDD／comparator／report assertions |
| KPI-005 | BG-001 | 除已登錄 link BUG 外的 owner／full verification failure 數 | baseline 曾被 BDD-016 阻擋 | 0 | Final implementation verification |

## 10. 追溯矩陣

| 業務成果 | 旅程 | 需求 | 驗收情境 | 成功指標 |
|---|---|---|---|---|
| BG-001 | J-001 | BR-001、FR-002、FR-003、NFR-002 | AC-002、AC-003、AC-007 | KPI-001、KPI-002、KPI-003 |
| BG-001 | J-001、J-002 | FR-001、FR-004、NFR-001、NFR-003、TR-001 | AC-001、AC-004、AC-006 | KPI-004 |
| BG-001 | J-001 | FR-005、NFR-004、TR-002 | AC-005、AC-007 | KPI-003、KPI-005 |
| BG-001 | J-001、J-002 | CR-001 | AC-008 | KPI-005 |

## 11. 已確認決策、假設與依賴

### 已確認決策

- D-001：以獨立 primary BUG delivery 修復，不在 link 或 NotebookLM worktree 中修改 baseline；決策者為 workspace user。
- D-002：保留 50k/5k workload、functional digest、cold／warm coverage 與 `2.0s` threshold；解決 verdict reliability，不以弱化門檻達成 green。
- D-003：Windows Git `Access denied` 與 link renderer BUG 均不納入本產品變更；前者缺共享根因 evidence，後者已有獨立 Work ID。
- D-004：未分類 timing 或環境狀態不得宣稱 pass 或 performance regression；machine consumer 必須能辨識其狀態。

### 已確認假設

- A-001：現行 50k/5k fixture 與固定 functional digest 仍是核准的規模／功能基準；來源為現行 benchmark、BDD 與 comparator assertions。
- A-002：本 BUG 不涉及敏感資料、安全、隱私、法規、身分或外部服務；所有 fixture 都是 synthetic local data。

### 依賴與外部限制

- DEP-001：本 work 必須在 generation 1 專用 worktree 與 branch 上進行；main 與兩個被阻擋 worktree 保持不動，直到另行核准整合。
- DEP-002：`work-20260905-knowledge-index-links-80dd5c6f` 保留其既有 blocked evidence；本 work 完成並整合後才可依 delivery contract 建立新 generation／baseline。
- DEP-003：本機只有 Windows／Python 3.14.6 實跑 evidence；Linux 結論只能由現有 deterministic tests 或實際 Linux report 支持，不得由本機推測。
- DEP-004：`wiki/log.md` 既有 entries 不可改寫，只能追加一筆合規 update。

### 延後至技術規劃的決策

- TP-001：以單一變因 probe 在取樣不足、fixture sequence、page traversal 與主機負載假設間決定最小修法。
- TP-002：選擇滿足 AC-002／AC-003 的 sample count、代表性 decision statistic、outlier／inconclusive 邊界與 report versioning；不得違反 NFR-001。
- TP-003：定義 outside-in BDD red、inner TDD seam、三次真實 benchmark、跨平台 proxy 與 exact full-command safeguards。
- TP-004：定義如何在 BUG verification 中隔離且明示既有 link failure，並於整合後安全續接 link work。

## 12. 邊界、錯誤與復原

- Timing samples 為空、非數值、負值、數量不足、順序漂移或 decision metadata 缺失：契約錯誤，fail closed，對應 FR-002、FR-004、AC-004。
- Functional digest、cold／warm digest、fixture counts 或 tracked shape 漂移：功能／fixture failure，不得由 timing pass 覆蓋，對應 FR-001、AC-001、AC-006。
- 單一 outlier、持續超限與無法歸類的混合分布：分別依 TERM-002、TERM-003、TERM-005 輸出，不得共用含糊 failure，對應 FR-003、AC-002、AC-003。
- Process、permission、timeout 或 cleanup 失敗：environment error；完成安全 cleanup 或回報 recovery requirement 後才可重跑，對應 FR-005、AC-005。
- 舊 report 缺少新 decision evidence：依 TR-001 明示 incompatible／legacy，不可由 default 值靜默補成 pass。

## 13. 完整性與開放事項

- 阻塞性開放事項：無。
- 品質門檻：13 個需求覆蓋面、單一需求品質、正常／outlier／持續回歸／不確定／環境／跨平台／過渡／治理驗收與完整追溯均通過；root-cause HOW、sample statistic 與 versioning 明確保留給 Planning，未形成需求缺口。
- 高風險判定：不適用；synthetic offline benchmark 不處理安全、隱私、法規、醫療、金融、兒少或身分資料。
- Gate binding：assessment、Requirements 與 required Knowledge postimages 將以 `conversation:bug-benchmark-requirements-v1` 同一次核准綁定；本 Candidate 展示不等同核准。
