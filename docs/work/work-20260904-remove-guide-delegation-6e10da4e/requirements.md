# 需求分析：移除 Durable Guide 與 Explicit Delegation

- 文件狀態：Ready
- 日期：2026-09-04
- 文件範圍：從 Codebase LLM Wiki 的公開契約、雙平台入口、安裝面、文件、測試與框架 Wiki 移除 Durable Guide 與 Explicit Delegation 兩項可執行能力。
- 需求來源：使用者於本工作明確要求兩項功能都刪除；現況證據來自 `.agents/skills/codebase-wiki/capabilities.json:2,41-108`、`.agents/skills/codebase-wiki/SKILL.md:5-7,28,38,71-72,89-90`、`AGENTS.md:26,33-35`、`.github/prompts/:5-6`、`.github/agents/:4-7`、`.codex/agents/:1-2`、`.agents/skills/codebase-wiki/scripts/install-framework.py:22-26,101-115,408-417`。
- 確認者：workspace-user
- Work ID：work-20260904-remove-guide-delegation-6e10da4e

## 1. 執行摘要

### 問題或機會

目前框架把 Durable Guide 與 Explicit Delegation 列為正式能力，並在共用 Skill、capability manifest、Copilot prompts/custom agents、Codex recipes/custom agents、安裝器、文件、測試與 Wiki 中維護對應契約。使用者已決定停止提供這兩項能力，因此若只刪單一入口，會留下可見但不可用的殘餘契約，或讓雙平台能力漂移。

### 為何現在做

本次明確的產品決策要求兩項能力同時下架。它們橫跨 contract v4 的 operation/group 計數、遞迴 installer surface、parity assertions 與既有文件；必須作為一個可獨立驗收的 breaking capability removal 一次收斂。

### 預期成果

- BG-001：框架的所有主動入口與公開能力清單不再提供或宣傳 Durable Guide 與 Explicit Delegation，Copilot 與 Codex 的剩餘能力保持一致且可驗證。
- BG-002：功能下架不破壞既有使用者建立的 Guide 頁面、append-only log 歷史或升級安全邊界。

## 2. 利害關係人與角色

| 角色 ID | 角色 | 需求／責任 | 決策或權限邊界 |
|---|---|---|---|
| ACT-001 | 框架使用者 | 使用剩餘 Wiki 工作流，不再看到或啟動已移除功能 | 可要求剩餘工作流；不能透過舊入口啟動 Guide 或 Wiki agent delegation |
| ACT-002 | 框架維護者 | 發布一致的契約、安裝面、文件與驗證 | 可修改本框架；不得替已安裝目標刪除使用者內容 |
| ACT-003 | 既有安裝的 Repo 維護者 | 安全升級並辨識舊受管檔 | 由其人工決定是否移除 obsolete 檔案 |

## 3. 範圍與優先順序

### 範圍內

- 從 machine-readable capability contract 移除 `guide` 與 `delegation` operations，以及對應 intent groups／entrypoints。
- 移除 Guide workflow、Guide template、Copilot `save-guide`／`onboarding-guide` prompt files 與 Query/Lint 的 `save-guide` follow-up。
- 移除 Copilot 與 Codex 的全部 Wiki custom-agent profiles；剩餘 Copilot prompts 必須能在沒有 named custom agents 時正常選用。
- 移除 Codex bundle 中只服務 subagent fan-out 的設定與所有 active delegation 說明。
- 更新 installer/parity、測試、README、Codex 手冊、AGENTS、docs、samples、ChangeLog 與框架 Wiki，使公開契約一致。
- 新安裝不得包含已移除檔案；由既有 install-state 識別的非 Wiki 舊檔在 upgrade plan 中列為 `obsolete_paths`。
- 保留 legacy Guide 頁面與 `guide` log operation 的解析、索引、lint 與 export 相容性。

### 範圍外

