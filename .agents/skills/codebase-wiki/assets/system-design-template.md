---
title: "{scope} System Design"
type: synthesis
summary: "{architecture decisions, principal views, quality strategy, and design Gaps}"
standards_profile: system-design-aligned-v1
coverage_status: partial
notebooklm_group: "{scope-slug}-system-design"
notebooklm_role: traceability
sources: []
derived_from: ["[[system-analysis]]"]
last_updated: YYYY-MM-DD
tags: [synthesis, system-design, standards-aligned]
status: active
---

# {scope} System Design

<!-- codebase-wiki:managed:start -->

## 文件控制

| 欄位 | 值 |
| --- | --- |
| 文件 ID／版本 | SD-{SCOPE}-001 / v1 |
| 系統／範圍 | {scope} |
| 產出日期／證據基準日 | YYYY-MM-DD / YYYY-MM-DD |
| Owner／Reviewer | {owner-or-gap} / {reviewer-or-gap} |
| 標準 Profile | `system-design-aligned-v1` |
| 文件狀態／Coverage | active / covered · partial · gap |
| 變更摘要 | {change-summary} |

> 本文件為 standard-aligned，不代表 conformance。IEEE 1016-2009 只作
> informative 歷史組織參考；現行 architecture-description basis 為
> ISO/IEC/IEEE 42010:2022。

## Architecture Summary、Scope 與 Design Drivers

{Design scope, approved approach, critical SA requirements, and largest Gap.}

| Driver | Upstream SA ID／Gap | Design consequence | Priority／Risk |
| --- | --- | --- | --- |
| {driver} | `SR/NFR/IF-{SCOPE}-NNN` / `gap-*` | {consequence} | {priority/risk} |

## 標準對照矩陣

| Profile reference | 對齊主題 | 本文件章節 | Coverage | Evidence／Gap |
| --- | --- | --- | --- | --- |
| ISO/IEC/IEEE 42010:2022 | stakeholders, concerns, viewpoints, views, correspondences, decisions | Concerns、View Catalog、Design Decisions | partial | {evidence-or-gap} |
| ISO/IEC 25010:2023 | quality characteristics and strategy | Quality Strategy | partial | {evidence-or-gap} |
| IEEE 1016-2009 (informative) | historical SDD organization | document navigation only | partial | not a conformance basis |

## Coverage Map

| SD section | Status | Evidence／Gap ID |
| --- | --- | --- |
| Architecture scope and design drivers | partial | {evidence-or-gap} |
| Stakeholders and concerns | partial | {evidence-or-gap} |
| Viewpoints, views, correspondences | partial | {VIEW-or-gap} |
| Architecture decisions and rationale | partial | {DE/ADR-or-gap} |
| Component/static structure | partial | {evidence-or-gap} |
| Runtime behavior | partial | {evidence-or-gap} |
| Data design | partial | {evidence-or-gap} |
| Interface design | partial | {evidence-or-gap} |
| Deployment and operations | gap | `gap-{scope}-deployment` |
| Security architecture | gap | `gap-{scope}-security-view` |
| Quality strategies | gap | `gap-{scope}-quality-strategy` |
| Traceability, risks, and Gaps | partial | {evidence-or-gap} |

## Stakeholders and Concerns

| Stakeholder | Concern | Priority | Addressed by View／Decision | Evidence／Gap |
| --- | --- | --- | --- | --- |
| {stakeholder} | {concern} | {priority} | `VIEW-{SCOPE}-{SLUG}` / `DE-{SCOPE}-NNN` / [[adr-page]] | {evidence-or-gap} |

## Viewpoint and View Catalog

| View ID | Viewpoint／Model kind | Concern and audience | Elements／Relations | Correspondence |
| --- | --- | --- | --- | --- |
| `VIEW-{SCOPE}-{SLUG}` | {viewpoint/model} | {concern/audience} | {scope} | {related-view/DE/ADR} |

## Architecture and Design Decisions

| Design ID | Decision／Selected approach | Alternatives／Rationale | Upstream SA | Affected views | Status／Evidence |
| --- | --- | --- | --- | --- | --- |
| `DE-{SCOPE}-NNN` | {decision} | {alternatives/rationale} | `SR/NFR/IF-{SCOPE}-NNN` / `gap-*` | `VIEW-{SCOPE}-{SLUG}` | approved / proposed / observed / gap |
| [[adr-page]] | {ADR decision} | {rationale} | {SA-ID-or-gap} | {views} | accepted / proposed |

## Component／Static View

| Component／Element | Responsibility | Owned data／Interface | Dependencies | Upstream SA／Decision |
| --- | --- | --- | --- | --- |
| {component} | {responsibility} | {data/interface} | {dependency} | {SA-ID} / `DE-{SCOPE}-NNN` |

