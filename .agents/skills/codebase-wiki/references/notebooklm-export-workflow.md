# NotebookLM Enterprise BA Functional Export Workflow

Use this workflow for NotebookLM export preparation. The fixed outcome is one
NotebookLM Enterprise notebook whose uploaded static sources contain only BA
functional documentation derived from the full safe codebase.

Schema v5 uses knowledge contract `business-functional-requirements-v2` and
retrieval contract `business-only-ba-v2`.

## Scope and authorization

Raw source code, configuration, behavioral tests, schemas, and project docs are
read-only analysis inputs. Wiki pages and the repository-local `.notebooklm/`
pack are the only writable surfaces. The workflow is offline: it does not call
NotebookLM, Google Cloud DLP, or an upload API.

The first phase is always read-only and always scans the full safe project
scope. Existing Wiki pages are the knowledge baseline, not a boundary on raw
discovery. Even when the Wiki is clean, show the functional-requirement,
process, rule, and file-disposition coverage preview
and wait for confirmation before updating Wiki or writing the local pack.

After confirmation, re-analyze the entire safe scope and regenerate managed BA
sections; do not limit work to previously stale pages. Preserve user-authored
notes, synchronize `wiki/index.md`, and append one valid operation selected from
`log-operations.md` (normally `ingest`, or `update` for framework maintenance)
covering the complete preparation. Raw project sources remain read-only.

## Safe project scope

Include every UTF-8 project-owned text file in these categories:

- runtime source and production entrypoints;
- runtime-required config and dependency manifests;
- database schemas, migrations, messages, and interface schemas;
- existing project documentation;
- behavioral tests and acceptance specifications (included by default).

`notebooklm.toml` may designate exact repo-relative UTF-8 files or directories
as `business_source_paths`. These are business-owned requirements, process
definitions, decision tables, or acceptance specifications. They may opt
selected text into the scan from dev-tooling scope, but never override
secret, binary/generated/dependency, configured exclusion, Wiki/output, or
symlink/reparse safety boundaries. PDF, Word, and Excel are not parsed in v1;
record them as explicit knowledge gaps.

Exclude CI/CD, IaC, build/development tooling, dependency and generated
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

Set `analysis_include_tests = false` only when the user explicitly narrows the
analysis contract. Every included safe file must be classified in
`wiki/synthesis/codebase-functional-coverage.md` as `functional-evidence`,
`supporting-technical`, `no-observable-behavior`, or `analysis-gap`. Export is
blocked for uncovered files, any remaining `analysis-gap`, a missing required
functional-requirement link, or a dangling requirement link.

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
the BA structural contract and full file-disposition ledger are complete,
required-document evidence is fresh, deterministic lint has no Critical
findings, and the exact post-mask payload fits the configured limits.

4. Read designated business sources first, then project documentation,
   use-case entrypoints, orchestration/services, state/data boundaries,
   messages, public interfaces, and integrations. Identify functional
   requirements by observable behavior, then connect actor, trigger,
   precondition, outcome, rule, exception, state transition, and stable
   acceptance criteria rather than mirroring directory shape.
5. Preview included file counts and reasons, pruned excluded-root counts and
   bounded metadata summaries, requirement/capability/process/rule/term
   coverage, Wiki pages to regenerate, disposition results, capacity estimate, and every
   unresolved gap. A truncated or unreadable excluded-root summary is a
   warning, not evidence that the root was included. Wait for confirmation.
6. After confirmation, create or update the required BA documentation set:
   - `wiki/overview.md`;
   - `wiki/synthesis/functional-requirement-catalog.md`;
   - `wiki/synthesis/business-process-catalog.md`;
   - `wiki/synthesis/business-rule-catalog.md`;
   - `wiki/synthesis/business-glossary.md`;
   - `wiki/synthesis/business-knowledge-gaps.md`;
   - `wiki/synthesis/codebase-functional-coverage.md` (local-only gate);
   - one `wiki/requirements/` page per independently testable capability;
   - one `wiki/processes/` page per cataloged end-to-end process;
   - one `wiki/rules/` page per independently queryable business rule.
7. Each requirement uses stable `fr-*` and `cap-*` IDs, links at least one
   process, and contains `## 驗收條件` with stable `AC-*` IDs. Use stable
   `business-{capability}` `notebooklm_group` values. Only BA pages use `notebooklm_role: business`;
   local governance and technical pages use `exclude`. Narrative content is
   Traditional Chinese.
8. Label claims as `business-confirmed`, `implementation-observed`, `inference`,
   or `gap`. Code/config/schema can prove observed behavior, not approved policy.
   Registered business gaps are allowed; unlabeled or dangling knowledge is not.
