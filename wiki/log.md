---
title: Wiki Activity Log
type: log
sources: []
last_updated: 2026-08-26
tags: [log]
status: active
---

# Activity Log

> Append-only 時序紀錄。每次 Ingest / Query / Lint / 手動修改操作後追加條目。
> 格式：`## [YYYY-MM-DD] {operation} | {subject}`

---

## [2026-04-16] init | Wiki 初始化

- 建立 Wiki 目錄骨架
- 建立 index.md、log.md、overview.md
- 建立子目錄：architecture、modules、entities、patterns、decisions、dependencies、guides、synthesis

## [2026-05-14] ingest | 框架本身文件化

- 全面閱讀專案所有核心文件（README.md、AGENTS.md、Codex.md、llm-wiki.md、agents、hooks、skills、prompts）
- 更新 wiki/overview.md：從佔位符升級為詳細框架總覽（含三層架構圖、目錄結構、兩種入口對比）
- 建立 wiki/guides/framework-introduction.md：完整功能介紹（五大 agents、六大操作、hooks、頁面規格、slash prompts、輔助腳本、模板、安裝指南、工作流程範例、相容性）
- 更新 wiki/index.md：加入 framework-introduction 條目，補齊 frontmatter（sources、tags）
- 受影響頁面：overview.md、index.md、log.md、guides/framework-introduction.md

## [2026-06-01] update | Codex workflow 雙入口同權化

- 重建並優化 Codex 入口：`AGENTS.md`、`Codex.md`、`.codex/`，改用短 AGENTS.md + `$codebase-wiki` skill 的 token-friendly 流程
- README 與 Codex.md 補上 Copilot ↔ Codex 功能對照，明確 Codex 使用自然語言 recipe 而不是偽造 Copilot slash prompt files
- 更新 wiki/overview.md 與 wiki/guides/framework-introduction.md，記錄雙入口同權維護與 Codex recipe 對照

## [2026-07-01] update | 雙入口 workflow SSOT 與 hook 安全強化

- 新增鏡像 references：intent routing、log operations、SQL live evidence、hooks specification、ADR、guide、synthesis、code archaeology workflow
- 新增 `/code-archaeology`、`/save-guide`、`validate-frontmatter.py`、`check-dual-entry-sync.py`
- 將 write guard 改為 `target` / `framework` 設定檔模式，並同步 Copilot / Codex hook scripts
- 更新 README.md、Codex.md、AGENTS.md、ChangeLog.md、`.github/`、`.codex/`、`.agents/` 以維持雙入口獨立安裝與同步驗證

## [2026-07-13] update | 共用 FTS5／Tree-sitter Runtime 與入口 parity

- 新增 `.codebase-wiki/runtime/` 共用 CLI、SQLite FTS5 索引、Tree-sitter query packs、setup/doctor/index/search 與冪等安裝器
- 將 `.agents/skills/codebase-wiki/` 定為 Copilot/Codex 唯一共同 skill，移除手動 `.github/skills` 鏡像並加入 capability parity check
- 更新雙入口 instructions、README、Codex 使用手冊與 Wiki 導覽；Query 維持唯讀，索引快取可重建且不進版控
- 受影響頁面：[[index]]、[[overview]]、[[framework-introduction]]

## [2026-07-14] update | Runtime 健康檢查與文件一致性修復

- 修正索引 stale 判斷，忽略不會被索引的根目錄文件，並正確處理 renamed source
- `doctor` 純文字輸出新增 Tree-sitter 狀態；JSON contract version 維持 1
- 恢復 runtime 測試並補上非索引文件、rename 與 doctor 回歸測試
- 更新 README、overview 與 framework guide 的歷史文件標籤及 Python 3.11+ 基線
- 受影響頁面：[[index]]、[[overview]]、[[framework-introduction]]

## [2026-07-14] lint | Wiki 健康檢查與孤兒產物盤點

- 驗證 frontmatter、source 路徑、入口 parity、雙入口同步、索引查詢與 Tree-sitter 結構解析
- 清理範圍限定為未版本控制的空鏡像目錄、空 runtime 目錄與非 venv 的可重建 `__pycache__`
- 現有 README staged 變更仍可能使 stale checker 保守提示 warning；未發現缺失 source
- 受影響頁面：[[index]]、[[overview]]、[[framework-introduction]]

## [2026-07-15] update | 移除本機搜尋 Runtime 並抽離框架安裝器

- 移除 SQLite FTS5、Tree-sitter、受管 venv、索引快取、舊 CLI 與結構索引腳本
- 新增零第三方依賴的 `install-framework.py`，提供 contract v2、dry-run／apply、雙 surface 與 legacy path 回報
- Query 回歸直接讀取 Markdown Wiki，再按需回溯 raw sources；同步更新安裝手冊、write guard 與 parity contract
- 受影響頁面：[[index]]、[[overview]]、[[framework-introduction]]

