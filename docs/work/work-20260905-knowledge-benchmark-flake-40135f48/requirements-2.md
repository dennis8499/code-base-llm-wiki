# 需求分析：穩定大型 Knowledge benchmark baseline

- Work ID：`work-20260905-knowledge-benchmark-flake-40135f48`
- Revision：`requirements-v2-20260905`
- 文件狀態：Ready（本 postimage 僅在完整 Candidate 核准並套用後成為 current）
- 日期：2026-09-05
- 文件範圍：修正 project-knowledge 50,000-file／5,000-page benchmark 的間歇性 timing verdict，並使其 portability 治理契約符合本 repository 已核准的本機手動驗證政策。
- 需求來源：workspace user 對獨立 BUG delivery 與本次 scope revision 的授權、`bug-knowledge-benchmark-baseline-flake` assessment、現行 benchmark／BDD／comparator，以及 repository 的 local-manual validation contract。
- 確認者：`workspace-user`
- 預定核准證據：`conversation:bug-benchmark-requirements-v2`
- Revision 關係：本 revision 核准後取代 `docs/work/work-20260905-knowledge-benchmark-flake-40135f48/requirements.md` 作為 current Requirements；舊檔保留為已核准歷史，不改寫。

## 1. 執行摘要

### 問題或機會

現行大型 repository benchmark 在固定 50k/5k workload 下，以每個操作的一次 wall-clock 值直接決定整體 pass／fail。相同 source SHA、fixture shape 與功能雜湊曾因單一 `index_candidate` 樣本超過 `2.0s` 而失敗，也曾在相鄰抽樣全部通過；因此無關 delivery 可能被不穩定 baseline 阻擋，且結果無法說明是真實回歸、量測 outlier 或環境錯誤。

Planning 又發現 portability 治理契約本身有可重現矛盾：repository 的公開文件與 regression 明確要求本機驗證、手動發版且 `.github/workflows/` 不含 YAML，但 project-knowledge Skill／validator 卻要求不存在的 `.github/workflows/knowledge-portability.yml`，同時要求根 `.gitignore` 含會忽略一般 `docs/` 的規則。這使 owner governance command 即使沒有 timing failure 仍必然失敗，也讓「如何取得 Windows／Linux evidence」沒有一致的可執行說法。

### 為何現在做

Timing 症狀已阻擋 `work-20260905-knowledge-index-links-80dd5c6f` 的 implementation preflight；該工作又是 `work-20260905-notebooklm-ba-sa-export-8dd366d8` 的前置修復。治理矛盾則會在 timing 修正後繼續阻擋同一 owner suite。若兩個邊界不在本次已授權的 revision 中明確對齊，後續工作仍只能靠重跑或忽略既有 gate，無法形成可審核證據。

### 預期成果

- `BG-001`：大型 Knowledge benchmark 在不降低 workload、功能正確性或效能門檻下，對相同條件產生可重複且可解釋的 verdict，並持續攔截真正的效能回歸。
- `BG-002`：Project Knowledge 的 portability 說明、validator 與實際 repository 政策一致，以本機手動方式取得兩平台報告，不引入被產品契約禁止的 GitHub workflow。

完成後，使用者可由一次 report 區分 pass、performance failure、inconclusive timing 與 environment error；Windows／Linux portability 則由兩個實際平台各自手動產生同版本 report，再以既有 comparator 離線比較。

## 2. 利害關係人與角色

| 角色 ID | 角色 | 需求／責任 | 決策或權限邊界 |
|---|---|---|---|
| `ACT-001` | Framework maintainer | 維護 benchmark、BDD、report、comparator、validator 與公開驗證說明 | 可修改 framework、tests、docs、`.gitignore` 與 Wiki；不得提高門檻、縮小 fixture 或新增 GitHub workflow YAML |
| `ACT-002` | Delivery executor | 以 owner suite baseline 判斷能否開始或完成實作 | 可依 machine-readable verdict 行動；不得把未分類的重跑成功冒充原失敗已解決 |
| `ACT-003` | Portability verifier | 在 Windows／Linux 各自產生報告並離線比較 | 只有兩份報告都符合相同版本、workload、功能 digest 與量測規則時可核准 portability |
| `ACT-004` | Repository maintainer | 維持 local-manual validation／release policy | 不接受 `.github/workflows/` 下的 `.yml`／`.yaml`；平台執行與報告搬移由人員或 repository 外部系統負責 |

