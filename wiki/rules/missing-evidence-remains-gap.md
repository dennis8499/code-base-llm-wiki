---
title: 缺少證據必須保留為 Gap
type: business-rule
summary: BA／SA／SD 在上游或證據不足時仍產出，但必須建立可追溯 Gap，禁止以推測補滿文字或 Mermaid
rule_id: br-analysis-missing-evidence-gap
applies_to: ["[[generate-analysis-document]]"]
evidence_state: business-confirmed
notebooklm_group: business-analysis-documents
notebooklm_role: business
notebooklm_terms: [Gap, 證據不足, 不臆造, coverage, Mermaid, 上游缺失, 待確認]
sources:
  - .agents/skills/codebase-wiki/references/analysis-document-standards.md
  - .agents/skills/codebase-wiki/references/business-analysis-workflow.md
  - .agents/skills/codebase-wiki/references/system-analysis-workflow.md
  - .agents/skills/codebase-wiki/references/system-design-workflow.md
source_digest: sha256:035285ae5e891e49038ed713bfca27f525f440c6d56ff8c04833af7727bc77c3
derived_from: ["[[generate-analysis-document]]"]
last_updated: 2026-09-04
tags: [business-rule, evidence, gap, standards-aligned, notebooklm]
status: active
---

# 缺少證據必須保留為 Gap

<!-- codebase-wiki:managed:start -->

## 規則

文件產出不能因 BA／SA 上游缺失或局部證據不足而靜默中止；也不能用 plausible
content 補滿。系統必須保留必要章節、coverage row 與 diagram slot，建立穩定
`gap-{scope}-{topic}`，並說明問題、影響 IDs／章節、已查 evidence、建議來源／
stakeholder 及狀態。

## 適用條件

- BA 缺少 actor、policy、target state、KPI、process、rule 或 change impact。
- SA 缺少 BA objective/ID、interface semantics、measurable NFR 或 V&V evidence。
- SD 缺少 SA driver、decision authority、component/runtime/data/deployment/security evidence。
- 任何 Mermaid node、edge、message、state 或 trust boundary 無可靠來源。

## Coverage 處置

| Evidence state | Document behavior | Coverage |
| --- | --- | --- |
| 全部核心 evidence 足夠且一致 | 產出 supported content/diagram | covered |
| 核心可用、局部缺失 | 產出內容並保留 open Gap | partial |
| 核心 baseline 無法可信建立 | 產出 Gap-oriented document，不宣稱 baseline 完成 | gap |

`status: active` 只表示頁面 freshness，不會把 `partial` 或 `gap` 自動升成 covered。

## Gap 關閉

Gap 關閉時保留 ID 與原問題，補上 resolution、authority、evidence、日期與受影響
traceability rows。不得刪除歷史 Gap 來營造完整 coverage。

## 驗收

- `AC-RULE-GAP-001`：缺少 BA 仍可產出 SA，缺少 SA 仍可產出 SD。
- `AC-RULE-GAP-002`：沒有 diagram evidence 時只顯示 Gap，不產生 Mermaid code block。
- `AC-RULE-GAP-003`：每個 Gap 都有具體 follow-up target，不使用無法執行的「待補」空話。

<!-- codebase-wiki:managed:end -->

<!-- codebase-wiki:user-notes:start -->
## 業務補充

目前無人工補充。
<!-- codebase-wiki:user-notes:end -->

<!-- notebooklm:local-only:start -->
## 本機追溯

- Workflow contracts：`.agents/skills/codebase-wiki/references/*-analysis-workflow.md`、
  `.agents/skills/codebase-wiki/references/system-design-workflow.md`
<!-- notebooklm:local-only:end -->
