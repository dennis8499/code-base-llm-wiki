# NotebookLM Enterprise Business Analyst Export Workflow

Use this workflow when a user explicitly asks to prepare the local Codebase
LLM Wiki for NotebookLM Enterprise or to refresh an existing source pack.

## Scope and authorization

This is a first-class `notebooklm_export` operation whose fixed audience is
Business Analysts. It is an offline export:
the workflow does not call NotebookLM, upload files, or modify raw sources.
The controlled output is the repository-local `.notebooklm/` directory.

The first phase is always read-only and always scans the full safe project
scope. Existing Wiki pages are the knowledge baseline, not a boundary on raw
discovery. Even when the Wiki is clean, show the business-process/rule coverage preview
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

`notebooklm.toml` may designate exact repo-relative UTF-8 files or directories
as `business_source_paths`. These are business-owned requirements, process
definitions, decision tables, or acceptance specifications. They may opt
selected text into the scan from tests/dev-tooling scope, but never override
secret, binary/generated/dependency, configured exclusion, Wiki/output, or
symlink/reparse safety boundaries. PDF, Word, and Excel are not parsed in v1;
record them as explicit knowledge gaps.

Exclude tests, CI/CD, IaC, build/development tooling, dependency and generated
directories, binaries, credentials/secrets, the Wiki and export output, and
installed Codebase LLM Wiki adapter/schema files. A production entrypoint is
runtime source even if it lives under a scripts directory. Walk the filesystem
top-down beneath the explicit `--root`, pruning an excluded directory before
enumerating its descendants; this keeps the fallback bounded without dropping
ignored, untracked, or nested-repository runtime source. Git status, a clean
worktree, or a root `.git` are not prerequisites. Nested repositories are
ordinary subdirectories: their project files follow the same rules, while
their `.git` metadata remains excluded as generated state. Each pruned root is
reported as a directory-level exclusion with bounded metadata-only counts; the
report never reads or hashes content from that tree.

## Source order

1. Read `wiki/index.md` and every Wiki Markdown page except `wiki/log.md`.
2. Run the deterministic frontmatter, stale-source, and Wiki lint checks.
   NotebookLM preflight keeps the structural and content checks but disables
   Git dirty-path, commit-date, and log-baseline lookups; the preflight remains
   filesystem-only.
3. Run the read-only inventory:

   ```powershell
   python .agents\skills\codebase-wiki\scripts\export-notebooklm.py `
     --root . --preflight --format json
   ```

Treat this first result as the discovery preflight. Its ID becomes invalid when
the confirmed documentation update changes Wiki content; do not reuse it for
apply. `ready_to_export` is true only when all mandatory BA documents are active,
the BA structural contract is complete, required-document evidence is fresh,
deterministic lint has no Critical findings, and the local DLP gate has no
blocking findings.

4. Read designated business sources first, then project documentation,
   use-case entrypoints, orchestration/services, state/data boundaries,
   messages, public interfaces, and integrations. Identify end-to-end business
   processes by actor, trigger, precondition, outcome, rule, exception, and
   state transition rather than directory shape.
5. Preview included file counts and reasons, pruned excluded-root counts and
   bounded metadata summaries, business capability/process/rule/term coverage, Wiki pages to
   add/update/leave unchanged, evidence paths, capacity estimate, and every
   unresolved gap. A truncated or unreadable excluded-root summary is a
   warning, not evidence that the root was included. Wait for confirmation.
6. After confirmation, create or update the required BA documentation set:
   - `wiki/overview.md`;
   - `wiki/synthesis/business-process-catalog.md`;
   - `wiki/synthesis/business-rule-catalog.md`;
   - `wiki/synthesis/business-glossary.md`;
   - `wiki/synthesis/business-knowledge-gaps.md`;
   - one `wiki/processes/` page per cataloged end-to-end process;
   - one `wiki/rules/` page per independently queryable business rule.
7. Use stable `business-{capability}` `notebooklm_group` values. BA pages use
   `notebooklm_role: business`; selected module/entity/architecture pages use
   `traceability`; unrelated pages use `exclude` or remain unclassified and are
   omitted with a warning. Narrative content is Traditional Chinese.
8. Label claims as `business-confirmed`, `implementation-observed`, `inference`,
   or `gap`. Code/config/schema can prove observed behavior, not approved policy.
   Registered business gaps are allowed; unlabeled or dangling knowledge is not.
9. Synchronize index/log and rerun Wiki checks. Then run a second readiness
   preflight and use its new ID for apply:

   ```powershell
   python .agents\skills\codebase-wiki\scripts\export-notebooklm.py `
     --root . --preflight --format json
   ```

