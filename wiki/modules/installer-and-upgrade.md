---
title: Installer 與 Upgrade
type: module
summary: Installer v3 以 dry-run、managed blocks、upstream fingerprints 與原子寫入安全部署雙平台框架
notebooklm_group: function-install-upgrade
notebooklm_role: traceability
sources:
  - .agents/skills/codebase-wiki/scripts/install-framework.py
  - .agents/skills/codebase-wiki/references/install-workflow.md
  - .agents/skills/codebase-wiki/assets/target-agents-block.md
  - .agents/skills/codebase-wiki/capabilities.json
  - tests/test_install_framework.py
source_digest: sha256:54d077f7b8bc01d7ba1ef70ae09eb0615c69b7c9dd1cdada52ab0ac2e02203a6
derived_from: ["[[system-architecture]]"]
last_updated: 2026-08-24
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
- 以 sibling transaction lock 序列化同一 target 的 apply；已有寫入者時後來的程序 fail closed。
- crash recovery 的 journal、lock、stage/backup 與 temporary sibling artifacts 不會進 Git 或
  release archive。
- 套用前拒絕會沿 target symlink/reparse point 解析到選定 target root 外的路徑，避免把框架檔案寫入外部目錄。
- Installer source tree 若包含 symlink 或 Windows junction/reparse point 也會 fail closed，避免 framework source 讀取 repo 外內容。

## 對外介面

```text
install-framework.py install|upgrade
  --target TARGET
  --surface codex|copilot
  --guard-mode wiki-only|coexist
  [--apply]
  [--format json|text]
```

JSON contract version 為 3，包含 `managed`、`changes`、`preserved`、
`conflicts` 與 `obsolete_paths`。沒有 `--apply` 時不修改目標 Repo；存在 conflict
時即使指定 apply 也不套用。

## Evidence

- `_prepare_plan()` 以 manifest baseline 比較目標與新 framework fingerprints。
- `_atomic_write()` 先建立 stage/backup，再使用 `os.replace()` 套用及回復。
- `_atomic_write()` 建立 active/committed transaction journal；下一次 apply 可在程序終止
  後恢復原檔並清理 stage/backup。
- `_TransactionLock` 以 Windows `msvcrt` 或 POSIX `fcntl` 保護同一 target 的整段
  plan/apply；`test_atomic_install_rejects_concurrent_writer` 驗證持鎖時不會開始第二次寫入。
- `tests/test_install_framework.py::test_atomic_install_recovers_after_process_kill` 以
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
- Starter Wiki 日期由注入的 `install_date` 產生，測試不依賴固定系統日期。

## Contradictions

- v0.1 對任意既有 `AGENTS.md` 直接報 conflict；v0.2 將框架區段合併進 managed block。
- 沒有 v3 manifest 的舊目標無法安全推定兩側基線，非 managed file 的差異仍會報 conflict。

## Inferences

- fingerprint manifest 避免了完整三方 merge 的複雜度，但刻意不自動合併同一受管檔案
  內的語意衝突。

## Gaps

- Obsolete paths 只回報，不自動刪除。
- 尚未提供跨版本互動式 conflict resolver。

## 相關頁面

- [[framework-introduction]]
- [[platform-hooks-and-guards]]
- [[platform-adapters-and-release]]
- [[system-analysis]]
