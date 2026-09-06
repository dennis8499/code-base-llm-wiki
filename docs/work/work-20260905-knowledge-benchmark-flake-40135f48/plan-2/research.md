# Research：大型 Knowledge benchmark measurement-mode revision

- Work ID：`work-20260905-knowledge-benchmark-flake-40135f48`
- Revision：`research-v2-20260906`
- Planning baseline：delivery generation 1 base `71e7d0289ff04ebb45eb0f09e7e14052cb9f4cd1`；current inspected implementation commit `1289f106e0dad48908449689e2ed244c21ff913f`
- Evidence policy：Observed／Required／Proposed分開；所有raw target code只讀，沒有網路或外部寫入。

## 1. Current evidence

| Evidence | Observation | Consequence |
|---|---|---|
| `requirements-4.md` SHA `9d9b94b0780f188af6be36bd9765133f6cd5088e7314fc94c69e634e2a1a8456` | Required：2.0s、每operation三樣本、完整50k/5k、controlled BDD、三個observed gates、non-pass保留。 | 不能以threshold、fixture、retry或classifier弱化取得green。 |
| assessment 3 JSON／MD | Confirmed intermittent；contract-level duplicate timing responsibility supported；underlying latency hypothesized／medium。 | 修法只處理evidence ownership與mode，不宣稱修復Windows latency。 |
| seq99 SHA `23924a268c6b1a625269d08e404458ef97cf243489cd7d00e5bc7b4fe6a247c9` | 同一product snapshot先有3個observed pass，之後BDD-016得到cold_query_1 2/3 breaches與cold_query_2 1/3 breach，functional SHA不變。 | classifier正確fail closed；owner BDD不能再重複裁決host performance。 |
| `knowledge_benchmark.py` at `1289f106e0dad48908449689e2ed244c21ff913f` | `run_benchmark`沒有controlled參數；11個operations皆透過`_timed`取得wall-clock；report為v2且無mode；CLI無controlled flag。 | highest existing seam可局部加入optional mapping，production default不需新adapter。 |
| `test_behavior.py` at `1289f106e0dad48908449689e2ed244c21ff913f` | BDD-016直接呼叫observed `run_benchmark`或載入`KNOWLEDGE_PORTABILITY_REPORT`，並要求verdict pass；BDD-019/020已覆蓋四態與三樣本。 | 修改既有scenario即可；移除persisted-report bypass，無需新BDD framework或ID。 |
| `compare_portability_reports.py` at `1289f106e0dad48908449689e2ed244c21ff913f` | 嚴格重播v2 raw timing／result hashes／producer identity，但沒有measurement source欄位可檢查。 | v3＋required mode是最小fail-closed migration。 |
| `validate_contracts.py --governance` | 2026-09-06實跑outcome passed、errors空；BDD discovery實跑21。 | local-manual/no-workflow carry-forward已存在，這輪只補mode文字與regression。 |

## 2. Knowledge context reread

Planning query `Requirements v4 controlled BDD observed performance gates measurement mode assessment revision 3 generation 2 seq99` 回傳的每個source ref均已重讀：current Requirements v4、舊Ready Plan、assessment 3 JSON／Markdown與一份無關completed outcome。無關outcome只證明query可回傳其他work，不用來支持本方案；沒有contested result。

## 3. Generation 2 constraint

Delivery `workspace-creation.md`要求later generation從primary approved base建立，只create-only materialize current Requirements、assessment與Ready plan；不得複製舊generation產品diff。Primary HEAD仍是`71e7d0289ff04ebb45eb0f09e7e14052cb9f4cd1`，而generation 1產品commit是`1289f106e0dad48908449689e2ed244c21ff913f`，parent同為base，tree為`64999e11ee446b41dda183153f6b0944bcab06a0`。

選定exact-postimage transport：`generation-1-baseline.json`只列17個framework product／test／docs／Wiki paths，逐檔SHA是commit raw blob bytes。Implementation先驗證Git object，再逐檔取回與核對；排除`docs/work/work-20260905-knowledge-benchmark-flake-40135f48/`、`docs/bugs/`與`docs/knowledge/`，因此新核准upstream artifacts仍由orchestrator唯一materialize。整體cherry-pick被拒絕，因為它會帶入Requirements v1/v2、assessment v1/v2、舊plan與Knowledge promotions。