## 3. 範圍與優先順序

### 範圍內

- 50,000 tracked files／5,000 Knowledge pages benchmark 的 timing 取樣與 verdict 語意。
- `BDD-016`、benchmark CLI、portability report／comparator 與 matching unit／behavior regression coverage。
- 可機器區分的正常通過、持續效能違規、孤立 outlier、不確定結果與 benchmark 環境故障。
- Raw samples、決策依據、fixture shape、功能 digest 與 cleanup evidence 的可觀察輸出。
- Project Knowledge Skill、governance validator 與本機驗證文件的 portability 說明對齊。
- 根 `.gitignore` 只新增 benchmark temporary root `.knowledge-test-tmp/`，使中斷後的 bounded fixture 不污染 Git inventory。
- Framework maintenance 所需的公開文件、`ChangeLog.md`、Wiki/index 與 append-only log 同步。

### 範圍外

- 新增任何 `.github/workflows/*.yml` 或 `.yaml`、CI service、scheduled job 或自動 release。
- 把 `docs/*`、`!docs/work/**`、`!docs/bugs/**`、`!docs/knowledge/**` 加入 framework repository 的 `.gitignore`；這些規則會改變一般產品文件的 future tracking，且無現行產品政策支持。
- `test_security_fault_matrix_rolls_back_and_requires_recovery` 曾遇到的 Windows Git `Access denied`；隔離抽樣 5/5 通過且沒有共享根因證據，需另行診斷才可開案。
- `bug-knowledge-index-relative-links` 的 renderer／href 修復，以及 NotebookLM BA／SA export 功能。
- 作業系統、即時防毒、filesystem filter、CPU 排程器或 hosted runner 的管理與調校。
- 一般 Knowledge query、promotion、recovery 或資料模型的功能改寫。

### 非目標

- 不提高 `2.0s` 門檻、不減少 50k/5k fixture、不移除 cold／warm query 或功能 digest oracle。
- 不採用「一直重跑直到成功」、任意 sleep、忽略 failed sample 或 full-suite blanket retry 作為成功條件。
- 不把單一 Windows 本機結果宣稱為跨平台證據，也不因本 BUG 宣稱所有 Windows subprocess failure 已修復。
- 不新增外部 runtime dependency、網路依賴或雲端帳號要求。
- 不藉由修正 validator 移除真實的 benchmark、functional、schema、cleanup 或 portability checks。

### 優先順序

Must：真實回歸敏感度、孤立 outlier 可解釋性、既有功能／規模／2.0 秒契約、fail-closed 分類、local-manual policy 與 deterministic evidence 均不可犧牲。Should：在現行 `900s` benchmark timeout 內控制多觀測成本並縮短診斷迴圈。

## 4. 使用者與業務旅程

### `J-001` — 執行可信的大型 repository baseline

- 主要角色：`ACT-001`、`ACT-002`
- 觸發與前置條件：同一 source SHA 的支援環境可使用 Python、Git 與 ripgrep，fixture root 可安全建立與清理。
- 主要流程：runner 建立或驗證固定 50k/5k fixture；驗證 cold／warm 功能結果；依事前宣告且具多個觀測值的 timing 規則評估操作；輸出 verdict、原始樣本與決策理由；清理 fixture。
- 替代、例外與復原：孤立 delay 不得直接冒充持續產品回歸；樣本不能支持 pass 或 regression 時輸出不確定分類；dependency、process、timeout、fixture 或 cleanup failure 輸出 environment error 且不得聲稱效能通過。
- 完成結果：executor 能以一次 machine-readable report 判斷 pass、performance regression、inconclusive 或 environment error，並追查每個判定的 evidence。
- 相關需求：`BR-001`、`FR-001`～`FR-005`、`NFR-001`～`NFR-004`、`TR-001`
- 驗收：`AC-001`～`AC-005`、`AC-007`

### `J-002` — 手動取得並比較 Windows／Linux portability evidence

