# Business Analysis Document Workflow

Use this workflow when the user explicitly asks for a Business Analysis
document, `BA文件`, `業務分析文件`, or `/business-analysis-doc {scope}`. The
explicit request authorizes the scoped Wiki output. A request that also says
NotebookLM, export, or source pack belongs to `notebooklm-export-workflow.md`.
Only a bare `BA` with no document/export context requires clarification.

Load `analysis-document-standards.md` completely and apply
`business-analysis-aligned-v1`.

## Output Contract

- Default path: `wiki/synthesis/business-analysis.md`.
- Scoped path: `wiki/synthesis/{kebab-scope}-business-analysis.md`.
- Frontmatter: `type: synthesis`,
  `standards_profile: business-analysis-aligned-v1`, and
  `coverage_status: covered | partial | gap`.
- Required tags: `synthesis`, `business-analysis`, `standards-aligned`.
- NotebookLM: `notebooklm_role: business`, stable
  `notebooklm_group`, and non-empty `notebooklm_terms`.
- Format: Traditional Chinese Markdown. Do not generate PDF or DOCX.

The standalone BA document is optional for NotebookLM readiness. When present,
its business-role content is included by the existing exporter and its
`notebooklm:local-only` blocks are removed. Never add it to NotebookLM's
required-document list or change schema v5 for this workflow.

## Source Order

1. Read `wiki/index.md` and recent `wiki/log.md`.
2. Read `wiki/overview.md`, existing BA catalogs, requirements, processes,
   rules, glossary, gaps, and relevant decisions/guides.
3. Read an upstream scope document supplied by the user, when any.
4. Inspect raw repo sources only when Wiki evidence is missing, stale,
   contradictory, or too vague. Treat code/config as
   `implementation-observed`, not approved business policy.

## Coverage Map

Build this map before writing and retain it in the output:

| BA section | Expected evidence |
| --- | --- |
| Business context, problem, opportunity | overview, charter, product docs, confirmed notes |
| Scope and outcomes | overview, requirements, confirmed boundaries |
| Stakeholders and needs | actor/process pages, ownership docs, explicit Gap |
| Current and target state | current evidence plus approved target statement |
| Capabilities and requirements | `cap-*`, `fr-*`, `AC-*` pages/catalog |
| Business processes and rules | `bp-*`, `br-*`, process/rule catalogs |
| Business information and glossary | glossary, schemas used only as observed evidence |
| Success measures | approved KPI/acceptance evidence or Gap |
| Risks, assumptions, constraints | decisions, rules, gaps, owner input |
| Change impact and transition needs | affected roles/processes/data and adoption evidence |

Mark every row `covered`, `partial`, or `gap` using
`analysis-document-standards.md`. The frontmatter value summarizes the whole
document; it is not automatically `covered` merely because every row exists.

## Stable IDs and Traceability

Reuse existing `cap-*`, `fr-*`, `bp-*`, `br-*`, and `AC-*` identities. Do not
create a second ID for the same capability, requirement, process, rule, or
acceptance criterion. The minimum chain is:

`business objective / need → cap-* → bp-* / br-* → fr-* → AC-*`

If a required upstream or catalog item does not exist, create a concrete
`gap-{scope}-{topic}` row; do not invent an ID-backed claim merely to fill the
matrix. BA-to-SA handoff records the affected capability/requirement IDs and
open Gap IDs without prescribing solution structure.

## Required Mermaid Slots

The template contains two slots:

- 業務流程：actor-trigger-outcome sequence for supported `bp-*` evidence;
- 現況／目標：approved current-to-target state relationship.

Render Mermaid only when actors, states, and transitions are supported. If not,
leave a `Gap` statement naming the evidence needed. Never turn a proposed or
unknown target state into a factual diagram.

## Regeneration and Writing Rules

- Start from `assets/business-analysis-template.md` and retain every required
  section.
- Regenerate only content inside `codebase-wiki:managed:start` / `end`.
- Preserve all content inside `codebase-wiki:user-notes:start` / `end`.
- Keep raw paths, symbols, implementation-only mappings, and reviewer detail in
  `notebooklm:local-only:start` / `end`.
- Use `[[wikilinks]]` for Wiki evidence and backticked repo-relative paths for
  raw evidence. Separate fact, inference, assumption, and Gap.
- Never invent stakeholders, business policy, target state, KPI threshold,
  requirement, rule, or process step.

## Persistence Steps

1. Choose the default or exact scoped path.
2. Merge the template while preserving user notes.
3. Populate `sources` only with real repo-relative raw evidence; put Wiki
   derivation in `derived_from`. Refresh `source_digest` when sources are
   non-empty.
4. Update `wiki/index.md`.
5. Append exactly one standalone `synthesis` entry to `wiki/log.md`.
6. Run frontmatter, stale, link/index, log, and Wiki lint checks; report
   coverage and open Gap IDs.

Framework maintenance may include BA with other framework Wiki changes in its
single `update` log entry. Installer and upgrade never generate or rewrite a
target repository's BA document.

## Completion Criterion

The BA document is complete when it uses
`business-analysis-aligned-v1`, every mandatory section and standards mapping
row has a coverage state, BA IDs and `AC-*` trace without duplication, both
Mermaid slots contain evidence-backed diagrams or concrete Gaps, managed/user
notes/local-only markers are intact, frontmatter and links validate, index/log
coupling is complete, and every unresolved point has a stable Gap ID and
follow-up evidence target.