10. Show the second result, including readiness gates, capacity, DLP status, and
    migration mode, then wait for a second confirmation. Apply only with the
    second ID:

   ```powershell
   python .agents\skills\codebase-wiki\scripts\export-notebooklm.py `
     --root . --apply --preflight-id <id> --output .notebooklm --format json
   ```

   Apply rescans the Wiki, safe inventory, and configuration. Any later change makes
   the ID invalid and requires a new preflight. Direct export without
   `--preflight` followed by `--apply` is rejected.

## Output contract

The exporter owns `.notebooklm/manifest.json`, `.notebooklm/upload-plan.md`,
`.notebooklm/README.md`, and generated `.notebooklm/sources/*.md`. Unknown files
inside the output directory are preserved.

Each generated source has a stable `logical_source_id`:

- `query-index` for the compact BA-first direct-lookup router;
- `project-map` for the generated navigation source;
- `docs:<business-group>` for complete curated BA Wiki documentation;
- `business-evidence:<business-group>` for designated business-owned text;
- `trace:<business-group>` for technical Wiki/raw implementation traceability;
- `docs:combined`, `business-evidence:combined`, or `trace:combined` only when slot pressure requires
  deterministic compaction;
- `#part-###` suffixes for sources split at safe boundaries.

The exporter accepts previous schema-v1/v2/v3 manifests. The first export from
a non-BA retrieval contract sets `migration.requires_full_rebuild=true` and
instructs the uploader to remove all old static sources before uploading the new
pack. The schema-v4 manifest records audience `business-analyst`, source roles,
business coverage, and scan summary, including
file-level exclusions and pruned excluded-root summaries,
business-process/rule coverage, input/output hashes, priorities, omissions,
limits, the offline DLP profile/safe finding summary, and the
`business-first-ba-v1` retrieval contract. The retrieval contract points
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

The query index, project map, BA documentation, and designated business evidence
are mandatory. They consume slots before technical traceability. Traceability
priority is: BA process/rule direct citations; multiply referenced state models,
interfaces, schemas, and config; other runtime implementation; explicitly marked
technical Wiki pages. If traceability cannot fit, omit complete lowest-priority
files and record `source_budget` in the manifest, project map, upload plan, and
final report. Never truncate or omit mandatory BA knowledge silently.

Excluded-root summaries use a fixed metadata entry bound. They may report
`truncated` or metadata errors, but they never inspect file content and do not
turn excluded files into evidence.

If mandatory documentation cannot fit after deterministic compaction/splitting,
or any source remains oversized, the exporter fails before committing a new
pack and preserves the previous pack.

`notebooklm.toml` may set `scan_profile = "target" | "framework"`,
`business_source_paths`, and `include_traceability`. Deprecated
`include_evidence` maps to `include_traceability`; conflicting values fail
closed. `target` is
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

Export is complete only when the full safe inventory and BA coverage preview
were shown, the user confirmed, the second readiness preflight succeeded, all
required documents and process/rule pages exist with explicit evidence states,
the DLP gate is passed or explicitly allowlisted, the
`query-index` and `project-map` sources are present, every generated source is
traceable, the manifest and upload plan were written atomically, no source
exceeds its limit, and the final report lists added,
changed, deleted, unchanged, skipped, traceability source-budget omissions,
DLP status, migration/full-rebuild status, and
all unresolved warnings, including excluded-root truncation or metadata errors.
Preflight alone never writes `.notebooklm/`.
