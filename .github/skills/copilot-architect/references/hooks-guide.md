# Hooks 配置指南

## 核心概念

Hooks 是 Copilot 生命週期中**唯一能提供確定性攔截**的機制。

> 指令（Instructions）可以「建議」AI 遵守規則；Hook 則能「強制執行」。

**配置位置**：`.github/hooks/*.json`（每個 Hook 配置一個 JSON 檔案）

> **更新註記（VS Code 2026 現行規格）**：Workspace hook JSON 使用 `{ "hooks": { "PreToolUse": [...], "PostToolUse": [...] } }` 結構；VS Code 會忽略 Claude 相容格式中的 `matcher`，建議在腳本內自行檢查 `tool_name` 與 `tool_input`。

---

## 生命週期事件

| 事件           | 觸發時機            | 主要用途                         |
| -------------- | ------------------- | -------------------------------- |
| `sessionStart` | 代理 session 啟動時 | 環境初始化、合規公告、狀態驗證   |
| `preToolUse`   | 任何工具執行**前**  | 安全攔截、危險命令封鎖、審計日誌 |
| `postToolUse`  | 任何工具執行**後**  | 敏感資訊脫敏、異常告警、審計記錄 |

---

## 規則清單

1. **Hooks 是安全底線**：不要只靠 Instructions 進行安全控制，高風險場景必須設 Hook。
2. **最小攔截範圍**：只攔截真正需要審查的工具（如 `bash`、`edit`），避免攔截所有工具降低效率。
3. **明確的回應格式**：Hook 腳本必須輸出合法的 JSON，`permissionDecision` 只接受 `"allow"` / `"deny"` / `"ask"`。
4. **日誌可審計性**：所有 deny 決策應寫入審計日誌，包括時間戳、觸發命令、拒絕原因。
5. **腳本冪等性**：Hook 腳本可能被多次呼叫，設計應為冪等（多次執行同樣結果）。
6. **失敗安全（Fail-Safe）**：若 Hook 腳本本身出錯，應預設 `"deny"`，而非因錯誤而放行。
7. **跨平台優先**：若團隊同時使用 Windows / macOS / Linux，優先以 Python 實作 Hook 腳本；若使用 Bash 或 PowerShell，請明示平台前提。

---

## JSON 配置規格

### 基本結構

```json
{
  "hooks": {
    "PreToolUse": [
      {
        "type": "script",
        "command": "執行的腳本路徑或 shell 指令（可為 .py / .ps1 / .sh）",
        "timeout": 10
      }
    ],
    "PostToolUse": []
  }
}
```

### 回應格式（Hook 腳本輸出）

Hook 腳本必須輸出以下 JSON 到 stdout：

```json
{
  "hookSpecificOutput": {
    "hookEventName": "PreToolUse",
    "permissionDecision": "allow | deny | ask",
    "permissionDecisionReason": "拒絕或詢問的說明（選填，但建議填寫）",
    "updatedInput": {}
  },
  "systemMessage": "可選：顯示給使用者的提醒"
}
```

| 決策      | 效果                            |
| --------- | ------------------------------- |
| `"allow"` | 放行工具執行                    |
| `"deny"`  | 阻止執行，並向代理顯示 `reason` |
| `"ask"`   | 暫停執行，詢問使用者是否允許    |

---

## 撰寫指南

### 三類 Hook 設計模式

**模式 1：黑名單攔截（Blacklist Guard）**
列出明確禁止的命令模式，命中即 deny。
```
適用：已知危險命令（rm -rf、git push --force、DROP TABLE）
```

**模式 2：白名單放行（Whitelist Gate）**
只允許已知安全的命令模式，否則一律 ask。
```
適用：高安全性環境（生產環境代理、財務系統修改）
```

**模式 3：條件式審核（Conditional Review）**
根據上下文（如目標分支、環境變數）決定是否需要人工確認。
```
適用：生產環境部署前的確認、跨服務邊界操作
```

### Guardrail 腳本設計（優先 Python）

若團隊成員跨平台作業，優先使用 Python，避免 Bash + `jq` 成為隱性相依：

