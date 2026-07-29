# Install And Upgrade Workflow

Use this workflow to install or upgrade a Copilot or Codex surface.

## Steps

1. Select `install` for a new target or `upgrade` for an existing target.
2. Run `scripts/install-framework.py` without `--apply`.
3. Review `files`, `conflicts`, and `obsolete_paths`.
4. Resolve conflicts manually; the installer keeps differing target content.
5. Re-run with `--apply`.
6. Run parity, frontmatter, stale, and lint checks in the target.

`install` seeds `wiki/` from `assets/wiki-starter/`. `upgrade` synchronizes only
the framework surface and preserves the target Wiki byte-for-byte. Both actions
install only `.agents/skills/codebase-wiki/`; unrelated local Skills are outside
the surface.

## Completion Criterion

Installation is complete when the selected platform entrypoints and common
Skill exist, guard mode is `target`, target Wiki validation passes, no unrelated
Skill was copied, and every conflict or obsolete path is reported.
