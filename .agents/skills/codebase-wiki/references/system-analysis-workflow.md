# System Analysis Document Workflow

Use this workflow when the user asks for an SA document, system analysis
document, SAD, `SA文件`, or `系統分析文件` generated from Codebase LLM Wiki
content.

## Output

- Default path: `wiki/synthesis/system-analysis.md`.
- Scoped path: `wiki/synthesis/{kebab-scope}-system-analysis.md`.
- Frontmatter type: `synthesis`.
- Required tags: `synthesis` and `system-analysis`.
- Default format: Markdown. Do not generate Word or PDF unless the user asks
  for that as a separate task.

## Source Order

1. Read `wiki/index.md` and recent `wiki/log.md`.
2. Read `wiki/overview.md` when present.
3. Read relevant pages from:
   - `wiki/architecture/`
   - `wiki/modules/`
   - `wiki/entities/`
   - `wiki/patterns/`
   - `wiki/dependencies/`
   - `wiki/decisions/`
   - `wiki/synthesis/`
4. Inspect raw sources only when wiki content is missing, stale,
   contradictory, or too vague for a required SA section.

## Coverage Map

Before writing, build a short coverage map for these sections:

| SA section | Typical evidence |
| --- | --- |
| Purpose and scope | overview, README, guides |
| Stakeholders and readers | docs, inferred audience from wiki |
| System overview and context | overview, architecture |
| Architecture and components | architecture, modules, dependencies |
| Module responsibilities | modules, entities |
| Main flows and use cases | modules, synthesis, source call paths |
| APIs and interfaces | entities, controllers, routes, public exports |
| Data model and data flow | entities, dependencies, source schemas |
| External integrations | dependencies, config, integration modules |
| Security and permissions | auth modules, config, middleware |
| Deployment and operations | architecture, config, scripts, docs |
| Non-functional requirements | docs, config, observed operational patterns |
| Errors and failure modes | services, handlers, logs, synthesis |
| Risks and technical debt | synthesis, lint findings, archaeology |

Mark each row as:

- `covered`: enough wiki/source evidence exists.
- `partial`: some evidence exists, but follow-up ingest would improve it.
- `gap`: no reliable evidence found.

## Writing Rules

- Use the local `assets/system-analysis-template.md` next to this skill as the
  starting structure.
- Preserve all standard SA sections. If evidence is missing, keep the section
  and write `待補` / `Gap` with a concrete follow-up ingest target.
- Prefer `[[wiki-page]]` links for wiki evidence and source paths in backticks
  for raw source evidence.
- Distinguish evidence-backed facts, inference, and speculation.
- Do not invent APIs, flows, actors, non-functional requirements, database
  fields, or deployment behavior.
- If database live evidence is used, keep it in a body evidence block with the
  required metadata. Do not place DB evidence in frontmatter `sources`.

## Persistence Steps

1. Choose the output path.
2. Write or update the SA document under `wiki/synthesis/`.
3. Start from `assets/system-analysis-template.md`.
4. Put only real repo-relative raw evidence in `sources`. Record Wiki evidence
   in `derived_from` using `[[wikilinks]]`; use `sources: []` when no raw source
   was inspected. Populate `summary` and refresh `source_digest` when sources
   are non-empty.
5. Update `wiki/index.md`.
6. Append `wiki/log.md` with operation `synthesis`.
7. Report coverage gaps and verification commands.

When System Analysis is produced inside a confirmed NotebookLM full-project
preparation, the composite workflow records all affected pages in its single
`ingest` log entry. Standalone SA requests continue to use `synthesis`.

## Completion Criterion

The SA document is complete when every coverage-map row and every standard
section is marked `covered`, `partial`, or `gap`; evidence and inference are
separated; frontmatter and links validate; the index links the document; one
append-only `synthesis` entry records it; and all follow-up ingest targets are
concrete repo paths or Wiki pages.