```python
#!/usr/bin/env python3
import datetime as dt
import json
import os
import pathlib
import re
import sys

BLOCKED_PATTERNS = [
  r"rm\s+-rf",
  r"git\s+push\s+--force",
  r"git\s+push\s+-f",
  r"DROP\s+TABLE",
  r"DROP\s+DATABASE",
  r"TRUNCATE",
  r"ghe-config-apply",
]

def respond(decision: str, reason: str | None = None) -> None:
  payload = {"permissionDecision": decision}
  if reason:
    payload["reason"] = reason
  print(json.dumps(payload, ensure_ascii=False))

try:
  payload = json.load(sys.stdin)
  command = payload.get("input", {}).get("command", "")

  audit_log = pathlib.Path.home() / ".copilot" / "audit.log"
  audit_log.parent.mkdir(parents=True, exist_ok=True)

  for pattern in BLOCKED_PATTERNS:
    if re.search(pattern, command, flags=re.IGNORECASE):
      with audit_log.open("a", encoding="utf-8") as fh:
        fh.write(
          f"{dt.datetime.now().isoformat()} [BLOCKED] pattern={pattern!r} command={command[:200]!r}\n"
        )
      respond("deny", f"命令已被安全政策封鎖（匹配模式: {pattern}）。若確實需要，請改為人工執行並附上理由。")
      raise SystemExit(0)

  respond("allow")
except Exception as exc:
  respond("deny", f"Hook 腳本執行失敗，依 fail-safe 政策拒絕本次操作：{exc}")
```

若團隊只在單一平台運作，才考慮改寫為 `.ps1` 或 `.sh` 版本。

### 環境感知攔截（生產環境保護）

以下範例以 Bash 示意；若要支援 Windows，請改寫為 PowerShell 或 Python 版本。

```bash
#!/bin/bash
PAYLOAD=$(cat)
BRANCH=$(git rev-parse --abbrev-ref HEAD 2>/dev/null || echo "unknown")
COMMAND=$(echo "$PAYLOAD" | jq -r '.input.command // empty')

# 若在 main/master/production 分支，Git 寫入操作需人工確認
if [[ "$BRANCH" =~ ^(main|master|production)$ ]]; then
  if echo "$COMMAND" | grep -E "^git (push|reset|rebase|merge)" > /dev/null 2>&1; then
    echo "{\"permissionDecision\":\"ask\",\"reason\":\"你正在 $BRANCH 分支執行 Git 寫入操作，請確認。\"}"
    exit 0
  fi
fi

echo '{"permissionDecision":"allow"}'
```

---

## 模板

### 模板 A：危險命令防護（`preToolUse-guardrails.json`）

```json
{
  "hooks": {
    "PreToolUse": [
      {
        "type": "script",
        "command": "python .github/hooks/scripts/guardrails.py",
        "timeout": 5
      }
    ]
  }
}
```

對應 `.github/hooks/scripts/guardrails.py`：

```python
#!/usr/bin/env python3
import datetime as dt
import json
import pathlib
import re
import sys

BLOCKED_PATTERNS = [
    r"rm\s+-rf",
    r"git\s+push\s+--force",
    r"git\s+push\s+-f",
    r"DROP\s+TABLE",
    r"DROP\s+DATABASE",
    r"chmod\s+777",
    r"curl.*\|.*bash",
]

def respond(decision, reason=None):
    payload = {"permissionDecision": decision}
    if reason:
        payload["reason"] = reason
    print(json.dumps(payload, ensure_ascii=False))

try:
    payload = json.load(sys.stdin)
    command = payload.get("input", {}).get("command", "")
    audit_log = pathlib.Path.home() / ".copilot" / "audit.log"
    audit_log.parent.mkdir(parents=True, exist_ok=True)

    for pattern in BLOCKED_PATTERNS:
        if re.search(pattern, command, re.IGNORECASE):
            with audit_log.open("a", encoding="utf-8") as fh:
                fh.write(f"{dt.datetime.now().isoformat()} [BLOCKED] command={command[:200]!r} pattern={pattern!r}\n")
            respond("deny", f"命令已被安全政策封鎖（匹配模式: {pattern}）。若確實需要，請手動在終端執行並附上理由。")
            raise SystemExit(0)

    respond("allow")
except Exception as exc:
    respond("deny", f"Hook 腳本執行失敗，依 fail-safe 政策拒絕本次操作：{exc}")
```

