#!/usr/bin/env python3
"""Validate the append-only Wiki activity log without rewriting it."""

from __future__ import annotations

import argparse
import datetime as dt
import json
from pathlib import Path
import re
import subprocess
from typing import Any

from frontmatter import (
    configure_utf8_stdio,
    parse_frontmatter_text,
    validate_regular_tree,
)


ALLOWED_OPERATIONS = {
    "ingest",
    "query",
    "lint",
    "update",
    "init",
    "adr",
    "synthesis",
    "guide",
    "archaeology",
}
CONTRACT_MARKER = "<!-- codebase-wiki:log-contract-v1 -->"
ENTRY_PATTERN = re.compile(
    r"^## \[(\d{4}-\d{2}-\d{2})\] ([a-z-]+) \| (\S.*)$", re.MULTILINE
)
HEADING_PATTERN = re.compile(r"^## (.+)$", re.MULTILINE)
WIKILINK_PATTERN = re.compile(r"\[\[([^\]]+)\]\]")


def _body(text: str) -> str:
    match = re.match(r"^---\s*\n.*?\n---\s*\n?", text, flags=re.DOTALL)
    return text[match.end() :] if match else text


def _baseline_body(log_path: Path, repo_root: Path) -> str | None:
    try:
        relative = log_path.resolve().relative_to(repo_root.resolve()).as_posix()
        result = subprocess.run(
            ["git", "-C", str(repo_root), "show", f"HEAD:{relative}"],
            check=True,
            capture_output=True,
            text=True,
            encoding="utf-8",
        )
    except (OSError, ValueError, subprocess.CalledProcessError):
        return None
    return _body(result.stdout)


def validate_log(
    log_path: Path, repo_root: Path, *, use_git: bool = True
) -> dict[str, Any]:
    errors: list[str] = []
    warnings: list[str] = []
    try:
        validate_regular_tree(log_path.parent)
        log_path.resolve(strict=False).relative_to(repo_root.resolve(strict=False))
    except (OSError, ValueError) as exc:
        return {
            "ok": False,
            "errors": [f"unsafe Wiki log path: {exc}"],
            "warnings": [],
            "entries": 0,
            "contract_marker": False,
        }
    if not log_path.is_file():
        return {"ok": False, "errors": [f"missing Wiki log: {log_path}"], "warnings": [], "entries": 0}

    try:
        text = log_path.read_text(encoding="utf-8")
    except (OSError, UnicodeError) as exc:
        return {
            "ok": False,
            "errors": [f"unable to read Wiki log: {exc}"],
            "warnings": [],
            "entries": 0,
            "contract_marker": False,
        }
    body = _body(text)
    marker_position = body.find(CONTRACT_MARKER)
    headings = list(HEADING_PATTERN.finditer(body))
    dates: list[dt.date] = []
    entry_count = 0

    for index, heading in enumerate(headings):
        value = heading.group(0)
        match = ENTRY_PATTERN.fullmatch(value)
        strict = marker_position >= 0 and heading.start() > marker_position
        issue_target = errors if strict else warnings
        if match is None:
            issue_target.append(f"invalid log heading: {value}")
            continue
        entry_count += 1
        raw_date, operation, _ = match.groups()
        try:
            entry_date = dt.date.fromisoformat(raw_date)
            dates.append(entry_date)
        except ValueError:
            issue_target.append(f"invalid log date: {raw_date}")
        if operation not in ALLOWED_OPERATIONS:
            issue_target.append(f"unsupported log operation: {operation}")

        end = headings[index + 1].start() if index + 1 < len(headings) else len(body)
        entry_body = body[heading.end() : end]
        if strict:
            affected_line = next(
                (
                    line
                    for line in entry_body.splitlines()
                    if "Affected pages:" in line or "受影響頁面：" in line
                ),
                "",
            )
            links = WIKILINK_PATTERN.findall(affected_line)
            if not links:
                errors.append(f"log entry lacks an affected-pages wikilink: {value}")
            for raw_target in links:
                target = raw_target.split("|", 1)[0].split("#", 1)[0].strip()
                if not any(path.stem == Path(target).stem for path in (repo_root / "wiki").rglob("*.md")):
                    errors.append(f"log entry references a missing Wiki page: [[{target}]]")

    for previous, current in zip(dates, dates[1:]):
        if current < previous:
            errors.append(
                f"log dates are not nondecreasing: {previous.isoformat()} then {current.isoformat()}"
            )

    frontmatter = parse_frontmatter_text(text)
    try:
        last_updated = dt.date.fromisoformat(str(frontmatter.get("last_updated", "")))
    except ValueError:
        last_updated = None
    if dates and (last_updated is None or last_updated < max(dates)):
        errors.append("log frontmatter.last_updated is earlier than the latest entry")

    baseline = _baseline_body(log_path, repo_root) if use_git else None
    if baseline is not None and not body.startswith(baseline):
        errors.append("existing wiki/log.md body differs from the Git baseline; entries are append-only")

    return {
        "ok": not errors,
        "errors": errors,
        "warnings": warnings,
        "entries": entry_count,
        "contract_marker": marker_position >= 0,
    }


def main(argv: list[str] | None = None) -> int:
    configure_utf8_stdio()
    parser = argparse.ArgumentParser()
    parser.add_argument("log_path", nargs="?", type=Path, default=Path("wiki/log.md"))
    parser.add_argument("--repo-root", type=Path, default=Path("."))
    parser.add_argument("--format", choices=("text", "json"), default="text")
    args = parser.parse_args(argv)
    # Preserve the caller-provided lexical log path until validate_log() has
    # checked its parent tree; resolving first would hide a symlink/reparse
    # parent from the append-only boundary check.
    result = validate_log(args.log_path, args.repo_root)
    if args.format == "json":
        print(json.dumps(result, ensure_ascii=False, indent=2))
    else:
        print(
            f"Wiki log: {result['entries']} entries, "
            f"{len(result['errors'])} errors, {len(result['warnings'])} warnings"
        )
        for value in result["errors"]:
            print(f"- ERROR: {value}")
        for value in result["warnings"]:
            print(f"- WARNING: {value}")
    return 0 if result["ok"] else 2


if __name__ == "__main__":
    raise SystemExit(main())