## [2026-07-22] update | Repo 產品化分層與 E2E 樣例

- 依執行元件、產品文件、驗證樣例與持久 Wiki 分層重整 Repo；README 收斂為導覽入口，詳細內容移至 `docs/`
- 新增無第三方依賴的 `samples/task-tracker/`，用於驗證 Copilot/Codex 的 Ingest、Query、Lint 與 raw-source protection
- Framework write guard 新增 `docs/`、`samples/`、`tests/` 邊界；target mode 仍只允許 `wiki/`
- 將歷史方法論與早期 prompt 移至 `docs/history/`，同步更新 evidence paths
- 受影響頁面：[[index]]、[[overview]]、[[framework-introduction]]

## [2026-07-22] update | Target Wiki starter 與框架 Wiki 分離

- Installer 改由 `.agents/skills/codebase-wiki/assets/wiki-starter/` 建立目標 Wiki，避免複製框架自己的 pages、source references 與 log history
- 保留 `install|upgrade`、`copilot|codex`、contract version 2 與 target-mode 轉換介面
- 受影響頁面：[[overview]]、[[framework-introduction]]

## [2026-07-29] update | Predictability contract 與單一實作收斂

- Installer 改用 Skill allowlist，分離 install/upgrade 並保留既有 target Wiki
- 高頻 instructions 收斂為 router，workflows 加入 completion criteria，頁面類型改用唯一 template assets
- Copilot/Codex agents 對齊 explicit delegation；Query 移除自動 Hand-Off
- 兩平台 hooks 改用 canonical implementation，新增 bounded SessionStart、唯讀 Wiki lint、index check 與 predictability regressions
- 受影響頁面：[[index]]、[[overview]]、[[framework-introduction]]

## [2026-07-29] update | 版本化發佈與 Extension 更新契約

- 新增 `VERSION`、SemVer tag 驗證、GitHub Release workflow、下載資產、SHA-256 checksums 與 `update-manifest.json`
- Installer 回報 `framework_version`，並在目標 Repo 保存 `.agents/skills/codebase-wiki/VERSION`；release workflow 不會被安裝到目標 surface
- 更新 README、release 文件與版本 Wiki，補上未來 Extension 的 manifest 與 conflict-safe upgrade 契約
- 受影響頁面：[[index]]、[[overview]]、[[framework-introduction]]、[[release-and-update]]

## [2026-08-17] update | NotebookLM Enterprise 離線 source pack 與增量更新契約

- 新增 Wiki-first `notebooklm_export` operation、共用 exporter、NotebookLM workflow reference、設定模板與 Copilot/Codex 入口
- Exporter 依 Wiki pages 與 declared evidence 建立 stable source IDs、hash manifest、檔案切分、敏感/生成檔排除與 added/changed/deleted/unchanged upload plan
- NotebookLM 流程只寫本機 `.notebooklm/` 產物，不呼叫 API、不修改 raw sources，並把 Enterprise hard limits 與較低 safety limits 納入 deterministic checks
- 受影響頁面：[[index]]、[[overview]]、[[framework-introduction]]、[[notebooklm-export]]、[[release-and-update]]

## [2026-08-20] update | NotebookLM 全專案功能文件化與 documents-first source pack

- NotebookLM workflow 改為每次唯讀重掃安全的全專案範圍，先預覽納入/排除 inventory、Wiki coverage、功能文件計畫、容量與未驗證項目，確認後才更新 Wiki 與本機 pack
- 新增繁體中文功能目錄模板、`notebooklm_group`、schema v2 功能群組 stable IDs、舊 manifest 遷移與 documents-first 預算；完整文件優先，低優先 evidence 省略會透明記錄
- Enterprise hard/safety limits 對齊每 source 200/180 MB 與 500,000/450,000 words；仍維持單一 notebook、手動上傳、raw sources 唯讀與 atomic output preservation
- 受影響頁面：[[index]]、[[overview]]、[[framework-introduction]]、[[notebooklm-export]]、[[release-and-update]]

## [2026-08-20] update | Query／Lint 後續行動選項

- 新增共用 `follow-up-actions.md` 契約，讓高價值 Query 與 Lint findings 提供有界的保存、更新、重新 Ingest、Lint 或暫不處理選項
- Copilot/Codex 入口同步維持 Query 唯讀、Lint 先報告，以及更新／修復的既有確認邊界
- 受影響頁面：[[index]]、[[overview]]、[[framework-introduction]]

## [2026-08-21] update | Codex Hook Windows shell 相容性修正

