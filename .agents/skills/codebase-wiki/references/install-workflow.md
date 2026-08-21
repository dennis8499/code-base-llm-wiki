# Install And Upgrade Workflow

Use this workflow to install or upgrade a Copilot or Codex surface.

## Steps

1. Select `install` for a new target or `upgrade` for an existing target.
2. Run `scripts/install-framework.py` without `--apply`.
3. Choose `--guard-mode wiki-only` (safe dedicated Wiki session) or explicit
   `coexist` (normal coding and Wiki work in the same repo).
4. Review `managed`, `changes`, `preserved`, `conflicts`, and `obsolete_paths`.
5. Resolve true two-sided conflicts manually; user-only changes are preserved.
6. Re-run with `--apply`.
7. Run parity, frontmatter, stale, log, and lint checks in the target.

`install` seeds `wiki/` from `assets/wiki-starter/`. `upgrade` synchronizes only
the framework surface and preserves the target Wiki byte-for-byte. Both actions
install only `.agents/skills/codebase-wiki/`; unrelated local Skills are outside
the surface.

Contract v3 stores `.agents/skills/codebase-wiki/install-state.json` with the
upstream fingerprints needed to distinguish upstream-only, user-only, and
two-sided changes. Root agent instructions use a managed marker block so local
content around the block survives upgrades. Writes are staged and rolled back
if application fails. Starter dates are rendered from the installation date.

## Completion Criterion

Installation is complete when the selected platform entrypoints and common
Skill exist, guard mode is the selected `wiki-only` or `coexist` value, target
Wiki validation passes, no unrelated Skill was copied, and every conflict or
obsolete path is reported.
