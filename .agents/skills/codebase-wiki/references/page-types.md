# Page Type Catalog

Choose one page type, then load its exact asset. Page shape lives in the asset;
field validity lives in `frontmatter-spec.md`.

| Type | Use when | Asset | Extra required fields |
| --- | --- | --- | --- |
| `overview` | High-level codebase purpose and major areas | `assets/overview-template.md` | — |
| `architecture` | Components, data flow, or deployment | `assets/architecture-template.md` | — |
| `module` | A logical directory, package, or bounded area | `assets/module-template.md` | — |
| `entity` | A key class, service, endpoint, or table | `assets/entity-template.md` | — |
| `pattern` | A repeated, evidence-backed implementation pattern | `assets/pattern-template.md` | — |
| `decision` | An architecture decision and rationale | `assets/adr-template.md` | `decision_date`, `decision_status` |
| `dependency` | A significant external package | `assets/dependency-template.md` | `package_name`, `version` |
| `guide` | Actionable onboarding, setup, debugging, or operations | `assets/guide-template.md` | — |
| `synthesis` | Durable cross-cutting analysis | `assets/synthesis-template.md` | — |
| `synthesis` (SA) | System Analysis document | `assets/system-analysis-template.md` | tags include `system-analysis` |
| `index` | Wiki navigation root | `assets/index-template.md` | `sources: []`, `tags: [index]` |
| `log` | Append-only activity history | `assets/log-template.md` | `sources: []`, `tags: [log]` |

## Selection Rules

- Create an Entity page for externally exposed handlers/services, persisted
  models, or symbols reused across several modules.
- Create Pattern and Dependency pages only when source evidence supports
  project-specific behavior or risk.
- Use Guide for procedures and Synthesis for analysis.
- Reuse an existing page when its identity matches; preserve authored notes.

## Completion Criterion

Selection is complete when exactly one asset was loaded, its type/path matches
`frontmatter-spec.md`, and every retained section is supported or marked as a
gap.
