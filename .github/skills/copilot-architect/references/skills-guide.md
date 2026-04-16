# Agent Skills 設計指南

## 適用場景

Agent Skill（`SKILL.md`）適合將**可攜帶、可重用的工作流**封裝成模組，特別是：

| 情境             | 說明                                                  |
| ---------------- | ----------------------------------------------------- |
| 多步驟工作流     | 需要判斷、分支、迭代的複雜任務                        |
| 帶腳本的自動化   | 需要執行外部腳本（Python、Bash）的能力                |
| 跨工具遷移       | 在 VS Code、Copilot CLI、雲端代理之間共用             |
| 可分享的最佳實踐 | 組織內標準化、可在支援 Skill 發現的工作區中共享與分發 |

**與 Instructions 的差異**：Instructions 是「始終開啟的背景規則」；Skills 是「按需加載的專業能力」。

---

## 目錄結構規範

```
.github/skills/<skill-name>/
├── SKILL.md            ← 必填：YAML frontmatter + 核心指令
├── scripts/            ← 選配：可執行的自動化腳本
│   └── *.sh / *.py
├── references/         ← 選配：靜態參考文件（API 指南、架構說明）
│   └── *.md
└── assets/             ← 選配：輸出模板、圖示、字型
    └── *.md / *.json
```

---

## YAML Frontmatter 規格

```yaml
---
name: skill-name                 # kebab-case，必填，唯一識別符
description: >                   # 觸發條件 + 功能說明，必填
  ...
compatibility:                   # 選填：工具/環境依賴
  tools:
    - bash
    - python3
---
```

### `name` 命名規則
- 使用 **kebab-case**（小寫 + 連字號）
- 使用動名詞或能力名稱：`reviewing-prs`、`writing-tests`、`deploying-services`
- 避免空泛名稱：`helper`、`utils`、`tools`

### `description` 觸發最佳化
`description` 是 Copilot 判斷「是否載入此 Skill」的核心依據：

```
✓ 說清楚「做什麼」AND「何時使用」
✓ 包含具體觸發關鍵詞
✓ 輕微「積極」措辭（讓 Skill 不會被漏觸發）
✓ 1024 字元以內
✗ 不要把實作細節塞進 description
✗ 不要使用 XML 標籤
✗ 不要以「我可以幫你...」開頭（用第三人稱）
```

**好的 description 範例**：
```
Generates production-ready test suites for Python services using pytest.
Use this skill whenever a user needs to write unit tests, integration tests,
add test coverage, mock external dependencies, or improve test quality.
Invoke even when the user mentions "tests" casually or asks to "cover" existing code.
```

---

## 規則清單

1. **500行限制**：理想 SKILL.md 保持 500 行以內，超過時將詳細知識移至 `references/`。
2. **漸進式披露**：metadata（name+description）→ SKILL.md body → references → scripts，按需加載。
3. **路由邏輯分離**：SKILL.md 只做「判斷和路由」，具體指南放 references/。
4. **說明 WHY**：每個重要步驟都說明「為什麼這樣做」，勝過死板的 MUST/NEVER。
5. **腳本複用**：若多個 test case 輸出相似的 helper 腳本，就將其固化在 `scripts/` 中。
6. **description 積極策略**：description 略帶「推送性」，避免 Copilot 漏觸發。
7. **更新時保持穩定**：修正既有 Skill 時，優先保留資料夾名稱、`name` frontmatter 與既有資源結構，只做最小必要修改。

---

## 撰寫指南

### 三層加載架構設計

```
Layer 1: metadata（name + description）
  ← 始終在上下文中，決定 Skill 是否被選用
  ← 約 100 字，只放「觸發所需的高信號資訊」

Layer 2: SKILL.md body（<500行）
  ← Skill 被選用後載入，包含：
     • 適用範圍（Scope）
     • 工作流程（Workflow）
     • 輸出格式規格（Output Spec）
     • 指向 references/ 的說明

Layer 3: references/ 和 scripts/（無限制）
  ← 依任務按需載入或執行
  ← 大型參考文件（>300行）須有目錄（TOC）
```

### 多領域技能的組織方式

當 Skill 需要支援多種框架/語言時，**不要把所有框架塞進 SKILL.md**：

```
cloud-deploy/
├── SKILL.md          ← 工作流 + 選擇邏輯（判斷部署目標）
└── references/
    ├── aws.md        ← AWS 專屬指令
    ├── gcp.md        ← GCP 專屬指令
    └── azure.md      ← Azure 專屬指令
```

SKILL.md 中的路由邏輯：
```markdown
若部署目標是 AWS，載入 `references/aws.md` 並依其指引操作。
若部署目標是 GCP，載入 `references/gcp.md`。
```

### 更新既有 Skill 的原則

