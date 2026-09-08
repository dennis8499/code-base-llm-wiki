---
title: 平台 Hooks 與寫入邊界
type: module
summary: 共用 canonical hooks 以 Git-root 定位與三種 guard modes 維持跨 cwd 寫入邊界
notebooklm_group: function-platform-hooks
notebooklm_role: traceability
sources:
  - .agents/skills/codebase-wiki/scripts/hooks/
  - .agents/skills/codebase-wiki/references/hooks-specification.md
  - .codex/hooks.json
  - .github/hooks/
  - tests/wiki/test_write_guard.py
source_digest: sha256:0cbb1e22216f65d3c873fe98c4d23435f151315f5cad160bd52c92fe281111c0
derived_from: ["[[system-architecture]]"]
last_updated: 2026-09-04
tags: [module, hooks, guard, codex, copilot]
status: active
---

# 平台 Hooks 與寫入邊界

## 職責

- SessionStart 在 `startup`、`resume`、`clear`、`compact` 產生不超過 30 行／4 KiB 的 Wiki 狀態摘要。
- PreToolUse 從多種 tool payload 擷取路徑並拒絕越界寫入。
- PostToolUse 對 Wiki 變更產生 append-only log reminder audit。
- 讓 Codex 與 Copilot 設定共同調用 `.agents/.../scripts/hooks/` 的唯一實作。

## Guard modes

| Mode | 行為 |
| --- | --- |
| `wiki-only` | 只允許 `wiki/`，缺失或無效設定時 fail closed 至此模式 |
| `coexist` | 允許 Repo 內一般 coding edit，對非 Wiki path 回傳 audit context；不擴張任務授權 |
| `framework` | 允許 Wiki、schema、adapters、docs、samples、tests、tools 與核准 root files |

舊 `target` 設定會映射成 `wiki-only`。任何解析後位於 Repo 外的 path 在所有模式都
被拒絕；Windows drive-qualified path 即使在非 Windows host 也會被拒絕。Codex
hook 以 session cwd 執行，所以 POSIX 與 Windows commands 都先用
`git rev-parse --show-toplevel` 定位 Git root；若目標不是 Git Repo，只有從安裝
root 啟動時才回退目前目錄。Windows wrapper 以 `Get-Location` 與 `Join-Path`
保留空白、8.3/full path alias 與非 ASCII root 的正確邊界。

## Evidence

- `common.py` 正規化 Codex/Copilot payload 與 apply-patch paths。
- `tests/wiki/test_write_guard.py` 覆蓋 Codex/Copilot payload shape、各 path key、malformed
  input、legacy guard mode、coexist audit context 與 fail-closed decisions。
- 三個 canonical hook 都先處理 malformed/non-object input；PreToolUse 對無法解析
  的 write payload fail closed，PostToolUse 對無效 payload 安全 no-op。
- `common.audit_path_is_safe()` 讓 SessionStart/PostToolUse audit writers 拒絕 repo
  外、symlink 與 Windows reparse-point 路徑，再嘗試 fallback audit location。
- Framework guard 的 approved root release files 與 release readiness 保持一致，包含
  `LICENSE.txt`，避免合法授權檔名被 framework mode 誤阻擋。
- SessionStart 對 Wiki page 與 log 先做 regular-tree/path safety 檢查，並對 unsafe 或
  非 UTF-8 檔案安全跳過，維持 bounded context 而不讀取外部內容或拋出 traceback。
- `wiki-write-guard.py` 對 coexist 只允許 repository-relative targets。
- `.codex/hooks.json` 對三個事件使用共享腳本與明確 `--platform codex`，並涵蓋 compact 後續上下文。
- `tests/wiki/test_write_guard.py` 直接呼叫設定中的三個 Codex commands，覆蓋 Git repo
  root、Git 子目錄與非 Git root，共九種 event/location 組合；每次都必須回傳有效
  JSON 且 exit 0。
- Query、Lint 與 Archaeology 的 authorization 由共用 capability/workflow contract
  決定；hooks 與 host permission 仍必須阻擋未核准的 shell writes。

## Contradictions

- 舊 `target` 模式同時被描述為 Wiki task 安全邊界與一般開發預設，造成正常 coding
  工作被靜態阻擋；v0.2 以顯式 `coexist` 解開這兩種工作階段。

## Inferences

- Hook 是 deterministic guardrail，不取代平台 sandbox，也不能把 Query/Lint 等唯讀
  intent 變成寫入授權。

## Gaps

- 不同 host 對 allow response 的 UI 呈現可能不同，audit context 仍需平台支援。
- 非 Git 安裝目標若從子目錄啟動，沒有可靠 repository marker 可反推出安裝 root；
  使用者必須從該目標 root 啟動 Codex。
- Hook matcher 目前不把 Bash/execute 當成完整 shell write policy；Copilot 的 shell
  寫入安全性仍由 host permission/sandbox 與任務授權共同負責。

## 相關頁面

- [[installer-and-upgrade]]
- [[framework-introduction]]
- [[system-analysis]]
