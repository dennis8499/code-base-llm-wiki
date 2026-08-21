---
applyTo: "wiki/**/*.md"
description: "Applies when editing any markdown file under the wiki/ directory. Enforces frontmatter format, cross-referencing rules, and page structure conventions for the Codebase LLM Wiki."
---

# Wiki Page Contract

## Sources of Truth

- Schema and allowed values:
  `.agents/skills/codebase-wiki/references/frontmatter-spec.md`
- Page-type selection and exact templates:
  `.agents/skills/codebase-wiki/references/page-types.md`
- Log operations:
  `.agents/skills/codebase-wiki/references/log-operations.md`

## Required Invariants

- Every page has `title`, `type`, `sources`, `last_updated`, `tags`, and
  `status`.
- `frontmatter.sources` contains raw repo-relative evidence or `sources: []`;
  Wiki dependencies use `derived_from` wikilinks.
- New or major evidence-page updates include `summary` and refresh
  `source_digest`.
- Page location matches its `type`.
- Wiki cross-references use `[[page-name]]`; source paths use backticks.
- Facts remain evidence-backed; inference, speculation, and gaps are labeled.
- User-authored notes remain intact.
- Existing `wiki/log.md` entries remain unchanged.

## Coupled Updates

- Page add, delete, rename, or major update synchronizes `wiki/index.md`.
- Ingest, accepted lint repair, ADR, guide, synthesis, system analysis,
  archaeology persistence, or major update appends one valid log operation.

Complete the edit only when frontmatter validation passes, wikilinks resolve or
are marked gaps, index coupling is complete, and required log coupling is
complete.