- 三個 Codex Hook 改用 workspace-relative script path，Windows `commandWindows` 改為 `cmd.exe` 相容語法，移除會造成 `PostToolUse hook (failed)` 的 PowerShell `$()` 與巢狀引號
- 新增 parity validation 與 sample contract smoke tests，直接驗證 `SessionStart`、`PreToolUse`、`PostToolUse` 可由 Windows command runner 成功啟動
- 受影響頁面：[[index]]、[[overview]]、[[framework-introduction]]

## [2026-08-21] update | Codex 文件來源 freshness 同步

- `Codex.md` 更新後同步 `[[notebooklm-export]]` 的 `last_updated`，維持 frontmatter source freshness check 通過
- 受影響頁面：[[notebooklm-export]]

<!-- codebase-wiki:log-contract-v1 -->

## [2026-08-21] update | v0.2.0 可靠性、證據與安裝治理

- NotebookLM 改為強制 preflight/apply identity gate，新增 framework scan profile，並移除重複 exporter 實作
- Wiki 品質新增 source digest、raw/Wiki provenance 分離、真正 orphan、managed index、append-only log validation 與明確 deterministic/semantic lint 狀態
- Installer contract 升至 v3，加入 managed instruction blocks、fingerprint manifest、wiki-only/coexist guard、動態 starter 日期與 atomic rollback
- 補齊 framework architecture、五個功能 module、project function catalog、System Analysis、跨平台 CI、release licensing gate 與上游方法論 attribution
- 受影響頁面：[[index]]、[[overview]]、[[system-architecture]]、[[installer-and-upgrade]]、[[wiki-quality-and-provenance]]、[[notebooklm-exporter]]、[[platform-hooks-and-guards]]、[[platform-adapters-and-release]]、[[project-function-catalog]]、[[system-analysis]]、[[framework-introduction]]、[[notebooklm-export]]、[[release-and-update]]

## [2026-08-21] update | Codex hooks、sandbox、coverage 與跨平台驗證強化

- Codex SessionStart 覆蓋 `startup`、`resume`、`clear`、`compact`，並改用 canonical agent thread 設定；read-only agents 明確採用 sandbox
- 補上 apply-patch/nested hook output、symlink path escape、200-page lint 與 preflight coverage regression tests
- Windows Python 3.11 改跑完整 CI suite，所有 Skill scripts/hooks 改用 compileall 驗證
- 受影響頁面：[[index]]、[[overview]]、[[notebooklm-exporter]]、[[platform-hooks-and-guards]]、[[platform-adapters-and-release]]、[[system-analysis]]、[[framework-introduction]]、[[notebooklm-export]]、[[release-and-update]]

## [2026-08-21] update | Release Wiki source digest refresh

- `[[platform-adapters-and-release]]` 同步 CI 與 release regression source 變更後的 `source_digest`
- 受影響頁面：[[platform-adapters-and-release]]

## [2026-08-23] update | Release 與 NotebookLM path safety hardening

- Release builder 排除 Codex/Copilot fallback hook audit directories；NotebookLM previous manifest 的 source file path 必須留在 output pack 內，避免 path traversal 讀寫或刪除外部檔案
- 新增對應的 release 與 exporter regression tests，並同步更新受影響 Wiki evidence digest
- 受影響頁面：[[index]]、[[notebooklm-exporter]]、[[notebooklm-export]]、[[platform-adapters-and-release]]、[[release-and-update]]、[[system-architecture]]、[[system-analysis]]

## [2026-08-23] update | Symlink boundary hardening

- Installer、release builder 與 stale checker 對跨 root 的 symlink path fail closed，避免外部檔案被寫入、打包或當作 Wiki raw source
- 新增 installer、release 與 stale checker 的 symlink regression tests；Windows 因 symlink privilege 限制會跳過該情境
- 受影響頁面：[[index]]、[[installer-and-upgrade]]、[[wiki-quality-and-provenance]]、[[platform-adapters-and-release]]、[[release-and-update]]、[[system-architecture]]、[[system-analysis]]、[[overview]]

## [2026-08-23] update | Verification evidence refresh

- System Analysis 同步本次雙版本 79-test suite、Windows symlink privilege skip，以及 506-page lint / 505-page preflight synthetic benchmark 的實際證據
- 將仍未完成的範圍收斂為 query 與完整 apply/export benchmark，保留 semantic review、host smoke 與 LICENSE gap
- 受影響頁面：[[index]]、[[system-analysis]]

## [2026-08-23] update | Pack and release input boundary hardening

- NotebookLM commit output keys 與既有 output tree、Installer framework source tree、release repository metadata 均加入 fail-closed 邊界驗證
- 新增 output path traversal/symlink、framework source symlink 與 repository URL input 的回歸測試
- 受影響頁面：[[index]]、[[notebooklm-exporter]]、[[notebooklm-export]]、[[installer-and-upgrade]]、[[platform-adapters-and-release]]、[[release-and-update]]、[[system-architecture]]、[[system-analysis]]

## [2026-08-23] update | Generated audit isolation

