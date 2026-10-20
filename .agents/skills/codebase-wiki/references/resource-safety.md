# Bounded evidence and Wiki writes

Use these helpers for local Git evidence, large-source discovery and every
authorized durable Wiki update. Parallel analysis may share evidence; one writer
commits pages, index and the operation log together.

## Local Git evidence

Run history commands through `scripts/offline-git.py --root <repo> -- <command>`.
For example, use `-- log --follow --name-status -- src/service.py` or
`-- show --format=fuller --stat --patch <sha>`. The helper allows local evidence
commands, disables lazy fetching, prompts, fsmonitor and external diff/textconv,
and stops the process tree after 30 seconds or 8 MiB of combined output.
`--timeout` and `--max-output-bytes` can explicitly bound a larger authorized
query. A missing object or exceeded budget remains a history/coverage gap;
narrow the path/range instead of fetching automatically.

## Scanner and snapshot

The shared scanner still enumerates ignored, untracked and nested sources.
It hashes and UTF-8 decodes one bounded stream per safe file. Configure
`scan_max_file_bytes` (default 64 MiB) and `scan_max_total_bytes` (default 256 MiB)
in `notebooklm.toml`; both must be positive integers. A source beyond either
budget is recorded as unreadable/blocked, so full Ingest and export remain
partial. Increase the explicit budget or resolve the source; an exclusion is
not an equivalent completion result. The total allowance charges actual bytes
read, including binary, invalid UTF-8 and oversized-file failures. Once it is
exhausted, discovery continues without opening subsequent sources. Reads start
at 8 KiB and grow to at most 1 MiB after full chunks, avoiding large allocations
for small files while keeping one stream for hashing and decoding. Exact total
boundaries require a current regular-file EOF observation; otherwise the file
remains blocked. Excluded-directory summaries consume at
most 4096 entries plus one lookahead, without reading excluded contents.

Preflight shares captured source text/SHA and Wiki text/frontmatter with DLP and
lint. Caches live only within that operation. Apply rebuilds the discovery and
Wiki byte identities under the output lock; changed source, scope, config or
Wiki bytes preserve the previous pack. Matching inputs reuse the already
validated deterministic plan and DLP results.

## Wiki transaction

1. Capture `python .agents/skills/codebase-wiki/scripts/wiki-write.py snapshot
   --root .` before preparing the authorized page preview.
2. Preserve user content and prepare one JSON plan in the OS temporary directory:

   ```json
   {
     "schema": "codebase-wiki-write/v1",
     "snapshot": {"wiki/index.md": "<sha256>", "wiki/log.md": "<sha256>"},
     "writes": {"wiki/index.md": "<complete index>", "wiki/modules/example.md": "<complete page>"},
     "deletes": [],
     "log_append": "## [YYYY-MM-DD] ingest | Subject\n\n- Affected pages: [[example]], [[index]]"
   }
   ```

   Keep the complete captured snapshot, including unchanged files. `writes`
   contains UTF-8 text and includes the synchronized index. Use
   `rebuild-index.py wiki --stdout` for a read-only index rendering when needed.
   The transaction appends one operation, preserving the entire existing log
   body; only its frontmatter date advances. An initial missing log receives
   the standard log header.
3. Apply the bounded authorized plan with `wiki-write.py apply --root . --plan
   <temporary-plan.json>`, then run the routed deterministic and semantic checks.
   Raw sources stay outside the write surface. The helper does not authorize
   additional content or replace review of the staged page text.

An OS lock rejects a second writer. Full-Wiki compare-and-swap rejects additions,
deletions and changed user notes after the preview. Refresh/reconcile a conflict;
retain the user's newer content. File staging and a recovery journal restore
interrupted writes. A conflicting edit after a crash stops recovery instead of
overwriting it. Shell/editor writes that bypass the helper do not participate in
its lock, so use the transaction for Agent Wiki persistence. Readers verify their
snapshot; the file transaction does not promise isolation for unlocked readers.

Standalone `rebuild-index.py wiki` also uses the writer and appends an `update`
operation. Batch Wiki work uses `--stdout` and includes its index in the one
combined transaction rather than creating an additional index-only operation.

Keep `.codebase-wiki-write.*` as generated, ignored local state when configuring
the target repository. Wiki operations do not edit the target's ignore policy.
