---
title: 平台 Hooks 與寫入邊界
type: module
summary: Codex 與 Copilot 共用 canonical hooks，並以 wiki-only、coexist、framework 三種模式明確控制寫入邊界
notebooklm_group: function-platform-hooks
sources:
  - .agents/skills/codebase-wiki/scripts/hooks/wiki-write-guard.py
  - .agents/skills/codebase-wiki/scripts/hooks/common.py
  - .agents/skills/codebase-wiki/references/hooks-specification.md
  - .codex/hooks.json
  - tests/test_write_guard.py
source_digest: sha256:e3dacb49b748fe0de3b22e7aee49007a93aee59881892c312e68c0f84b13f7ca
derived_from: ["[[system-architecture]]"]
last_updated: 2026-08-21
tags: [module, hooks, guard, codex, copilot]
status: active
---

# 平台 Hooks 與寫入邊界

## 職責

- SessionStart 產生不超過 30 行／4 KiB 的 Wiki 狀態摘要。
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
被拒絕。Codex Windows command 使用 workspace-relative `cmd.exe` 相容路徑。

## Evidence

- `common.py` 正規化 Codex/Copilot payload 與 apply-patch paths。
- `wiki-write-guard.py` 對 coexist 只允許 repository-relative targets。
- `.codex/hooks.json` 對三個事件使用共享腳本與明確 `--platform codex`。

## Contradictions

- 舊 `target` 模式同時被描述為 Wiki task 安全邊界與一般開發預設，造成正常 coding
  工作被靜態阻擋；v0.2 以顯式 `coexist` 解開這兩種工作階段。

## Inferences

- Hook 是 deterministic guardrail，不取代平台 sandbox，也不能把 Query/Lint 等唯讀
  intent 變成寫入授權。

## Gaps

- 不同 host 對 allow response 的 UI 呈現可能不同，audit context 仍需平台支援。

## 相關頁面

- [[installer-and-upgrade]]
- [[framework-introduction]]
- [[system-analysis]]