- 主要角色：`ACT-003`、`ACT-004`
- 觸發與前置條件：相同 source SHA 與工具版本可分別在 Windows、Linux 支援主機執行；repository 內不建立 GitHub workflow。
- 主要流程：每個平台依公開命令執行 owner suite 與 benchmark；保存未改寫的 JSON report；將兩份 report 放入 bounded comparison directory；離線執行 comparator。
- 替代、例外與復原：缺少任一平台、schema／decision contract 漂移、功能 digest drift、environment／inconclusive report 或 performance failure 均不得產生 portability pass；外部報告傳輸與主機管理不由本 framework 自動化。
- 完成結果：跨平台通過只代表兩份實際平台報告均符合相同功能與效能判定契約；單一平台結果明確保持 local-only evidence。
- 相關需求：`BR-002`、`FR-004`、`FR-006`、`FR-007`、`NFR-003`、`NFR-005`、`TR-001`
- 驗收：`AC-004`、`AC-006`、`AC-009`

## 5. 證據與 BUG context

### Primary timing BUG

- BUG ID：`bug-knowledge-benchmark-baseline-flake`
- Assessment Markdown：`docs/bugs/bug-knowledge-benchmark-baseline-flake/assessment-1.md`，SHA-256 `f4ec3052d0aacf8c5ae784d29e365141b9663ad4bb87f72b71d756108490468e`
- Assessment JSON：`docs/bugs/bug-knowledge-benchmark-baseline-flake/assessment-1.json`，SHA-256 `e1777f5193812514a82c6705be205b077761e9b55af66ee9612b584809723571`
- Verdict／reproduction：`confirmed`／`intermittent`
- Observed：相同 base SHA、50k/5k fixture 與正確功能 digest 下，留存 failure 的 `index_candidate=3.470925499976147s`，而留存 pass 與五個受控樣本通過；受控範圍為 `0.7987834999803454–0.9807830000063404s`。
- Root cause status／confidence：`hypothesized`／`medium`。已支持單一 wall-clock sample 直接控制 verdict 的失真邊界；底層 outlier 來源仍未確認。

### Planning 發現的治理契約矛盾

- `tests/test_contracts.py:473-477` 穩定要求 `.github/workflows/` 沒有 YAML；focused regression 實跑 1/1 通過。
- `ChangeLog.md:39-40`、`docs/validation/README.md:55` 與 `wiki/modules/platform-adapters-and-release.md:45` 均把本機驗證／手動 release、repository 不含 workflow YAML 定為 current policy。
- `.agents/skills/project-knowledge/SKILL.md:77` 卻聲稱跨平台 evidence 來自 `.github/workflows/knowledge-portability.yml`。
- `.agents/skills/project-knowledge/scripts/validate_contracts.py:97-104,211-236` 要求該不存在的 workflow，並要求 `.gitignore` 含四個未被 repository policy 支持的 `docs` patterns 與一個合理的 `.knowledge-test-tmp/` pattern。
- `python -X utf8 -B .agents/skills/project-knowledge/scripts/validate_contracts.py --governance` 在 planning baseline 穩定回傳 exit 1 與 11 個 findings；這是 timing 以外、但會阻擋同一 required owner suite 的 integration gap。
- Workspace user 已明確選擇：把治理對齊納入本 revision；維持 local-manual policy、不新增 GitHub workflow，只加入 `.knowledge-test-tmp/` ignore，並移除 validator 對四個 `docs` ignore patterns 的錯誤要求。

此治理對齊不改寫 primary assessment 的 timing root-cause 狀態，也不把 governance drift 冒充 timing 症狀根因；它是完成已核准 portability／full-suite acceptance 的明示 integration scope。

## 6. 領域詞彙

| 詞彙 ID | 詞彙 | 定義 |
|---|---|---|
| `TERM-001` | 固定 workload | 50,000 tracked files、5,000 Knowledge pages、39,998 source files、五個既定 query tokens 與既定 functional digest 的完整 benchmark 輸入 |
| `TERM-002` | 孤立 outlier | 在功能與環境前置有效時，少數 timing 觀測偏離相鄰樣本，且不足以依核准規則證明持續效能違規 |
| `TERM-003` | 持續效能回歸 | 依核准的多觀測規則，代表性 timing 超過既有 `2.0s` 門檻的可重現產品違規 |
| `TERM-004` | 環境故障 | dependency、process launch、timeout、fixture、permission 或 cleanup 使 benchmark 無法取得有效產品效能結論的非通過狀態 |
| `TERM-005` | 不確定結果 | 已取得部分合法 timing evidence，但既不能依規則判定 pass，也不能證明持續效能回歸的明示狀態 |
| `TERM-006` | 本機手動 portability | Windows／Linux 各由人員在 repository 內使用同一公開命令產生 report，再離線交由 comparator 驗證；repository 不負責 CI orchestration |