- NotebookLM framework scan 與 release builder 一致排除 `.codex-hook-logs/`、`.github-hook-logs/` fallback audit state
- 新增 preflight regression coverage，確認兩平台本機產生的 audit output 不會成為 evidence
- 受影響頁面：[[index]]、[[notebooklm-exporter]]、[[notebooklm-export]]、[[platform-adapters-and-release]]、[[release-and-update]]、[[system-architecture]]、[[system-analysis]]

## [2026-08-23] update | Regression matrix expansion

- 回歸矩陣新增 NotebookLM output key/tree、Installer source symlink、release repository input 與 fallback audit exclusion cases；System Analysis 改以版本矩陣描述測試證據，避免固定測試數漂移
- 受影響頁面：[[index]]、[[notebooklm-exporter]]、[[notebooklm-export]]、[[installer-and-upgrade]]、[[platform-adapters-and-release]]、[[release-and-update]]、[[system-architecture]]、[[system-analysis]]

## [2026-08-23] update | Explicit exporter configuration validation

- NotebookLM exporter 對明確指定的 `--config` 路徑採 fail-closed 行為；缺少或無法解析的設定不會靜默回退到預設值
- 新增 missing-config CLI regression test，並同步更新 exporter guide/module contract
- 受影響頁面：[[index]]、[[notebooklm-exporter]]、[[notebooklm-export]]

## [2026-08-23] update | Cross-platform drive path validation

- Wiki source、hook guard 與 installer target state 統一拒絕 Windows drive-qualified path，避免在 Linux host 被誤判為 repo-relative
- 新增 frontmatter、stale、lint、guard 與 installer 的跨平台 path regression tests
- 受影響頁面：[[index]]、[[wiki-quality-and-provenance]]、[[platform-hooks-and-guards]]、[[installer-and-upgrade]]、[[system-architecture]]、[[system-analysis]]

## [2026-08-23] update | NotebookLM output identity binding

- CLI `--output` override 納入 NotebookLM preflight identity，並提前拒絕 repo root 或 repo 外輸出路徑
- 新增 output-directory validation 與 preflight ID binding regression tests，避免沿用不同輸出目錄的舊 ID
- 受影響頁面：[[index]]、[[notebooklm-exporter]]、[[notebooklm-export]]、[[system-architecture]]、[[system-analysis]]、[[overview]]

## [2026-08-23] update | NotebookLM unsplittable limit enforcement

- Exporter 遇到單一 UTF-8 字元無法符合 byte limit 時 fail closed，避免產生超限 source chunk
- 新增最小 byte limit regression test，確認失敗發生在 atomic output commit 前
- 受影響頁面：[[index]]、[[notebooklm-exporter]]、[[notebooklm-export]]、[[system-architecture]]、[[system-analysis]]、[[overview]]

## [2026-08-23] update | Sensitive path exclusion

- NotebookLM scan 由只檢查檔名改為檢查完整 path components，排除 `secrets/`、`credentials/` 等敏感目錄內容
- 新增 nested sensitive-directory regression coverage，確認敏感檔案不進入 inventory 或 source pack
- 受影響頁面：[[index]]、[[notebooklm-exporter]]、[[notebooklm-export]]、[[system-architecture]]、[[system-analysis]]、[[overview]]

## [2026-08-23] update | Evidence digest synchronization

- 重新計算本輪程式與文件變更後的 evidence `source_digest`，使 stale check、lint 與 NotebookLM framework preflight 回到一致狀態
- 受影響頁面：[[system-architecture]]、[[notebooklm-export]]、[[notebooklm-exporter]]、[[overview]]、[[system-analysis]]

## [2026-08-23] update | Release artifact isolation

- Release builder 排除敏感 credentials/secrets/private-key path 與 repo 內自訂 output tree，避免公開 archive 帶入本機機密或重複封裝既有產物
- 新增 release fixture 回歸測試，確認重跑 build 的 archive members 保持一致
- 受影響頁面：[[index]]、[[platform-adapters-and-release]]、[[release-and-update]]

## [2026-08-23] update | Large Wiki full-pack verification

- 以 505-file synthetic project 完成 504 個 Wiki pages 的 NotebookLM preflight、documents-first pack materialization 與 atomic apply；`ready_to_export=true`，產出 4 個 sources
- 將大規模未驗證範圍收斂為 query/host 層 benchmark，保留 LICENSE、semantic review 與實際 host smoke gap
- 受影響頁面：[[index]]、[[system-analysis]]、[[notebooklm-exporter]]、[[notebooklm-export]]

## [2026-08-23] update | Delegated read-only tool boundary

- Copilot query profile 收斂為 `read/search`；lint 與 archaeology 移除直接 `edit/agent`，並保留 execute 僅供 read-only checks/history
- parity 與 contract tests 固定雙平台 delegated read-only roles 的工具邊界
- 受影響頁面：[[index]]、[[platform-hooks-and-guards]]、[[system-analysis]]

