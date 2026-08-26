# Changelog

本檔案記錄 Codebase LLM Wiki 框架的所有重要變更。格式基於 [Keep a Changelog](https://keepachangelog.com/)。

---

## [Unreleased]

### Added

- **BA 功能需求與完整覆蓋 schema**：新增 `business-requirement` page type、`fr-*`／
  `cap-*`／stable `AC-*` 契約、functional requirement catalog、managed/user-notes/local-only
  markers，以及 local-only codebase functional coverage ledger。
- **文件總覽入口**：新增 `docs/README.md`，集中整理架構、安裝、工作流、驗證、發布、歷史、樣例與測試文件的閱讀路徑。

### Changed

- **NotebookLM Exporter schema v5 BA-only contract**：改用
  `business-functional-requirements-v2`／`business-only-ba-v2`，全量分析安全 codebase（預設包含
  behavioral tests），要求每個安全檔案具有 non-gap disposition，只 materialize BA Wiki。
  Raw code/config/business evidence/traceability 永不進入 upload sources；DLP 改為分析副本、
  managed Wiki 與 exact final payload 的 mask-then-residual-block，移除 allowlist。Enterprise
  hard/safety byte limits更新為 500/450 MB，舊 schema v1–v4 pack 要求 full rebuild。
- **GitHub Repo 導覽**：重整根目錄 README 的專案結構圖與文件索引，保留既有 `.agents/`、`.github/`、`.codex/`、`samples/`、`tests/`、`tools/` 與 `wiki/` 路徑契約。
- **NotebookLM Exporter 改為 BA-first knowledge contract**：manifest 升級至 schema v4 與
  `business-first-ba-v1`，以 business process、business rule、glossary、knowledge gaps 和
  明確 evidence state 作為必備來源；business evidence 必須保留，technical traceability
  改為獨立可選附錄。新增 `business_source_paths`、`include_traceability`、兩次 preflight
  workflow、舊 retrieval contract full-rebuild migration，以及固定 BA 驗收題組。

### Fixed

- **NotebookLM exclusion-aware fallback traversal**：exporter 與 Wiki stale digest fallback
  改用 top-down 剪枝 walker；保留 ignored、untracked、nested repository 的 runtime source，
  在進入 `.git`、dependencies、generated/cache、tests、CI/IaC、tooling、Wiki/output 等
  排除目錄前停止遞迴，並以 bounded metadata-only root summary 回報排除範圍與 truncation，
  避免大型專案在全量 fallback 掃描時因無界 `rglob` 超過 timeout。
- **NotebookLM filesystem-root inventory**：exporter 改以明確 `--root` 的檔案系統內容作為
  inventory 邊界，不要求 `.git` 或 clean working tree，也不因 nested repository 阻擋；
  NotebookLM preflight 的 Wiki lint 停用 Git dirty-path、commit-date 與 log-baseline lookup，
  但保留安全排除、內容 hash、DLP 與 preflight identity。
- **NotebookLM Wiki-first direct lookup**：Exporter 新增 `query-index` Markdown router，
  將最多五個主要來源群組、文件優先/evidence 查核、直接回答、引用與 gap 契約帶入
  NotebookLM；manifest/preflight 暴露 retrieval contract，README 提供 Custom instructions
  與同一本 Notebook 的一次性清空重傳步驟。
- **NotebookLM mixed-language word estimation**：exporter 改用
  `han_characters_plus_non_han_tokens` 加總模型，修正繁中敘事與程式碼混合時以
  `max()` 估算造成的 source 字數低估，並在 manifest/preflight 暴露計數模型。
- **NotebookLM local Basic DLP gate**：exporter 新增離線 deterministic 檢核，涵蓋
  信用卡、金融帳號、GCP credentials、GCP API key 與明文密碼；未 allowlist 的 finding
  會阻擋 preflight/apply，安全報告不保存命中值，manifest 升級至 schema v3。
- **Generated cache boundaries**：將 `.mypy_cache/` 與 `.ruff_cache/` 納入 Git ignore、release archive 與 NotebookLM evidence exclusion，並補上回歸測試。
- **Windows path spelling parity**：NotebookLM exporter 接受同一 Repo 的 Unicode 長路徑與 8.3 短路徑表示，同時維持 symlink/reparse 與 repository boundary 的 fail-closed 檢查。
- **Hook payload type safety**：PreToolUse 與 PostToolUse 對合法 JSON 但非 object
  的 host payload 不再拋 `AttributeError`；write guard fail closed，log reminder
  安全 no-op，並補上 regression coverage。
- **Hook audit path safety**：SessionStart/PostToolUse audit writers 現在拒絕 repo
  外、symlink 與 Windows reparse-point path，避免 audit state 跟隨連結寫出 framework root。
- **Wiki read boundary and hook resilience**：Wiki stale/frontmatter/lint/stats tools
  在讀取前拒絕 symlink/reparse tree，validate-log 也獨立驗證 log containment；
  SessionStart 對 unsafe 或非 UTF-8 Wiki/log 檔案安全跳過並維持 bounded context，
  補上 regression coverage。
- **NotebookLM Wiki pre-read boundary**：exporter 在收集任何 Wiki page 前先驗證
  regular tree，拒絕 symlink/reparse point，避免安全檢查前讀取外部內容；補上 invalid
  external junction regression coverage。
- **CLI root boundary parity**：lint 與 NotebookLM CLI 在 canonicalization 前拒絕使用者
  提供的 symlink/reparse root，避免命令列入口繞過 regular-tree safety guard；補上兩個
  root-level regression cases。
- **Log CLI boundary parity**：validate-log CLI 保留 lexical log path 到 regular-tree
  驗證完成，避免 symlink/reparse parent 在 canonicalization 後繞過 append-only guard；
  補上直接 CLI regression。
- **Exporter library root boundary**：NotebookLM page collection 也拒絕 symlink/reparse
  project root，讓直接 library 呼叫與 CLI 的 repository boundary 保持一致。
- **Malformed state fail-closed handling**：exporter、installer、Wiki validators 與 release
  CLI 對非 UTF-8 config/manifest/journal/page state 回傳受控錯誤，不再讓 UnicodeDecodeError
  穿透成 traceback；補上 exporter malformed-state regression。
- **Framework license path parity**：framework guard allowlist 補上 `LICENSE.txt`，
  與 release readiness 支援的三種 LICENSE 檔名一致。
- **NotebookLM scale regression**：新增 500 個 synthetic module 的 full preflight/apply
  regression，將大規模 Wiki 證據從一次性手動檢查提升為可重跑測試。
- **Hook and quality CLI contract coverage**：補齊雙平台 hook payload/mode/error matrix
  與 stale/frontmatter CLI exit-path regression，讓安全邊界與使用者入口都有直接測試。
- **Release CLI encoding**：release validate/build CLI 強制 UTF-8 stdout/stderr，修正
  Windows 非 ASCII workspace path 造成 JSON output decode failure 的跨平台問題。
- **Atomic output recovery coverage**：補上 NotebookLM output replacement failure regression，
  驗證舊 pack、manifest 與 source 在 commit 失敗後恢復，並清理暫存 stage/backup。
- **Crash recovery journal**：installer 與 NotebookLM exporter 新增 active/committed
  transaction journal，並以子程序終止測試驗證下一次操作能恢復未完成的 atomic replacement。
- **Concurrent transaction protection**：installer 與 NotebookLM exporter 以 Windows
  `msvcrt` / POSIX `fcntl` sibling lock 序列化同一 target/output 的 apply/commit；並行 writer
  fail closed；release/export inventory、跨程序 regression 與 Git ignore 都排除 sibling recovery metadata。
- **NotebookLM config boundary**：明確指定的 `--config` 現在在讀取前必須位於 Repo root
  內，並拒絕 symlink/reparse path，避免設定檔讀取越過 exporter 的 repository boundary。
- **Recovery artifact boundaries**：installer/exporter 的 stage、backup 與 journal temporary
  artifacts 不再進入 NotebookLM evidence inventory 或 release archive，並加入 Git ignore
  與 crash-window regression coverage。
- **CI workflow contract coverage**：新增 regression 釘住 Linux/Windows Python matrix
  與 release validate/build/publish gate，避免 workflow 宣告與產品契約漂移。
- **Managed index write safety**：`rebuild-index.py` 在讀取或更新 index 前拒絕 Wiki
  tree 的 symlink/reparse point，並以 structured error 結束，不跟隨連結寫出 Wiki root。
- **Release output write safety**：release builder 保留 lexical output boundary，拒絕
  output root、parent components 與既有 artifact symlink/reparse points，避免覆寫外部檔案。
- **Installer managed-block idempotence**：修正空白 target 初次安裝後，`AGENTS.md`
  managed block 因前後空白 canonicalization 不一致而在每次 plan 重複回報變更；補上
  Codex/Copilot surface 的 zero-change regression coverage。
- **NotebookLM sensitive-path scope**：敏感檔名判定改為只檢查 repo-relative components，
  避免專案位於 `secrets` 或 `credentials` 父目錄時整體 evidence 被誤排除。
- **Wiki severity documentation**：修正 System Analysis 對 stale source 嚴重度的描述，
  與 check-stale/lint contract 一致區分全數缺失的 Critical 與部分缺失的 Warning。
- **Installer target-root boundary**：CLI 在 canonicalization 前保留 lexical target root，
  因此 target 本身是 symlink 或 Windows reparse point 時會 fail closed，不會繞過安全檢查。
- **Static analysis cleanup**：移除 framework CLI/hook 的未使用 imports/locals 與
  無效 f-string，保持 deterministic scripts 的 F-lint 為 clean。
- **CLI contract hardening**：`check-stale.py`、`validate-frontmatter.py` 與
  `wiki-stats.py` 現在支援標準 `--help`，並以 no-Git directory source fallback
  regression test 固定離線/乾淨目錄行為。
- **Release/export path safety**：release assets now exclude both platform hook
  fallback audit directories; NotebookLM apply rejects previous-manifest file
  paths that are absolute, traversal-based, or resolve outside the output pack.
- **Security regression coverage**：新增 release audit-log exclusion 與 malicious
  previous-manifest path 的回歸測試，確認失敗時不刪除輸出目錄外檔案。
- **Symlink boundary hardening**：Installer、release builder 與 stale checker 對跨 root
  的 symlink path fail closed，並加入對應的 regression coverage。
- **Windows reparse boundary hardening**：Exporter output、Installer target/source 與
  release source 也辨識 directory junction/reparse point，不讓 `Path.is_symlink()` 的
  Windows 差異繞過 path boundary。
- **Pack and release input validation**：NotebookLM commit output keys、既有 output tree
  與 Installer framework source symlink 均 fail closed；release repository owner/name
  只接受安全的 `OWNER/NAME` 元件。
- **Explicit exporter configuration**：明確指定不存在的 `--config` 檔案會 fail closed，
  不再靜默套用 exporter 預設值。
- **Cross-platform path validation**：Wiki source、hook guard 與 installer target state
  統一正規化 separator 並拒絕 Windows drive-qualified/traversal path，避免在 Linux host
  被誤判為 repo-relative。
- **Exporter identity binding**：CLI `--output` 會納入 NotebookLM preflight identity，
  並提前拒絕 repo root 本身或外部輸出路徑。
- **Exporter output symlink boundary**：在 canonicalize output path 前拒絕 output root
  或其既有 parent components 的 symlink，避免繞過 pack boundary。
- **Exporter limit enforcement**：無法在設定 byte/word limits 內安全切分的 UTF-8
  內容會在 commit 前 fail closed，不再產生超限 chunk。
- **Sensitive path exclusion**：NotebookLM scan 會檢查完整路徑元件，連同 `secrets/`、
  `credentials/` 等敏感目錄下的檔案一併排除。
- **Release artifact isolation**：release builder 排除 `.env`、credentials/secrets、private-key
  paths 與 repo 內自訂 output tree，避免敏感資料或既有產物被重複封裝。
- **Generated audit isolation**：NotebookLM scan 與 release builder 一致排除兩平台 fallback
  hook audit directories，避免本機產生狀態進入 evidence 或 release assets。
- **Codex lifecycle 與設定契約**：SessionStart now covers `clear`/`compact`，改用
  `max_concurrent_threads_per_session`，parity check 驗證 canonical 設定與 compact context。
- **唯讀 agent 邊界**：Codex query、lint、archaeology agents 明確設定
  `sandbox_mode = "read-only"`，並將修復交回父 agent 或 write-capable workflow。
- **Copilot delegated tool boundary**：query 不再暴露 shell/agent；lint 與 archaeology
  不再暴露直接 edit，並由 parity 與 contract tests 固定 read-only tool surface。
- **Copilot shell boundary documented**：明確記錄 `execute` 對應 shell，profile instruction
  不是技術 sandbox；實際唯讀保證仍需 host permission/sandbox smoke。
- **Prompt workflow binding**：Copilot ingest/query/lint/ADR/guide/synthesis/SA/export
  entrypoints 明確載入 authoritative references，並由 contract test 固定授權與 index/log coupling。
- **Cross-platform source paths**：stale checker 與 aggregate digest 會正規化 Windows-style
  repo-relative separators，避免在 Linux CI 將合法 Wiki sources 誤判為 missing。
- **Hook 與 exporter 回歸**：補上真實 apply-patch payload、nested hook output、symlink
  path escape、200-page lint regression，以及 NotebookLM preflight coverage status。
- **跨平台驗證**：CI 將 Windows Python 3.11 提升為完整 suite，並 compile 所有 Skill scripts/hooks。

## [0.2.0] — 2026-08-21

### 新增

- **強制 NotebookLM preflight/apply 契約**：preflight 回傳 inventory hash、
  `preflight_id`、必要文件與 lint readiness；apply 重新掃描並拒絕 stale ID、
  不完整文件或 Critical findings
- **Installer contract v3**：新增 managed instruction blocks、upstream fingerprint
  manifest、user-only preservation、two-sided conflicts、動態 starter 日期與
  staged atomic rollback
- **Wiki provenance v2**：新增 `summary`、`derived_from`、`source_digest`，並加入
  aggregate content freshness、append-only log validator 與 managed index region
- **三種 guard mode**：新增 `wiki-only`、`coexist`、`framework`，保留 `target`
  作為 `wiki-only` alias，並擴充 framework 的 `VERSION` / `tools/` 維護邊界
- **框架自我攝取與 CI**：新增 system architecture、五個功能 module、function
  catalog、System Analysis，以及 Linux Python 3.11/3.14 與 Windows smoke workflow
- **公開發布治理**：`VERSION` 升至 0.2.0；在擁有者選擇 LICENSE 前 release
  validate/build fail closed；上游方法論改為 attribution、原創摘要與來源連結

- **Query／Lint follow-up actions**：高價值 Query 與 Lint findings 會依共用契約提供有界的 Synthesis、Guide、重新 Ingest、Lint 或暫不處理選項；Query 維持唯讀，更新與修復仍遵守既有 preview/confirmation 與 index/log 規則。
- **NotebookLM 全專案功能文件化**：`--preflight` 每次唯讀掃描可分享的 runtime source、必要 config/manifests、schema/migrations 與既有文件，回報完整納入/排除 inventory、Wiki coverage、文件計畫、容量與未驗證項目；確認後由 Agent 依功能產生繁體中文分層 Wiki。
- **Documents-first source pack schema v2**：新增功能群組 `notebooklm_group`、project function catalog 模板、`docs:<group>` / `evidence:<group>` stable IDs、舊 manifest v1 遷移與透明 `source_budget` omission；Enterprise hard/safety limits 對齊 200/180 MB 與 500,000/450,000 words。
- **NotebookLM Enterprise 離線匯出**：新增 Wiki-first `notebooklm_export` operation、共用 `export-notebooklm.py`、穩定 source IDs、manifest、增量 upload plan、容量/字數上限與敏感/生成檔排除；Copilot/Codex 只產生本機 `.notebooklm/`，不自動呼叫或上傳 NotebookLM
- **版本化發佈契約**：新增 `VERSION`、穩定 SemVer tag 驗證、GitHub Release
  workflow、ZIP/TAR.GZ 下載資產、SHA-256 checksums 與供未來 Extension 使用的
  `update-manifest.json`；installer 同步保存 `framework_version`。
- **Predictability contract**：contract v2 新增九個 intent groups、十個
  machine operations、authorization policy 與完整 entrypoint mapping
- **唯讀 Wiki lint**：新增 `lint-wiki.py` 與 `rebuild-index.py --check`，
  deterministic 檢查 frontmatter、sources、links、orphans 與 index，並把
  contradictions／module coverage 標為 `agent_review_required`
- **完整 page templates**：補齊 overview、architecture、dependency、
  guide 與 synthesis assets，`page-types.md` 收斂為 template catalog
- **Predictability regression**：新增 installer allowlist、upgrade Wiki
  preservation、instruction budget、canonical hooks、SessionStart budget 與
  lint JSON regression tests
- **Repo 產品化文件分層**：新增 `docs/architecture/`、`docs/setup/`、`docs/workflows/`、`docs/validation/` 與 `docs/history/`，將架構、安裝、11 個工作流、驗證與歷史脈絡從單一 README 拆分為可導覽文件
- **Task Tracker E2E 樣例**：新增無第三方依賴的 `samples/task-tracker/`，涵蓋 entity、repository abstraction、設定驗證、狀態轉換、錯誤分支、injected clock 與 Copilot/Codex 手動驗收流程
- **Repo 格式、write guard 與 sample contract 測試**：驗證本機文件連結、framework/target guard boundary、雙 surface 安裝與 sample raw-source hashes
- **乾淨 Target Wiki starter**：Installer 改由 `.agents/skills/codebase-wiki/assets/wiki-starter/` 建立目標 Wiki，避免複製框架自身的文件 sources 與活動歷史

- **獨立框架安裝器與 parity manifest**：新增無第三方依賴的 `install-framework.py`、`install` / `upgrade` dry-run／apply 流程、legacy path 回報、`.agents/skills/codebase-wiki/capabilities.json` contract v2 與 `parity-check.py`

- **雙入口 SSOT references**：新增並鏡像 `intent-routing.md`、`log-operations.md`、`mssql-evidence-rules.md`、`hooks-specification.md`、`adr-workflow.md`、`code-archaeology-workflow.md`、`guide-workflow.md`、`synthesis-workflow.md`，讓 Copilot 與 Codex 入口各自獨立安裝但以同步檢查維持一致
- **新增 Copilot prompts**：加入 `/code-archaeology` 與通用 `/save-guide`，保留 `/onboarding-guide` 作為新人導覽專用入口
- **新增 deterministic validation scripts**：加入並鏡像 `validate-frontmatter.py` 與 `check-dual-entry-sync.py`，分別驗證 wiki frontmatter schema 與 `.agents` / `.github` skills、`.codex` / `.github` hook scripts 是否漂移
- **新增 hook guard mode config**：新增 `.github/hooks/config.toml`，並在 `.codex/config.toml` 加入 `[wiki_guard] mode`，支援 `target` 與 `framework` 兩種寫入邊界
- **Codex 版完整重建**：依 OpenAI Codex customization surface 重新落地 `AGENTS.md`、`Codex.md`、`.agents/skills/codebase-wiki/`、`.codex/config.toml`、`.codex/hooks.json` 與 `.codex/agents/*.toml`，讓 README 宣稱的 Codex 支援有實體檔案支撐
- **Codex hook 官方 schema 對齊**：Codex hooks 使用 `SessionStart`、`PreToolUse`、`PostToolUse` 事件與 `hookSpecificOutput` 輸出格式，並保留 `.codex/hooks/logs/` 到 `.codex-hook-logs/` 的 audit fallback
- **README 新增 Codex 版完整使用範例**：新增從安裝、初始化、增量維護、wiki-first query、synthesis 保存、SA 系統分析文件、SQL Server live evidence、lint 修復、custom agents delegation 到交付前檢查的端到端操作劇本
- **雙入口同權維護說明**：README 與 Codex.md 補上 Copilot ↔ Codex parity table，明確定義兩邊維持同一組 wiki 能力、邊界、安全規則與驗收結果，但各自使用平台原生入口
- **Codex 自然語言 recipe 對照**：Codex.md 新增 9 個 Copilot slash prompt 對應的 Codex recipe，包含 SA 系統分析文件產出，避免偽造 Codex project-level custom slash prompts
- **wiki-query SQL Server live evidence 同步支援**：GitHub Copilot 端 `wiki-query` 新增 VS Code Microsoft SQL Server extension tools 後，Codex 端同步在 `AGENTS.md` 與 `.codex/agents/wiki-query.toml` 補上資料庫證據規則，允許 schema discovery、metadata lookup 與有界線的唯讀 `SELECT`
- **新增 Codex 原生框架結構**：加入 `.codex/` 與 `.agents/skills/codebase-wiki/`，讓 OpenAI Codex 可使用 project-local hooks、custom agents 與 repo-local skill，而不必依賴 Copilot `.github/` 元件
- **新增 Codex custom agents**：將 `.github/agents/` 五個 Copilot agent 轉寫為 `.codex/agents/*.toml`，包含 `wiki-keeper`、`wiki-ingest`、`wiki-query`、`wiki-lint`、`wiki-archaeologist`
- **新增 Codex hooks**：加入 `.codex/hooks.json`，呼叫共用 Skill 下的 canonical hooks，提供 `SessionStart` 狀態摘要、`PreToolUse` 寫入保護與 `PostToolUse` log reminder
- **新增 Codex repo-local skill**：將 `codebase-wiki` skill 複製到 `.agents/skills/codebase-wiki/`，並加入 `agents/openai.yaml` 作為 Codex skill metadata
- **新增 SA 系統分析文件 workflow**：`$codebase-wiki` 現在可依 wiki-first 流程產生 Markdown SA 文件，使用 `wiki/synthesis/`、`type: synthesis` 與 `tags: [synthesis, system-analysis]`，並提供 coverage gap 標示規則與模板
- **新增 OpenAI Codex 版入口**：加入根目錄 `AGENTS.md`，將 Codebase LLM Wiki 的意圖路由、Ingest / Query / Lint / Archaeology / ADR 工作流程、frontmatter 規格與禁止事項整理成 Codex 可直接讀取的專案指令
- **README 新增雙版本使用說明**：補上 GitHub Copilot 版與 OpenAI Codex 版的支援矩陣、安裝方式、快速開始、自然語言工作流與相容性說明
- **新增無外部依賴的 frontmatter parser**：加入 `.github/skills/codebase-wiki/scripts/frontmatter.py`，讓 `check-stale.py`、`rebuild-index.py`、`wiki-stats.py` 在沒有 `PyYAML` 的環境也能執行
- **新增 hook 稽核輸出忽略規則**：根目錄 `.gitignore` 新增 `.github/hooks/logs/` 與 `__pycache__/`

### 變更

- **NotebookLM 匯出語意升級**：Wiki 從唯一掃描邊界改為可增量更新的知識基線；每次重跑仍重掃整個安全專案範圍，先保留完整功能文件，再以剩餘預算加入關鍵原始 evidence。
- **Installer allowlist 與 action 分離**：只發佈 `codebase-wiki` Skill；
  `install` 建立 starter Wiki，`upgrade` 永遠保留既有 Wiki，conflict-safe
  策略維持不變
- **Progressive disclosure**：`SKILL.md`、`AGENTS.md`、Copilot instructions
  與 Wiki file instructions 收斂為 router／不變量；各 branch 使用具
  completion criterion 的 reference
- **Explicit delegation 統一**：Copilot/Codex agent descriptions 都以前置
  marker 宣告 explicit-delegation only；Query 維持唯讀並只建議獨立後續
  操作
- **Canonical hooks**：移除兩平台鏡像 scripts，設定統一呼叫
  `.agents/skills/codebase-wiki/scripts/hooks/`；SessionStart 限制為 30 行／4 KB
- **README 收斂為產品入口**：根 README 改為專案定位、結構、核心元件、特色、快速開始、E2E 樣例與文件索引；詳細操作移至 `docs/`
- **Framework guard boundary 擴充**：framework mode 允許 `docs/`、`samples/`、`tests/`，target mode 維持只允許 `wiki/`；Copilot/Codex 設定共用 canonical hook scripts
- **歷史文件歸檔**：`llm-wiki.md` 與 `prompt.txt` 移至 `docs/history/`，不刪除原始內容，並同步更新 Wiki sources 與內部連結
- **框架 Wiki 同步**：更新 `wiki/overview.md`、`wiki/guides/framework-introduction.md` 與 index，並在 append-only log 追加產品化重整紀錄

- **移除手動 `.github/skills` 鏡像**：現代 Copilot 與 Codex 共用 `.agents/skills/codebase-wiki/`；VS Code prompt 仍保留為 IDE 入口糖衣，CLI 透過 agents、skills 與自然語言使用
- **統一寫入語意**：Query／Archaeology 預設唯讀，只有明確確認才持久化 Wiki；hook guard 明確定位為 edit-tool 防呆層，不取代 shell sandbox

- **入口內 DRY 收斂**：`AGENTS.md`、`.github/copilot-instructions.md`、`.github/instructions/wiki-pages.instructions.md`、`SKILL.md` 與 wiki agents 改為保留摘要並指向對應 references；frontmatter、log operation、SQL live evidence 與 workflow 細節不再多點展開
- **Intent routing 統一為 9 類**：Install / setup、Ingest、Query、Lint、ADR、Synthesis / Guide、System Analysis / SA、Archaeology、Delegation 在 Copilot keeper、Codex keeper、AGENTS、SKILL 與 Copilot instructions 中對齊
- **Log operation 清單統一**：`wiki/log.md` operation 統一為 `ingest|query|lint|update|init|adr|synthesis|guide|archaeology`
- **Hook scripts 跨平台共用**：`wiki-session-init.py`、`wiki-write-guard.py`、`wiki-log-reminder.py` 使用單一 canonical implementation，平台設定只提供 adapter 參數
- **README / Codex.md 更新**：補上新 prompts、guard mode 安裝提醒、frontmatter validation、雙入口 sync check 與 reference-first SQL 規則
- **README Codex Workflow 功能範例擴寫**：新增「Codex 版完整使用範例」與「Codex Workflow 功能範例（逐項）」章節，逐項覆蓋 Interactive Ingest、Batch Ingest、Query、Query+SQL Server live evidence、Lint、Archaeology、ADR、Synthesis、Guide、System Analysis / SA、Delegation，每項皆提供何時使用、可直接貼上的 prompt、預期產出與驗收重點
- **Codex project instructions token 最佳化**：AGENTS.md 收斂為短核心規則，長流程與模板維持在 `$codebase-wiki` skill 的 `.agents/skills/codebase-wiki/` 下，讓 Codex 透過 progressive disclosure 按需載入
- **Codex hooks feature key 更新**：`.codex/config.toml` 改用 `[features] hooks = true`，保留 `agents.max_threads = 6` 與 `agents.max_depth = 1`，避免遞迴 subagent fan-out 增加 token 與 latency
- **Codex hook audit fallback**：canonical hooks 在 `.codex/hooks/logs/` 因 Windows ACL 無法寫入時，會退到 root-level `.codex-hook-logs/`
- **Codex Query 流程加入 DB live evidence 契約**：Query 回答若使用 DB-derived result，必須標註 `connected_at`、`source_tool`、`server`、`database`、`query_scope`、`result_limit`、`row_count`、`freshness_note`；DB 證據不得寫入 wiki frontmatter `sources`
- **README 補上資料庫 Live Evidence 說明**：新增 Copilot / Codex 入口的 SQL Server live evidence 對照、唯讀限制、fallback 原則與查詢範例
- **AGENTS.md 對齊 Codex 原生路徑**：將 Codex skill 與輔助腳本路徑從 `.github/skills/codebase-wiki/` 更新為 `.agents/skills/codebase-wiki/`，並補充 `.codex/agents` 只在明確委派時使用
- **README 改為三層 Codex 說明**：Codex 版文件現在同時描述 `AGENTS.md`、`.codex/`、`.agents/skills/`，並新增 Codex Custom Agents 對照表與 Codex Hooks 說明
- **wiki-query 唯讀契約**：Query 可提出 re-ingest、lint 或 synthesis
  建議，但不直接寫入或自動 Hand-Off
- **統一 wiki agents 的 `tools` 宣告格式**：`wiki-keeper`、`wiki-query`、`wiki-ingest`、`wiki-lint`、`wiki-archaeologist` 全數改為 inline YAML array（例如 `tools: [read, edit, search]`），讓代理能力清單更精簡且更容易比對
- **Hook 設定對齊 GitHub Copilot hooks schema**：三個 hook 設定檔改為 `version: 1`，事件名稱改用 `preToolUse`、`postToolUse`、`sessionStart`，並改以 `bash` / `powershell` 與 `timeoutSec` 宣告執行方式
- **wiki agents manifest 移除非官方 frontmatter 欄位**：`wiki-keeper`、`wiki-query`、`wiki-ingest`、`wiki-lint`、`wiki-archaeologist` 不再在 frontmatter 中宣告 `hooks:` 或 `agents:`，避免讓維護者誤以為 Copilot 會自動載入這些非標準欄位
- **Hook 輸出策略調整為稽核工件**：`wiki-log-reminder.py` 與 `wiki-session-init.py` 不再嘗試輸出 `systemMessage` 注入 agent context，改為寫入 `.github/hooks/logs/` 下的稽核檔案
- **Index / Log frontmatter 規格正式化**：`index.md`、`log.md` 現在明確使用 `type: index` / `type: log`，並要求 `sources: []` 與 `tags`
- **ADR 規格統一**：ADR 的決策狀態改由 `decision_status` 表示，`status` 保留給頁面生命週期（`active` / `stale` / `placeholder`）

### 移除

- **移除本機搜尋 Runtime**：刪除 `.codebase-wiki/`、受管 venv、SQLite FTS5 索引、Tree-sitter parsers／query packs，以及 `setup`、`doctor`、`index`、`search`、`show` 命令
- **移除舊結構索引腳本與快取寫入例外**：刪除 `structure-index.py`、`tree-sitter-preflight.py` 和 runtime-only 測試；target mode write guard 回復為只允許 `wiki/`
- **Breaking migration**：舊 target repo 的 `.codebase-wiki/` 不會被 upgrade 自動刪除；新安裝器只透過 `obsolete_paths` 回報，必須確認沒有人工內容後手動清理

### 修正

- **修正 Copilot keeper 意圖缺漏**：`.github/agents/wiki-keeper.agent.md` 補齊 Synthesis / Guide、Install / setup、Delegation，並改指向 `intent-routing.md`
- **修正目標 repo write guard 過寬**：target mode 現在只允許 `wiki/` 寫入；framework mode 才允許框架 schema/docs 路徑
- **修正多處 log operation 不一致**：Copilot instructions、wiki page instructions、prompts 與 docs 對齊 `log-operations.md`
- **README / 實體檔案一致性修復**：恢復 README 中列出的 Codex 入口檔案，避免 `AGENTS.md`、`Codex.md`、`.codex/` 與 `.agents/skills/codebase-wiki/` 被文件引用但不存在
- **Codex write guard 對齊框架維護規則**：`.codex/hooks/scripts/wiki-write-guard.py` 現在允許明確的框架維護工作更新根目錄 `README.md`、`ChangeLog.md`、`Codex.md`、`llm-wiki.md`、`prompt.txt` 與 `AGENTS.md`
- **`wiki-write-guard.py` 改為真正可執行的寫入保護**：直接輸出 `permissionDecision` / `permissionDecisionReason`，並解析 `toolArgs`，現在會實際拒絕對 `wiki/`、`.github/` 以外路徑的寫入
- **三個輔助腳本移除 `PyYAML` 硬依賴**：`check-stale.py`、`rebuild-index.py`、`wiki-stats.py` 已改用內建 frontmatter parser
- **Windows 終端輸出相容性修正**：三個輔助腳本在執行前會切換為 UTF-8 stdio，避免 CP950 主控台因 emoji 或非 ASCII 字元輸出失敗
- **Codex Windows Hook 啟動修正**：三個 Codex Hook 改用 workspace-relative、`cmd.exe` 相容的命令，移除造成 `PostToolUse hook (failed)` 的 PowerShell `$()` 與巢狀引號
- **`rebuild-index.py` 產出的 `index.md` frontmatter 與規格同步**：自動補上 `sources: []` 與 `tags: [index]`

### 受影響的檔案

| 檔案                                                                  | 變更類型                                                                                                                    |
| --------------------------------------------------------------------- | --------------------------------------------------------------------------------------------------------------------------- |
| `AGENTS.md`                                                           | 新增 / 更新（OpenAI Codex 版專案指令；Query 流程新增 SQL Server live evidence 規則）                                        |
| `README.md`                                                           | 更新（新增 Copilot / Codex 雙版本說明、Codex custom agents、hooks、資料庫 Live Evidence，以及 Codex workflow 功能逐項範例） |
| `ChangeLog.md`                                                        | 更新（追加 README 的 Codex workflow 功能範例擴寫紀錄）                                                                      |
| `.agents/skills/codebase-wiki/references/system-analysis-workflow.md` | 新增（Codex SA 系統分析文件 workflow）                                                                                      |
| `.agents/skills/codebase-wiki/assets/system-analysis-template.md`     | 新增（Codex SA 文件模板）                                                                                                   |
| `.github/prompts/system-analysis-doc.prompt.md`                       | 新增（Copilot SA 文件 slash prompt）                                                                                        |
| `.github/skills/codebase-wiki/references/system-analysis-workflow.md` | 新增（Copilot SA 系統分析文件 workflow）                                                                                    |
| `.github/skills/codebase-wiki/assets/system-analysis-template.md`     | 新增（Copilot SA 文件模板）                                                                                                 |
| `.codex/config.toml`                                                  | 新增（Codex hooks 與 subagent defaults）                                                                                    |
| `.codex/hooks.json`                                                   | 新增（Codex hook 事件設定）                                                                                                 |
| `.codex/agents/wiki-keeper.toml`                                      | 新增（Codex wiki 路由 custom agent）                                                                                        |
| `.codex/agents/wiki-ingest.toml`                                      | 新增（Codex wiki 攝入 custom agent）                                                                                        |
| `.codex/agents/wiki-query.toml`                                       | 新增 / 更新（Codex wiki 查詢 custom agent；同步 SQL Server live evidence 規則）                                             |
| `.codex/agents/wiki-lint.toml`                                        | 新增（Codex wiki 健康檢查 custom agent）                                                                                    |
| `.codex/agents/wiki-archaeologist.toml`                               | 新增（Codex 程式碼考古 custom agent）                                                                                       |
| `.codex/hooks/scripts/wiki-write-guard.py`                            | 新增 / 更新（Codex 寫入保護 hook；允許明確框架維護文件）                                                                    |
| `.codex/hooks/scripts/wiki-log-reminder.py`                           | 新增（Codex log reminder hook）                                                                                             |
| `.codex/hooks/scripts/wiki-session-init.py`                           | 新增（Codex session state hook）                                                                                            |
| `.agents/skills/codebase-wiki/`                                       | 新增（Codex repo-local skill，含 templates、references、scripts）                                                           |
| `.github/agents/wiki-query.agent.md`                                  | 更新（Hand-Off 流程與 VS Code MSSQL tools）                                                                                 |
| `.github/prompts/query-wiki.prompt.md`                                | 更新（+11/-2）                                                                                                              |
| `.github/agents/wiki-keeper.agent.md`                                 | 格式整理（`tools` 改為 inline array）                                                                                       |
| `.github/agents/wiki-ingest.agent.md`                                 | 格式整理（`tools` 改為 inline array）                                                                                       |
| `.github/agents/wiki-lint.agent.md`                                   | 格式整理（`tools` 改為 inline array）                                                                                       |
| `.github/agents/wiki-archaeologist.agent.md`                          | 格式整理（`tools` 改為 inline array）                                                                                       |
| `.github/hooks/wiki-write-guard.json`                                 | Hook schema 對齊（`version: 1`、`preToolUse`、`bash` / `powershell`）                                                       |
| `.github/hooks/wiki-log-reminder.json`                                | Hook schema 對齊（`version: 1`、`postToolUse`、`bash` / `powershell`）                                                      |
| `.github/hooks/wiki-session-init.json`                                | Hook schema 對齊（`version: 1`、`sessionStart`、`bash` / `powershell`）                                                     |
| `.github/hooks/scripts/wiki-write-guard.py`                           | 寫入防護邏輯修正（改為直接回傳 `permissionDecision`）                                                                       |
| `.github/hooks/scripts/wiki-log-reminder.py`                          | 行為調整（改寫入 `.github/hooks/logs/wiki-log-reminder.jsonl`）                                                             |
| `.github/hooks/scripts/wiki-session-init.py`                          | 行為調整（改寫入 `.github/hooks/logs/wiki-session-state.md`）                                                               |
| `.github/copilot-instructions.md`                                     | Frontmatter 規格補強（加入 `index` / `log` 與 `sources: []` 說明）                                                          |
| `.github/instructions/wiki-pages.instructions.md`                     | Frontmatter 規格補強（加入 `index` / `log` 與 `sources: []` 說明）                                                          |
| `.github/skills/codebase-wiki/assets/index-template.md`               | 模板修正（補 `sources: []`、`tags: [index]`）                                                                               |
| `.github/skills/codebase-wiki/assets/log-template.md`                 | 模板修正（補 `sources: []`、`tags: [log]`）                                                                                 |
| `.github/skills/codebase-wiki/references/page-types.md`               | ADR 規格修正（加入 `decision_status`，釐清 `status` 語意）                                                                  |
| `.github/skills/codebase-wiki/references/lint-checklist.md`           | `type` 驗證規則補上 `index` / `log`                                                                                         |
| `.github/skills/codebase-wiki/scripts/frontmatter.py`                 | 新增（無外部依賴 frontmatter parser）                                                                                       |
| `.github/skills/codebase-wiki/scripts/check-stale.py`                 | 相依修正（移除 `PyYAML`）                                                                                                   |
| `.github/skills/codebase-wiki/scripts/rebuild-index.py`               | 相依與輸出修正（移除 `PyYAML`、補齊 index frontmatter）                                                                     |
| `.github/skills/codebase-wiki/scripts/wiki-stats.py`                  | 相依與輸出修正（移除 `PyYAML`、UTF-8 stdio）                                                                                |
| `.gitignore`                                                          | 新增忽略規則（hook logs、`__pycache__/`）                                                                                   |
