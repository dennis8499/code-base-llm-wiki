---
name: business-analysis-doc
description: >
  基於 Codebase LLM Wiki 產生 standard-aligned BA 業務分析文件，保留人工註記並明列 Gap。
agent: "agent"
argument-hint: "可選：範圍，例如：整體系統、訂單取消、會員管理"
---

## 任務

產出一份繁中 Markdown Business Analysis 文件。

**分析範圍**：${input:scopeName:整體系統}

## 流程

1. 完整載入 `.agents/skills/codebase-wiki/references/business-analysis-workflow.md`、
   `.agents/skills/codebase-wiki/references/analysis-document-standards.md` 與
   `.agents/skills/codebase-wiki/assets/business-analysis-template.md`。
2. 讀取 `wiki/index.md`、近期 `wiki/log.md`、overview、requirements、processes、
   rules、glossary 與 gaps；Wiki 不足、stale 或矛盾時才唯讀回溯 raw sources。
3. 依 `business-analysis-aligned-v1` 建立 standards matrix、coverage map、
   `cap-*`／`fr-*`／`bp-*`／`br-*`／`AC-*` 追溯與具體 Gap。
4. 有證據才產出業務流程與現況／目標 Mermaid；否則保留槽位並寫 Gap。
5. 整體系統寫入 `wiki/synthesis/business-analysis.md`；指定範圍寫入
   `wiki/synthesis/{kebab-scope}-business-analysis.md`。
6. 只重建 managed block，保留 user-notes，技術 path／symbol 放 local-only。
7. 更新 `wiki/index.md`，並在 `wiki/log.md` 追加一筆 `synthesis` 記錄。

## 品質要求

- Frontmatter 必須有 `standards_profile: business-analysis-aligned-v1`、
  `coverage_status` 與 `notebooklm_role: business`。
- `sources` 只列真實 raw source 路徑；Wiki 證據放 `derived_from`；無 raw
  evidence 時使用 `sources: []`。
- 不得編造 stakeholder、政策、KPI、target state、流程或需求；證據不足仍產出
  文件並登錄 Gap。
- 完成前執行 frontmatter、stale、index、log 與 lint 檢查。
