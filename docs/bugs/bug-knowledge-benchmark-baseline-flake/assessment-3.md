# BUG Assessment：bug-knowledge-benchmark-baseline-flake／大型知識庫效能 baseline 間歇失敗

- BUG ID：`bug-knowledge-benchmark-baseline-flake`
- Revision：3
- Verdict：`confirmed`
- Severity：`medium`
- Relation：`intake`
- Source Work：無
- Disposition：`delivery`

## Observed／Expected／Impact

- Observed：原始相同 base SHA、50,000-file／5,000-page fixture 與正確 functional digest 曾因單一 `index_candidate=3.470925499976147s` 超過 `2.0s` 而失敗。三樣本 classifier 實作後，同一 implementation snapshot 的三個獨立 strict-clean observed reports 均通過；但後續 owner full suite 的 `BDD-016` 再執行真實 wall-clock workload 時，`cold_query_1` 有 2/3 超限、`cold_query_2` 有 1/3 超限，功能 digest 仍正確，因而正確輸出 `MIXED_OPERATION_EVIDENCE`／`inconclusive` 並在 seq99 停止。
- Expected：完整 50k/5k 的 deterministic owner BDD 必須驗證功能、schema、producer、cleanup、三樣本與四態分類契約，而不以該次不可控制的主機 wall-clock 決定預期 verdict；只有三個事前宣告、各自 strict-clean 的 standalone observed commands 承擔 delivery performance gate。任一 observed command non-pass 必須保留並停止，不得 retry-until-green。
- Impact：同一正確 implementation 可先以 3/3 standalone reports 通過真實效能 gate，隨後又因 owner BDD 重複量測主機 wall-clock 而產生 inconclusive，使 delivery 無法同時滿足 deterministic owner-suite baseline 與 fail-closed completion contract，也無法可靠區分產品回歸與未分類 host latency。
- Symptom oracle：在相同 implementation snapshot、完整 fixture 與 functional digest 下，先執行三個 standalone observed commands，再執行包含 `BDD-016` 的 owner full suite；若 dedicated reports 通過而 BDD 因另一次真實 wall-clock distribution 產生 non-pass，重複 performance responsibility 的症狀存在。

## Reproduction／Amplification

- Status：`intermittent`
- 最小步驟：於 strict-clean worktree 依核准順序執行三個 `python -X utf8 -B .agents/skills/project-knowledge/scripts/knowledge_benchmark.py --repo . --fixture-root .knowledge-test-tmp --output <create-only-report>` observed commands，保存 3/3 結果；接著執行 `python -X utf8 -B .agents/skills/project-knowledge/scripts/run_full_suite.py --scope all --fixture-root .knowledge-test-tmp`，比較 `BDD-016` report 的 mode、functional SHA、raw samples、classification 與 exit code。
- 固定條件與樣本：Windows／Python 3.14.6；implementation commit `1289f106e0dad48908449689e2ed244c21ff913f`；50,000 files／5,000 pages；每 operation 三樣本；threshold `2.0s`。三個 retained observed pass 的最大樣本為 `1.1978953999932855s`、`1.6081831000046805s`、`1.45902730000671s`；seq99 的 `cold_query_1=[1.3286805999814533,2.0839867999893613,2.394746900012251]`、`cold_query_2=[2.055227900040336,1.2933956000488251,1.1293651000014506]`，fixture setup `49.119367600011174s`，functional SHA 不變。
- Evidence refs：`implementation:runs/d9141c19feac3dfe2b921ce705b1feaaa1f0967173a415cafd5f9910b36409f6/evidence/raw/preliminary-round-1-reverify-timing-inconclusive.json`、`implementation:runs/d9141c19feac3dfe2b921ce705b1feaaa1f0967173a415cafd5f9910b36409f6/commands/sequence/0099-CMD-TEST-FULL-001-preliminary-round-1-reverify/record.json`、`diagnosis:bug-knowledge-benchmark-baseline-flake/revision-3-evidence-summary`。

## Compare／Trace

