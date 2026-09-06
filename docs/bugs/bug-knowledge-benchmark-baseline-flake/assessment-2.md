# BUG Assessment：bug-knowledge-benchmark-baseline-flake／大型知識庫效能 baseline 間歇失敗

- BUG ID：`bug-knowledge-benchmark-baseline-flake`
- Revision：2
- Verdict：`confirmed`
- Severity：`medium`
- Relation：`intake`
- Source Work：無
- Disposition：`delivery`

## Observed／Expected／Impact

- Observed：在相同 base SHA `71e7d0289ff04ebb45eb0f09e7e14052cb9f4cd1`、50,000 個 tracked files、5,000 個 knowledge pages 與相同功能雜湊下，`BDD-016` 曾因單次 `index_candidate=3.470925499976147s` 超過 `2.0s` 而失敗；同一版本的留存 focused sample 與本輪五個受控樣本則通過，本輪 `index_candidate` 範圍為 `0.7987834999803454–0.9807830000063404s`。
- Expected：大型 repository 的效能 gate 必須在固定 workload 與支援環境下提供可重複、可解釋的判定；持續或具代表性的 `2.0s` 違規必須失敗，而相同功能結果不得因未分類的單一計時異常而讓 delivery baseline 隨機在 pass／fail 間切換。
- Impact：未修改相關產品的 delivery 會被 baseline 阻擋，重跑又可能通過，使實作者無法可靠區分真實效能回歸、測量變異與環境故障；影響所有以 project-knowledge full suite 作 preflight 的工作。
- Symptom oracle：在相同 source SHA、50k/5k fixture 與功能雜湊下重複執行正式效能驗證；若沒有可辨識的產品或環境差異卻交替產生 pass／fail，症狀存在。

## Reproduction／Amplification

- Status：`intermittent`
- 最小步驟：於 repository root 執行 `python -X utf8 -B .agents/skills/project-knowledge/scripts/test_behavior.py --group delivery --fixture-root .knowledge-test-tmp`，或直接以相同預設 workload 呼叫 `knowledge_benchmark.run_benchmark(Path('.knowledge-test-tmp'))`；比較 `outcome`、`functional_sha256` 與 `durations_seconds.index_candidate`。
- 固定條件與樣本：Windows／Python 3.14.6；base SHA 固定；50,000 files／5,000 pages；threshold `2.0s`。留存樣本至少一失敗、一通過；本輪 fresh 一次加 reuse 四次皆通過，且每次功能與 cold／warm query 雜湊相等。
- Evidence refs：`implementation-run:14a4fc0688112aff6c114ad3a07b6b8c94d053ca5c80c601efd4cdd8713bb7a3/preflight-baseline-recovery`、`implementation-run:14a4fc0688112aff6c114ad3a07b6b8c94d053ca5c80c601efd4cdd8713bb7a3/bdd016-sample-3`、`diagnosis:bug-knowledge-benchmark-baseline-flake/controlled-samples`。

## Compare／Trace

- 最近正常／目前異常：失敗樣本與通過樣本的 `file_count`、`page_count`、`functional_sha256` 與 expected digest 相同；可觀察差異集中在 wall-clock duration。相同失敗 run 的 governance suite 通過，因此沒有證據把治理測試與效能失敗視為同一根因。
- 最小案例：`BDD-016` 的唯一失敗 oracle 是 report `outcome`；`knowledge_benchmark.py` 以一次 fresh run 中每個 cold query、warm query 與單一 `index_candidate` duration 全部 `<= 2.0s` 才通過。功能雜湊與 fixture shape 可保持正確而仍被單一 duration 判為失敗。
- Data／control flow：`build_stage_candidate_draft` 經 `_current_pages` 讀取與排序 5,000 個 sidecars、產生 index；`run_benchmark` 只取得一個 `index_candidate` wall-clock sample，隨即把任何超限值映射成 report `failed`，`BDD-016` 再把 report outcome 映射成整個 owner suite failure。第一個已證明破裂的 invariant 是「同一有效 workload 的 gate verdict 可重複」，不是功能正確性。

## Hypotheses

| Rank | ID | Causal statement | Variable | Prediction | Falsifier | Outcome | Evidence |
|---|---|---|---|---|---|---|---|
| 1 | H-001 | 單次 wall-clock `index_candidate` 樣本直接決定整體 verdict，使正常的 filesystem／scheduler latency 變異被誤分類為穩定效能回歸。 | 在 source、fixture 與功能雜湊不變時增加同一操作的受控重複樣本。 | verdict 會隨單一 outlier 改變，但多數相鄰樣本維持門檻內且功能結果相同。 | 固定環境的超限可穩定重現，且定位到產品內部同一慢路徑而非樣本變異。 | `supported` | `diagnosis:bug-knowledge-benchmark-baseline-flake/controlled-samples` |
| 2 | H-002 | 先前 BDD scenario 或 fresh fixture 建置留下可辨識的 cache／filesystem 狀態，使 `_current_pages` 的 5,000-page traversal 出現序列相依延遲。 | 只改變 BDD 前置序列或 fresh／reuse fixture 狀態。 | 超限會穩定聚集在特定前置序列或 fixture 狀態。 | 同一前置序列反覆執行仍無相關性，或無前置序列也以相同分布超限。 | `untested` | `source:.agents/skills/project-knowledge/scripts/knowledge_workflow.py#L63` |
| 3 | H-003 | Windows 主機的外部 CPU、filesystem filter 或程序啟動壓力造成偶發延遲，產品與 benchmark 只能觀察到 wall-clock outlier。 | 在其餘條件不變時控制或量測主機資源壓力。 | outlier 頻率與外部壓力相關，且離開壓力後恢復。 | 在隔離、低負載環境仍能由產品內部變因穩定切換失敗／通過。 | `untested` | `implementation-run:14a4fc0688112aff6c114ad3a07b6b8c94d053ca5c80c601efd4cdd8713bb7a3/preflight-baseline-recovery` |

## Root cause confidence

- Status：`hypothesized`
- Confidence：`medium`
- Summary：已確認單樣本 verdict 與相同功能結果的 timing variance 共同造成間歇性 gate failure；尚未證明 latency outlier 的底層來源是產品 traversal、fixture 序列或 Windows 外部負載。
- Evidence refs：`source:.agents/skills/project-knowledge/scripts/knowledge_benchmark.py#L24-L26`、`source:.agents/skills/project-knowledge/scripts/knowledge_benchmark.py#L431-L506`、`source:.agents/skills/project-knowledge/scripts/test_behavior.py#L2318-L2355`、`diagnosis:bug-knowledge-benchmark-baseline-flake/controlled-samples`。

## Risks／Safety

- Security／privacy／data risk：否
- Redacted summary：不適用
- Secure evidence refs：不適用
- Named human reviewer：不適用

## Disposition 與下一步

- Disposition：以獨立 BUG delivery 定義可重複的效能 oracle、保留 50k/5k 與功能雜湊契約，並要求真實超限仍 fail closed。Windows Git `Access denied` 事件位於不同控制邊界，隔離抽樣 5/5 通過且共享根因無 evidence，故不納入本 BUG。
- Next falsifiable action／owner：Requirements owner 固定外部可見的 pass／fail／environment-classified outcome 與驗收分布；Planning 再以單一變因 probe 決定量測穩定化或產品效能修法。
- 禁止聲明：尚未修復；不得自動建立 issue／commit／push／merge／deploy／通知。只有經使用者明確授權的 delivery workspace 建立可在 assessment 後進行，assessment 與 Requirements 仍須在第一道 gate 一起確認後才寫入 repository。
