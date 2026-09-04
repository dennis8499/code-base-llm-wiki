# BA／SA／SD Standards Profiles

This reference defines the stable, versioned profiles used by the standalone
Business Analysis (BA), System Analysis (SA), and System Design (SD) Markdown
workflows. The profiles organize evidence in a way that is aligned with the
named standards; they do not reproduce standards text and do not claim
certification, audit approval, or formal compliance.

`standard-aligned`／「標準對齊」表示文件具有可追溯的章節、觀點與 coverage
evidence；不代表 conformance。若組織需要正式符合性聲明，必須另外取得標準全文、
定義適用條款、保留稽核證據，並由具權責的人員評估。

## Profile Registry

| Profile | Primary references | Workflow boundary |
| --- | --- | --- |
| `business-analysis-aligned-v1` | ISO/IEC/IEEE 29148:2018；IIBA Business Analysis Standard v2.0 | 業務問題、價值、利害關係人、能力、流程、規則、需求與成功指標 |
| `system-analysis-aligned-v1` | ISO/IEC/IEEE 29148:2018；ISO/IEC/IEEE 15288:2023；ISO/IEC 25010:2023 | solution-neutral 的系統邊界、needs、use cases、需求、介面、品質與驗證需求 |
| `system-design-aligned-v1` | ISO/IEC/IEEE 42010:2022；ISO/IEC 25010:2023；IEEE 1016-2009（informative only） | 架構 concerns/viewpoints/views、決策、元件、runtime、資料、介面、部署、安全與品質策略 |

Profiles pin the named editions. A later standards revision requires a new
profile version and an explicit migration; do not silently reinterpret `v1`.

## Authoritative Links and Use