## 7. 需求

### `BR-001` — Baseline verdict 必須可信

- 需求：大型 repository baseline 必須以固定、事前可知且可重複驗證的規則區分通過、持續效能回歸、孤立 outlier／不確定結果與環境故障。
- 理由與來源：`BG-001`、`J-001`、confirmed intermittent assessment。
- 優先順序：Must。
- 驗收：`AC-001`、`AC-002`、`AC-003`、`AC-005`

### `BR-002` — Portability 治理必須符合 repository policy

- 需求：Project Knowledge 的 Skill、validator、測試與公開驗證說明必須一致採用本機手動 portability，不得要求或新增 repository 已禁止的 GitHub workflow YAML。
- 理由與來源：`BG-002`、`J-002`、Planning governance evidence、workspace user scope decision。
- 優先順序：Must。
- 驗收：`AC-006`、`AC-009`

### `FR-001` — 固定功能與規模 oracle

- 需求：benchmark 必須維持 `50,000` tracked files、`5,000` pages、`39,998` source files、cold／warm query 等價與既定 `EXPECTED_FUNCTIONAL_SHA256`；任一不符都不得通過。
- 理由與來源：`BR-001`、`.agents/skills/project-knowledge/scripts/knowledge_benchmark.py:24-36,417-506`。
- 優先順序：Must。
- 驗收：`AC-001`、`AC-004`、`AC-006`

### `FR-002` — Timing 判定必須使用可重複觀測

- 需求：每個 timing-sensitive operation 的 verdict 必須由事前宣告、具多個有效觀測值且順序固定的量測契約產生；report 必須保存所有 raw durations、門檻、決策統計與判定理由。
- 理由與來源：`BR-001`、`TERM-002`、assessment `H-001`、`.agents/skills/project-knowledge/scripts/knowledge_benchmark.py:431-506`。
- 優先順序：Must。
- 驗收：`AC-001`、`AC-002`、`AC-003`、`AC-004`

### `FR-003` — 孤立 outlier、混合樣本與持續違規必須有不同結果

- 需求：功能 oracle 正確且受控 timing 只有一個孤立超限觀測時，不得宣告持續產品回歸；受控 timing 依核准規則持續超過 `2.0s` 時必須輸出 performance failure；不能可靠歸類的混合樣本必須輸出 machine-distinguishable inconclusive。
- 理由與來源：`BR-001`、`TERM-002`、`TERM-003`、`TERM-005`。
- 優先順序：Must。
- 驗收：`AC-002`、`AC-003`、`AC-005`

### `FR-004` — 所有 report consumer 必須使用同一 verdict 語意

- 需求：`BDD-016`、benchmark CLI、portability comparator 與 matching tests 必須驗證相同 timing decision contract，不得一處依代表性判定、另一處仍以任一 raw outlier 直接失敗。
- 理由與來源：`J-001`、`J-002`、`.agents/skills/project-knowledge/scripts/test_behavior.py:2318-2355`、`.agents/skills/project-knowledge/scripts/compare_portability_reports.py:24-118`。
- 優先順序：Must。
- 驗收：`AC-004`、`AC-006`

### `FR-005` — 環境與 cleanup failure 必須 fail closed

- 需求：dependency、subprocess、permission、timeout、fixture integrity 或 cleanup failure 必須輸出與 performance regression 可區分的 environment error，保留安全診斷且 exit code 非零；不得產生效能通過聲明，fixture 最終必須移除或明示 recovery requirement。
- 理由與來源：`J-001`、`TERM-004`、現行 `BENCHMARK_ENVIRONMENT` 與 safe fixture cleanup boundary。
- 優先順序：Must。
- 驗收：`AC-005`

### `FR-006` — 兩平台報告以本機手動流程產生與比較

- 需求：公開驗證說明與 Project Knowledge Skill 必須提供同一組離線命令，讓 Windows／Linux 各自產生 report 並由 comparator 比較；單一 OS 結果不得標示為 cross-platform passed，缺任一平台必須 fail closed。
- 理由與來源：`BR-002`、`TERM-006`、現行 local-manual policy 與 comparator contract。
- 優先順序：Must。
- 驗收：`AC-006`、`AC-009`

