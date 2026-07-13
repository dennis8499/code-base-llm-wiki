#!/usr/bin/env python3
"""Deprecated compatibility wrapper for the capability parity check.

Usage:
    python .agents/skills/codebase-wiki/scripts/check-dual-entry-sync.py

The old byte-comparison model produced false drift on Windows line endings and
did not validate platform adapters. Use ``parity-check.py`` for the canonical
semantic check.
"""

from __future__ import annotations

import hashlib
import pathlib
import sys


REPO_ROOT = pathlib.Path(__file__).resolve().parents[4]


def file_hash(path: pathlib.Path) -> str:
    return hashlib.sha256(path.read_bytes()).hexdigest()


def iter_files(root: pathlib.Path, *, exclude: set[str] | None = None) -> dict[str, pathlib.Path]:
    exclude = exclude or set()
    result: dict[str, pathlib.Path] = {}
    for path in sorted(root.rglob("*")):
        if not path.is_file():
            continue
        rel = path.relative_to(root).as_posix()
        if rel in exclude:
            continue
        if "__pycache__" in path.parts or path.suffix == ".pyc":
            continue
        result[rel] = path
    return result


def compare_tree(
    label: str,
    left_root: pathlib.Path,
    right_root: pathlib.Path,
    *,
    left_exclude: set[str] | None = None,
    right_exclude: set[str] | None = None,
) -> list[str]:
    errors: list[str] = []
    left = iter_files(left_root, exclude=left_exclude)
    right = iter_files(right_root, exclude=right_exclude)

    left_only = sorted(set(left) - set(right))
    right_only = sorted(set(right) - set(left))
    changed = sorted(rel for rel in set(left) & set(right) if file_hash(left[rel]) != file_hash(right[rel]))

    for rel in left_only:
        errors.append(f"{label}: missing in {right_root}: {rel}")
    for rel in right_only:
        errors.append(f"{label}: missing in {left_root}: {rel}")
    for rel in changed:
        errors.append(f"{label}: content drift: {rel}")
    return errors


def main() -> None:
    """Compatibility entrypoint; parity-check is the canonical validator."""
    parity_script = REPO_ROOT / ".agents" / "skills" / "codebase-wiki" / "scripts" / "parity-check.py"
    namespace: dict[str, object] = {"__file__": str(parity_script), "__name__": "__parity_check__"}
    exec(compile(parity_script.read_text(encoding="utf-8"), str(parity_script), "exec"), namespace)
    result = namespace["main"]
    raise SystemExit(result())


if __name__ == "__main__":
    main()
