# System Design Document Workflow

Use this workflow when the user explicitly asks for a System Design document,
SD document, SDD, `SD文件`, `系統設計文件`, or
`/system-design-doc {scope}`. The explicit request authorizes the scoped Wiki
output.

Load `analysis-document-standards.md` completely and apply
`system-design-aligned-v1`. ISO/IEC/IEEE 42010:2022 is the architecture
description basis; ISO/IEC 25010:2023 organizes quality strategies. IEEE
1016-2009 is informative historical SDD organization only and is not a current
conformance basis.

## Output Contract

- Default path: `wiki/synthesis/system-design.md`.
- Scoped path: `wiki/synthesis/{kebab-scope}-system-design.md`.
- Frontmatter: `type: synthesis`,
  `standards_profile: system-design-aligned-v1`, and
  `coverage_status: covered | partial | gap`.
- Required tags: `synthesis`, `system-design`, `standards-aligned`.
- NotebookLM: `notebooklm_role: traceability`; SD never enters the BA upload
  payload.
- Format: Traditional Chinese Markdown. Do not generate PDF or DOCX.

## Source Order

1. Read `wiki/index.md` and recent `wiki/log.md`.
2. Read the scoped SA when present, then its BA, requirements, decisions,
   architecture, module, entity, dependency, security, operations, and Gap
   pages.
3. Inspect raw sources only for missing, stale, contradictory, or insufficient
   design evidence.

An absent SA does not block SD. Create specific `gap-{scope}-sa-*` entries for
missing system/interface/quality requirements. Do not invent a design driver or
claim that a current implementation is approved architecture.

## Coverage Map

| SD section | Expected evidence |
| --- | --- |
| Architecture scope and design drivers | SA IDs, constraints, quality requirements, open Gaps |
| Stakeholders and concerns | owner/operator/security/developer concerns or Gap |
| Viewpoints, views, and correspondences | purpose, audience, model kind, related view IDs |
| Architecture decisions and rationale | existing ADRs or `DE-*` decision records |
| Component/static structure | responsibility, boundary, dependency, owned requirements |
| Runtime behavior | evidence-backed interactions, concurrency/state/error semantics |
| Data design | logical/physical models, ownership, lifecycle, integrity, migration |
| Interface design | `IF-*`, protocol/schema/version/error/security details |
| Deployment and operations | nodes, topology, configuration, scaling, observability, recovery |
| Security architecture | trust boundaries, identities, authorization, secrets, audit, threats |
| Quality strategies | tactics and verification for each `NFR-*` |
| Traceability, risks, and Gaps | SA → design → view/ADR → verification chain |

Mark every row `covered`, `partial`, or `gap` using the common profile.

## Stable Design IDs and Traceability

- Design element/decision: `DE-{SCOPE}-NNN`.
- Architecture view: `VIEW-{SCOPE}-{SLUG}`.
- Reuse existing ADR identities and `[[adr-page]]` links; do not mint duplicate
  ADRs merely for the SD document.
- Missing evidence: `gap-{scope}-{topic}`.

Minimum chain:

`SA SR/NFR/IF or Gap → DE-* / existing ADR → VIEW-* → verification strategy`

Each design element records responsibility, selected approach, alternatives or
rationale, upstream requirements, affected views, quality/security effects,
and verification. A documented observation that lacks decision evidence is
labeled `implementation-observed`, not an approved decision.

## Required Mermaid Slots

The template includes five independently evidence-gated slots:

- 元件 view;
- runtime interaction view;
- 資料 view;
- 部署 view;
- 安全／trust-boundary view.

Render a slot only when its nodes and edges are supported by Wiki or raw
evidence. Otherwise retain the heading and record a concrete `Gap` with the
missing source or stakeholder; never generate a plausible-looking design.

## Regeneration and Writing Rules

- Start from `assets/system-design-template.md` and retain all required
  42010-aligned description sections.
- Regenerate only `codebase-wiki:managed`; preserve
  `codebase-wiki:user-notes`; keep paths/symbols/reviewer provenance inside
  `notebooklm:local-only`.
- Distinguish approved decision, constraint, implementation observation,
  inference, and Gap.
- Use `[[wikilinks]]` for Wiki evidence and backticked repo-relative paths for
  raw evidence.
- Do not invent components, protocols, schemas, topology, trust boundaries,
  scaling targets, failure recovery, or security controls.

## Persistence Steps

1. Choose the default or exact scoped path.
2. Build the stakeholder/concern, viewpoint, design-element, and coverage
   inventories before writing.
3. Merge the template while preserving user notes.
4. Put only real repo-relative raw evidence in `sources`; use `derived_from`
   for Wiki evidence; refresh `source_digest` when sources are non-empty.
5. Update `wiki/index.md` and append exactly one standalone `synthesis` entry
   to `wiki/log.md`.
6. Run frontmatter, stale, link/index, log, and Wiki lint checks; report open
   Gap IDs and unverified design decisions.

Framework maintenance may include SD with other framework Wiki changes in its
single `update` log entry. Installer and upgrade never generate or rewrite a
target repository's SD document.

## Completion Criterion

The SD document is complete when it uses `system-design-aligned-v1`, maps
stakeholders/concerns to declared viewpoints and `VIEW-*` views, traces every
`DE-*`/ADR to SA evidence or a concrete Gap and verification strategy, all five
Mermaid slots contain supported diagrams or Gaps, every mandatory coverage row
has a state, markers/frontmatter/links validate, and index plus append-only log
coupling is complete.
