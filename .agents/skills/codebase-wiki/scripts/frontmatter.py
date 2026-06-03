"""Small frontmatter parser for the wiki maintenance scripts.

This intentionally supports only the YAML subset used by the wiki templates:
plain scalars, quoted scalars, inline arrays, and simple block arrays.
Keeping it dependency-free lets the helper scripts run in a clean Copilot
agent environment without requiring PyYAML.
"""

from __future__ import annotations

import re
import sys


FRONTMATTER_PATTERN = re.compile(r"^---\s*\n(.*?)\n---", re.DOTALL)


def _strip_quotes(value: str) -> str:
    if len(value) >= 2 and value[0] == value[-1] and value[0] in {"'", '"'}:
        return value[1:-1]
    return value


def _parse_scalar(value: str):
    value = value.strip()
    if value == "[]":
        return []
    if value.startswith("[") and value.endswith("]"):
        inner = value[1:-1].strip()
        if not inner:
            return []
        return [_strip_quotes(item.strip()) for item in inner.split(",") if item.strip()]
    return _strip_quotes(value)


def parse_frontmatter_text(text: str) -> dict:
    match = FRONTMATTER_PATTERN.match(text)
    if not match:
        return {}

    frontmatter: dict[str, object] = {}
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


def configure_utf8_stdio():
    for stream in (sys.stdout, sys.stderr):
        if hasattr(stream, "reconfigure"):
            stream.reconfigure(encoding="utf-8", errors="replace")