## 4. Controlled seam options

| Option | Evidence fidelity | Risk | Decision |
|---|---|---|---|
| Optional `controlled_operation_samples` on `run_benchmark` | 執行相同full功能calls，只替換operation duration source；可在fixture write前驗證closed shape。 | API需明示test-only；必須防止CLI暴露。 | Selected |
| Mock `time.perf_counter` globally | 會同時改變fixture setup、subprocess與其他elapsed diagnostics。 | 測試脆弱且難證明只有operation verdict受控。 | Rejected |
| 只建synthetic report，不跑full fixture | 可驗classifier／comparator。 | 不能證明50k/5k功能、digests、producer與cleanup。 | Rejected |
| 繼續observed BDD或retry | 保留真實host timing。 | 重現seq99衝突或挑選pass，違反AC-007/011。 | Rejected |

Controlled mapping contract：keys順序必須精確等於`OPERATION_ORDER`；每key恰好3個finite non-negative number且bool非法；validation先於任何fixture mutation。Controlled path不呼叫operation-level `_timed`，但每個operation函式仍實際執行三次並產生三個result hashes。Fixture setup duration可保留為observed diagnostic；`TIMING_CONTRACT`只評估operation samples。

## 5. Report migration

選定`knowledge-portability-report/v3`＋required top-level `measurement_mode`，closed enum為`observed`／`controlled`。不修改`knowledge-timing-contract/v1`、reason codes、precedence、functional schema或legacy duration projection。CLI沒有controlled選項且省略in-process mapping，因此正式producer只能輸出observed。BDD-016只接受controlled。Comparator只接受v3 observed；v2、缺欄、unknown與controlled各有negative oracle，不從host或caller推斷default。

## 6. Test and command evidence

- Observed discovery：`test_behavior.py --list-scenarios` → discovered 21、run 0、failed 0、skipped 0。
- Observed CLI help：只有fixture-root、reuse-fixture、keep-fixture、output；沒有controlled／measurement-mode flag。
- Observed governance：`validate_contracts.py --governance` → outcome passed、errors empty。
- Proposed absence：整個`docs/work/work-20260905-knowledge-benchmark-flake-40135f48/plan-2/`目前不存在，因此baseline verifier與new Ready bundle尚未執行；source code也沒有`controlled_operation_samples`、`measurement_mode`或report v3。
- Full-scale BDD與每個standalone gate timeout保持900s級別；owner aggregate使用1800s。Network一律forbidden。

## 7. Fixed execution and failure disposition

1. Plan核准後delivery進implementation，因`global-baseline`建立generation 2與new run；舊run保持terminal。
2. 驗證manifest source，exact carry-forward；任何source/hash failure為Blocked且不寫產品。
3. 按WP逐一取得BDD assertion red、inner test red、minimal green與focused/related green。
4. Fresh執行build、owner full、root full與八個governance commands；link residual只接受Ready command列出的exact identities。
5. 取得獨立commit授權後commit，再證明strict-clean。
6. 固定output paths依序跑observed 1、2、3；每一份均驗schema v3、mode observed、producer clean、functional oracle、11×3、2.0s、cleanup removed、exit 0及create-only。
7. 第一個non-pass保存stdout/stderr/report/record/source snapshot並停止；不執行後續gate或fresh review，不以第四份取代。
8. 3/3 pass後才進preliminary/final fresh review與BUG verification；Linux report仍是release follow-up而非本機虛構證據。

## 8. Residual uncertainty

底層seq99 latency來源仍未在filesystem state、Windows external load或query traversal之間確認；這不被本計畫提升為root cause。若三個新observed gates任何一個持續或mixed non-pass，證據回到diagnosis／upstream，而不是再改BDD或classifier。已知link BUG保持獨立；NotebookLM export仍待本 prerequisite delivery完成。