---

### 模板 B：Session 初始化 Hook（`session-start.json`）

以下範例同樣以 Bash 示意；跨平台團隊可改用 Python / PowerShell 輸出相同 JSON 結構。

```json
{
  "hooks": {
    "SessionStart": [
      {
        "type": "script",
        "command": ".github/hooks/scripts/session-init.sh",
        "timeout": 10
      }
    ]
  }
}
```

對應 `.github/hooks/scripts/session-init.sh`：

```bash
#!/bin/bash
# 確認工作目錄正確
if [ ! -f ".github/copilot-instructions.md" ] && [ ! -f "AGENTS.md" ]; then
  echo '{"message":"警告：找不到 copilot-instructions.md 或 AGENTS.md，請確認是否在正確的專案根目錄。"}'
fi

# 顯示合規公告
echo '{"displayMessage":"⚠️ 合規提醒：本工作階段受 AcmeCorp 安全政策監控。禁止提交憑證或 PII 至 Git。"}'
```

---

### 模板 C：生產環境部署確認 Hook（`pre-deploy-check.json`）

此範例偏向 POSIX shell；若部署流程主要在 Windows 環境，請改寫腳本 runtime，並在腳本內自行檢查 `tool_name` / `tool_input`。

```json
{
  "hooks": {
    "PreToolUse": [
      {
        "type": "script",
        "command": ".github/hooks/scripts/prod-deploy-gate.sh",
        "timeout": 5
      }
    ]
  }
}
```

對應 `.github/hooks/scripts/prod-deploy-gate.sh`：

```bash
#!/bin/bash
PAYLOAD=$(cat)
COMMAND=$(echo "$PAYLOAD" | jq -r '.input.command // empty')
BRANCH=$(git rev-parse --abbrev-ref HEAD 2>/dev/null || echo "unknown")

if [[ "$BRANCH" != "main" ]] && [[ "$BRANCH" != "release/"* ]]; then
  echo "{\"permissionDecision\":\"deny\",\"reason\":\"部署命令只能從 main 或 release/* 分支執行。當前分支：$BRANCH\"}"
  exit 0
fi

echo "{\"permissionDecision\":\"ask\",\"reason\":\"即將部署至生產環境（分支：$BRANCH）。請確認此操作已通過 Change Advisory Board 審核。\"}"
```

---

## 使用範例

### 範例 1：防止 AI 刪除生產資料

**使用者需求**：「我擔心 Copilot Agent 在處理資料清理任務時，不小心刪除了生產資料庫的資料」

**設計方案**：
1. 設 `preToolUse` Hook 攔截所有 `bash` 工具呼叫
2. 偵測命令中是否包含 `DELETE` / `TRUNCATE` 並搭配 production DB 的 host/env 變數
3. 命中時返回 `"ask"`，要求使用者確認並提供 ticket 編號

---

### 範例 2：API Key 洩漏防護

**使用者需求**：「確保 Copilot 不會把 `.env` 檔案中的 API Key 提交到 Git」

**設計方案**：

```bash
#!/bin/bash
# postToolUse Hook：偵測 git add 後是否包含敏感檔案
PAYLOAD=$(cat)
COMMAND=$(echo "$PAYLOAD" | jq -r '.input.command // empty')

if echo "$COMMAND" | grep -E "git add" > /dev/null 2>&1; then
  STAGED=$(git diff --cached --name-only 2>/dev/null)
  SENSITIVE_FILES=(".env" ".env.local" ".env.production" "*.pem" "*.key" "secrets.yaml")
  
  for pattern in "${SENSITIVE_FILES[@]}"; do
    if echo "$STAGED" | grep -E "$pattern" > /dev/null 2>&1; then
      echo "{\"permissionDecision\":\"deny\",\"reason\":\"偵測到敏感檔案 ($pattern) 在 staging area。請先將其加入 .gitignore，再繼續操作。\"}"
      exit 0
    fi
  done
fi

echo '{"permissionDecision":"allow"}'
```
