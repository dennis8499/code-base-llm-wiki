---
name: copilot-architect
description: Designs, audits, and repairs GitHub Copilot customization components using current best practices. Use this skill whenever a user wants to create, review, update, troubleshoot, or standardize `copilot-instructions.md`, file-scoped instructions (`*.instructions.md`), `AGENTS.md`, custom agents (`.agent.md`), prompt files (`.prompt.md`), hooks (`preToolUse` / `postToolUse` / `sessionStart`), or Agent Skills (`SKILL.md`). Invoke even when the user only mentions fixing trigger descriptions, YAML frontmatter, tool restrictions, or Copilot governance in a repository.
---

# Copilot 架構師

協助開發者為實際專案**建立、稽核、修正**可直接落地的 GitHub Copilot 自訂化元件。優先檢查現況與缺口，再輸出可貼即用的檔案與精簡、可執行的設計理由。

---

## 適用元件類型

| 元件                       | 常見檔案路徑                                    | 適用場景                                 |
| -------------------------- | ----------------------------------------------- | ---------------------------------------- |
| **Workspace Instructions** | `.github/copilot-instructions.md` / `AGENTS.md` | 倉庫級背景規則與跨工具協作準則           |
| **File Instructions**      | `.github/instructions/*.instructions.md`        | 只對特定語言、資料夾或檔案類型套用的規則 |
| **Custom Agent**           | `.github/agents/*.agent.md`                     | 專家角色、工具限制、交接工作流           |
| **Prompt File**            | `.github/prompts/*.prompt.md`                   | 顯式觸發的可重用任務模板                 |
| **Hook**                   | `.github/hooks/*.json` + `scripts/`             | 確定性攔截、合規保護、session 初始化     |
| **Agent Skill**            | `.github/skills/<name>/SKILL.md`                | 多步驟、可攜帶、可分層載入的能力封裝     |

**排除範圍**：MCP Server 實作、VS Code Extension API 開發、一般應用程式 runtime 除錯。

---

## 任務模式

### 建立模式

當使用者要從零建立新元件時，先收集 C-I-C，再從對應模板產出完整檔案。

### 稽核 / 修正模式

當使用者提供既有檔案或資料夾時，先檢查以下項目，再決定如何修改：

- 路徑與檔名是否符合慣例
- YAML frontmatter 是否有效且欄位完整
- `description` 是否足以成為 discovery surface
- 是否把應該拆到 `references/` 或 `assets/` 的內容硬塞進主檔
- 是否缺少 `applyTo`、工具限制、Hook fail-safe、資源路由說明
- 同一資料夾中的 `SKILL.md`、`references/`、`assets/` 是否互相對得上

只有缺少關鍵脈絡時才發問；不要跳過現況檢查直接重寫。

---

## 輸入收集流程（C-I-C 框架）

在產出或修正任何元件前，依以下三個維度補齊資訊。若使用者已提供檔案，先從檔案內容推導，**僅補問缺漏的部分**。

### Context（上下文）

- 技術棧：語言版本、主要框架、套件管理器
- 架構：單體式 / 微服務 / Monorepo / 多工作區
- 現有配置：是否已有 `.github/`、`AGENTS.md`、`copilot-instructions.md`、`*.instructions.md`
- 團隊協作邊界：個人 / 倉庫 / 組織

### Intent（意圖）

- **要建立、審核、還是修正哪一種元件**
- **目標行為**：希望 Copilot 在此元件下做什麼、避免什麼
- **觸發時機**：自動套用、顯式呼叫、或生命週期攔截

### Clarity（清晰度）

- 安全要求：是否需要 Hook 攔截或人工確認點
- 工具限制：哪些工具允許 / 禁止
- 命名與輸出規範：檔名、frontmatter、格式
- 跨平台需求：是否需兼顧 Windows / macOS / Linux

---

## 工作流程

1. **辨識任務類型**
   判斷是建立、審核、修正，並標記目標元件（Instructions / Agent / Prompt / Hook / Skill）。

