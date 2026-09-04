---
title: "{scope} System Analysis"
type: synthesis
summary: "{系統邊界、stakeholder needs、可驗證需求與主要 Gap 的一句話摘要}"
standards_profile: system-analysis-aligned-v1
coverage_status: partial
notebooklm_group: "{scope-slug}-system-analysis"
notebooklm_role: traceability
sources: []
derived_from: ["[[overview]]"]
last_updated: YYYY-MM-DD
tags: [synthesis, system-analysis, standards-aligned]
status: active
---

# {scope} System Analysis

<!-- codebase-wiki:managed:start -->

## 文件控制

| 欄位 | 值 |
| --- | --- |
| 文件 ID／版本 | SA-{SCOPE}-001 / v1 |
| 系統／範圍 | {scope} |
| 產出日期／證據基準日 | YYYY-MM-DD / YYYY-MM-DD |
| Owner／Reviewer | {owner-or-gap} / {reviewer-or-gap} |
| 標準 Profile | `system-analysis-aligned-v1` |
| 文件狀態／Coverage | active / covered · partial · gap |
| 變更摘要 | {change-summary} |

> 本文件為 standard-aligned，不代表 conformance。SA 是
> solution-neutral；技術選型與部署設計屬於 SD／ADR。

## 摘要與分析範圍

{System purpose, analysis boundary, principal stakeholder need, and key Gap.}

### In scope

- {externally observable system behavior or information boundary}

### Out of scope

- {solution component, technology, or deployment decision}

## 標準對照矩陣

| Profile reference | 對齊主題 | 本文件章節 | Coverage | Evidence／Gap |
| --- | --- | --- | --- | --- |
| ISO/IEC/IEEE 29148:2018 | stakeholder/system requirements and traceability | Needs、SR/NFR/IF、追溯 | partial | {evidence-or-gap} |
| ISO/IEC/IEEE 15288:2023 | stakeholder needs, system requirements, V&V concerns | 情境、需求、驗證需求 | partial | {evidence-or-gap} |
| ISO/IEC 25010:2023 | product quality model | Quality requirements | partial | {evidence-or-gap} |

## Coverage Map

| SA section | Status | Evidence／Gap ID |
| --- | --- | --- |
| Purpose, scope, system boundary | partial | {evidence-or-gap} |
| Stakeholders, actors, needs | partial | {evidence-or-gap} |
| Assumptions, constraints, dependencies | partial | {evidence-or-gap} |
| Use cases and operational scenarios | partial | {evidence-or-gap} |
| Functional system requirements | partial | {SR-or-gap} |
| External interface requirements | partial | {IF-or-gap} |
| Quality requirements | gap | `gap-{scope}-quality-targets` |
| Conceptual information model and flow | partial | {evidence-or-gap} |
| Failure and exceptional behavior | partial | {evidence-or-gap} |
| Verification and validation needs | partial | {evidence-or-gap} |
| Traceability and unresolved gaps | partial | {evidence-or-gap} |

## Stakeholders、Actors 與 Needs

| Stakeholder／Actor | Need／Concern | Upstream BA ID／Gap | Priority／Authority | Coverage |
| --- | --- | --- | --- | --- |
| {actor} | {need} | `cap-*` / `fr-*` / `gap-*` | {evidence-or-gap} | covered / partial / gap |

## 系統邊界與 Context

| External actor/system | Relationship／Exchanged information | Boundary assumption | Evidence／Gap |
| --- | --- | --- | --- |
| {external-party} | {interaction} | {assumption} | {evidence-or-gap} |

### Mermaid 槽位：系統脈絡

> Gap: `gap-{scope}-context-diagram` — evidence insufficient; do not invent
> actors, external systems, or relationships.

## Assumptions、Constraints 與 Dependencies

| ID | Kind | Statement | Source／Authority | Affected requirements |
| --- | --- | --- | --- | --- |
| {id} | assumption / constraint / dependency | {statement} | {evidence-or-gap} | {SR/NFR/IF-or-gap} |

## Use Cases 與 Operational Scenarios

