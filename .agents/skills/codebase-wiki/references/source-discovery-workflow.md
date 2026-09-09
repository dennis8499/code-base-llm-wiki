# Source Discovery with tgrep

This is an optional read-only accelerator for Interactive/Batch Ingest and Code
Archaeology. It is not a new user-facing operation and it is never part of the
Wiki-first Query workflow.

## Boundary

1. Read `wiki/index.md` and the relevant Wiki pages first.
2. Inspect the listed raw sources only when the Wiki is missing, stale,
   contradictory, or insufficient.
3. Use `scripts/tgrep-search.py` to locate candidate files, symbols, imports,
   exports, routes, or historical field references.
4. Re-read every candidate source with the normal read operation before making
   an evidence-backed claim. Search output is a locator, not a source digest or
   a substitute for reading the current file.

Query must continue to use only the Wiki and its listed source paths. Do not
invoke this wrapper for Query, Lint, BA, SA, SD, or NotebookLM export routing.

## Invocation

Run from the repository root and always provide the search root and scope:

```powershell
python .agents\skills\codebase-wiki\scripts\tgrep-search.py `
  --root . --path src --fixed --files-only --pattern "PaymentService"
```

Supported wrapper options are deliberately narrow: `--pattern`, `--files`,
`--fixed`, `--ignore-case`, `--files-only`, `--count`, `--context`, repeated
`--glob`, repeated `--type`, `--no-index`, and `--json`. The wrapper places
`--` before a search pattern, does not use a shell, and rejects a path that
resolves outside `--root`.

Use `--fixed` for a user-provided symbol or string, `--files-only` before a
broad content query, and `--context 2` or `--context 3` when surrounding code
is needed. Use `--no-index` when the latest filesystem state is required or an
existing index may be stale.

## Tool and index policy

The packaged binary is Windows x64 only. On unsupported hosts, a missing
binary, an invalid manifest, or a hash mismatch, the wrapper reports a
controlled unavailable result and the workflow continues with the host's
normal read/search tools. There is no PATH fallback.

The wrapper invokes search only. It never invokes `tgrep index` or `tgrep
serve`, never creates `.tgrep/`, and never changes raw sources. If a user has
already started a tgrep server or created an on-disk index, tgrep may use it;
otherwise it performs its normal full scan. Existing index/server results may
lag behind edits, so current evidence must use `--no-index` and direct reads.

The tgrep process exit codes are preserved: `0` means a match, `1` means no
match, and `2` means a search error. Wrapper availability/configuration errors
use `3`; a workflow should treat that as a tooling fallback, not as a source
claim.

## Safety

- The binary path and SHA-256 are pinned in `bin/tgrep-manifest.json`.
- Search roots are canonicalized and must remain within the requested repo
  root; symlink/reparse escapes are rejected.
- Only allowlisted search flags are forwarded.
- Search patterns are passed after `--`, so values such as `serve`, `index`, or
  `status` remain patterns rather than subcommands.
- `.tgrep/` is generated local state and must remain untracked and out of
  release archives.