## [2026-08-23] update | Evidence digest synchronization

- 重新計算 `Codex.md`、validation 與 release surface 變更後的兩個 Wiki evidence digest，清除 stale source warnings
- 受影響頁面：[[framework-introduction]]、[[platform-adapters-and-release]]

## [2026-08-23] update | Copilot shell permission boundary

- 依平台 tool semantics 補充 `execute` 是 shell capability；Copilot lint/archaeology 的 instruction-only read-only 不能取代 host permission/sandbox
- 將實際 Copilot permission deny、trust、compact 與 audit smoke 保留為未驗證 gap
- 受影響頁面：[[index]]、[[framework-introduction]]、[[platform-hooks-and-guards]]、[[system-analysis]]

## [2026-08-23] update | Prompt workflow binding

- 將 Copilot workflow entrypoints 綁定到 authoritative references，並新增 contract regression 覆蓋 authorization、source schema、index/log 與 completion coupling
- 受影響頁面：[[platform-adapters-and-release]]、[[platform-hooks-and-guards]]

## [2026-08-23] update | Cross-platform source path normalization

- stale checker 與 source digest 對 repo-relative source 統一處理 `/` 與 `\\` separator，補上跨 host regression
- 受影響頁面：[[wiki-quality-and-provenance]]、[[system-analysis]]

## [2026-08-23] update | Installer target path normalization

- Installer target state path 在 host-independent validation 前正規化 `/` 與 `\\` separator，拒絕 traversal 與 drive-qualified path
- 受影響頁面：[[installer-and-upgrade]]、[[platform-adapters-and-release]]

## [2026-08-23] update | Evidence digest synchronization

- 重新計算 cross-platform source normalization 與 installer path validation 變更後的 architecture、overview、system-analysis evidence digests
- 受影響頁面：[[system-architecture]]、[[overview]]、[[system-analysis]]

## [2026-08-23] update | NotebookLM output symlink boundary

- Exporter 在 canonicalize output path 前拒絕 output root 與既有 parent components 的 symlink，並補上 regression test
- 受影響頁面：[[notebooklm-exporter]]、[[notebooklm-export]]、[[system-architecture]]、[[overview]]、[[system-analysis]]

## [2026-08-23] update | Windows reparse-point boundary

- Exporter、Installer 與 release builder 改以 symlink/reparse-point detection 保護 output、target、framework source 與 release source，並補上 junction regression
- 受影響頁面：[[notebooklm-exporter]]、[[notebooklm-export]]、[[installer-and-upgrade]]、[[platform-adapters-and-release]]、[[system-architecture]]、[[overview]]、[[system-analysis]]

## [2026-08-23] update | Reparse evidence digest synchronization

- 重新計算 exporter、installer、release 與其架構/guide/system-analysis Wiki pages 的 source digests
- 受影響頁面：[[system-architecture]]、[[notebooklm-export]]、[[release-and-update]]、[[installer-and-upgrade]]、[[notebooklm-exporter]]、[[platform-adapters-and-release]]、[[overview]]、[[system-analysis]]

## [2026-08-23] update | Reparse portability implementation

- 將 Windows reparse detection 改用 `os.stat(..., follow_symlinks=False)`，保持 Python 3.11 CI 的相容性
- 受影響頁面：[[notebooklm-exporter]]、[[installer-and-upgrade]]、[[platform-adapters-and-release]]、[[system-architecture]]、[[overview]]、[[system-analysis]]

## [2026-08-23] update | Validation CLI help and no-Git fallback

- `check-stale.py`、`validate-frontmatter.py` 與 `wiki-stats.py` 補上標準 `--help` contract，並以 no-Git directory source regression 固定 filesystem fallback
- 受影響頁面：[[wiki-quality-and-provenance]]、[[framework-introduction]]

## [2026-08-23] update | Static analysis cleanup

- 移除 framework CLI、hook 與 index helper 的未使用 imports/locals 與無效 f-string；F-lint 現在無 findings
- 受影響頁面：[[wiki-quality-and-provenance]]、[[platform-hooks-and-guards]]、[[platform-adapters-and-release]]、[[notebooklm-exporter]]

## [2026-08-23] update | Type evidence digest synchronization

- 同步 type annotation、helper cleanup 與 exporter/index source 變更後的 Wiki evidence digests
- 受影響頁面：[[system-architecture]]、[[notebooklm-export]]、[[notebooklm-exporter]]、[[platform-adapters-and-release]]、[[wiki-quality-and-provenance]]、[[overview]]、[[system-analysis]]

## [2026-08-23] update | Installer target-root reparse guard

