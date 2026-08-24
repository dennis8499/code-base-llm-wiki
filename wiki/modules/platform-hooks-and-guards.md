---
title: 平台 Hooks 與寫入邊界
type: module
summary: Codex 與 Copilot 共用 canonical hooks，並以 wiki-only、coexist、framework 三種模式明確控制寫入邊界
notebooklm_group: function-platform-hooks
sources:
  - .agents/skills/codebase-wiki/scripts/hooks/wiki-write-guard.py
  - .agents/skills/codebase-wiki/scripts/hooks/wiki-session-init.py
  - .agents/skills/codebase-wiki/scripts/hooks/wiki-log-reminder.py
  - .agents/skills/codebase-wiki/scripts/hooks/common.py
  - .agents/skills/codebase-wiki/references/hooks-specification.md
  - .codex/hooks.json
  - .codex/agents/
  - .github/hooks/
  - .github/agents/
  - tests/test_write_guard.py
source_digest: sha256:73e54516d3e104d719a7edacdc04e4e49ecf131329e6644f17e47cbf6e697ccd
derived_from: ["[[system-architecture]]"]
last_updated: 2026-08-23
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
Windows command 使用 workspace-relative `cmd.exe` 相容路徑。

## Evidence

- `common.py` 正規化 Codex/Copilot payload 與 apply-patch paths。
- `tests/test_write_guard.py` 覆蓋 Codex/Copilot payload shape、各 path key、malformed
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
- Codex 的 query、lint、archaeology custom agents 明確設定 `sandbox_mode = "read-only"`；
  Copilot 對應 profiles 不暴露直接 `edit` 或 `agent` tool，lint/archaeology 的
  `execute` 依 profile instruction 僅用於 read-only checks 或 Git history；這不是
  shell 層級的技術 sandbox，host permission 仍必須阻擋未核准的 shell writes。

## Contradictions

- 舊 `target` 模式同時被描述為 Wiki task 安全邊界與一般開發預設，造成正常 coding
  工作被靜態阻擋；v0.2 以顯式 `coexist` 解開這兩種工作階段。

## Inferences

- Hook 是 deterministic guardrail，不取代平台 sandbox，也不能把 Query/Lint 等唯讀
  intent 變成寫入授權。

## Gaps

- 不同 host 對 allow response 的 UI 呈現可能不同，audit context 仍需平台支援。
- Hook matcher 目前不把 Bash/execute 當成完整 shell write policy；Copilot 的 shell
  寫入安全性仍由 host permission/sandbox 與任務授權共同負責。

## 相關頁面

- [[installer-and-upgrade]]
- [[framework-introduction]]
- [[system-analysis]]
