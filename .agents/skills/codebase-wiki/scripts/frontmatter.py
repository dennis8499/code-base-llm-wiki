"""Small frontmatter parser for the wiki maintenance scripts.

This intentionally supports only the YAML subset used by the wiki templates:
plain scalars, quoted scalars, inline arrays, and simple block arrays.
Keeping it dependency-free lets the helper scripts run in a clean Codex
environment without requiring PyYAML.
"""

from __future__ import annotations

import os
from pathlib import Path
import re
import stat
import sys
from typing import Any


FRONTMATTER_PATTERN = re.compile(r"^---\s*\n(.*?)\n---", re.DOTALL)


def is_reparse_point(path: Path) -> bool:
    """Detect symlinks and Windows reparse points without following them."""

    try:
        if path.is_symlink():
            return True
    except OSError:
        return True
    if os.name != "nt":
        return False
    try:
        attributes = os.stat(path, follow_symlinks=False).st_file_attributes
    except FileNotFoundError:
        return False
    except OSError:
        return True
    return bool(attributes & getattr(stat, "FILE_ATTRIBUTE_REPARSE_POINT", 0x400))


def validate_regular_tree(root: Path) -> None:
    """Reject a directory tree containing links or Windows reparse points."""

    if is_reparse_point(root):
        raise OSError(f"directory must not be a symlink or reparse point: {root}")
    if not root.is_dir():
        raise OSError(f"directory is not a directory: {root}")
    for path in root.rglob("*"):
        if is_reparse_point(path):
            raise OSError(f"directory tree must not contain symlink or reparse point: {path}")


def _strip_quotes(value: str) -> str:
    if len(value) >= 2 and value[0] == value[-1] and value[0] in {"'", '"'}:
        return value[1:-1]
    return value


def _parse_scalar(value: str) -> Any:
    value = value.strip()
    if value == "[]":
        return []
    if value.startswith("[") and value.endswith("]"):
        inner = value[1:-1].strip()
        if not inner:
            return []
        return [_strip_quotes(item.strip()) for item in inner.split(",") if item.strip()]
    return _strip_quotes(value)


def parse_frontmatter_text(text: str) -> dict[str, Any]:
    match = FRONTMATTER_PATTERN.match(text)
    if not match:
        return {}

    frontmatter: dict[str, Any] = {}
    current_list_key: str | None = None

    for raw_line in match.group(1).splitlines():
        if not raw_line.strip() or raw_line.lstrip().startswith("#"):
            continue

        if raw_line.startswith((" ", "\t")):
            line = raw_line.strip()
            if current_list_key and line.startswith("- "):
                value = _parse_scalar(line[2:])
                frontmatter.setdefault(current_list_key, [])
                if isinstance(frontmatter[current_list_key], list):
                    frontmatter[current_list_key].append(value)
            continue

        current_list_key = None
        if ":" not in raw_line:
            continue

        key, value = raw_line.split(":", 1)
        key = key.strip()
        value = value.strip()

        if not key:
            continue
        if value == "":
            frontmatter[key] = []
            current_list_key = key
        else:
            frontmatter[key] = _parse_scalar(value)

    return frontmatter


def configure_utf8_stdio() -> None:
    for stream in (sys.stdout, sys.stderr):
        if hasattr(stream, "reconfigure"):
            stream.reconfigure(encoding="utf-8", errors="replace")
