---
title: Installer 與 Upgrade
type: module
summary: Installer v7 以 dry-run、package completeness、managed blocks、upstream fingerprints 與原子寫入安全部署雙平台框架及 BA／SA／SD／NotebookLM current-state 資源，並同步安裝且驗證含獨立 MIT 授權的 pinned tgrep bundle
notebooklm_group: function-install-upgrade
notebooklm_role: traceability
sources:
  - ".agents/skills/codebase-wiki/scripts/install-framework.py"
  - ".github/workflows/release.yml"
  - ".agents/skills/codebase-wiki/references/install-workflow.md"
  - ".agents/skills/codebase-wiki/assets/target-agents-block.md"
  - ".agents/skills/codebase-wiki/capabilities.json"
  - ".agents/skills/codebase-wiki/references/code-audit-workflow.md"
  - ".agents/skills/codebase-wiki/assets/code-audit-template.md"
  - ".agents/skills/codebase-wiki/scripts/validate-code-audit.py"
  - "tests/installer/test_install_framework.py"
  - ".github/prompts/code-audit.prompt.md"
  - ".agents/skills/codebase-wiki/scripts/tgrep-search.py"
  - ".agents/skills/codebase-wiki/bin/tgrep-manifest.json"
  - ".agents/skills/codebase-wiki/scripts/wiki-visualize.py"
  - ".agents/skills/codebase-wiki/references/visualization-workflow.md"
  - ".gitattributes"
  - ".agents/skills/codebase-wiki/vendor/archify-manifest.json"
  - ".agents/skills/codebase-wiki/bin/windows-x64/LICENSE.txt"
source_digest: "sha256:fd9007e298eb2417aafceba26de46700dee2205b98ea9b6553ccef0d1345b534"
derived_from: ["[[system-architecture]]"]
last_updated: 2026-11-01
tags: [module, installer, upgrade, atomicity]
status: active
---

# Installer 與 Upgrade

## 職責

- 在 `install` 與 `upgrade` 前先產生不寫入的變更計畫。
- 只安裝共用 Skill 與選定的 Codex/Copilot adapter；新 starter 建立 processes/rules 目錄，
  upgrade 不碰目標 Wiki。
- 將 root instructions 放入 managed marker block，保留 marker 外的專案規則。
- 透過 `install-state.json` 分辨 upstream-only、user-only 與 two-sided changes。
- 將所有輸出 staging 後原子替換，失敗時回復原檔。
- Windows stage 以安全隨機 sibling directory 繼承 target parent ACL，避免 Python
  3.13+ `mkdtemp()` 的 owner-only DACL 隨 staged files 移入安裝目標。
- 以 sibling transaction lock 序列化同一 target 的 apply；已有寫入者時後來的程序 fail closed。
- crash recovery 的 journal、lock、stage/backup 與 temporary sibling artifacts 不會進 Git 或
  release archive。
- 套用前拒絕會沿 target symlink/reparse point 解析到選定 target root 外的路徑，避免把框架檔案寫入外部目錄。
- Installer source tree 若包含 symlink 或 Windows junction/reparse point 也會 fail closed，避免 framework source 讀取 repo 外內容。
- 共用 Skill 以同一份受管 surface 安裝 tgrep wrapper、manifest、Windows x64 binary 與相鄰 MIT `LICENSE.txt`；installer 在任何 target 寫入前驗證 manifest 的授權資訊與檔案 SHA-256。
  Copilot／Codex 不各自維護副本，且 installer 不建立 target 的 `.tgrep/` index/server。
- Copilot surface 直接枚舉目前 `.github/` 內容；framework-only 的
  `.github/workflows/release.yml` 由 installer 明確排除，不會把 release workflow
  安裝到 target，其他 surface contract 維持不變。
- Release package README marker 啟用額外完整性 gate：在任何 target 寫入前確認共用
  Skill、Wiki starter、VERSION、target `AGENTS.md` template 與所選 Codex／Copilot
  adapter 都存在；選錯平台包會 fail closed。
- v7 隨共用 Skill 安裝三份 standards-aligned templates/workflows 與兩份 NotebookLM
  current-state BA／SA templates，Copilot surface 另取得
  BA／SA／SD／Codebase audit 薄 prompt adapters；共用 Codebase audit workflow、報告模板與
  `validate-code-audit.py`
  亦隨兩個 surface 安裝。Audit adapter 每次先從目前 Codebase 入口建立 inventory，
  再按呼叫路徑追查；upgrade 仍不改寫目標 `wiki/`。

## 對外介面

```text
install-framework.py install|upgrade
  --target TARGET
  --surface codex|copilot
  --guard-mode wiki-only|coexist
  [--apply]
  [--format json|text]
```

JSON contract version 為 7，包含 `managed`、`changes`、`preserved`、
`conflicts` 與 `obsolete_paths`。沒有 `--apply` 時不修改目標 Repo；存在 conflict
時即使指定 apply 也不套用。

## Archify bundle

Installer contract v7 carries the complete pinned Archify package, MIT license, and file-hash manifest into both platform bundles. The installer validates the 200-file inventory and rejects metadata or hash drift before writing; users do not run npm install or download the tool. The root `.gitattributes` sets `-text` for the vendored Archify files and manifest so Windows checkouts preserve the pinned bytes and hashes.