- 不移除 GitHub Copilot 或 OpenAI Codex 產品本身的原生 custom-agent/subagent 能力。
- 不自動刪除已安裝目標 Repo 的 obsolete 檔案。
- 不刪除既有 `wiki/guides/*.md`、既有 `guide` log entries 或使用者筆記。
- 不改變 Ingest、Query、Lint、ADR、Synthesis、BA、SA、SD、NotebookLM export、Archaeology 與 hooks 的核心行為。
- 不修改任何目標 codebase 的 raw sources。

### 非目標

- 不以重新命名方式保留兩項功能的等價入口。
- 不藉本次變更導入新的 orchestration 或文件工作流。
- 不宣稱 Copilot runtime 已因本次變更取得實機驗證。

### 優先順序

Must：完整移除主動能力、維持雙平台 parity、保護既有資料與 append-only 歷史、通過框架驗證。Should：upgrade plan 清楚列出舊受管檔。Could：後續版本另提供人工清理說明，但不納入本次自動行為。

## 4. 使用者與業務旅程

### J-001 — 使用剩餘框架能力

- 主要角色：ACT-001
- 觸發與前置條件：使用者安裝或升級移除功能後的框架。
- 主要流程：查看公開能力或使用平台入口，選擇仍受支援的 Wiki 工作流，完成對應任務。
- 替代、例外與復原：若使用舊 Guide／delegation 指令，框架不得把它路由為已移除能力；使用者可改用一般外部文件編輯或平台原生代理功能，但不屬於本框架契約。
- 完成結果：所有公開入口只呈現剩餘能力，Copilot/Codex contract 一致。
- 相關需求：FR-001、FR-002、FR-003、FR-004
- 驗收情境：AC-001、AC-002、AC-003、AC-004

### J-002 — 安全升級既有安裝

- 主要角色：ACT-003
- 觸發與前置條件：目標 Repo 的 install-state 記錄舊 Guide／custom-agent 受管檔，且可能已有使用者 Guide 內容。
- 主要流程：執行 upgrade dry-run，檢視 changes、conflicts 與 obsolete_paths，再自行決定舊檔處置。
- 替代、例外與復原：使用者修改過的檔案仍依既有 conflict/preserved 規則處理；Wiki 內容不得進入自動 obsolete 清單。
- 完成結果：新受管 surface 不再提供兩項能力，既有 Wiki 內容與歷史仍可驗證。
- 相關需求：TR-001、TR-002、NFR-001
- 驗收情境：AC-005、AC-006

## 5. 需求

### FR-001 — 移除能力契約

- 需求：框架必須從 active capability manifest 與 intent routing 移除 `guide`、`delegation` operations、groups、authorization policies 與 entrypoints，並使 operation/group 計數反映剩餘能力。
- 理由與來源：BG-001；現況由 `.agents/skills/codebase-wiki/capabilities.json:2,41-108` 證明。
- 優先順序：Must
- 驗收：AC-001

### FR-002 — 移除 Guide 主動入口與資源

- 需求：框架必須停止提供 Durable Guide 的 workflow reference、template、Copilot prompts、Codex recipes、follow-up action與 active 文件說明。
- 理由與來源：BG-001；現況由 `.agents/skills/codebase-wiki/references/guide-workflow.md:1-43`、`.github/prompts/save-guide.prompt.md:1-20`、`.github/prompts/onboarding-guide.prompt.md:1-20` 與 `Codex.md:59-60,112-116` 證明。
- 優先順序：Must
- 驗收：AC-002

### FR-003 — 移除 Wiki delegation surface

- 需求：框架必須停止安裝、宣傳或依賴 Wiki custom-agent profiles；所有仍保留的 Copilot prompt 入口必須在沒有這些 profiles 時維持有效。
- 理由與來源：BG-001；現況由 `AGENTS.md:33-35`、`.github/agents/*.agent.md:4-7`、`.codex/agents/*.toml:1-2` 與 `.github/prompts/*.prompt.md:5-6` 證明。
- 優先順序：Must
- 驗收：AC-003、AC-004

### FR-004 — 同步公開說明與框架知識