### `FR-007` — Governance validator 與 temporary fixture 規則必須對齊

- 需求：Project Knowledge governance validator 必須驗證 local-manual 命令、report producer、comparator 與「無 GitHub workflow YAML」契約；不得再要求不存在的 workflow 或四個未核准 `docs` ignore patterns。根 `.gitignore` 必須新增且僅就本 scope 新增 `.knowledge-test-tmp/`。
- 理由與來源：Planning governance evidence、workspace user scope decision、`NFR-004`。
- 優先順序：Must。
- 驗收：`AC-007`、`AC-009`

### `NFR-001` — 2.0 秒效能門檻不得弱化

- 需求：核准量測契約的代表性 operation timing 必須以 `<= 2.0s` 才能通過；不得提高門檻、縮小 workload 或排除原本受測的 cold queries、warm queries、index Candidate。
- 理由與來源：`FR-001`、`FR-002`、`.agents/skills/project-knowledge/scripts/knowledge_benchmark.py:24-26,497-506`。
- 優先順序：Must。
- 驗收：`AC-001`、`AC-003`、`AC-006`

### `NFR-002` — 判定重複性

- 需求：固定 source、fixture、功能輸出與受控 timing sequence 下，重複十次的 machine verdict 必須一致；同一支援主機的三次完整 50k/5k 驗證不得在沒有明示 environment／inconclusive 分類下交替產生 pass 與 performance failure。
- 理由與來源：`BG-001`、symptom oracle。
- 優先順序：Must。
- 驗收：`AC-002`、`AC-003`、`AC-007`

### `NFR-003` — Deterministic 與跨平台 evidence

- 需求：除真實 timing 與 host metadata 外，相同輸入的 functional payload、digests、sample ordering、decision metadata 與 JSON key semantics 必須 deterministic；Windows／Linux 必須使用相同門檻與判定規則。
- 理由與來源：`J-002`、現行 portability contract。
- 優先順序：Must。
- 驗收：`AC-004`、`AC-006`

### `NFR-004` — 執行成本、離線與 bounded write

- 需求：新增量測不得需要網路或外部 dependency；完整 benchmark 必須維持在現行 `900s` command timeout 內，report 分離 fixture setup 與受評估 operation timing，所有 temporary writes 限於 `.knowledge-test-tmp/` 並於正常或錯誤路徑安全清理。
- 理由與來源：現行 full-suite timeout、離線 Project Knowledge 架構與可比較性需求。
- 優先順序：Must。
- 驗收：`AC-001`、`AC-005`、`AC-007`

### `NFR-005` — 不新增 repository CI surface

- 需求：實作後 `.github/workflows/` 必須仍不含 `.yml` 或 `.yaml`，且公開文件不得把本機手動命令描述成自動 CI 或自動 release。
- 理由與來源：`BR-002`、`tests/test_contracts.py:473-477`、`docs/validation/README.md:55`。
- 優先順序：Must。
- 驗收：`AC-009`

### `TR-001` — Report 與 automation consumer 相容

- 需求：現行 `knowledge-portability-report/v1` 的 fixture、host、functional、digest 與 duration evidence 不得遺失或改變既有意義；若新判定增加欄位或 schema version，CLI、BDD、comparator、tests、Skill 與本機驗證文件必須同時遷移，舊報告不得被靜默誤判為符合新契約。
- 理由與來源：`ACT-002`、`ACT-003`、`FR-004`、`FR-006`。
- 優先順序：Must。
- 驗收：`AC-004`、`AC-006`

### `TR-002` — 與已知連結 BUG 的過渡邊界

- 需求：本 BUG verification 必須完整報告 `bug-knowledge-index-relative-links` 造成的既有 repository-link failure，且只允許該精確已登錄 failure 作為外部殘留；不得修改其 renderer／tests，也不得讓任何新增 failure 被該例外掩蓋。
- 理由與來源：獨立 delivery 決策與 `work-20260905-knowledge-index-links-80dd5c6f` blocked record。
- 優先順序：Must。
- 驗收：`AC-007`

### `TR-003` — Primary BUG 與治理 integration scope 保持可辨識