## Evidence

- `_prepare_plan()` 以 manifest baseline 比較目標與新 framework fingerprints。
- 一般上游移除的受管檔案不進入新安裝；upgrade 將舊路徑列入 `obsolete_paths` 並保留實體檔，
  `test_upgrade_reports_removed_live_database_rule_without_deleting_it` 與
  `test_upgrade_marks_removed_capability_paths_obsolete_without_deleting_them` 固定此相容性契約。
  已明確撤下的開發規格五個檔案依下方歸屬驗證與交易式刪除規則處理。
- `_atomic_write()` 先建立 stage/backup，再使用 `os.replace()` 套用及回復。
- On Windows, `_create_stage_directory()` creates a secure random sibling stage under the target parent so it inherits that ACL. The regression `test_windows_installed_files_inherit_target_permissions` grants Authenticated Users (`S-1-5-11`) an inheritable read/execute ACE on the temporary parent and verifies the installed file ACL contains that SID. It does not assert the rendered `(I)` marker.
- `_atomic_write()` 建立 active/committed transaction journal；下一次 apply 可在程序終止
  後恢復原檔並清理 stage/backup。
- `_TransactionLock` 以 Windows `msvcrt` 或 POSIX `fcntl` 保護同一 target 的整段
  plan/apply；`test_atomic_install_rejects_concurrent_writer` 驗證持鎖時不會開始第二次寫入。
- `tests/installer/test_install_framework.py::test_atomic_install_recovers_after_process_kill` 以
  子程序在第一個新檔替換後終止，驗證 journal recovery 保留舊檔且不留下孤兒暫存目錄。
- `_target_path_is_safe()` 在 plan 與 atomic write 邊界檢查 target path 的實際解析位置。
- `_target_path_is_safe()` 也拒絕跨平台 drive-qualified target path，避免 Windows state
  在其他 host 被誤解為 repo-relative。
- `_target_path_is_safe()` 先正規化 `/` 與 `\\` separator，再拒絕 traversal，維持
  Windows/Linux host 對 target state 的相同判定。
- `_target_path_is_safe()` 同時拒絕 target root 與其 path components 的 symlink/reparse
  point，避免 Windows junction 改變實際寫入邊界。
- CLI 對非 UTF-8 install-state、transaction journal 或 framework source 會回傳受控
  failure，不讓 recovery/installation 直接拋出 UnicodeDecodeError traceback。
- CLI 入口在安全檢查前保留 lexical target root；因此 target 本身是 symlink 或
  Windows reparse point 時，不會先被 `resolve()` 隱藏。
- `_render_managed_document()` 對只有 managed block 的新 target 使用 canonical bytes，
  因此第一次 apply 後的第二次 plan 不會反覆回報 `AGENTS.md` 變更；Codex/Copilot
  surface 都有整合 smoke 與 regression coverage。
- `COMMON_SURFACE_PATHS` 遞迴納入 `scripts/tgrep-search.py`、
  `bin/tgrep-manifest.json`、`bin/windows-x64/tgrep.exe` 與 `bin/windows-x64/LICENSE.txt`，
  因此兩個 surface 的 fresh install 與 upgrade 都共享相同 tgrep artifact；wrapper 的 read-only 契約另由
  `tests/tgrep/test_tgrep_search.py` 驗證。
- Starter Wiki 日期由注入的 `install_date` 產生，測試不依賴固定系統日期。

## Contradictions

- v0.1 對任意既有 `AGENTS.md` 直接報 conflict；v0.2 將框架區段合併進 managed block。
- 沒有相容 manifest baseline 的舊目標無法安全推定兩側基線，非 managed file 的差異仍會報 conflict。

## Inferences

- fingerprint manifest 避免了完整三方 merge 的複雜度，但刻意不自動合併同一受管檔案
  內的語意衝突。

## Gaps

- 除已明確撤下並可驗證歸屬的開發規格檔案外，其餘 obsolete paths 只回報，不自動刪除。
- 尚未提供跨版本互動式 conflict resolver。

## 相關頁面

- [[framework-introduction]]
- [[platform-hooks-and-guards]]
- [[platform-adapters-and-release]]
- [[business-analysis]]
- [[system-analysis]]
- [[system-design]]

## 已移除功能的升級

開發規格的五個受管理檔案在升級時依 install-state 的原 SHA-256 驗證後刪除。
`changes` 列出刪除項目，`obsolete_paths` 保留過時清單；JSON contract version 為 7，並支援從 v6 安裝狀態升級。
本機修改或無安裝歸屬時列為 conflicts，停止全部套用。刪除與其他更新共用 before-image
交易、失敗回復與程序中斷復原；使用者的 Wiki 與規格文件保留。

歷史入口與既有文件的處理方式見 [[development-specification]]。

## 0.6.3 工具交付

新增離線 Git、bounded process、Wiki writer／CAS 及其 CLI 均隨原生 Skill scripts 封裝，維持標準函式庫、唯讀 raw-source 與既有 installer 交易契約。持久 Wiki 的檔案交易與 installer／NotebookLM output locks 各自保護所屬表面，操作見 [[bounded-resource-operations]]。