- Installer CLI 在安全檢查前保留 lexical target root，拒絕 target 本身的 symlink 或 Windows reparse point，並新增 portable regression coverage
- 受影響頁面：[[index]]、[[installer-and-upgrade]]、[[system-architecture]]、[[overview]]、[[system-analysis]]

## [2026-08-23] update | Stale severity documentation correction

- System Analysis 改正 stale source 嚴重度：全數 source 缺失是 deterministic Critical，部分缺失、digest mismatch 或 orphan 才是 Warning
- 受影響頁面：[[index]]、[[system-analysis]]、[[wiki-quality-and-provenance]]

## [2026-08-23] update | NotebookLM sensitive-path scope

- 敏感檔名判定改為只檢查 repo-relative path components，避免專案絕對父目錄名稱造成整體 evidence 誤排除，並補上 regression coverage
- 受影響頁面：[[index]]、[[notebooklm-exporter]]、[[notebooklm-export]]、[[system-architecture]]、[[overview]]、[[system-analysis]]

## [2026-08-23] update | Installer managed-block idempotence

- 修正空白 target 初次安裝後 `AGENTS.md` managed block 的 canonical bytes，避免第二次 plan 永遠回報變更；補上 Codex/Copilot surface zero-change smoke 與 regression coverage
- 受影響頁面：[[index]]、[[installer-and-upgrade]]、[[system-architecture]]、[[overview]]、[[system-analysis]]

## [2026-08-23] update | Hook payload type safety

- PreToolUse 與 PostToolUse 對合法 JSON 但非 object 的 payload 分別 fail closed 與安全 no-op，補上兩個 canonical hook regression checks，並同步完整 hook lifecycle evidence sources
- 受影響頁面：[[index]]、[[platform-hooks-and-guards]]

## [2026-08-23] update | Hook audit path safety

- 共用 audit path boundary 會拒絕 repo 外、symlink 與 Windows reparse-point 目錄，SessionStart/PostToolUse 才會建立或追加安全的 audit state
- 受影響頁面：[[index]]、[[platform-hooks-and-guards]]

## [2026-08-23] update | Managed index write safety

- `rebuild-index.py` 在讀取或更新 managed index 前拒絕 Wiki tree 的 symlink/reparse point，並補上 structured error regression coverage
- 受影響頁面：[[index]]、[[wiki-quality-and-provenance]]

## [2026-08-23] update | Release output write safety

- release builder 保留 lexical output boundary，拒絕 output root、parent components 與既有 artifact symlink/reparse points，並補上 victim-preservation regression coverage
- 受影響頁面：[[index]]、[[platform-adapters-and-release]]、[[release-and-update]]

## [2026-08-23] update | Evidence digest synchronization

- 重新計算 shared hook boundary 變更後的 architecture evidence `source_digest`
- 受影響頁面：[[system-architecture]]

## [2026-08-23] update | Wiki read boundary and hook resilience

- Wiki stale/frontmatter/lint/stats tools 讀取前拒絕 symlink/reparse tree；SessionStart 對 unsafe 或非 UTF-8 Wiki/log 檔案安全跳過，避免讀取外部內容或拋出 traceback
- 新增 regular-tree 與 bounded session regression coverage，並同步更新 evidence digest
- 受影響頁面：[[index]]、[[wiki-quality-and-provenance]]、[[platform-hooks-and-guards]]、[[system-architecture]]、[[system-analysis]]

## [2026-08-23] update | Direct log boundary validation

- `validate-log.py` 直接執行時也會驗證 log parent tree 與 repo containment，遇到 symlink/reparse 或 repo 外 path fail closed
- 新增 direct validator regression coverage，維持各 Wiki quality CLI 的一致安全邊界
- 受影響頁面：[[index]]、[[wiki-quality-and-provenance]]

## [2026-08-23] update | Framework license path parity

- framework guard allowlist 補上 `LICENSE.txt`，與 release readiness 支援的 LICENSE、LICENSE.md、LICENSE.txt 一致
- 新增 framework-mode path regression coverage，避免合法授權檔案被 guard 誤阻擋
- 受影響頁面：[[index]]、[[platform-hooks-and-guards]]、[[platform-adapters-and-release]]、[[release-and-update]]

## [2026-08-23] update | NotebookLM scale regression evidence

- 新增 500 個 synthetic module 的 NotebookLM full preflight/apply regression，驗證大規模 Wiki 與 source-limit compaction
- 將 system analysis 的 scale evidence 改為可重跑測試來源，保留 500+ pages query benchmark gap
- 受影響頁面：[[index]]、[[notebooklm-exporter]]、[[system-analysis]]、[[platform-adapters-and-release]]

## [2026-08-23] update | Hook and quality CLI contract coverage

