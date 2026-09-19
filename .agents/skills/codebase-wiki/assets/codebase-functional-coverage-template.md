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
coverage_schema_version: 2
---

# Codebase Functional Coverage

> This page is a local export gate and is never uploaded to NotebookLM.

Analyzed discovery ID: `{sha256-from-confirmed-discovery-preview}`

<!-- codebase-wiki:managed:start -->
## Disposition Ledger

Every safe file found by the selected scan profile must match exactly one row with
the current scanner hash. Schema v2 rows are file-specific; directory prefixes
are retained only as migration diagnostics and never satisfy the gate.
`functional-evidence` and `supporting-technical` require one or more
functional-requirement wikilinks.

| Path | SHA-256 | Scanner category | Disposition | Functional requirements | Function/process association | Reason |
| --- | --- | --- | --- | --- | --- | --- |
| `src/example.py` | `sha256:{file-hash}` | runtime_source | functional-evidence | [[{business-requirement-page}]] | [[{capability-page}]] / [[{process-page}]] | {why this file is evidence} |

Allowed dispositions: `functional-evidence`, `supporting-technical`,
`no-observable-behavior`, and `analysis-gap`. Export is blocked while any safe
file is uncovered, any `analysis-gap` remains, or any linked requirement is missing.
Only write the analyzed discovery ID after every safe input in that exact snapshot has
been read, classified, hash-checked, and reflected in the capability BA／SA documents.
<!-- codebase-wiki:managed:end -->

<!-- codebase-wiki:user-notes:start -->
## Reviewer Notes

<!-- Preserve manual review notes across regeneration. -->
<!-- codebase-wiki:user-notes:end -->