| Use case | Primary actor | Trigger／Precondition | Observable result | Alternate／Failure | Upstream ID |
| --- | --- | --- | --- | --- | --- |
| {use-case} | {actor} | {trigger/precondition} | {result} | {alternate/failure} | `bp-*` / `fr-*` / `AC-*` |

### Mermaid 槽位：主要情境

> Gap: `gap-{scope}-scenario-diagram` — evidence insufficient; do not invent
> participants, messages, or branches.

## Functional System Requirements

| Requirement ID | Shall statement | Rationale | Upstream BA／Gap | Verification method | Coverage |
| --- | --- | --- | --- | --- | --- |
| `SR-{SCOPE}-NNN` | The system shall {observable behavior}. | {why} | `fr-*` / `AC-*` / `gap-*` | test / analysis / inspection / demonstration | covered / partial / gap |

## External Interface Requirements

| Interface ID | External party | Information／Event | Behavioral contract | Error／Timing need | Upstream／Verification |
| --- | --- | --- | --- | --- | --- |
| `IF-{SCOPE}-NNN` | {party} | {input/output} | {solution-neutral semantics} | {need-or-gap} | {BA-ID-or-gap} / {method} |

## Quality Requirements

| Requirement ID | ISO/IEC 25010 characteristic | Condition | Measure／Target | Rationale | Verification／Gap |
| --- | --- | --- | --- | --- | --- |
| `NFR-{SCOPE}-NNN` | {quality-characteristic} | {condition} | {measurable-target-or-gap} | {why} | {method-or-gap} |

## Conceptual Information Model and Flow

| Information concept | Meaning／Owner | Input source | Consumer／Outcome | Lifecycle／Rule | Evidence state |
| --- | --- | --- | --- | --- | --- |
| {concept} | {business meaning/owner} | {source} | {consumer/outcome} | {lifecycle/rule} | confirmed / observed / inference / gap |

> Describe concepts and observable information movement only. Storage engines,
> schemas, partitions, and physical models belong to SD.

## Failure and Exceptional Behavior

| Failure／Condition | Detection need | Externally visible response | Recovery／Continuity need | Requirement／Gap |
| --- | --- | --- | --- | --- |
| {failure} | {detection} | {response} | {recovery-need} | {SR/NFR/IF-or-gap} |

## Verification and Validation Needs

| SA ID | Verification method | Required evidence | Acceptance／Success relation | Owner／Gap |
| --- | --- | --- | --- | --- |
| `SR/NFR/IF-{SCOPE}-NNN` | test / analysis / inspection / demonstration | {evidence} | `AC-*` / {business outcome} | {owner-or-gap} |

## BA → SA 追溯矩陣

| BA objective／ID／Gap | SA ID | Requirement type | Scenario／Interface | Verification | Coverage |
| --- | --- | --- | --- | --- | --- |
| `cap-*` / `fr-*` / `bp-*` / `br-*` / `AC-*` / `gap-*` | `SR/NFR/IF-{SCOPE}-NNN` | functional / quality / interface | {scenario/interface} | {method} | covered / partial / gap |

## Gap Register

| Gap ID | Question／Contradiction | Affected IDs／Sections | Evidence checked | Suggested source／Stakeholder | Status |
| --- | --- | --- | --- | --- | --- |
| `gap-{scope}-{topic}` | {question} | {ids/sections} | {checked} | {target} | open |

## 來源附錄

- Wiki evidence: [[business-analysis]], [[overview]]
- Raw evidence: `{repo-relative-path}` or `Gap` when none was inspected
- Explicit inferences: {list-or-none}

<!-- codebase-wiki:managed:end -->

<!-- codebase-wiki:user-notes:start -->
## SA 人工補充

<!-- 重新產出時保留本區。首次重跑 legacy SA 時，把完整原正文逐字放在本區。 -->
<!-- codebase-wiki:user-notes:end -->

<!-- notebooklm:local-only:start -->
## 本機追溯

- Reviewer paths／symbols: `{repo-relative-path-or-gap}`
- Downstream design handoff: [[system-design]]
<!-- notebooklm:local-only:end -->
