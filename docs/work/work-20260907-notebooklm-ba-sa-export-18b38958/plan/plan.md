# 技術規劃：NotebookLM 現況 BA／SA 匯出

- 狀態與核准證據：見 `handoff.json.approval`。
- Candidate revision：notebooklm-ba-sa-r1
- 日期：2026-09-07
- 唯一來源規格：`docs/work/work-20260907-notebooklm-ba-sa-export-18b38958/requirements.md`
- Planning baseline：repo_id `3a6b11d008ffd5ef15f38f901249bf99b363ea4742fe8c587add45cd96949ab9`；HEAD `71e7d0289ff04ebb45eb0f09e7e14052cb9f4cd1`；status SHA-256 `44c3afc94485626bfc75882191a3c807ce30059793b63b6ebae47eb26e5d62f0`。
- Primary／handoff：`docs/work/work-20260907-notebooklm-ba-sa-export-18b38958/plan/plan.md`／`docs/work/work-20260907-notebooklm-ba-sa-export-18b38958/plan/handoff.json`。

## 1. 成果、範圍與限制

Required：每次全量盤點當下安全 Codebase，預覽後一次確認；每個 cap-* 各產生可追溯的繁中現況 BA/SA，再輸出供單一 Notebook 使用的文件包。來源衝突以 code 為準；未提供證據與尚未分析必須區分。

CON-001：原始碼唯讀；無雲端呼叫、自動上傳或目標架構設計。CON-002：保留 notes、敏感資料遮罩、限額及失敗復原。CON-003：PDF/Office 等不支援來源明列，不假裝完成解析。所有需求與 CR-001～004 由 SRC-001 支持。

## 2. 證據與變更影響

| Source | Observed／Required 內容 | Plan refs | WP |
|---|---|---|---|
| SRC-001 | Ready 需求、AC-001～011、治理與範圍 | CON-001、TD-001～003 | 全部 |
| SRC-002 | AGENTS 的 source/read-only、Wiki index/log、framework 檢查 | CON-002、SEAM-003 | 全部 |
| SRC-003 | exporter 既有 scan、coverage、preflight、pack、CLI | MOD-001～003 | WP-001、WP-002 |
| SRC-004 | export workflow 現有 BA-only 與兩次確認 | TD-001、TD-002 | 全部 |
| SRC-005 | 現有 exporter unittest fixtures 與 transaction 測試 | BDD-FWK-001、TEST-001～004 | WP-001、WP-002 |
| SRC-006 | frontmatter 的 role、source_digest 與 synthesis 規則 | TD-001、MOD-002 | WP-001、WP-003 |
| SRC-007 | 本機驗證／平台入口維護契約 | TEST-005、SEAM-003 | WP-003 |
| SRC-008 | research.md 保存官方來源、runtime、absence probes | TD-001～003、BDD-FWK-001 | 全部 |

Current → target：BA-only schema v5 改為 schema v6，`content_mode=ba_sa`，knowledge contract `codebase-ba-sa-v1`、retrieval contract `codebase-ba-sa-retrieval-v1`。Capability contract 隨公開確認／輸出語義升至 v6，仍維持原有 11 intents，不新增 user-facing intent。

## 3. 設計與決策

TD-001：新增 export 專用現況 profiles `codebase-business-analysis-v1` 與 `codebase-system-analysis-v1`。不改寫 standalone BA/SA 的目標需求語義；修改其 references 中「SA 永不匯出」的絕對敘述，改為僅合格的 export profile 可選入。SD 與一般 traceability 仍 exclude。

- 每個 active capability 恰有 `wiki/synthesis/{capability}-ba.md`、`{capability}-sa.md`，各使用 `type: synthesis`、`capability_id`、`notebooklm_document: ba|sa`、上述 profile、同一穩定 business group；BA role=business，SA role=analysis。新增 frontmatter 驗證，但 legacy 未標示頁保持可讀。
- BA 描述現況角色/trigger/process/rules/results/exceptions；SA 描述邊界、I/O、狀態、資料、外部介面與失敗。兩份文件都有來源 locator、互連及 `Codebase 未提供證據` 欄位；不得填入新的政策或品質數值。
- 完整性依 active capability 清單及逐檔 disposition 驗證。缺配對、重複 role、無效 locator、dangling link、stale source 或 analysis-gap 阻擋；有證據缺口的 partial 文件可匯出。沿用來源摘要；managed 區重建，user-notes 保留，legacy 原文移入 user-notes 後不覆寫。
- Codebase 不具可識別業務功能時，預覽明列空集合，停止且不產生偽造功能包。