- 需求：框架必須從 active README、Codex 手冊、架構／工作流／驗證／樣例文件及框架 Wiki 移除兩項能力的現行宣稱，並以 ChangeLog Removed 項目記錄此次 breaking removal。
- 理由與來源：BG-001；framework maintenance completion criterion 位於 `.agents/skills/codebase-wiki/references/framework-maintenance.md:16-21`。
- 優先順序：Must
- 驗收：AC-004、AC-006

### TR-001 — 安全升級處置

- 需求：安裝器必須讓新安裝省略已移除的 framework files；升級既有 install-state 時，必須把不再受管的非 Wiki 舊檔列入 `obsolete_paths`，且不得自動刪除。
- 理由與來源：BG-002、J-002；現行遞迴 surface 與 obsolete 規則位於 `.agents/skills/codebase-wiki/scripts/install-framework.py:22-26,101-115,408-417`。
- 優先順序：Must
- 驗收：AC-005

### TR-002 — Legacy Guide 資料相容

- 需求：框架必須繼續接受、索引、lint 與匯出既有 `type: guide` 頁面及驗證歷史 `guide` log operation，但不得提供建立新 Guide 的主動工作流。
- 理由與來源：BG-002；preserved authorship 與 append-only 規則位於 `.agents/skills/codebase-wiki/SKILL.md:69-78`，現行 legacy parsers 位於 `validate-frontmatter.py:33,64`、`validate-log.py:29`、`rebuild-index.py:56`。
- 優先順序：Must
- 驗收：AC-006

### NFR-001 — 可驗證的一致性

- 需求：變更後的完整 unit suite、parity、frontmatter、stale、log、Wiki lint 與 index checks 必須全部通過；任何 active adapter 不得引用已刪除檔案或 agent。
- 理由與來源：BG-001、BG-002；`.agents/skills/codebase-wiki/references/framework-maintenance.md:16-21`。
- 優先順序：Must
- 驗收：AC-001 至 AC-006

## 6. 驗收情境

### AC-001 — Capability contract 不含兩項功能

- Given：更新後的 framework repository。
- When：解析 capabilities manifest 並執行 parity check。
- Then：不存在 `guide` 或 `delegation` operation/group/entrypoint；manifest 的 active operations 與 intent groups 各為 11，兩平台剩餘能力一致。
- 驗證需求：FR-001、NFR-001

### AC-002 — Guide 執行資源已移除

- Given：更新後的 framework repository。
- When：盤點 Skill references/assets、Copilot prompts、Codex recipes 與 follow-up actions。
- Then：不存在 Guide workflow/template/save/onboarding 入口或 save-guide suggestion；legacy schema/parser 相容項除外。
- 驗證需求：FR-002、TR-002、NFR-001

### AC-003 — Custom Wiki agents 已移除

- Given：更新後的 Copilot 與 Codex framework surfaces。
- When：盤點 `.github/agents/`、`.codex/agents/`、Codex agent fan-out config 與 active instructions。
- Then：不再包含 Wiki custom-agent profiles或框架 delegation 規則；剩餘 prompts 不引用已移除 named agents。
- 驗證需求：FR-003、NFR-001

### AC-004 — Active 文件不再宣傳功能

- Given：README、Codex、AGENTS、docs、samples 與 framework Wiki。
- When：搜尋兩項功能的 active terminology 與入口名稱。
- Then：只允許 migration/history、legacy compatibility、Requirements/ChangeLog 等明確歷史語境；不存在可執行或現行支援宣稱。
- 驗證需求：FR-004、NFR-001

### AC-005 — 安裝與升級保持安全

- Given：一個乾淨新 target 與一個 install-state 含舊 Guide/custom-agent managed paths 的既有 target。
- When：分別執行 install 與 upgrade dry-run/apply regression。
- Then：新 target 不收到已移除資源；upgrade 將舊非 Wiki managed paths列為 obsolete、沒有自動刪除，且既有 Wiki paths 不列入 obsolete。
- 驗證需求：TR-001、NFR-001

