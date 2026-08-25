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
mandatory documents are active, required-document evidence is fresh,
deterministic lint has no Critical findings, and the local DLP gate has no
blocking findings.

4. Read every included file in functional batches. Identify functions from
   runtime entrypoints, use cases, data boundaries, public interfaces, and
   external integrations rather than directory shape alone.
5. Preview included/excluded counts and reasons, functional coverage, Wiki
   pages to add/update/leave unchanged, evidence paths, capacity estimate, and
   every unresolved gap. Wait for confirmation.
6. After confirmation, create or update the required documentation set. Documentation is mandatory for export:
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

Each generated source has a stable `logical_source_id`:

- `query-index` for the compact Wiki-first direct-lookup router;
- `project-map` for the generated navigation source;
- `docs:<notebooklm-group>` for complete curated Wiki documentation;
- `evidence:<notebooklm-group>` for deduplicated raw evidence;
- `docs:combined` or `evidence:combined` only when slot pressure requires
  deterministic compaction;
- `#part-###` suffixes for sources split at safe boundaries.

The exporter accepts previous schema-v1/v2 manifests and produces an actionable
one-time migration plan. The schema-v3 manifest records scan summary,
functional-document coverage, input/output hashes, priorities, omissions,
limits, the offline DLP profile/safe finding summary, and the
`wiki-first-direct-lookup-v1` retrieval contract. The retrieval contract points
to `query-index.md`, limits the primary route to at most five source groups, and
keeps the copy/paste Custom instructions in the local README. The upload plan
contains:

- `added`: upload the new source;
- `changed`: remove the old static source, then upload the replacement;
- `deleted`: remove the old source;
- `unchanged`: no NotebookLM action.

Do not upload `manifest.json`, `upload-plan.md`, or the README as evidence.

The generated README also documents a one-time rebuild procedure: remove old
static sources from the same NotebookLM notebook, upload every Markdown file
under `sources/`, and apply the Custom instructions when the tenant UI exposes
them. The exporter remains offline and does not delete or upload cloud sources.

## Limits and safety

The default Enterprise profile is bounded to 300 sources, 200 MB per source,
and 500,000 words per source. The exporter uses lower safety defaults of 180 MB
and 450,000 estimated words, supports `reserved_source_slots`, and rejects any
configuration above the Enterprise hard limits. `estimated_words` uses the
`han_characters_plus_non_han_tokens` model: Han/CJK characters are counted
individually and non-Han, non-whitespace token runs are counted separately, so
mixed Traditional Chinese and code content is not underestimated. A different
Workspace tier must lower `source_limit` in `notebooklm.toml`.

The query index, project map, and documentation are mandatory and consume slots
before evidence. Evidence
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

## Offline DLP preflight

The exporter runs a local, deterministic Basic DLP profile before packaging
content. It does not call Google Cloud, Model Armor, or NotebookLM. The default
`notebooklm-enterprise-basic` profile checks high-confidence
`CREDIT_CARD_NUMBER`, `FINANCIAL_ACCOUNT_NUMBER`, `GCP_CREDENTIALS`,
`GCP_API_KEY`, and `PASSWORD` patterns. Existing sensitive filename exclusions
remain a separate safety layer.

The default enforcement is `inspect_and_block`: any non-allowlisted finding
makes `ready_to_export` false and prevents `--apply` from replacing an existing
pack. Reports contain only repo-relative path, line, rule, severity, and a
SHA-256 fingerprint; matched values and surrounding text are never persisted.

Known false positives can be allowlisted exactly in `notebooklm.toml`:

```toml
dlp_profile = "notebooklm-enterprise-basic"
dlp_allowlist = [
  { path = "docs/example.md", rule = "GCP_API_KEY", fingerprint = "sha256:<64 lowercase hex>" },
]
```

An allowlisted match is reported as `passed_with_allowlist` with a warning. The
local profile is an export-side approximation; tenant-specific Advanced
Sensitive Data Protection templates may apply additional cloud-side checks.

For tenant-specific behavior, verify the current [Google Cloud Gemini Notebook
Enterprise limits](https://docs.cloud.google.com/gemini/enterprise/notebooklm-enterprise/docs/overview?authuser=2)
and [NotebookLM source type and sync rules](https://support.google.com/notebooklm/answer/16215270?co=GENIE.Platform%3DDesktop&hl=en).

## Completion Criterion

Export is complete only when the full safe inventory and functional preview
were shown, the user confirmed, all required documents exist with explicit
coverage states, the DLP gate is passed or explicitly allowlisted, the
`query-index` and `project-map` sources are present, every generated source is
traceable, the manifest and upload plan were written atomically, no source
exceeds its limit, and the final report lists added,
changed, deleted, unchanged, skipped, source-budget omissions, DLP status, and
all unresolved warnings. Preflight alone never writes `.notebooklm/`.
