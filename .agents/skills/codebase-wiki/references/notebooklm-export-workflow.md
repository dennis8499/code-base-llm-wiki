# NotebookLM Enterprise Export Workflow

Use this workflow when a user explicitly asks to prepare the local Codebase
LLM Wiki for NotebookLM Enterprise or to refresh an existing source pack.

## Scope and authorization

This is a first-class `notebooklm_export` operation. It is an offline export:
the workflow does not call NotebookLM, upload files, or modify raw sources.
The controlled output is the repository-local `.notebooklm/` directory.

The first phase is always read-only and always scans the full safe project
scope. Existing Wiki pages are the knowledge baseline, not a boundary on raw
discovery. Even when the Wiki is clean, show the functional coverage preview
and wait for confirmation before updating Wiki or writing the local pack.

After confirmation, use the Batch Ingest rules below, preserve user-authored
content, update only missing/stale/changed knowledge, synchronize
`wiki/index.md`, and append one `ingest` entry covering the complete NotebookLM
preparation. Then run the exporter. Raw project sources remain read-only.

## Safe project scope

Include every UTF-8 project-owned text file in these categories:

- runtime source and production entrypoints;
- runtime-required config and dependency manifests;
- database schemas, migrations, messages, and interface schemas;
- existing project documentation.

Exclude tests, CI/CD, IaC, build/development tooling, dependency and generated
directories, binaries, credentials/secrets, the Wiki and export output, and
installed Codebase LLM Wiki adapter/schema files. A production entrypoint is
runtime source even if it lives under a scripts directory. Enumerate Git
tracked plus non-ignored untracked files; use a filesystem fallback outside Git.

## Source order

1. Read `wiki/index.md` and every Wiki Markdown page except `wiki/log.md`.
2. Run the deterministic frontmatter, stale-source, and Wiki lint checks.
3. Run the read-only inventory:

   ```powershell
   python .agents\skills\codebase-wiki\scripts\export-notebooklm.py `
     --root . --preflight --format json
   ```

   Record the returned `preflight_id`. `ready_to_export` is true only when all
   mandatory documents are active, required-document evidence is fresh, and
   deterministic lint has no Critical findings.

4. Read every included file in functional batches. Identify functions from
   runtime entrypoints, use cases, data boundaries, public interfaces, and
   external integrations rather than directory shape alone.
5. Preview included/excluded counts and reasons, functional coverage, Wiki
   pages to add/update/leave unchanged, evidence paths, capacity estimate, and
   every unresolved gap. Wait for confirmation.
6. After confirmation, create or update the required documentation set:
   - `wiki/overview.md`;
   - `wiki/synthesis/project-function-catalog.md`;
   - `wiki/architecture/system-architecture.md`;
   - module/entity pages for every discovered functional area;
   - `wiki/synthesis/system-analysis.md`.
7. Give NotebookLM-prepared pages a stable kebab-case `notebooklm_group`.
   Narrative content is Traditional Chinese; preserve code identifiers, API
   names, and source paths exactly. Mark required coverage as `covered`,
   `partial`, or `gap` instead of inventing facts.
8. Synchronize index/log, rerun Wiki checks, then run:

   ```powershell
   python .agents\skills\codebase-wiki\scripts\export-notebooklm.py `
     --root . --apply --preflight-id <id> --output .notebooklm --format json
   ```

   Apply rescans the Wiki, safe inventory, and configuration. Any change makes
   the ID invalid and requires a new preflight. Direct export without
   `--preflight` followed by `--apply` is rejected.

## Output contract

The exporter owns `.notebooklm/manifest.json`, `.notebooklm/upload-plan.md`,
`.notebooklm/README.md`, and generated `.notebooklm/sources/*.md`. Unknown files
inside the output directory are preserved.

Each schema-v2 source has a stable `logical_source_id`:

- `project-map` for the generated navigation source;
- `docs:<notebooklm-group>` for complete curated Wiki documentation;
- `evidence:<notebooklm-group>` for deduplicated raw evidence;
- `docs:combined` or `evidence:combined` only when slot pressure requires
  deterministic compaction;
- `#part-###` suffixes for sources split at safe boundaries.

The exporter accepts a previous schema-v1 manifest and produces an actionable
one-time migration plan. The schema-v2 manifest records scan summary,
functional-document coverage, input/output hashes, priorities, omissions, and
limits. The upload plan contains:

- `added`: upload the new source;
- `changed`: remove the old static source, then upload the replacement;
- `deleted`: remove the old source;
- `unchanged`: no NotebookLM action.

Do not upload `manifest.json`, `upload-plan.md`, or the README as evidence.

## Limits and safety

The default Enterprise profile is bounded to 300 sources, 200 MB per source,
and 500,000 words per source. The exporter uses lower safety defaults of 180 MB
and 450,000 estimated words, supports `reserved_source_slots`, and rejects any
configuration above the Enterprise hard limits. A different Workspace tier
must lower `source_limit` in `notebooklm.toml`.

Documentation is mandatory and always consumes slots before evidence. Evidence
priority is: explicit extra paths; overview/function-catalog/architecture/SA
direct citations; multiply referenced entrypoints, interfaces, schemas, and
config; other runtime implementation; existing docs. If evidence cannot fit,
omit complete lowest-priority files and record `source_budget` in the manifest,
project map, upload plan, and final report. Never silently truncate evidence.

If mandatory documentation cannot fit after deterministic compaction/splitting,
or any source remains oversized, the exporter fails before committing a new
pack and preserves the previous pack.

`notebooklm.toml` may set `scan_profile = "target" | "framework"`. `target` is
the default and excludes installed framework adapters. The framework repository
uses `framework`, which treats its `.agents`, `.codex`, non-CI `.github`, and
release tooling as product evidence while retaining secret/generated/test/CI
exclusions.

For tenant-specific behavior, verify the current [Google Cloud Gemini Notebook
Enterprise limits](https://docs.cloud.google.com/gemini/enterprise/notebooklm-enterprise/docs/overview?authuser=2)
and [NotebookLM source type and sync rules](https://support.google.com/notebooklm/answer/16215270?co=GENIE.Platform%3DDesktop&hl=en).

## Completion Criterion

Export is complete only when the full safe inventory and functional preview
were shown, the user confirmed, all required documents exist with explicit
coverage states, every generated source is traceable, the manifest and upload
plan were written atomically, no source exceeds its limit, and the final report
lists added, changed, deleted, unchanged, skipped, source-budget omissions, and
all unresolved warnings. Preflight alone never writes `.notebooklm/`.
