---
title: Codebase Functional Coverage
type: synthesis
summary: Local-only disposition ledger proving every safe analysis input was classified against functional requirements.
notebooklm_group: local-governance
notebooklm_role: exclude
sources: []
derived_from: ["[[functional-requirement-catalog]]"]
last_updated: YYYY-MM-DD
tags: [synthesis, coverage, notebooklm, local-only]
status: active
---

# Codebase Functional Coverage

> This page is a local export gate and is never uploaded to NotebookLM.

Analyzed discovery ID: `{sha256-from-confirmed-discovery-preview}`

<!-- codebase-wiki:managed:start -->
## Disposition Ledger

Every safe file found by the selected scan profile must match exactly one most-specific row.
Use a trailing `/` for a directory prefix. `functional-evidence` and
`supporting-technical` require one or more functional-requirement wikilinks.

| Path or prefix | Disposition | Functional requirements |
| --- | --- | --- |
| `src/` | functional-evidence | [[{business-requirement-page}]] |

Allowed dispositions: `functional-evidence`, `supporting-technical`,
`no-observable-behavior`, and `analysis-gap`. Export is blocked while any safe
file is uncovered, any `analysis-gap` remains, or any linked requirement is missing.
Only write the analyzed discovery ID after every safe input in that exact snapshot has
been read, classified, and reflected in the capability BA／SA documents.
<!-- codebase-wiki:managed:end -->

<!-- codebase-wiki:user-notes:start -->
## Reviewer Notes

<!-- Preserve manual review notes across regeneration. -->
<!-- codebase-wiki:user-notes:end -->