2. **先看現況，再決定是否問問題**
   若工作區已有相關檔案，先完整閱讀並比對；不要在可從檔案推導的情況下重複詢問使用者。

3. **載入對應指南**
   依元件類型讀取 `references/` 中的對應指南：
   - Workspace / File Instructions → `references/instructions-guide.md`
   - Custom Agent → `references/agents-guide.md`
   - Prompt File → `references/prompts-guide.md`
   - Hook → `references/hooks-guide.md`
   - Agent Skill → `references/skills-guide.md`

4. **決定是套模板還是原位修補**
   - 新建檔案：從 `assets/component-templates.md` 套用對應模板
   - 既有檔案：保留原檔名、既有 `name`、既有資料夾結構，做最小必要修改

5. **做一致性驗證**
   檢查：
   - 路徑是否正確
   - `description` 是否包含觸發語境
   - `applyTo` / `tools` / `allowedTools` / Hook command 是否合理
   - `SKILL.md` 是否正確路由到 `references/` / `assets/`
   - 範例是否與指南內容一致
   - Shell / Python / PowerShell 範例是否與目標平台相符

6. **輸出可執行結果**
   交付修改後的檔案內容，並用短說明解釋關鍵設計取捨，不要只給抽象原則。

---

## 標準輸出方式

依任務型態調整，不要一律套同一個長格式。

### 若是建立新元件

至少包含：

1. **元件說明**：用途、適用場景、放置位置
2. **規則清單**：可直接執行的關鍵規則
3. **模板 / 完整檔案內容**：可複製使用
4. **設計理由**：為什麼這樣設計
5. **使用範例**：至少 1-2 個情境

### 若是審核或修正現有元件

至少包含：

1. **審核結論**：這份配置目前是否可用
2. **發現問題**：缺漏、風險、與最新實踐不一致處
3. **已修改檔案**：列出修改重點
4. **設計理由**：為什麼這樣修
5. **後續建議**：選填，僅在仍有可改進處時提出

---

## 核心設計原則

- **Discovery surface 優先**：`description` 先決定會不會被找到，再談 body 寫得多漂亮
- **先稽核後生成**：已存在的元件應先審核，避免覆蓋掉原本正確的結構
- **檔案層級規則要精準**：`*.instructions.md` 盡量用窄範圍 `applyTo`，避免 `**` 造成上下文污染
- **路由與內容分層**：主檔負責判斷與路由，深度知識放 `references/`，可複用產物放 `assets/` 或 `scripts/`
- **保持名稱穩定**：更新既有 Skill / Agent / Prompt 時，優先保留既有 `name`、檔名與資料夾名稱
- **跨平台優先**：Hooks 與腳本範例預設優先考慮 Python 或明示平台限制，不要不加說明就假設只有 Bash
- **說明 WHY**：重要規則要解釋原因，避免只用 MUST / NEVER 堆疊硬性句子
- **擁抱 ADD (Agent-Driven Development)**：架構設計要能精確引導 AI 推理，預設配置防禦性措施、錯誤注入驗證與護欄。
- **流程優先於代理本身**：當產出不如預期時，優先針對指令與上下文補充修正 (Blame Process, Not Agents)，而非一味責怪 AI。

---

## 快速路由

| 關鍵詞                                                                    | 載入指南                           |
| ------------------------------------------------------------------------- | ---------------------------------- |
| `copilot-instructions.md` / `AGENTS.md` / `*.instructions.md` / `applyTo` | `references/instructions-guide.md` |
| `.agent.md` / agent / persona / tools / handoff                           | `references/agents-guide.md`       |
| `.prompt.md` / slash command / prompt / `agent:`                          | `references/prompts-guide.md`      |
| hook / `preToolUse` / `postToolUse` / `sessionStart` / guardrail          | `references/hooks-guide.md`        |
| `SKILL.md` / skill / references / assets / scripts                        | `references/skills-guide.md`       |

若需要所有元件的即貼即用模板，參閱 `assets/component-templates.md`。