- 需求：BUG verification 必須把 timing symptom／regression evidence 與治理契約對齊 evidence 分別列出；治理對齊不得提高 assessment 的 root-cause confidence，也不得宣稱解決 Windows Git launch 或 link renderer BUG。
- 理由與來源：assessment revision 1、Planning gap decision。
- 優先順序：Must。
- 驗收：`AC-007`、`AC-009`

### `CR-001` — Framework maintenance 同步

- 需求：行為修正必須具備 matching regressions、公開驗證說明、`ChangeLog.md` 更新、framework Wiki/index 同步，以及一筆有效且 append-only 的 `wiki/log.md` update operation。
- 理由與來源：`.agents/skills/codebase-wiki/references/framework-maintenance.md`。
- 優先順序：Must。
- 驗收：`AC-008`

## 8. 驗收情境

### `AC-001` — 正常 workload 通過且 evidence 完整

- Given：固定 50k/5k fixture、正確 functional digest、可用 dependencies，且受控的代表性 cold／warm／index timing 均在 `2.0s` 內。
- When：執行正式 benchmark。
- Then：exit code 0、verdict pass；report 含完整 raw samples、decision statistic、threshold、fixture counts、host、cold／warm digests 與 cleanup 結果。

### `AC-002` — 單一 timing outlier 不冒充持續回歸

- Given：固定功能結果與一組受控 timing sequence，只有一個觀測超過 `2.0s`，其餘符合門檻且滿足核准的 isolated-outlier 規則。
- When：同一 sequence 重複判定十次。
- Then：十次 machine verdict 完全相同，均不宣告 sustained performance regression；report 保留超限 raw sample 與 outlier 理由。

### `AC-003` — 持續超限必須穩定失敗

- Given：固定功能結果與一組依核准規則代表 sustained violation 的受控 timing sequence。
- When：同一 sequence 重複判定十次。
- Then：十次均輸出 performance failure、exit code 非零，diagnostic 指出 operation、threshold、decision statistic 與 raw samples；不得因單次快速樣本轉為 pass。

### `AC-004` — BDD、CLI 與 comparator 語意一致

- Given：pass、isolated outlier、inconclusive 與 sustained violation 四組合法 report evidence。
- When：分別交給 benchmark decision／CLI、`BDD-016` 與 portability comparator 的 matching regressions。
- Then：所有 consumer 對每組 evidence 的分類一致；schema 或 required timing evidence 不完整時 fail closed。

### `AC-005` — 環境故障不產生產品結論

- Given：注入 dependency unavailable、subprocess launch failure、timeout、fixture drift 或 cleanup failure 之一。
- When：執行 benchmark。
- Then：輸出 machine-distinguishable environment error 與非零 exit code，不宣告 pass 或 performance regression；敏感資料不出現在 diagnostic，fixture 已安全清理或提供 recovery requirement。

### `AC-006` — Windows／Linux 手動 portability 契約保持

- Given：Windows 與 Linux 各一份由相同 source SHA、report version、workload 與 decision contract 產生的實際 report。
- When：依公開 local-manual 流程執行 comparator。
- Then：只有兩份均通過 functional digest、cold／warm 等價、2.0 秒 decision 與完整 evidence 時才通過；任一平台缺失、performance failure、environment／inconclusive 或 contract drift 都明確失敗；單一平台不產生 cross-platform pass。

### `AC-007` — 真實重複驗證與已知 failure 隔離

- Given：修正後的同一 source SHA、strict-clean worktree 與支援 Windows host。
- When：連續三次執行完整 50k/5k benchmark，並執行 Project Knowledge owner／behavior suites 與 repository full verification。
- Then：三次 benchmark 不在未分類情況下交替 pass／performance failure；Project Knowledge governance／owner／behavior suites 無本 scope failure；full verification 除精確映射至 `bug-knowledge-index-relative-links` 的既有 failure 外不得有其他 failure，該殘留必須明列且本 work 不修改其產品或測試。

### `AC-008` — Framework 文件與 Wiki 同步

- Given：本次 framework 行為變更完成。
- When：檢查公開驗證文件、ChangeLog、Wiki index、log integrity、frontmatter、staleness、parity 與 lint。
- Then：文件描述 timing decision、local-manual portability 與限制；`wiki/index.md` 同步；一筆新 update operation 追加至 `wiki/log.md`；所有適用治理檢查通過。

### `AC-009` — 治理 validator 與 no-workflow policy 一致

