# 即貼即用元件模板彙整

本文件彙整所有 GitHub Copilot 擴展元件的完整模板，可直接複製使用。
每個模板後附有「快速客製化清單」，說明哪些欄位需要替換。

---

## 目錄

1. [Workspace Instructions 模板](#1-workspace-instructions-模板)
2. [File Instructions 模板](#2-file-instructions-模板)
3. [AGENTS.md 模板](#3-agentsmd-模板)
4. [Custom Agent 模板](#4-custom-agent-模板)
5. [Prompt File 模板](#5-prompt-file-模板)
6. [Hook 配置模板](#6-hook-配置模板)
7. [Agent Skill SKILL.md 模板](#7-agent-skill-skillmd-模板)

---

## 1. Workspace Instructions 模板

### `.github/copilot-instructions.md`

```markdown
# Copilot Instructions — PROJECT_NAME

## 技術背景 (WHAT)
- 語言/框架：LANGUAGE VERSION + FRAMEWORK VERSION
- 架構：ARCHITECTURE_TYPE（單體式/微服務/Monorepo）
- 主要依賴：DB_TYPE、CACHE_TYPE、MESSAGE_QUEUE（若有）
- 測試框架：TEST_FRAMEWORK

## 專案意圖 (WHY)
- 核心業務：BUSINESS_DOMAIN_DESC（1-2 句話）
- 設計優先順序：可讀性 > 效能 > 功能完整性
- 核心禁止行為：FORBIDDEN_PATTERN（如：Service 層不直接操作 DB）

## 工作流程 (HOW)
- 命名規範：CLASS_NAME_STYLE，FUNCTION_NAME_STYLE，CONST_NAME_STYLE
- 錯誤處理：ERROR_HANDLING_STRATEGY（如：所有外部 IO 包裝 try/catch）
- 日誌格式：參照 `LOG_FILE_PATH`，格式：LOG_FORMAT
- PR 規範：PR_TEST_REQUIREMENT（如：PR 需包含測試，覆蓋率 ≥ 80%）
```

**快速客製化清單**：
- `PROJECT_NAME` → 專案名稱
- `LANGUAGE VERSION + FRAMEWORK VERSION` → 如 `Python 3.12 + FastAPI 0.115`
- `ARCHITECTURE_TYPE` → 如 `微服務，透過 RabbitMQ 溝通`
- `BUSINESS_DOMAIN_DESC` → 如 `負責用戶認證與授權，不涉及業務邏輯`
- `FORBIDDEN_PATTERN` → 如 `Service 層一律透過 Repository 操作資料庫`
- `LOG_FILE_PATH` → 如 `src/core/logger.py`

---

## 2. File Instructions 模板

### `.github/instructions/PYTHON_API.instructions.md`

```markdown
---
applyTo: "src/api/**/*.py"
description: "Applies when editing Python API handlers under src/api."
---

# Python API File Instructions

## 適用範圍
- 只適用於 `src/api/**/*.py`

## 規則
- Endpoint 一律回傳明確的 response schema
- 路由層不直接操作 ORM session；透過 service 或 use case 層
- 驗證錯誤需轉成一致的 API error payload
- 若新增 endpoint，請同步更新對應的 OpenAPI / 測試
```

**快速客製化清單**：
- `applyTo` → 使用窄範圍 glob，不要直接用 `**`
- `description` → 補充這份檔案要處理的語境，讓 discovery 更穩定
- 規則內容 → 只寫這個 glob 真正獨有的規則，避免和 workspace instructions 重複

---

## 3. AGENTS.md 模板

```markdown
# AGENTS.md — PROJECT_NAME

## What（技術背景）
TECH_STACK_SUMMARY（2-3 句話，涵蓋語言、框架、部署環境）

## Why（專案意圖）
BUSINESS_GOAL_SUMMARY（2-3 句話，說明核心業務目標與設計哲學）

## How（工作流程規範）

### 程式碼規範
- 命名：CLASS_NAMING / FUNCTION_NAMING / CONST_NAMING
- 格式：INDENT_STYLE（如：2 spaces, Prettier v3 配置）
- 禁止：FORBIDDEN_PATTERNS（一行一條，盡量具體）

### 安全要求
- 不得將憑證（API Key、密碼、Token）寫入程式碼或 Git 歷史
- 所有使用者輸入必須通過驗證層（INPUT_VALIDATION_LAYER_PATH）
- 日誌中不得包含 PII；需在 MIDDLEWARE_PATH 進行脫敏處理

### 測試要求
- 新增功能需附帶單元測試
- 測試覆蓋率目標：COVERAGE_TARGET%
- 測試框架：TEST_FRAMEWORK

## 參考文件
- 架構圖：ARCHITECTURE_DOC_PATH
- API 規格：API_SPEC_PATH
- 貢獻指南：CONTRIBUTING_PATH
```

**快速客製化清單**：
- 所有 `UPPERCASE_PLACEHOLDER` 欄位依實際專案填入
- 若無對應項目，刪除該行（不要留空白值）
- 建議總行數控制在 60 行以內

---

## 4. Custom Agent 模板

### `.github/agents/AGENT_ROLE.agent.md`

```markdown
---
name: AGENT_IDENTIFIER
description: >
  PERSONA_DESCRIPTION（說明代理是誰、有什麼專業背景）.
  Use when TRIGGER_CONDITION_1 or TRIGGER_CONDITION_2.
  Only ALLOWED_ACTION — never FORBIDDEN_ACTION.
tools:
  - read_file
  - grep_search
  - file_search
  - semantic_search
  - get_errors
  # 取消註解以開放寫入工具（名稱依宿主環境而異）：
  # - <edit tool>   # 例如：apply_patch / editFiles / replace_string_in_file
  # - create_file
  # 不開放執行工具（唯讀代理不應有此權限）：
  # - run_in_terminal
---

# AGENT_DISPLAY_NAME

PERSONA_NARRATIVE（用「流動意識」風格描述代理的思考方式、工作哲學、優先考量）

## 工作框架

AGENT_WORKFLOW_STEP_1（說明代理在收到任務後如何思考）
AGENT_WORKFLOW_STEP_2
AGENT_WORKFLOW_STEP_3

## 禁止行為

此代理**不**執行以下操作：
- FORBIDDEN_ACTION_1
- FORBIDDEN_ACTION_2

## 輸出格式

STRUCTURED_OUTPUT_FORMAT

## 交接機制（若有多代理協作）

完成後輸出交接摘要：

### 交接摘要
- **完成事項**：[列表]
- **待解決問題**：[列表]
- **建議下一步**：轉交 `NEXT_AGENT_NAME`
```

**快速客製化清單**：
- `AGENT_IDENTIFIER` → kebab-case，如 `security-reviewer`
- `PERSONA_DESCRIPTION` → 第三人稱描述，說明角色與觸發條件
- `tools` → 依需求取消/加入工具；請改成目標宿主實際支援的 tool 名稱
- `PERSONA_NARRATIVE` → 第一人稱或敘述式，說明代理的思維方式
- `FORBIDDEN_ACTION` → 明確列出不做的事，增加可預測性

---

## 5. Prompt File 模板

### `.github/prompts/PROMPT_NAME.prompt.md`

```markdown
---
name: PROMPT_IDENTIFIER
description: >
  PROMPT_PURPOSE_DESC（說明用途與觸發方式）
mode: ask
---

ROLE_SETTING（可選，若任務需要特定專業知識則設定角色）

## 任務

TASK_DESCRIPTION（具體說明要做什麼、給誰用、產出什麼）

DYNAMIC_VARIABLE_SECTION：
${selection}
```
（或 `${file}`、`${input:variableName}`，依需求選擇）

## 輸出格式

OUTPUT_FORMAT_SPECIFICATION（說明格式要求、結構、驗收條件）

EXAMPLE_SECTION（可選，2-3 個示範性 input/output 範例）
```

**快速客製化清單**：
- `PROMPT_IDENTIFIER` → kebab-case，如 `pr-summary`、`generate-tests`
- `mode` → `ask`（分析/對話）、`edit`（直接改寫目前內容）或 `agent`（需要工具）
- 動態變量選擇：選取內容用 `${selection}`；整個檔案用 `${file}`；互動輸入用 `${input:xxx}`
- 若客戶端以檔名決定 slash command 名稱，請讓檔名與 `PROMPT_IDENTIFIER` 保持一致
- 若有固定格式要求，在「輸出格式」中提供完整模板（不要只用文字描述）

---

## 6. Hook 配置模板

### `.github/hooks/guardrails.json`（preToolUse 安全攔截）

```json
{
  "hooks": [
    {
      "event": "preToolUse",
      "matcher": {
        "tool": "bash"
      },
      "action": {
        "type": "script",
        "command": "python .github/hooks/scripts/guardrails.py",
        "timeout": 5
      }
    }
  ]
}
```

### `.github/hooks/scripts/guardrails.py`（黑名單防護腳本）

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
    r"TRUNCATE\s+TABLE",
    r"chmod\s+777",
    r"curl.*\|.*bash",
    r"wget.*\|.*sh",
]

def respond(decision, reason=None):
    payload = {"permissionDecision": decision}
    if reason:
        payload["reason"] = reason
    print(json.dumps(payload, ensure_ascii=False))

payload = json.load(sys.stdin)
command = payload.get("input", {}).get("command", "")

audit_log = pathlib.Path.home() / ".copilot" / "audit.log"
audit_log.parent.mkdir(parents=True, exist_ok=True)

for pattern in BLOCKED_PATTERNS:
    if re.search(pattern, command, re.IGNORECASE):
        with audit_log.open("a", encoding="utf-8") as fh:
            fh.write(f"{dt.datetime.now().isoformat()} [BLOCKED] pattern={pattern!r} command={command[:200]!r}\n")
        respond("deny", f"命令已被安全政策封鎖（模式: {pattern}）。若確實需要此操作，請在終端手動執行並附上變更原因。")
        raise SystemExit(0)

respond("allow")
```

### `.github/hooks/session-start.json`（Session 初始化）

```json
{
  "hooks": [
    {
      "event": "sessionStart",
      "action": {
        "type": "script",
        "command": ".github/hooks/scripts/session-init.sh",
        "timeout": 10
      }
    }
  ]
}
```

```bash
#!/bin/bash
# Session 初始化腳本 — 依需求客製化公告與驗證

# 驗證工作目錄
PROJECT_ROOT_INDICATOR="INDICATOR_FILE_OR_DIR"  # 替換為你的專案特徵檔案
if [ ! -e "$PROJECT_ROOT_INDICATOR" ]; then
  echo '{"message":"警告：請確認你在正確的專案根目錄中執行。"}'
fi

# 顯示合規公告（依組織政策修改）
echo '{"displayMessage":"COMPLIANCE_MESSAGE"}'
```

**快速客製化清單**：
- `BLOCKED_PATTERNS` → 依專案需求新增/移除禁止的命令模式
- 若團隊跨平台協作 → 優先維持 Python 版本；若只在單一平台運作，再改成 `.ps1` 或 `.sh`
- `AUDIT_LOG` → 修改審計日誌路徑（確保有寫入權限）
- `PROJECT_ROOT_INDICATOR` → 替換為確認工作目錄的特徵檔案（如 `pyproject.toml`、`package.json`）
- `COMPLIANCE_MESSAGE` → 替換為組織合規公告內容

---

## 7. Agent Skill SKILL.md 模板

### `.github/skills/SKILL_NAME/SKILL.md`

```markdown
---
name: SKILL_IDENTIFIER
description: >
  SKILL_DESCRIPTION_THIRD_PERSON.
  Use this skill whenever TRIGGER_CONDITION_1, TRIGGER_CONDITION_2,
  or TRIGGER_CONDITION_3.
  Invoke even when the user EDGE_TRIGGER_CONDITION.
---

# SKILL_DISPLAY_NAME

SKILL_VALUE_PROPOSITION（一句話說明此 Skill 的核心價值）

---

## 適用範圍

**適用**：
- APPLICABLE_SCENARIO_1
- APPLICABLE_SCENARIO_2
- APPLICABLE_SCENARIO_3

**不適用**：
- EXCLUSION_1 → 應使用 ALTERNATIVE_1
- EXCLUSION_2 → 應使用 ALTERNATIVE_2

---

## 輸入收集

執行前確認以下資訊（未提供時主動詢問）：
- **INPUT_REQUIREMENT_1**：REASON_WHY_NEEDED
- **INPUT_REQUIREMENT_2**：REASON_WHY_NEEDED

---

## 工作流程

1. **STEP_1_NAME**
   （原因：WHY_THIS_STEP_FIRST）

2. **STEP_2_NAME**
   若 CONDITION_A，執行 ACTION_A；若 CONDITION_B，載入 `references/RELEVANT_GUIDE.md`。

3. **STEP_3_NAME**

4. **STEP_4_NAME**
   套用 `assets/component-templates.md` 中的對應模板，填入收集到的資訊。

---

## 輸出格式

每次輸出都包含：

### OUTPUT_SECTION_1
OUTPUT_SECTION_1_DESC

### OUTPUT_SECTION_2
OUTPUT_SECTION_2_TEMPLATE_OR_FORMAT

---

## 參考資源

| 資源     | 路徑                             | 用途                   |
| -------- | -------------------------------- | ---------------------- |
| 詳細指南 | `references/DOMAIN_guide.md`     | 載入當前任務的深度說明 |
| 模板彙整 | `assets/component-templates.md`  | 即貼即用的完整模板     |
| 輔助腳本 | `scripts/SCRIPT_NAME.sh`（若有） | 可執行的自動化腳本     |
```

**快速客製化清單**：
- `SKILL_IDENTIFIER` → kebab-case，如 `reviewing-code`、`writing-migrations`
- `description` → 第三人稱，包含觸發關鍵詞，稍帶「積極」措辭（避免漏觸發）
- 所有 `UPPERCASE_PLACEHOLDER` → 依實際 Skill 的業務邏輯替換
- 適用/不適用範圍 → 明確排除案例，避免 Skill 被誤用
- 超過 500 行時 → 將詳細知識移至 `references/`，在 SKILL.md 中只保留路由邏輯

---

## 選用指南

| 你想要...                     | 使用元件               | 主要模板 |
| ----------------------------- | ---------------------- | -------- |
| 設定全域程式碼規範            | Workspace Instructions | 模板 1   |
| 只針對特定資料夾/語言套規則   | File Instructions      | 模板 2   |
| 跨 AI 工具共用指令            | AGENTS.md              | 模板 3   |
| 建立專業角色（如安全審計員）  | Custom Agent           | 模板 4   |
| 不重複輸入的任務快捷鍵        | Prompt File            | 模板 5   |
| 強制安全攔截（如防止 rm -rf） | Hook                   | 模板 6   |
| 封裝可攜帶的複雜工作流        | Agent Skill            | 模板 7   |
