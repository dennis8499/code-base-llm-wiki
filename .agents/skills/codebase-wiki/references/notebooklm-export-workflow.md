# NotebookLM Enterprise Export Workflow

Use this workflow when a user explicitly asks to prepare the local Codebase
LLM Wiki for NotebookLM Enterprise or to refresh an existing source pack.

## Scope and authorization

This is a first-class `notebooklm_export` operation. It is an offline export:
the workflow does not call NotebookLM, upload files, or modify raw sources.
The controlled output is the repository-local `.notebooklm/` directory.

The first phase is read-only. If Wiki pages are missing, stale, placeholder, or
contradictory, report the gap and the bounded Ingest scope. Wait for the user's
confirmation before updating Wiki. After confirmation, use the existing Ingest
workflow, update `wiki/index.md`, and append the required `ingest` entry before
running the exporter. If preflight is clean, the user's explicit export request
authorizes the local pack without a raw-tree rescan.

## Source order

1. Read `wiki/index.md` and the relevant Wiki pages; for a whole-project export,
   read every Markdown page except `wiki/log.md`.
2. Run the deterministic frontmatter, stale-source, and Wiki lint checks.
3. Inspect only the raw paths named by Wiki `frontmatter.sources`, plus paths
   explicitly listed in `notebooklm.toml`.
4. If coverage is insufficient, preview the required Batch/Interactive Ingest
   scope and wait for confirmation.
5. Run:

   ```powershell
   python .agents\skills\codebase-wiki\scripts\export-notebooklm.py `
     --root . --output .notebooklm --format json
   ```

## Output contract

The exporter owns `.notebooklm/manifest.json`, `.notebooklm/upload-plan.md`,
`.notebooklm/README.md`, and generated `.notebooklm/sources/*.md`. Unknown files
inside the output directory are preserved.

Each source has a stable `logical_source_id`:

- `project-map` for the generated navigation source;
- `wiki:<repo-relative-path>` for a curated Wiki page;
- `evidence:<parent-directory>` for deduplicated raw evidence groups;
- `#part-###` suffixes for sources split at safe boundaries.

The manifest records input hashes and output hashes. The upload plan contains:

- `added`: upload the new source;
- `changed`: remove the old static source, then upload the replacement;
- `deleted`: remove the old source;
- `unchanged`: no NotebookLM action.

Do not upload `manifest.json`, `upload-plan.md`, or the README as evidence.

## Limits and safety

The default Enterprise profile is bounded to 300 sources, 500 MB per source,
and 500,000 words per source. The exporter uses lower safety defaults of 450 MB
and 450,000 estimated words, supports `reserved_source_slots`, and rejects any
configuration above the Enterprise hard limits. A different Workspace tier
must lower `source_limit` in `notebooklm.toml`.

The default selection excludes credentials, binary files, generated/build
directories, dependency directories, framework adapter directories, and the
export output itself. An excluded path is reported in `manifest.json` rather
than silently treated as evidence.

If a source pack exceeds the available source count or cannot be split within
the configured limits, the exporter fails before committing a new pack.

For tenant-specific behavior, verify the current [Google Cloud Gemini Notebook
Enterprise limits](https://docs.cloud.google.com/gemini/enterprise/notebooklm-enterprise/docs/overview?authuser=2)
and [NotebookLM source type and sync rules](https://support.google.com/notebooklm/answer/16215270?co=GENIE.Platform%3DDesktop&hl=en).

## Completion Criterion

Export is complete only when the Wiki preflight is clean or its confirmed
Ingest is complete, every generated source is traceable to existing evidence,
the manifest and upload plan are written atomically, no source exceeds its
configured limit, and the final report lists all added, changed, deleted,
unchanged, skipped, and unresolved warning items.
