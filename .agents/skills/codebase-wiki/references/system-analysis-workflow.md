# System Analysis Document Workflow

Use this workflow when the user asks for an SA document, system analysis
document, SAD, `SA文件`, `系統分析文件`, or
`/system-analysis-doc {scope}`. The existing command and default path are
preserved. An explicit request authorizes the scoped Wiki output.

Load `analysis-document-standards.md` completely and apply
`system-analysis-aligned-v1`: ISO/IEC/IEEE 29148:2018 and
ISO/IEC/IEEE 15288:2023 organize stakeholder needs and system requirements;
ISO/IEC 25010:2023 classifies measurable quality requirements.

## Output Contract

- Default path: `wiki/synthesis/system-analysis.md`.
- Scoped path: `wiki/synthesis/{kebab-scope}-system-analysis.md`.
- Frontmatter: `type: synthesis`,
  `standards_profile: system-analysis-aligned-v1`, and
  `coverage_status: covered | partial | gap`.
- Required tags: `synthesis`, `system-analysis`, `standards-aligned`.
- NotebookLM: `notebooklm_role: traceability`; this solution-neutral standalone
  SA is not an upload candidate. Schema-v6 export may create a separate
  current-state per-capability SA with `codebase-system-analysis-v1` and
  `notebooklm_document: sa`.
- Format: Traditional Chinese Markdown. Do not generate PDF or DOCX.

## Analysis Boundary

SA is `solution-neutral`. It defines what observable behavior, information,
interface, quality, failure handling, and verification the system needs. It
不得包含技術選型，亦不得包含部署設計。Do not prescribe frameworks,
libraries, component allocation, protocols, storage engines, runtime topology,
cloud products, or implementation mechanisms. Route those decisions to SD or
an ADR.

Existing implementation may prove current behavior or expose a constraint; it
does not by itself make that implementation the required solution. Separate
stakeholder need, requirement, observed behavior, inference, and Gap.

## Source Order

1. Read `wiki/index.md` and recent `wiki/log.md`.
2. Read the scoped BA document when present, then relevant overview,
   requirement, process, rule, glossary, gap, and decision pages.
3. Read existing architecture/module/entity pages only to establish observed
   system boundary, actors, external interactions, and constraints—not to copy
   their design into requirements.
4. Inspect raw sources only when Wiki evidence is missing, stale,
   contradictory, or too vague for a testable requirement.

When the SA is paired with a current-state NotebookLM export, trace each
scenario from entrypoint through the observable call chain. Retain the
preconditions, step order, data and state changes, interface handoffs,
success result, failure branch, and retry/rollback behavior with source
locators. Classify unfinished tracing as `analysis-gap`, absent source
evidence as `evidence-gap`, and unconfirmed operational policy as
`business-confirmation`; preserve observed behavior in the latter two cases
without turning it into a requirement or policy.

An absent BA does not block SA. Create stable `gap-{scope}-ba-*` records for
missing business objectives, actors, policies, or success criteria and proceed
with the evidence that exists.

## Coverage Map

| SA section | Expected evidence |
| --- | --- |
| Purpose, scope, and system boundary | BA scope, overview, context evidence |
| Stakeholders, actors, and needs | BA stakeholders/needs or explicit Gap |
| Assumptions, constraints, dependencies | approved constraints, rules, external systems |
| Use cases and operational scenarios | `bp-*`, `fr-*`, `AC-*`, observed entry/exit behavior |
| Functional system requirements | testable response/state/result statements |
| External interface requirements | actors/systems, exchanged information, timing/error semantics |
| Quality requirements | measurable ISO/IEC 25010 characteristic, condition, measure, target |
| Conceptual information model and flow | business concepts, ownership, lifecycle, input/output—not storage design |
| Failure and exceptional behavior | detection, externally visible response, recovery need |
| Verification and validation needs | method and evidence needed for each requirement |
| Traceability and unresolved gaps | upstream BA IDs/Gaps to SA IDs and verification |

Mark each row `covered`, `partial`, or `gap` using the common profile. A section
can be partial even when observed behavior exists if stakeholder approval or a
measurable target is missing.

## Stable Requirements and Traceability

- Functional/system requirement: `SR-{SCOPE}-NNN`.
- Quality requirement: `NFR-{SCOPE}-NNN`.
- External interface requirement: `IF-{SCOPE}-NNN`.
- Missing evidence: `gap-{scope}-{topic}`.

Each requirement is atomic, necessary, feasible as far as evidence shows,
unambiguous, externally verifiable, and solution-neutral. Record rationale,
source/upstream ID, verification method, and coverage state. Minimum chain:

`BA cap-* / fr-* / bp-* / br-* / AC-* or Gap → SR/NFR/IF → verification need`

Do not invent a requirement to make traceability complete. Use a Gap row and
name the stakeholder or source needed to resolve it.

Do not reduce a cross-functional scenario to a title or four-step summary.
Include the concrete interface, state, data, and failure details that allow
the paired BA and shared business source to be read independently.

## Required Mermaid Slots

- 系統脈絡：actors and external systems around the system boundary.
- 主要情境：one evidence-backed use-case sequence expressed without internal
  component or technology design.

Render Mermaid only when participants and relationships are supported. If
evidence is insufficient, retain the slot and write a concrete `Gap`; do not
emit a guessed graph.

## Regeneration and Legacy Preservation

Start from `assets/system-analysis-template.md`.

For a current document with all three marker pairs, regenerate only the
`codebase-wiki:managed` block, preserve `codebase-wiki:user-notes`, and keep
reviewer-only provenance inside `notebooklm:local-only`.

For a legacy SA that has no managed/user-notes/local-only markers:

1. Read and retain its frontmatter separately.
2. Copy the complete legacy 原正文 (every byte after the closing frontmatter)
   verbatim into a clearly labeled `Legacy SA snapshot — non-normative` section
   inside the new `codebase-wiki:user-notes` block.
3. Generate the new solution-neutral managed content before that preserved
   snapshot and add the local-only block.
4. Never summarize, normalize, or silently discard the legacy body on this
   first rerun.

Installer and upgrade never apply this conversion and never rewrite a target
Wiki. Conversion occurs only when the user explicitly reruns the SA workflow.

## Persistence Steps

1. Choose the default or exact scoped path.
2. Build the coverage map and requirement inventory before writing.
3. Merge the template using the marker/legacy rules.
4. Put only real repo-relative raw evidence in `sources`; record Wiki evidence
   in `derived_from`; refresh `source_digest` when sources are non-empty.
5. Update `wiki/index.md` and append exactly one standalone `synthesis` entry
   to `wiki/log.md`.
6. Run frontmatter, stale, link/index, log, and Wiki lint checks; report Gap IDs
   and any requirement that lacks validation/verification evidence.

Framework maintenance may include SA with other framework Wiki changes in its
single `update` log entry.

## Completion Criterion

The SA document is complete when it uses `system-analysis-aligned-v1`, remains
solution-neutral, every coverage row and required section has a state, every
SR/NFR/IF traces to upstream evidence or a concrete Gap and a verification need,
both Mermaid slots contain supported diagrams or Gaps, a first-rerun legacy 原正文
is preserved verbatim in user-notes, markers/frontmatter/links validate, and
index plus append-only log coupling is complete.