9. Regenerate content inside `codebase-wiki:managed` markers, preserve content
   inside `codebase-wiki:user-notes` markers, and place reviewer-only paths or
   symbols inside `notebooklm:local-only` markers. Synchronize index/log and
   rerun Wiki checks. Then run a second readiness preflight and use its new ID
   for apply:

   ```powershell
   python .agents\skills\codebase-wiki\scripts\export-notebooklm.py `
     --root . --preflight --format json
   ```

10. Show the second result, including readiness gates, exact `pack_plan`,
    capacity, DLP masking status, and migration mode, then wait for a second
    confirmation. Apply only with the
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

- `query-index` for the BA functional-requirement router;
- `project-map` for the generated navigation source;
- `docs:<business-group>` for complete curated BA Wiki documentation;
- `docs:combined` only when slot pressure requires deterministic compaction;
- `#part-###` suffixes for sources split at safe boundaries.

The exporter accepts previous schema-v1/v2/v3/v4 manifests. The first export
from an older schema or retrieval contract sets
`migration.requires_full_rebuild=true` and
instructs the uploader to remove all old static sources before uploading the new
pack. The schema-v5 manifest records audience `business-analyst`, source roles,
functional/business coverage, and scan summary, including
file-level exclusions and pruned excluded-root summaries,
requirement/process/rule coverage, file dispositions, input/output hashes,
limits, the offline DLP profile/safe finding summary, and the
`business-only-ba-v2` retrieval contract. The retrieval contract points
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

The default Enterprise profile is bounded to 300 sources, 500 MB per source,
and 500,000 words per source. The exporter uses lower safety defaults of 450 MB
and 450,000 estimated words, supports `reserved_source_slots`, and rejects any
configuration above the Enterprise hard limits. `estimated_words` uses the
`han_characters_plus_non_han_tokens` model: Han/CJK characters are counted
individually and non-Han, non-whitespace token runs are counted separately, so
mixed Traditional Chinese and code content is not underestimated. A different
Workspace tier must lower `source_limit` in `notebooklm.toml`.

The query index, project map, and BA documentation are mandatory. Raw business
evidence, source code, configuration, and technical traceability are never
upload candidates. If the BA documents cannot fit, compact/split them
deterministically or fail; never silently omit functional knowledge.

Excluded-root summaries use a fixed metadata entry bound. They may report
`truncated` or metadata errors, but they never inspect file content and do not
turn excluded files into evidence.

If mandatory documentation cannot fit after deterministic compaction/splitting,
or any source remains oversized, the exporter fails before committing a new
pack and preserves the previous pack.

`notebooklm.toml` may set `scan_profile = "target" | "framework"`,
`content_mode = "ba_only"`, `analysis_include_tests`, and
`business_source_paths`. Schema v5 rejects legacy `include_traceability`,
`include_evidence`, and `dlp_allowlist` settings with a migration message.
`target` is
the default and excludes installed framework adapters. The framework repository
uses `framework`, which treats its `.agents`, `.codex`, non-CI `.github`, and
release tooling as product evidence while retaining secret/generated/CI
exclusions.

## Offline DLP masking

The exporter runs a local deterministic DLP profile during analysis, managed
Wiki materialization, and exact final-payload planning. It does not call Google
Cloud, Model Armor, or NotebookLM. The
`notebooklm-enterprise-ba-mask-v1` profile checks high-confidence
`CREDIT_CARD_NUMBER`, `FINANCIAL_ACCOUNT_NUMBER`, `GCP_CREDENTIALS`,
`GCP_API_KEY`, and `PASSWORD` patterns. Existing sensitive filename exclusions
remain a separate safety layer.

Analysis operates on an in-memory copy and replaces matches with
`[MASKED:<RULE>]`; raw repository files are never modified. Managed Wiki inputs
are masked before materialization. The exact final payload is masked again,
hashed again, and rescanned; any residual finding blocks commit and preserves
the previous pack. Reports contain only path, line, rule, severity, and a
SHA-256 fingerprint; matched values and surrounding text are never persisted.
There is no allowlist.

For tenant-specific behavior, verify the current [Google Cloud Gemini Notebook
Enterprise limits](https://docs.cloud.google.com/gemini/enterprise/notebooklm-enterprise/docs/overview)
and [NotebookLM source type and sync rules](https://support.google.com/notebooklm/answer/16215270).

## Completion Criterion

Export is complete only when the entire safe scope was regenerated into the BA
model, user notes were preserved, every safe file has a non-gap disposition,
every active requirement is cataloged and has stable acceptance criteria, Wiki
checks pass, the exact final payload passes post-mask DLP and capacity limits,
`query-index` and `project-map` are present, the schema-v5 manifest and upload
plan were written atomically, and the final report lists actions, coverage, DLP
masking counts, migration mode, and unresolved business-confirmation gaps.
Preflight alone never writes `.notebooklm/`.
