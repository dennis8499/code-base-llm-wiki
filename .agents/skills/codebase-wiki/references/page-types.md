# Page Type Catalog

Choose one page type, then load its exact asset. Page shape lives in the asset;
field validity lives in `frontmatter-spec.md`.

| Type | Use when | Asset | Extra required fields |
| --- | --- | --- | --- |
| `overview` | High-level codebase purpose and major areas | `assets/overview-template.md` | — |
| `business-process` | An end-to-end actor/trigger/outcome business flow | `assets/business-process-template.md` | `process_id`, `actors`, `coverage_status`, NotebookLM metadata |
| `business-requirement` | A testable BA-facing system behavior | `assets/business-requirement-template.md` | `requirement_id`, `capability_id`, `applies_to`, `evidence_state`, stable `AC-*` IDs, NotebookLM metadata |
| `business-rule` | A condition/decision/exception rule applied to business processes | `assets/business-rule-template.md` | `rule_id`, `applies_to`, `evidence_state`, NotebookLM metadata |
| `architecture` | Components, data flow, or deployment | `assets/architecture-template.md` | — |
| `module` | A logical directory, package, or bounded area | `assets/module-template.md` | — |
| `entity` | A key class, service, endpoint, or table | `assets/entity-template.md` | — |
| `pattern` | A repeated, evidence-backed implementation pattern | `assets/pattern-template.md` | — |
| `decision` | An architecture decision and rationale | `assets/adr-template.md` | `decision_date`, `decision_status` |
| `dependency` | A significant external package | `assets/dependency-template.md` | `package_name`, `version` |
| `guide` | Actionable onboarding, setup, debugging, or operations | `assets/guide-template.md` | — |
| `synthesis` | Durable cross-cutting analysis | `assets/synthesis-template.md` | — |
| `synthesis` (function catalog) | Optional technical capability coverage for traceability or legacy Wiki maintenance | `assets/project-function-catalog-template.md` | tags include `function-catalog`; not a BA export prerequisite |
| `synthesis` (functional requirement catalog) | Mandatory BA-facing index of every active `fr-*` requirement | `assets/functional-requirement-catalog-template.md` | tags include `functional-requirements`; every active requirement must be linked |
| `synthesis` (codebase functional coverage) | Mandatory local-only disposition ledger for every safe analysis input | `assets/codebase-functional-coverage-template.md` | `notebooklm_role: exclude`; no uncovered or `analysis-gap` row may remain at export |
| `synthesis` (business process catalog) | BA-facing capability and process coverage | `assets/business-process-catalog-template.md` | tags include `business-process-catalog` |
| `synthesis` (business rule catalog) | BA-facing rule coverage and evidence states | `assets/business-rule-catalog-template.md` | tags include `business-rule-catalog` |
| `synthesis` (business glossary) | Canonical business terms, aliases, and state meanings | `assets/business-glossary-template.md` | tags include `business-glossary` |
| `synthesis` (business gaps) | Explicit unresolved business questions | `assets/business-knowledge-gaps-template.md` | tags include `business-knowledge-gaps` |
| `synthesis` (SA) | System Analysis document | `assets/system-analysis-template.md` | tags include `system-analysis` |
| `index` | Wiki navigation root | `assets/index-template.md` | `sources: []`, `tags: [index]` |
| `log` | Append-only activity history | `assets/log-template.md` | `sources: []`, `tags: [log]` |

## Selection Rules

- Create an Entity page for externally exposed handlers/services, persisted
  models, or symbols reused across several modules.
- Create one Business Process page per end-to-end actor/trigger/outcome flow and
  one Business Rule page per independently queryable condition or decision.
- Create Pattern and Dependency pages only when source evidence supports
  project-specific behavior or risk.
- Use Guide for procedures and Synthesis for analysis.
- New or major evidence-backed pages populate `summary`; pages with raw
  `sources` also populate `source_digest`. Wiki-only derivation uses
  `derived_from`, not `sources`.
- Reuse an existing page when its identity matches; preserve authored notes.

## Completion Criterion

Selection is complete when exactly one asset was loaded, its type/path matches
`frontmatter-spec.md`, and every retained section is supported or marked as a
gap.
