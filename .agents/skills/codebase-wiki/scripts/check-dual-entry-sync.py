#!/usr/bin/env python3
"""Check that mirrored Copilot and Codex entrypoint files stay in sync.

Usage:
    python .agents/skills/codebase-wiki/scripts/check-dual-entry-sync.py

This validates intentionally mirrored files only:
- .agents/skills/codebase-wiki/ <-> .github/skills/codebase-wiki/
- .codex/hooks/scripts/ <-> .github/hooks/scripts/

Platform-specific config, hook JSON files, and Codex-only skill metadata are
not compared.
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
    checks = [
        (
            "skills",
            REPO_ROOT / ".agents" / "skills" / "codebase-wiki",
            REPO_ROOT / ".github" / "skills" / "codebase-wiki",
            {"agents/openai.yaml"},
            set(),
        ),
        (
            "hook scripts",
            REPO_ROOT / ".codex" / "hooks" / "scripts",
            REPO_ROOT / ".github" / "hooks" / "scripts",
            set(),
            set(),
        ),
    ]

    errors: list[str] = []
    for label, left, right, left_exclude, right_exclude in checks:
        if not left.is_dir():
            errors.append(f"{label}: left root missing: {left}")
            continue
        if not right.is_dir():
            errors.append(f"{label}: right root missing: {right}")
            continue
        errors.extend(compare_tree(label, left, right, left_exclude=left_exclude, right_exclude=right_exclude))

    if errors:
        print("Dual Entry Sync Check")
        print("=" * 40)
        for error in errors:
            print(f"- {error}")
        print(f"\nFAILED: {len(errors)} drift item(s)")
        sys.exit(1)

    print("OK: mirrored skill files and hook scripts are in sync")


if __name__ == "__main__":
    main()