- 先檢查 `description` 是否真的描述了「做什麼 + 何時使用」
- 再檢查 `SKILL.md` 是否只保留高頻路由邏輯
- 最後檢查 `references/`、`assets/`、`scripts/` 是否有被主檔正確引用
- 若既有名稱已被團隊使用，除非必要，不要任意改 Skill 名稱或資料夾名稱

### 什麼時候加 scripts/

當觀察到以下情況時，表示需要將邏輯固化為腳本：
- 多次迭代中，模型都「重新撰寫」相同的 helper function
- 任務涉及大量資料處理或計算，用自然語言難以精確描述
- 需要確定性執行（固定輸出）的步驟

---

## 模板

### 模板 A：標準 SKILL.md 骨架

```markdown
---
name: skill-name
description: >
  [功能描述，第三人稱] [觸發條件，包含具體關鍵詞].
  Use this skill whenever [觸發情境 1] or [觸發情境 2].
  Invoke even when the user [邊緣觸發條件].
---

# [Skill 名稱]

[一句話說明這個 Skill 的核心價值]

---

## 適用範圍

**適用**：[列出 3-5 個具體使用情境]
**不適用**：
- [排除情境 1] → 應使用 [alternative]
- [排除情境 2] → 應直接 [alternative action]

---

## 輸入收集

在執行前，確認以下資訊已具備（若無，主動詢問）：
- **[資訊 1]**：[說明為何需要]
- **[資訊 2]**：[說明為何需要]

---

## 工作流程

1. **[步驟 1]**
   （原因：[為什麼先做這步]）

2. **[步驟 2]**
   若 [條件 A]，執行 [行動 A]；若 [條件 B]，載入 `references/[guide].md`。

3. **[步驟 3]**

---

## 輸出格式

每次輸出都包含：

### [輸出節 1]
[說明包含什麼]

### [輸出節 2]
[格式規格或模板]

---

## 參考資源

- 詳細指南：`references/[domain]-guide.md`
- 可用模板：`assets/[template].md`
- 輔助腳本：`scripts/[script].sh`（若有）
```

---

### 模板 B：帶 scripts/ 的資料處理 Skill 骨架

````markdown
---
name: data-transformer
description: >
  Transforms and validates structured data files (CSV, JSON, YAML)
  following project schema conventions. Use whenever a user needs to
  convert data formats, validate against schemas, or batch-process records.
compatibility:
  tools:
    - python3
    - bash
---

# 資料轉換工具

---

## 工作流程

1. 識別來源格式（CSV / JSON / YAML）
2. 執行驗證腳本：

   ```bash
   python scripts/validate_schema.py --input <file> --schema <schema-file>
   ```

3. 若驗證通過，執行轉換：

   ```bash
   python scripts/transform.py --input <file> --output-format <format>
   ```

4. 輸出轉換結果與驗證報告

---

## 腳本說明

`scripts/validate_schema.py`：
- 輸入：`--input`（來源檔案）、`--schema`（JSON Schema 檔案）
- 輸出：驗證報告（stdout）；失敗時 exit code 1

`scripts/transform.py`：
- 輸入：`--input`、`--output-format`（csv / json / yaml）
- 輸出：轉換後的檔案（同目錄，副檔名變更）
````

---

## 使用範例

### 範例 1：程式碼審查 Skill

**情境**：建立一個 PR 程式碼審查 Skill，依照 SOLID 原則和安全規範輸出結構化審查報告

**YAML frontmatter 設計**：

```yaml
---
name: reviewing-prs
description: >
  Performs structured code reviews against SOLID principles, security
  best practices (OWASP Top 10), and project coding conventions.
  Use whenever a user wants to review code, audit a PR, check for
  code quality issues, or get feedback on implementation. Invoke even
  when the user casually asks to "look at my code" or "check this PR".
---
```

**關鍵設計決策**：
- description 包含「casually asks」的容錯說明 → 避免因不精確措辭而漏觸發
- references/ 中分別放 `solid-guide.md`（SOLID 規則說明）和 `owasp-quick-ref.md`（OWASP 快速參考）

---

### 範例 2：從 Iteration 到固化腳本

**情境**：資料庫查詢最佳化 Skill，反覆測試時發現模型每次都重寫相同的 `explain_analyzer.py`

**解法**：
1. 將每次生成的 `explain_analyzer.py` 整理為標準版本
2. 放入 `scripts/explain_analyzer.py`
3. 在 SKILL.md 中直接引用：
   ```markdown
   分析查詢效能：
   ```bash
   python scripts/explain_analyzer.py --query "<SQL>" --db-url $DATABASE_URL
   ```
   ```

**效果**：未來每次觸發此 Skill，模型可直接使用既有腳本，不需重新撰寫。