TD-002：分開 discovery 與 readiness 身分，保留現有 CLI seam。

- `--preflight` 保持唯讀，新增 `discovery_id`，綁 sorted safe path/hash、排除處置、config/scan profile 與語義契約；不含 Wiki bytes。完整 preview 含功能候選、各功能 BA/SA 現況、未分析與證據缺口、排除／無法讀取項目。
- 使用者確認後，Skill 保存該 ID 並重新處理整個安全 scope；coverage ledger 標記 `analyzed_discovery_id`，僅在全量處理及語意核對完成後記錄。該標記是流程 evidence，不被宣稱為自動理解程式碼的證明。
- 文件完成後 Skill 自動執行 readiness preflight，使用 `--apply --discovery-id <confirmed-id> --preflight-id <latest-id>`；不再詢問人類。Apply 必須重驗兩個 ID 與 analyzed_discovery_id。
- Code/config/scope drift 拒絕舊確認；單純 Wiki 重建可取得新 readiness ID 並沿用同一來源確認。重試相同有效快照可重做檢查，不增加人類 gate。CLI flag 表示 caller 已獲授權，不宣稱能驗證人的身分。

TD-003：沿用離線編排及原子 commit，新增兩層輸出。

- `.notebooklm/documents/{capability}-ba.md` 與 `-sa.md` 保存獨立、遮罩後完整功能文件；`.notebooklm/sources/*.md` 是實際上傳候選，包含 query-index、project-map 及由文件無損合併／安全分割的 sources。兩層都記錄 hashes 與映射；README 清楚說明只上傳 sources。
- Router 同時提供 BA 與 SA 問題導航；文件 role/profile/capability 配對必須明確，不能將全部 technical pages 誤上傳。每個功能可追到來源群組，任何必要內容都不得因 slot 壓力被略過。
- 保留 300-source／500 MB／500,000-word hard cap 及 450 MB／450,000 estimated-word safety defaults，Han 字元加 non-Han token 計數；source slots 包含 router/map。單一 Notebook 仍無法容納時 fail closed。
- DLP 同時處理 documents 與 sources，report 不保存 matched values；known residual、無法完成檢查或超限不 commit。保留既有敏感檔案與 reparse/escape 排除。
- 新增 local-only governance.md，列產品版本／官方來源／查核日期、本機檢查、租戶控制待驗證項目及管理員責任；不將 optional Google 能力誤列成所有租戶必須開啟。
- schema v1～v5 來源包 migration 標記 full rebuild；`ba_only` 設定回 migration guidance，不靜默保留 BA-only 模式。保留舊包直到新包通過原子 commit，unknown files 不刪除。

| Module | Caller-facing contract／Seam | 隱藏細節 |
|---|---|---|
| MOD-001 inventory | SEAM-001：CLI preflight JSON／stable discovery ID，零寫入 | 安全 traversal、來源指紋與 exclusions |
| MOD-002 analysis coverage | SEAM-002：coverage issues、capability→BA/SA mapping | profiles、locator、pair、stale 與 ledger 驗證 |
| MOD-003 pack | SEAM-001：apply success/exit 2、完整 output manifest | masking、packing、transaction、migration |
| MOD-004 installed workflow | SEAM-003：Copilot prompt／Codex recipe 與 installer 輸出 | 共用 Skill 細節與平台薄 adapters |

不新增 production adapter 或第三方依賴；檔案系統為本機真實 temporary fixture，沒有外部服務 mock。所有 proposed 路徑／欄位與函式內部切分由 Implementation 在此 contract 內落實。

## 4. 測試策略

BDD-FWK-001：沿用 Python 標準 unittest，最低 Python 3.11；本機 probe 為 3.14.6。新增 test-only runner `tests/notebooklm_acceptance.py`、bindings/features `tests/test_notebooklm_acceptance.py` 與 inner contracts `tests/test_notebooklm_contract.py`。無 pip 安裝；SOURCE SRC-005、SRC-008。BOOT 不適用：既有 main CLI 可載入。