- [ISO/IEC/IEEE 29148:2018](https://www.iso.org/standard/72089.html) supplies
  requirements-engineering concepts used to structure stakeholder and system
  requirements, characteristics, and traceability. BA and SA use it at
  different abstraction levels.
- [IIBA Business Analysis Standard v2.0](https://www.iiba.org/globalassets/business-analysis-resources/the-business-analysis-standard/files/the-business-analysis-standard.pdf)
  supplies the BA framing for context, value, stakeholders, change, needs,
  solutions, and business-analysis practices.
- [ISO/IEC/IEEE 15288:2023](https://www.iso.org/standard/81702.html) supplies the
  system life-cycle framing used by SA for stakeholder needs, system
  requirements, validation, and verification concerns.
- [ISO/IEC 25010:2023](https://www.iso.org/standard/78176.html) supplies the
  product-quality model used to classify measurable quality requirements in SA
  and the corresponding quality strategies in SD.
- [ISO/IEC/IEEE 42010:2022](https://www.iso.org/standard/74393.html) supplies the
  architecture-description concepts used by SD: stakeholders, concerns,
  viewpoints, views, correspondences, decisions, and rationale.
- [IEEE 1016-2009](https://standards.ieee.org/ieee/1016/4502/) is
  inactive-reserved. It is an informative historical reference for familiar
  Software Design Description organization only; it is not a current
  conformance basis and must not override the 42010 profile.

## Separation of Concerns

| Layer | Governing question | Allowed content | Content routed elsewhere |
| --- | --- | --- | --- |
| BA | Why is change needed and what business outcome is required? | current/target state, actors, capability, process, rule, business data term, success metric, risk/change impact | system boundary and testable system requirements go to SA; solution structure goes to SD |
| SA | What externally observable behavior and quality must the system provide? | system boundary, stakeholder needs, use cases, functional/interface/quality requirements, conceptual information flow, failure and verification needs | product/technology selection, component allocation, protocols, topology, implementation mechanism, and deployment design go to SD |
| SD | How will an approved solution satisfy the SA requirements? | architecture decisions, views, components, runtime interactions, logical/physical data, interfaces, deployment, security controls, quality tactics | unapproved business policy returns to BA; missing or conflicting needs return to SA |

SA is explicitly `solution-neutral`. Observed implementation may be cited as
evidence of current behavior, but a technology or topology must not be promoted
to a requirement unless an authoritative constraint establishes that need.

## Common Document Control

Every new BA／SA／SD output uses `type: synthesis` and includes:

- `standards_profile` with the exact profile ID;
- `coverage_status: covered | partial | gap`;
- document identity, scope, owner/reviewer gaps, version/status, evidence
  baseline date, and change summary;
- a standards mapping matrix, section coverage map, upstream/downstream
  traceability matrix, explicit Gap register, and source appendix;
- Traditional Chinese narrative with stable English standard terms where they
  prevent ambiguity;
- repo-relative raw evidence in `sources`, Wiki evidence in `derived_from`, and
  no invented actor, requirement, interface, quality target, component, or
  deployment fact.

`status: active` describes Wiki freshness. `coverage_status` separately
describes evidence completeness:

| Value | Meaning |
| --- | --- |
| `covered` | Every mandatory section and traceability row has sufficient, non-conflicting evidence; no open Gap affects the document's core purpose. |
| `partial` | The document is useful and has evidence for its core purpose, but one or more sections, attributes, links, or approvals remain incomplete. |
| `gap` | Evidence is insufficient for the document's core purpose or an unresolved contradiction prevents a trustworthy baseline. Keep the document and list concrete Gap records. |

## Evidence and Gap Contract

Each material claim is evidence-backed or explicitly labeled as inference. If
evidence is absent, retain the section and create a stable, concrete
`gap-{scope}-{topic}` entry with:

- the unanswered question or contradiction;
- affected IDs and document sections;
- evidence already checked;
- suggested Wiki page or repo-relative source target;
- responsible stakeholder when known, otherwise `待確認`;
- open/resolved state and resolution evidence when later closed.

Missing upstream BA or SA output does not block standalone generation. SA and SD
instead create specific Gap rows for unavailable upstream IDs. A Gap placeholder
must not be rendered as a factual Mermaid node or fabricated interaction.

## Stable IDs and Traceability

| Layer | IDs | Minimum trace |
| --- | --- | --- |
| BA | existing `cap-*`, `fr-*`, `bp-*`, `br-*`, `AC-*` | business objective/need → capability → process/rule → functional requirement → acceptance criterion |
| SA | `SR-{SCOPE}-NNN`, `NFR-{SCOPE}-NNN`, `IF-{SCOPE}-NNN` | upstream BA ID or Gap → system requirement/interface/quality requirement → verification need |
| SD | `DE-{SCOPE}-NNN`, `VIEW-{SCOPE}-{SLUG}`, existing `ADR-*` / `[[adr-page]]` | upstream SA ID or Gap → design element/view/decision → verification strategy |

`{SCOPE}` is a stable uppercase ASCII token derived from kebab scope, such as
`ORDER` or `CODEBASE-WIKI`; numbering is three digits and never reused for a
different item. Do not renumber an existing ID merely to close a sequence.

## Managed Content and Diagrams

All three templates use these non-overlapping marker pairs:

- `codebase-wiki:managed` contains regenerable evidence-derived content;
- `codebase-wiki:user-notes` preserves human-authored notes across reruns;
- `notebooklm:local-only` contains reviewer-only paths, symbols, detailed
  provenance, or technical traceability that must not enter a BA source pack.

Only BA has `notebooklm_role: business`; SA and SD use `traceability`. BA is an
optional NotebookLM business page when present and is not added to the required
document list. Local-only blocks are removed by the existing exporter.

Required Mermaid slots are:

- BA: 業務流程 and 現況／目標狀態;
- SA: 系統脈絡 and 主要情境;
- SD: 元件, runtime, 資料, 部署, and 安全 views.

Render Mermaid only when node and edge evidence is sufficient. Otherwise keep
the slot and write a Gap with the missing evidence; do not emit a guessed graph.

## Completion Criterion

A profile is applied only when the exact profile ID, pinned references,
layer boundary, document controls, coverage semantics, stable IDs, markers,
diagram Gap behavior, and traceability rules above are all reflected in the
selected workflow and output.