### Mermaid 槽位：元件

> Gap: `gap-{scope}-component-view` — evidence insufficient; do not invent
> components or dependencies.

## Runtime View

| Scenario | Participants | Interaction／State | Failure／Concurrency behavior | SA／Design IDs |
| --- | --- | --- | --- | --- |
| {scenario} | {participants} | {interaction/state} | {behavior} | {SA-IDs} / `DE-{SCOPE}-NNN` |

### Mermaid 槽位：runtime

> Gap: `gap-{scope}-runtime-view` — evidence insufficient; do not invent
> calls, messages, ordering, or branches.

## Data View

| Data element／Store | Logical／Physical form | Owner | Integrity／Lifecycle | Migration／Retention | Trace |
| --- | --- | --- | --- | --- | --- |
| {data} | {model} | {owner} | {integrity/lifecycle} | {migration/retention-or-gap} | {SA/DE} |

### Mermaid 槽位：資料

> Gap: `gap-{scope}-data-view` — evidence insufficient; do not invent entities,
> stores, cardinalities, or flows.

## Interface Design

| Interface／IF ID | Protocol／Schema／Version | Authentication／Authorization | Error／Retry semantics | Consumer／Provider | Decision |
| --- | --- | --- | --- | --- | --- |
| `IF-{SCOPE}-NNN` | {protocol/schema/version} | {control} | {semantics} | {parties} | `DE-{SCOPE}-NNN` / [[adr-page]] |

## Deployment and Operations View

| Node／Environment | Hosted elements | Connectivity／Trust zone | Scaling／Availability | Configuration／Observability | Evidence |
| --- | --- | --- | --- | --- | --- |
| {node} | {elements} | {network/trust} | {strategy} | {config/telemetry} | {evidence-or-gap} |

### Mermaid 槽位：部署

> Gap: `gap-{scope}-deployment-view` — evidence insufficient; do not invent
> nodes, zones, regions, or topology.

## Security View

| Trust boundary／Asset | Threat／Concern | Identity／Access control | Protection／Audit | Requirement／Decision |
| --- | --- | --- | --- | --- |
| {boundary/asset} | {threat} | {identity/control} | {protection/audit} | {NFR/IF} / `DE-{SCOPE}-NNN` |

### Mermaid 槽位：安全

> Gap: `gap-{scope}-security-view` — evidence insufficient; do not invent trust
> boundaries, identities, controls, or data paths.

## Quality Strategy

| NFR ID／Characteristic | Design tactic | Measure／Verification | Responsible element／View | Risk／Gap |
| --- | --- | --- | --- | --- |
| `NFR-{SCOPE}-NNN` / {ISO 25010 characteristic} | {tactic} | {measure/method} | {component/view} | {risk-or-gap} |

## Cross-view Correspondences and Consistency

| Source element／View | Related element／View | Correspondence rule | Consistency evidence／Gap |
| --- | --- | --- | --- |
| `VIEW-{SCOPE}-{SLUG}` | `VIEW-{SCOPE}-{SLUG}` / `DE-{SCOPE}-NNN` | {rule} | {evidence-or-gap} |

## SA → SD 追溯矩陣

| SA ID／Gap | Design ID／ADR | View | Quality／Security effect | Verification strategy | Coverage |
| --- | --- | --- | --- | --- | --- |
| `SR/NFR/IF-{SCOPE}-NNN` / `gap-*` | `DE-{SCOPE}-NNN` / [[adr-page]] | `VIEW-{SCOPE}-{SLUG}` | {effect} | {test/analysis/inspection/demonstration} | covered / partial / gap |

## Risks、Technical Debt 與 Gap Register

| ID | Type | Question／Decision debt | Affected IDs／Views | Evidence checked／Owner | Status |
| --- | --- | --- | --- | --- | --- |
| `gap-{scope}-{topic}` | gap / risk / debt | {statement} | {ids/views} | {evidence/owner} | open |

## 來源附錄

- Wiki evidence: [[system-analysis]], [[system-architecture]], [[adr-page]]
- Raw evidence: `{repo-relative-path}` or `Gap` when none was inspected
- Implementation observations／inferences: {explicit list or none}

<!-- codebase-wiki:managed:end -->

<!-- codebase-wiki:user-notes:start -->
## SD 人工補充

<!-- 重新產出時保留本區全部內容。 -->
<!-- codebase-wiki:user-notes:end -->

<!-- notebooklm:local-only:start -->
## 本機追溯

- Reviewer paths／symbols: `{repo-relative-path-or-gap}`
- Detailed evidence mapping: {SA/DE/VIEW/ADR-to-source mapping}
<!-- notebooklm:local-only:end -->