- Given：repository 保持沒有 GitHub workflow YAML，根 `.gitignore` 只新增 `.knowledge-test-tmp/`，Project Knowledge production scripts／manual commands 均存在。
- When：執行 focused local-manual policy regression、Project Knowledge `validate_contracts.py --governance` 與 repository contract suite。
- Then：三者均通過；validator 不再要求不存在的 workflow 或四個 `docs` ignore patterns；Skill 與 validation docs 指示在兩個 OS 手動產生 report 再比較，且不宣稱本機單一 OS 即為 portability pass。

## 9. 成功指標

| 指標 ID | 對應成果 | 指標與計算方式 | 基準 | 目標 | 來源 |
|---|---|---|---|---|---|
| `KPI-001` | `BG-001` | 固定 isolated-outlier sequence 十次判定中，錯誤宣告 sustained regression 的次數 | 現行單樣本可直接失敗 | `0/10` | deterministic focused regression |
| `KPI-002` | `BG-001` | 固定 sustained-over-limit sequence 十次判定中，未輸出 performance failure 的次數 | 尚無多觀測 coverage | `0/10` | deterministic focused regression |
| `KPI-003` | `BG-001` | 同 SHA 三次完整 50k/5k run 中未分類 verdict 轉換次數 | 留存 evidence 至少一 pass、一 fail | `0` | BUG verification |
| `KPI-004` | `BG-001` | Fixture count、functional digest、cold／warm digest 或 2.0s threshold drift 數 | `0` | `0` | BDD／comparator assertions |
| `KPI-005` | `BG-002` | Project Knowledge governance findings 中 workflow／unsupported `.gitignore` contract findings | `11` 個總 findings | `0` | `validate_contracts.py --governance` |
| `KPI-006` | `BG-002` | `.github/workflows/` 下的 `.yml`／`.yaml` 數 | `0` | `0` | repository contract regression |
| `KPI-007` | 兩項成果 | 除已登錄 link BUG 外的 owner／full verification failure 數 | baseline 有 timing 與 governance blockers | `0` | final verification |

## 10. 追溯矩陣

| 業務成果 | 旅程 | 需求 | 驗收情境 | 成功指標 |
|---|---|---|---|---|
| `BG-001` | `J-001` | `BR-001`、`FR-002`、`FR-003`、`NFR-002` | `AC-002`、`AC-003`、`AC-007` | `KPI-001`、`KPI-002`、`KPI-003` |
| `BG-001` | `J-001`、`J-002` | `FR-001`、`FR-004`、`NFR-001`、`NFR-003`、`TR-001` | `AC-001`、`AC-004`、`AC-006` | `KPI-004` |
| `BG-001` | `J-001` | `FR-005`、`NFR-004`、`TR-002`、`TR-003` | `AC-005`、`AC-007` | `KPI-003`、`KPI-007` |
| `BG-002` | `J-002` | `BR-002`、`FR-006`、`FR-007`、`NFR-005` | `AC-006`、`AC-009` | `KPI-005`、`KPI-006` |
| `BG-001`、`BG-002` | `J-001`、`J-002` | `CR-001` | `AC-008` | `KPI-007` |

## 11. 已確認決策、假設與依賴

### 已確認決策

- `D-001`：以獨立 primary BUG delivery 修正 timing baseline，不在 link 或 NotebookLM worktree 中改動；決策者為 workspace user。
- `D-002`：保留 50k/5k workload、functional digest、cold／warm coverage 與 `2.0s` threshold；解決 verdict reliability，不以弱化門檻達成 green。
- `D-003`：Windows Git `Access denied` 與 link renderer BUG 不納入產品變更；前者無共享根因 evidence，後者已有獨立 Work ID。
- `D-004`：未分類 timing 或 environment 狀態不得宣稱 pass 或 performance regression；machine consumer 必須辨識其狀態。
- `D-005`：維持 repository local-manual validation／release policy，不建立 GitHub workflow；兩平台 evidence 由各平台手動命令與 comparator 組成。
- `D-006`：治理對齊納入本 revision，但與 primary timing diagnosis 分別追溯；Project Knowledge validator 移除 workflow 與四個 `docs` ignore expectations，根 `.gitignore` 只新增 `.knowledge-test-tmp/`。

### 已確認假設

