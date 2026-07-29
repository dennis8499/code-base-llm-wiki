# Framework Maintenance

Use this branch only for changes to the Codebase LLM Wiki framework repository.

## Maintained Surfaces

- Root entrypoints: `AGENTS.md`, `Codex.md`, `README.md`, `ChangeLog.md`
- Shared schema: `.agents/skills/codebase-wiki/`
- Platform adapters: `.github/`, `.codex/`
- Product evidence: `docs/`, `samples/`, `tests/`, `wiki/`

Keep target-codebase rules distinct from framework-repository maintenance.
Installer surfaces exclude framework-only docs, samples, tests, and the
framework Wiki.

## Completion Criterion

Maintenance is complete when behavior changes have matching regression tests,
both platform adapters pass parity, product documentation reflects the public
contract, `ChangeLog.md` is updated, the framework Wiki/index are synchronized,
and one append-only `update` log entry records the change.