- 補齊雙平台 hook payload、guard mode、malformed input 與 coexist context regression，並加入 stale/frontmatter CLI exit-path coverage
- 更新 Wiki evidence，明確區分 library checks 與實際使用者 CLI contract
- 受影響頁面：[[index]]、[[platform-hooks-and-guards]]、[[wiki-quality-and-provenance]]

## [2026-08-23] update | Release CLI UTF-8 output

- release validate/build CLI 強制 UTF-8 stdout/stderr，並以含非 ASCII workspace path 的 temporary fixture 驗證 JSON output
- 修正 Windows release automation 可能因 console encoding 造成的 decode failure；owner LICENSE gate 行為維持不變
- 受影響頁面：[[index]]、[[platform-adapters-and-release]]、[[release-and-update]]

## [2026-08-23] update | NotebookLM atomic replacement recovery

- 新增 output replacement fault-injection regression，驗證 NotebookLM commit 失敗後舊 pack、manifest/source 與暫存清理均維持正確
- 文件明確區分已驗證的 replacement rollback 與尚未執行的真正 process-kill recovery
- 受影響頁面：[[index]]、[[notebooklm-exporter]]、[[notebooklm-export]]、[[system-analysis]]

## [2026-08-24] update | Crash recovery transaction journals

- installer 與 NotebookLM exporter 新增 active/committed transaction journal；子程序終止後，下一次 recovery 會恢復舊內容並清理 stage/backup
- 新增 installer/exporter process-kill regression，將 atomic recovery 從 exception rollback 擴展到程序終止窗口
- 受影響頁面：[[index]]、[[installer-and-upgrade]]、[[notebooklm-exporter]]、[[notebooklm-export]]、[[system-architecture]]、[[system-analysis]]

## [2026-08-24] update | CI and release workflow contract coverage

- 新增 contract regression，固定 Linux Python 3.11/3.14、Windows Python 3.11 matrix，以及 release validate/build/publish gate 宣告
- 明確標示 workflow contract test 不取代實際 GitHub runner 執行
- 受影響頁面：[[index]]、[[platform-adapters-and-release]]、[[release-and-update]]

## [2026-08-24] update | Concurrent transaction protection

- installer 與 NotebookLM exporter 以跨平台 sibling transaction lock 防止同一 target/output 的並行 writer 互相覆蓋 journal
- 新增跨程序 lock regression，並將 exporter lock artifact 與 journal 一起排除在 evidence inventory 外
- 受影響頁面：[[index]]、[[installer-and-upgrade]]、[[notebooklm-exporter]]、[[notebooklm-export]]、[[system-architecture]]、[[system-analysis]]

## [2026-08-24] update | Recovery metadata release exclusion

- release builder 與 framework `.gitignore` 排除 NotebookLM transaction journal/lock sibling artifacts，避免 crash state 進入 Git 或 release archive
- 受影響頁面：[[index]]、[[platform-adapters-and-release]]、[[release-and-update]]、[[notebooklm-exporter]]

## [2026-08-24] update | NotebookLM config boundary

- 明確指定的 `--config` 在讀取前限制於 Repo root 內，並拒絕 symlink/reparse path
- 受影響頁面：[[index]]、[[notebooklm-exporter]]、[[notebooklm-export]]

## [2026-08-24] update | Recovery artifact boundaries

- installer/exporter 的 stage、backup 與 journal temporary artifacts 不進 evidence inventory 或 release archive，並同步 Git ignore
- 受影響頁面：[[index]]、[[installer-and-upgrade]]、[[notebooklm-exporter]]、[[platform-adapters-and-release]]、[[notebooklm-export]]、[[release-and-update]]

## [2026-08-24] update | Copilot hook adapter execution coverage

- sample contract 現在會在安裝後實際執行 Copilot JSON hooks，驗證 sessionStart、Wiki allow、raw-source deny 與 postToolUse output；同時確認 sample raw source hashes 未變更
- 受影響頁面：[[index]]、[[platform-hooks-and-guards]]、[[platform-adapters-and-release]]

## [2026-08-24] update | NotebookLM Wiki pre-read boundary

- exporter 在讀取任何 Wiki page 前先驗證 regular tree，拒絕 symlink/reparse point，並以 invalid external junction regression 固定 fail-closed 邊界
- 受影響頁面：[[index]]、[[notebooklm-exporter]]、[[notebooklm-export]]、[[system-architecture]]、[[system-analysis]]

## [2026-08-24] update | CLI root boundary parity

- lint 與 NotebookLM CLI 在 canonicalization 前拒絕 caller-provided symlink/reparse root，避免命令列入口繞過 regular-tree safety guard
- 受影響頁面：[[index]]、[[wiki-quality-and-provenance]]、[[notebooklm-exporter]]、[[notebooklm-export]]、[[system-analysis]]

## [2026-08-24] update | Log CLI boundary parity