Runner 必須提供 `--list`、`--scenario BDD-NNN`、`--all`、`--inner TEST-NNN`、`--related`、`--build`、`--unit-all`、`--governance`。JSON stdout 記錄 discovered/selected/executed/passed/failed/errors/skipped 與 IDs；選取 0、runner/load error、unexpected skip 或缺少 inventory 必須非零退出。Discovery 只列 BDD-001～005，不執行 fixture。測試暫存範圍為 ignored `.notebooklm-tests-tmp/`，runner 將 tempfile root 指向其中並保留 raw report 至執行證據收集完成，再由 runner 清理 fixtures；不得刪除 scope 外路徑。

| BDD／inner | Given → When → Then 與獨立 oracle | AC／WP |
|---|---|---|
| BDD-001／TEST-001 | 有舊 Wiki、新功能及 excluded files → preflight → 新來源出現在完整 preview，來源 bytes 不變，excluded 原文不讀取；添加 raw file 使 discovery ID 改變，只有 Wiki 改動不改 discovery ID。原版缺 discovery ID／pair preview 的 assertion 為 red。 | AC-001／WP-001 |
| BDD-002／TEST-002 | 手寫且獨立核對的 cap-* BA/SA fixture，另有 missing/duplicate/stale/analysis-gap/documented-gap 變體 → preflight → 完整配對可通過，處理缺漏被拒絕，明列無證據可通過；輸出 locator 必須存在。原版拒絕 SA 或不檢查配對為 red。 | AC-003～006／WP-001 |
| BDD-003／TEST-003 | confirmed discovery ID 與舊有效包 → 重建 Wiki、重新 readiness、apply → 新包成功；raw/config drift 後相同流程必須拒絕且舊包 hashes 不變。正確 red 使用既有 main/CLI：只有 readiness ID、沒有已確認 discovery ID 的 apply 原版會接受，測試應要求拒絕；不得以 unknown flag、argparse crash 或缺 runner 當 red。 | AC-002、AC-008／WP-002 |
| BDD-004／TEST-004 | 完整 BA/SA、SD/traceability decoys、DLP sentinel、低 slot/byte/word limits、unknown output file 與 v5 manifest → apply → documents 配對與 sources mapping 完整；遮罩且無原始秘密、router 支援雙角色，超限保留舊包，unknown 保留，migration 指引可見。 | AC-007～010／WP-002 |
| BDD-005／TEST-005 | 隔離 Task Tracker fixtures → 分別安裝 Codex/Copilot surface → 共用 export workflow、現況模板、單一確認 contract 與治理文件均可用，standalone BA/SA 與 SD 邊界清楚，繁中 sample 保留識別碼與 user-notes。 | AC-002、AC-004、AC-005、AC-011／WP-003 |

TEST-001 驅動 snapshot 決定性與安全排除；TEST-002 驅動 pairing/locator/gap/profile；TEST-003 驅動 ID/drift/transaction 邊界；TEST-004 驅動雙層 source mapping、capacity/masking/migration；TEST-005 驅動 installer/parity/markers。每個 TEST 的 fixture 與獨立 oracle 同列 BDD，inner tests 經其 Module Interface，不以 production formatter 產生 expected output。

每個 BDD 依序 outside-in 正確 red → 對應 TEST red/minimal green/refactor → focused BDD/related green；5 個 scenario 順序固定，不把缺 runner/fixture 當 red。完整 commands 及 timeout/write/network contract 唯一權威為 handoff.json；尚未建立的 runner commands 均為 Proposed。Full build 在記憶體 compile 所有 Git-eligible Python 並解析 JSON schemas；full tests 探索整個 tests 目錄並報告 inventory，不能只跑新案例。Governance 執行 parity、frontmatter、stale、log、index --check、Wiki lint；任何新 Critical、schema/error 或不符合契約的 stale 都失敗。

人工語意核對按 research.md 程序保存逐項 evidence，補足 AC-004/005/011 與自動測試不能证明的萃取語意／實際人類確認次數。兩平台各執行一個完整 fixture journey，人工只回覆一次預覽，記錄後續事件；缺 host runtime 時保持未驗證，不以靜態 tests 冒充完成。沒有雲端 tenant 實測的問答與控制維持未驗證。此 repo 無 CI，本次採相同 commands 本機執行，不新增 workflow。

