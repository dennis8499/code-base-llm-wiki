---
title: "{scope} Business Analysis"
type: synthesis
summary: "{業務問題、目標價值、需求與主要證據缺口的一句話摘要}"
standards_profile: business-analysis-aligned-v1
coverage_status: partial
notebooklm_group: "business-{scope-slug}"
notebooklm_role: business
notebooklm_terms: ["{業務能力}", "{主要角色}", "{主要結果}"]
sources: []
derived_from: ["[[overview]]"]
last_updated: YYYY-MM-DD
tags: [synthesis, business-analysis, standards-aligned, notebooklm]
status: active
---

# {scope} Business Analysis

<!-- codebase-wiki:managed:start -->

## 文件控制

| 欄位 | 值 |
| --- | --- |
| 文件 ID／版本 | BA-{SCOPE}-001 / v1 |
| 範圍 | {scope} |
| 產出日期／證據基準日 | YYYY-MM-DD / YYYY-MM-DD |
| Owner／Reviewer | {owner-or-gap} / {reviewer-or-gap} |
| 標準 Profile | `business-analysis-aligned-v1` |
| 文件狀態／Coverage | active / covered · partial · gap |
| 變更摘要 | {change-summary} |

> 本文件為 standard-aligned，不代表 conformance、認證或稽核通過。

## 執行摘要

{Business problem, desired value, affected stakeholders, and the most material Gap.}

## 標準對照矩陣

| Profile reference | 對齊主題 | 本文件章節 | Coverage | Evidence／Gap |
| --- | --- | --- | --- | --- |
| ISO/IEC/IEEE 29148:2018 | stakeholder/business requirements and traceability | 能力與需求、追溯矩陣 | partial | {evidence-or-gap} |
| IIBA Business Analysis Standard v2.0 | context, value, stakeholders, change, needs | 業務脈絡、現況／目標、變更影響 | partial | {evidence-or-gap} |

## Coverage Map

| BA section | Status | Evidence／Gap ID |
| --- | --- | --- |
| Business context, problem, opportunity | partial | {evidence-or-gap} |
| Scope and outcomes | partial | {evidence-or-gap} |
| Stakeholders and needs | partial | {evidence-or-gap} |
| Current and target state | gap | `gap-{scope}-target-state` |
| Capabilities and requirements | partial | {cap/fr/ac-or-gap} |
| Business processes and rules | partial | {bp/br-or-gap} |
| Business information and glossary | partial | {evidence-or-gap} |
| Success measures | gap | `gap-{scope}-success-measures` |
| Risks, assumptions, constraints | partial | {evidence-or-gap} |
| Change impact and transition needs | gap | `gap-{scope}-change-impact` |

## 業務脈絡、問題與機會

{Evidence-backed current context; label inference and assumptions.}

## 範圍、目標與預期成果

### In scope

- {in-scope outcome}

### Out of scope

- {out-of-scope item}

## 利害關係人與 Needs

| Stakeholder／Actor | Need／Concern | Value／Outcome | Authority／Evidence | Status |
| --- | --- | --- | --- | --- |
| {actor} | {need} | {value} | {source-or-gap} | covered / partial / gap |

## 現況／目標狀態

| Dimension | Current state | Target state | Difference／Change | Evidence state |
| --- | --- | --- | --- | --- |
| {dimension} | {current} | {approved-target-or-gap} | {change} | business-confirmed / implementation-observed / inference / gap |

### Mermaid 槽位：現況／目標

> Gap: `gap-{scope}-current-target-diagram` — evidence insufficient; list the
> missing approved states/transitions instead of producing Mermaid.

## 能力、需求與驗收

| Capability ID | Business capability | Requirement ID | Acceptance IDs | Priority | Evidence state |
| --- | --- | --- | --- | --- | --- |
| `cap-*` | {capability} | `fr-*` | `AC-*` | {priority-or-gap} | {state} |

## 業務流程與規則

| Process ID | Actor／Trigger | Outcome | Applied Rule IDs | Coverage |
| --- | --- | --- | --- | --- |
| `bp-*` | {actor/trigger} | {outcome} | `br-*` | covered / partial / gap |

### Mermaid 槽位：業務流程

> Gap: `gap-{scope}-business-flow-diagram` — evidence insufficient; do not
> invent actors, steps, branches, or outcomes.

## Business Information 與詞彙

| Term／Information concept | Definition | Owner | Lifecycle／Rule | Evidence state |
| --- | --- | --- | --- | --- |
| {term} | {business-definition} | {owner-or-gap} | {state/rule-or-gap} | {state} |

## 成功指標與驗收方法

| Measure ID | Outcome／Metric | Baseline | Target／Timeframe | Measurement owner | Status |
| --- | --- | --- | --- | --- | --- |
| {metric-id} | {measure} | {baseline-or-gap} | {target-or-gap} | {owner-or-gap} | covered / partial / gap |

## Risks、Assumptions 與 Constraints

| ID | Type | Statement | Impact | Evidence／Owner | Status |
| --- | --- | --- | --- | --- | --- |
| {id} | risk / assumption / constraint | {statement} | {impact} | {evidence-or-gap} | open / confirmed / resolved |

## 變更影響與 Transition Needs

| Affected area | Current responsibility | Required change | Adoption／Migration need | Owner／Gap |
| --- | --- | --- | --- | --- |
| {role/process/data/policy} | {current} | {change} | {transition} | {owner-or-gap} |

## BA → SA 追溯矩陣

| Objective／Need | Capability | Process／Rule | Functional requirement | Acceptance | SA handoff／Gap |
| --- | --- | --- | --- | --- | --- |
| {objective} | `cap-*` | `bp-*` / `br-*` | `fr-*` | `AC-*` | {SA-ID-or-gap} |

## Gap Register

| Gap ID | Question／Contradiction | Affected IDs／Sections | Evidence checked | Suggested source／Stakeholder | Status |
| --- | --- | --- | --- | --- | --- |
| `gap-{scope}-{topic}` | {question} | {ids/sections} | {checked} | {target} | open |

## 來源附錄

- Wiki evidence: [[overview]], [[business-process-catalog]], [[business-rule-catalog]]
- Raw evidence: `{repo-relative-path}` or `Gap` when none was inspected
- Inference／speculation: {explicit list or none}

<!-- codebase-wiki:managed:end -->

<!-- codebase-wiki:user-notes:start -->
## BA 人工補充

<!-- 重新產出時保留本區全部內容。 -->
<!-- codebase-wiki:user-notes:end -->

<!-- notebooklm:local-only:start -->
## 本機追溯

- Reviewer paths／symbols: `{repo-relative-path-or-gap}`
- Detailed technical traceability: [[system-analysis]], [[system-design]]
<!-- notebooklm:local-only:end -->