- validate-log CLI 保留 lexical log path 到 regular-tree 驗證完成，避免 symlink/reparse parent 繞過 append-only guard，並新增直接 CLI regression
- 受影響頁面：[[index]]、[[wiki-quality-and-provenance]]、[[platform-hooks-and-guards]]、[[system-analysis]]

## [2026-08-24] update | Exporter library root boundary

- NotebookLM page collection API 也拒絕 symlink/reparse project root，讓直接 library 呼叫與 CLI repository boundary 一致
- 受影響頁面：[[index]]、[[notebooklm-exporter]]、[[notebooklm-export]]、[[system-analysis]]

## [2026-08-24] update | Malformed state fail-closed handling

- exporter、installer、Wiki validators 與 release CLI 對非 UTF-8 state 或 filesystem failure 回傳受控錯誤，並新增 exporter malformed-state regression
- 受影響頁面：[[index]]、[[notebooklm-exporter]]、[[installer-and-upgrade]]、[[wiki-quality-and-provenance]]、[[platform-adapters-and-release]]、[[system-analysis]]

## [2026-08-24] update | Generated cache and Windows path parity

- `.mypy_cache/` 與 `.ruff_cache/` 現在由 Git、release builder 與 NotebookLM inventory 一致排除；exporter 同時接受 Windows Unicode 長短路徑別名並維持 symlink/reparse boundary guard
- 新增 cache exclusion、canonical path 與 malformed config regression；清理現有可重建 cache/log artifacts，但保留 `.notebooklm/` source pack
- 受影響頁面：[[index]]、[[notebooklm-exporter]]、[[platform-adapters-and-release]]、[[release-and-update]]

## [2026-08-25] update | NotebookLM mixed-language word estimation

- exporter 將 source 字數估算由 CJK/token 的 `max()` 改為 `han_characters_plus_non_han_tokens` 加總，並以 regression test 固定混合繁中與程式碼不再低估
- preflight 與 manifest 的 `limits` 現在記錄 `word_count_model`；同步 NotebookLM workflow、設定模板與相關 Wiki provenance
- 受影響頁面：[[index]]、[[overview]]、[[system-architecture]]、[[notebooklm-exporter]]、[[notebooklm-export]]、[[system-analysis]]

## [2026-08-25] update | NotebookLM local Basic DLP gate

- exporter 新增離線 Basic DLP 檢核、精確 allowlist 與 safe findings；未 allowlist 命中會阻擋 apply 並保留既有 pack
- manifest 升級至 schema v3，preflight contract 升級至 v2；同步 exporter workflow、設定、測試與使用文件
- 受影響頁面：[[index]]、[[overview]]、[[system-architecture]]、[[notebooklm-exporter]]、[[notebooklm-export]]、[[project-function-catalog]]、[[system-analysis]]、[[framework-introduction]]

## [2026-08-25] update | NotebookLM Wiki-first direct lookup

- exporter 新增 `query-index` source，將 Wiki-first Query 的問題路由、最多五個主要來源群組、直接回答、文件優先 evidence 查核與 gap 標示帶入 NotebookLM；`project-map` 同步改為 direct lookup 導覽
- manifest/preflight 暴露 `wiki-first-direct-lookup-v1` retrieval contract，README 提供 Custom instructions 與同一本 Notebook 清空舊 static sources 後重建的操作說明
- 受影響頁面：[[index]]、[[overview]]、[[system-architecture]]、[[notebooklm-exporter]]、[[notebooklm-export]]、[[project-function-catalog]]、[[system-analysis]]

## [2026-08-26] update | NotebookLM filesystem-root inventory

- exporter 改以明確 `--root` 的檔案系統內容作為 NotebookLM inventory，不要求 `.git` 或 clean working tree，也不因 nested repository 阻擋；nested `.git` metadata 仍依 generated 排除規則處理
- NotebookLM preflight 的 Wiki lint 停用 Git dirty-path、commit-date 與 log-baseline lookup，維持結構檢查、內容 hash、DLP 與 preflight identity；新增無 Git/nested repository regression
- 受影響頁面：[[index]]、[[overview]]、[[system-architecture]]、[[wiki-quality-and-provenance]]、[[framework-introduction]]、[[release-and-update]]、[[notebooklm-exporter]]、[[notebooklm-export]]、[[system-analysis]]

## [2026-08-26] update | NotebookLM exclusion-aware fallback traversal

- exporter 與 Wiki stale digest fallback 改用 top-down 剪枝 walker，保留 ignored、untracked 與 nested repository runtime source，避免大型排除樹造成無界 fallback 掃描
- manifest/preflight inventory 新增 directory-level `excluded_roots` bounded metadata summary；不讀取或 hash 排除內容，並對 truncation/metadata error 發出 warning；directory evidence 與 inventory 共用 exclusion-aware walker
- 受影響頁面：[[index]]、[[notebooklm-exporter]]、[[notebooklm-export]]