## 5. 工作包

WP-001（無前置）：讓完整 preview 揭露每個功能的 BA/SA 與證據狀態。修改 exporter scan/preflight/coverage、frontmatter 規格與 validator、新增 `assets/notebooklm-ba-template.md`、`assets/notebooklm-sa-template.md`，更新 coverage template。Consumes SRC-001/002/003/004/005/006/008；produces discovery、pairing contracts。順序 BDD-001→TEST-001，再 BDD-002→TEST-002；各 focused/related 綠燈，沒有處理缺漏可蒙混通過。

WP-002（依賴 WP-001）：已確認來源一次處理後可取得完整單一 Notebook 包。修改 exporter CLI/settings/pack/manifest/transaction、`assets/notebooklm.toml` 與 root config、export workflow。Consumes discovery/pairing；produces v6 pack/雙層輸出/治理與 migration。順序 BDD-003→TEST-003，再 BDD-004→TEST-004；DLP、容量與 raw drift 負向情境保留前版 hashes。

WP-003（依賴 WP-002）：安裝後的兩平台可使用同一新流程。修改 capabilities/parity/installer payload inventory、`.github/prompts/export-notebooklm.prompt.md`、Codex recipes、相關 SA/BA references、README/Codex/ChangeLog、docs/workflows、docs/validation 與框架 Wiki。保留一般 standalone 文件工作流的既有邊界。BDD-005→TEST-005，更新 sample/UAT expected evidence，同步 Wiki index/digests 並追加單一 implementation update log。Full build/test/BDD/governance 與 fresh review 通過，人工語意/兩平台 journey 結果明列。

## 6. 風險與追溯

| Risk | 觸發／影響 | Mitigation／owner |
|---|---|---|
| RISK-001 | 只用 structural coverage 宣稱讀懂全部功能 | code-first locator、實際讀取／全量處理紀錄及人工語意 review；WP-001/003 |
| RISK-002 | Wiki 更新誤使已確認 raw snapshot 失效或 raw drift 未察覺 | discovery/readiness 分離，TOCTOU 再檢查；WP-002 |
| RISK-003 | 2N 文件突破 slots 或合併丟內容 | documents/sources 分層、完整 mapping、邊界 fixtures；WP-002 |
| RISK-004 | 本機 DLP 被誤稱為租戶已合規 | report 分開 local checks 與 administrator verification；WP-002/003 |
| RISK-005 | standalone SA／SD 誤進 pack | export profile+role+capability 三者共同選源；WP-001/003 |

追溯：FR-001/002→BDD-001；FR-004～009、BR-001～003→BDD-002/005；FR-003→BDD-003/005；NFR-001/002→BDD-001/005；NFR-003、TR-001、CR-001～004→BDD-003/004。每個 BDD 對應同號 TEST、CMD-BDD/CMD-TDD，並依上述 WP 分配。Sources/contract/WP/DAG 的機器索引見 handoff.json。跨 WP shared interface、framework、來源或 full commands 的修改為 global-baseline；wp-local 僅可使用完整 downstream closure。

## 7. Artifacts 與 readiness

| Artifact | Role | 權威內容 |
|---|---|---|
| plan.md | primary | 設計、模組、驗收與工作包 |
| research.md | supporting | 官方及 runtime 證據、absence probes、人工程序 |
| handoff.json | handoff | hashes、approval、sources、commands、DAG |

產品需求與技術選項無未決事項；Candidate schema/cross-reference/source/hash 檢查通過後才展示。尚未執行 Proposed commands，未宣稱產品測試通過。規劃內容的核准狀態以 handoff.json 為準。

交付工具銜接問題：planning delivery protocol 要求核准前封存，但 knowledge_workflow._planning_bundle_operations 只接受 approval.status=Ready。此 Candidate 保持 Candidate/null 核准欄位，不偽造 Ready 或確認時間。本次若獲使用者同意調整順序，先核准精確 plan bundle，才填入實際 approval metadata、封存 no-change promotion 與其 log/receipt，使用同一核准完成 apply 與 planning→implementation；不新增 claim、不變更計畫內容、不修改驗證器。若未授權順序例外，停在此銜接點。
