---
title: Wiki Activity Log
type: log
sources: []
last_updated: 2026-07-29
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