- 最近正常／目前異常：同一 snapshot 的三個 standalone reports 均為 observed／pass、功能 digest 正確且 cleanup 完成；seq99 的同一功能 digest 仍正確，但另一次 BDD wall-clock distribution 為 mixed／inconclusive。可觀察差異位於量測時窗與 consumer responsibility，不是功能輸出。
- 最小案例：四態 classifier 對 seq99 samples 的結果符合既有契約；移除 BDD 對「真實 host duration 必須 pass」的 expectation、改以 controlled samples 驗證同一 classifier 後，owner contract oracle 不再與獨立 observed gate 重複，但完整 fixture、真實功能路徑、三樣本、2.0 秒分類與 fail-closed consumers 都仍被驗證。
- Data／control flow：`BDD-016` 建立完整 fixture後直接呼叫 observed `run_benchmark`，再把當次 report verdict 映射為 owner-suite outcome；delivery 另以三個 standalone calls 對同一產品重做 observed gate。第一個已證明破裂的 completion invariant 是「deterministic owner contract gate 不應由另一個未預先承諾的 host timing window重新裁決已獨立驗證的 performance」。

## Hypotheses

| Rank | ID | Causal statement | Variable | Prediction | Falsifier | Outcome | Evidence |
|---|---|---|---|---|---|---|---|
| 1 | H-001 | Owner BDD 與 standalone commands 都以不可控制的真實 wall-clock 裁決 performance，讓不同 timing window 的合法 variance 可對同一 snapshot 產生衝突 completion verdict。 | 只改變 `BDD-016` 的 timing evidence mode，保持 fixture、功能路徑、三樣本與 classifier 不變。 | Controlled BDD 對固定 sequences 重複一致，而 standalone observed gates 仍能對真實 2.0 秒違規 fail closed。 | Controlled BDD 仍因 host duration 隨機切換，或 standalone observed gates不再能偵測持續違規。 | `supported` | `implementation:seq99`、`requirements:requirements-v3-20260906` |
| 2 | H-002 | Fresh fixture 的 cache／filesystem 狀態使 5,000-page traversal 或 cold query 在特定前置序列中偶發變慢。 | 只改變 predecessor sequence 或 fresh／reuse fixture 狀態。 | 超限會穩定聚集於特定序列或 fixture 狀態。 | 同一序列反覆執行無相關性，或隔離序列仍有相同分布。 | `untested` | `source:.agents/skills/project-knowledge/scripts/knowledge_workflow.py#L63-L88` |
| 3 | H-003 | Windows 外部 CPU、filesystem filter 或 process pressure 是 seq99 latency window 的主要來源。 | 在其餘輸入固定時同步量測與控制主機資源壓力。 | Outlier 頻率與外部壓力相關，壓力移除後回復。 | 隔離低負載環境可由產品內部單一變因確定切換失敗與通過。 | `untested` | `implementation:seq99-fixture-setup-49.119367600011174s` |

## Root cause confidence

- Status：`hypothesized`
- Confidence：`medium`
- Summary：Evidence 支持「重複的 observed wall-clock responsibility 使同一 snapshot 的 completion verdict 受不同 timing window 影響」這個 contract-level causal boundary；但 seq99 latency outlier 的底層來源仍無法在 traversal state、fixture sequence與外部 Windows load 間確認，因此不提高原 assessment 的根因 certainty。
- Evidence refs：`source:.agents/skills/project-knowledge/scripts/test_behavior.py#L2547-L2609`、`source:.agents/skills/project-knowledge/scripts/knowledge_benchmark.py#L84-L150`、`implementation:seq99-timing-inconclusive`、`requirements:requirements-v3-20260906`。

## Risks／Safety

- Security／privacy／data risk：否
- Redacted summary：不適用
- Secure evidence refs：不適用
- Named human reviewer：不適用

## Disposition 與下一步

- Disposition：維持獨立 BUG delivery，保留原始 timing symptom 與 seq99 non-pass；Requirements 只把 deterministic BDD contract gate 與三個 standalone observed performance gates 分責，不把 controlled evidence 冒充主機效能，也不把未證實的 Windows latency 來源納入產品修法。
- Next falsifiable action／owner：Requirements owner 以本 revision 3 assessment 與 Requirements v4 同一核准綁定；Planning owner 再定義最小 controlled timing seam、measurement-mode contract、generation 2 承接與固定 verification sequence。
- 禁止聲明：尚未修復；不得自動建立 issue／額外 commit／push／merge／deploy／通知；不得重開舊 implementation run、改寫 seq99 或以未核准重跑取代 non-pass。