- `A-001`：現行 50k/5k fixture 與固定 functional digest 仍是核准的規模／功能基準；來源為現行 benchmark、BDD 與 comparator assertions。
- `A-002`：本 scope 不涉及敏感資料、安全、隱私、法規、身分或外部服務；所有 fixture 都是 synthetic local data。
- `A-003`：實際 Linux performance 結果必須由 Linux 主機產生；Windows 本機只能驗證 deterministic contract 與 Windows report，不外推 Linux 數值。

### 依賴與外部限制

- `DEP-001`：本 work 必須在 generation 1 專用 worktree 與 branch 上進行；main 與兩個被阻擋 worktree 保持不動，直到另行核准整合。
- `DEP-002`：`work-20260905-knowledge-index-links-80dd5c6f` 保留 blocked evidence；本 work 完成並整合後，才可依 delivery contract 建立新 generation／baseline。
- `DEP-003`：本機只有 Windows／Python 3.14.6 實跑 evidence；Linux performance／portability pass 必須等待實際 Linux report，本次可驗證 comparator 對 synthetic Windows／Linux metadata 的共同 contract，但不得冒充實際雙平台 pass。
- `DEP-004`：`wiki/log.md` 既有 entries 不可改寫，只能追加一筆合規 update。
- `DEP-005`：正式 Requirements revision、Knowledge postimages 與 receipt 必須由同一 exact Candidate approval 原子套用。

### 延後至技術規劃的決策

- `TP-001`：以 assessment 的 fresh／reuse controlled samples 與必要的單一變因 probe，決定最小 timing 修法；不把未確認的 Windows 外部負載寫成產品根因。
- `TP-002`：選擇滿足 `AC-002`／`AC-003` 的 sample count、decision statistic、outlier／inconclusive boundary 與 report versioning；不得違反 `NFR-001`。
- `TP-003`：定義 outside-in BDD red、inner TDD seam、三次真實 benchmark、手動雙平台 proxy 與 exact full-command safeguards。
- `TP-004`：將 timing decision 與 local-manual governance alignment 切成可獨立審查的 work packages，並定義最小相依關係。
- `TP-005`：定義 BUG verification 如何隔離並明示既有 link failure，以及整合後如何安全續接 link work。

## 12. 邊界、錯誤與復原

- Timing samples 為空、bool、非數值、負值、非 finite、數量不足、順序漂移或 decision metadata 缺失：contract failure，fail closed，對應 `FR-002`、`FR-004`、`AC-004`。
- Functional digest、cold／warm digest、fixture counts 或 tracked shape 漂移：functional／fixture failure，不得由 timing pass 覆蓋，對應 `FR-001`、`AC-001`、`AC-006`。
- 單一 outlier、持續超限與無法歸類的混合分布：分別輸出 isolated-outlier evidence、performance failure 與 inconclusive，不共用含糊 failure，對應 `FR-003`。
- Process、permission、timeout 或 cleanup failure：environment error；安全 cleanup 或明示 recovery requirement 後才可重跑，對應 `FR-005`。
- 舊 report 缺新 decision evidence：明示 incompatible／legacy，不可由 default 值補成 pass，對應 `TR-001`。
- 只有一個 OS report：comparator 明示 missing OS 並失敗；不把 deterministic synthetic metadata test 宣稱為實際雙平台效能通過，對應 `FR-006`、`DEP-003`。
- 任一 proposed change 產生 GitHub workflow YAML、加入四個 `docs` ignore patterns，或使 `test_validation_and_release_are_local_manual_workflows` 失敗：scope violation，停止並回到 upstream reapproval。
- Full verification 出現 link BUG 以外的新 failure：不得以已知例外吞掉；停止、保存 evidence 並依 relation 分流。

## 13. 完整性與開放事項

- 阻塞性開放事項：無；workspace user 已選定 local-manual alignment 方向。
- 品質門檻：18 個 requirements、正常／outlier／持續回歸／inconclusive／environment／手動雙平台／治理／過渡／文件驗收與完整追溯均有明確 oracle。
- Primary assessment：維持 revision 1、`hypothesized`／`medium`；本 revision 不虛增 root-cause certainty。
- 高風險判定：不適用；synthetic offline benchmark 不處理安全、隱私、法規、醫療、金融、兒少或身分資料。
- Gate binding：assessment、`requirements-2.md` 與全部 required Knowledge postimages 必須以 `conversation:bug-benchmark-requirements-v2` 同一次核准綁定；展示 Candidate 不等同核准。