### AC-006 — Legacy Guide 與完整驗證仍通過

- Given：包含既有 Guide pages 與 guide log history 的 Wiki fixture。
- When：執行 frontmatter、log、index、lint、export 與完整 framework checks。
- Then：legacy content 仍可讀且通過適用檢查；框架 Wiki index 已同步，`wiki/log.md` 只追加一筆 `update`。
- 驗證需求：TR-002、NFR-001

## 7. 成功指標

| 指標 ID | 對應成果 | 指標與計算方式 | 基準 | 目標 | 量測期間／資料來源 |
|---|---|---|---|---|---|
| KPI-001 | BG-001 | Active capability manifest 中已移除 operation 數 | 2 | 0 | 變更完成時；capabilities + parity |
| KPI-002 | BG-001 | 仍依賴已刪除 Guide/custom-agent paths 的 active adapter 數 | 現況大於 0 | 0 | 變更完成時；repository search + tests |
| KPI-003 | BG-002 | Legacy Guide fixture 的適用 validation failures | 0 | 0 | 完整驗證時；frontmatter/log/index/lint/export |
| KPI-004 | BG-001、BG-002 | Framework maintenance required checks 通過率 | 待本次執行 | 100% | 實作完成時；本機完整驗證輸出 |

## 8. 追溯矩陣

| 業務成果 | 旅程 | 需求 | 驗收情境 | 成功指標 |
|---|---|---|---|---|
| BG-001 | J-001 | FR-001、FR-002、FR-003、FR-004、NFR-001 | AC-001、AC-002、AC-003、AC-004 | KPI-001、KPI-002、KPI-004 |
| BG-002 | J-002 | TR-001、TR-002、NFR-001 | AC-005、AC-006 | KPI-003、KPI-004 |

## 9. 已確認決策、假設與依賴

### 已確認決策

- D-001：使用者要求 Durable Guide 與 Explicit Delegation 兩項功能都移除。
- D-002：移除主動能力不等於銷毀既有資料；依 preserved authorship、append-only log 與 installer non-deletion 邊界保留 legacy Guide 資料相容。
- D-003：Copilot 與 Codex 必須在同一變更中收斂，不保留任一平台專屬入口。

### 已確認假設

- A-001：`guide` page type、Guide index section、Guide log token 與 exporter mapping 僅作 legacy content compatibility 時，不構成 Durable Guide 主動功能。
- A-002：平台產品原生的 subagent/custom-agent 能力不由本框架擁有，移除範圍限於 Repo 內的 Wiki delegation surface。

### 依賴與外部限制

- DEP-001：installer 依 install-state 差集產生非 Wiki `obsolete_paths`，且現行設計不自動刪除；本次不得弱化此安全邊界。
- DEP-002：框架 Wiki 的既有 Guide pages 與歷史 log 必須保持可驗證，因此相關 legacy parser tokens 仍需存在。
- DEP-003：framework maintenance 要求 matching regression tests、platform parity、ChangeLog、Wiki/index 與單一 append-only update log。

### 延後至技術規劃的決策

- TP-001：capability contract 的版本號調整與 migration assertion。
- TP-002：剩餘 Copilot prompts 使用何種平台預設 agent metadata。
- TP-003：regression tests 的最小切片與 obsolete-path fixture 形狀。
- TP-004：active documentation search 的允許歷史／legacy 字串清單。

## 10. 完整性與開放事項

本框架必須停止提供 Durable Guide 與 Explicit Delegation 兩項可執行能力，同時保留既有 Wiki Guide 文件與 append-only 歷史的可讀與可驗證相容性。

- 阻塞性開放事項：無。
- 品質門檻：通過。每項需求皆有唯一義務、來源、可觀察驗收與雙向追溯；資料保存、升級例外、平台邊界及完整驗證均已涵蓋；安全、隱私、法規、效能、無障礙與在地化沒有新增產品行為，判定不適用。
