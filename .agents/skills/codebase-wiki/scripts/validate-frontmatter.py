#!/usr/bin/env python3
"""Validate Codebase LLM Wiki frontmatter.

Usage:
    python .agents/skills/codebase-wiki/scripts/validate-frontmatter.py [wiki_dir]

The check intentionally validates schema shape and enum/date values. Source
existence is covered by check-stale.py.
"""

from __future__ import annotations

import datetime as _dt
import argparse
import pathlib
import re
import sys
from typing import Any

from frontmatter import configure_utf8_stdio, parse_frontmatter_text, validate_regular_tree


REQUIRED_FIELDS = {"title", "type", "sources", "last_updated", "tags", "status"}
ALLOWED_TYPES = {
    "module",
    "entity",
    "pattern",
    "decision",
    "dependency",
    "guide",
    "synthesis",
    "overview",
    "architecture",
    "index",
    "log",
}
ALLOWED_STATUS = {"active", "stale", "placeholder"}
ALLOWED_DECISION_STATUS = {"proposed", "accepted", "deprecated", "superseded"}
NOTEBOOKLM_GROUP_PATTERN = re.compile(r"^[a-z0-9]+(?:-[a-z0-9]+)*$")
SOURCE_DIGEST_PATTERN = re.compile(r"^sha256:[0-9a-f]{64}$")
DERIVED_FROM_PATTERN = re.compile(r"^\[\[[^\[\]]+\]\]$")

TYPE_PATHS = {
    "module": pathlib.PurePosixPath("modules"),
    "entity": pathlib.PurePosixPath("entities"),
    "pattern": pathlib.PurePosixPath("patterns"),
    "decision": pathlib.PurePosixPath("decisions"),
    "dependency": pathlib.PurePosixPath("dependencies"),
    "guide": pathlib.PurePosixPath("guides"),
    "synthesis": pathlib.PurePosixPath("synthesis"),
    "architecture": pathlib.PurePosixPath("architecture"),
}


def is_non_empty_string(value: Any) -> bool:
    return isinstance(value, str) and bool(value.strip())


def is_valid_date(value: Any) -> bool:
    if not isinstance(value, str):
        return False
    try:
        parsed = _dt.date.fromisoformat(value)
    except ValueError:
        return False
    return parsed.isoformat() == value


def is_list(value: Any) -> bool:
    return isinstance(value, list)


def relative_posix(path: pathlib.Path, root: pathlib.Path) -> pathlib.PurePosixPath:
    return pathlib.PurePosixPath(path.relative_to(root).as_posix())


def validate_page(path: pathlib.Path, wiki_dir: pathlib.Path) -> list[str]:
    errors: list[str] = []
    text = path.read_text(encoding="utf-8")
    fm = parse_frontmatter_text(text)
    rel = relative_posix(path, wiki_dir)

    if not fm:
        return [f"{rel}: missing YAML frontmatter"]

    missing = sorted(REQUIRED_FIELDS - set(fm))
    if missing:
        errors.append(f"{rel}: missing required field(s): {', '.join(missing)}")

    if "title" in fm and not is_non_empty_string(fm.get("title")):
        errors.append(f"{rel}: title must be a non-empty string")

    page_type = fm.get("type")
    if page_type not in ALLOWED_TYPES:
        errors.append(
            f"{rel}: type must be one of {', '.join(sorted(ALLOWED_TYPES))}; got {page_type!r}"
        )

    if "sources" in fm and not is_list(fm.get("sources")):
        errors.append(f"{rel}: sources must be an array")
    elif "sources" in fm:
        for source in fm.get("sources", []):
            if not isinstance(source, str) or not source.strip():
                errors.append(f"{rel}: every sources entry must be a non-empty repo-relative string")
                continue
            source_path = pathlib.PurePosixPath(source.replace("\\", "/"))
            if (
                source_path.is_absolute()
                or ".." in source_path.parts
                or re.fullmatch(r"[A-Za-z]:.*", source_path.as_posix())
            ):
                errors.append(f"{rel}: source must stay inside the repository: {source!r}")
            elif source_path.parts and source_path.parts[0].lower() == "wiki":
                errors.append(
                    f"{rel}: sources must reference raw repository evidence; "
                    "use derived_from for Wiki pages"
                )

    if "last_updated" in fm and not is_valid_date(fm.get("last_updated")):
        errors.append(f"{rel}: last_updated must be a valid YYYY-MM-DD date")

    if "tags" in fm and not is_list(fm.get("tags")):
        errors.append(f"{rel}: tags must be an array")

    status = fm.get("status")
    if status not in ALLOWED_STATUS:
        errors.append(
            f"{rel}: status must be one of {', '.join(sorted(ALLOWED_STATUS))}; got {status!r}"
        )

    notebooklm_group = fm.get("notebooklm_group")
    if notebooklm_group is not None and (
        not isinstance(notebooklm_group, str)
        or not NOTEBOOKLM_GROUP_PATTERN.fullmatch(notebooklm_group)
    ):
        errors.append(f"{rel}: notebooklm_group must be a non-empty kebab-case string")

    summary = fm.get("summary")
    if summary is not None and not is_non_empty_string(summary):
        errors.append(f"{rel}: summary must be a non-empty string when present")

    source_digest = fm.get("source_digest")
    if source_digest is not None and (
        not isinstance(source_digest, str)
        or not SOURCE_DIGEST_PATTERN.fullmatch(source_digest)
    ):
        errors.append(f"{rel}: source_digest must use sha256:<64 lowercase hex>")

    derived_from = fm.get("derived_from")
    if derived_from is not None:
        if not is_list(derived_from):
            errors.append(f"{rel}: derived_from must be an array")
        else:
            for value in derived_from:
                if not isinstance(value, str) or not DERIVED_FROM_PATTERN.fullmatch(value):
                    errors.append(
                        f"{rel}: every derived_from entry must be a [[wiki-page]] wikilink"
                    )

    if page_type == "decision":
        if not is_valid_date(fm.get("decision_date")):
            errors.append(f"{rel}: decision_date must be a valid YYYY-MM-DD date")
        decision_status = fm.get("decision_status")
        if decision_status not in ALLOWED_DECISION_STATUS:
            errors.append(
                f"{rel}: decision_status must be one of "
                f"{', '.join(sorted(ALLOWED_DECISION_STATUS))}; got {decision_status!r}"
            )

    if page_type == "dependency":
        if not is_non_empty_string(fm.get("package_name")):
            errors.append(f"{rel}: dependency pages require non-empty package_name")
        if not is_non_empty_string(fm.get("version")):
            errors.append(f"{rel}: dependency pages require non-empty version")

    expected_dir = TYPE_PATHS.get(str(page_type))
    if expected_dir and rel.parent != expected_dir:
        errors.append(f"{rel}: type {page_type!r} must live under wiki/{expected_dir}/")
    elif page_type == "overview" and rel != pathlib.PurePosixPath("overview.md"):
        errors.append(f"{rel}: type 'overview' must be wiki/overview.md")
    elif page_type == "index" and rel != pathlib.PurePosixPath("index.md"):
        errors.append(f"{rel}: type 'index' must be wiki/index.md")
    elif page_type == "log" and rel != pathlib.PurePosixPath("log.md"):
        errors.append(f"{rel}: type 'log' must be wiki/log.md")

    return errors


def main(argv: list[str] | None = None) -> None:
    configure_utf8_stdio()
    parser = argparse.ArgumentParser(
        prog="validate-frontmatter.py",
        description="Validate frontmatter and Wiki page placement.",
    )
    parser.add_argument("wiki_dir", nargs="?", type=pathlib.Path, default=pathlib.Path("wiki"))
    args = parser.parse_args(argv)
    wiki_dir = args.wiki_dir
    if not wiki_dir.is_dir():
        print(f"Error: wiki directory not found: {wiki_dir}", file=sys.stderr)
        sys.exit(1)

    try:
        validate_regular_tree(wiki_dir)
    except (OSError, UnicodeError) as exc:
        print(f"Error: {exc}", file=sys.stderr)
        sys.exit(2)

    all_errors: list[str] = []
    try:
        for path in sorted(wiki_dir.rglob("*.md")):
            all_errors.extend(validate_page(path, wiki_dir))
    except (OSError, UnicodeError) as exc:
        print(f"Error: {exc}", file=sys.stderr)
        sys.exit(2)

    if all_errors:
        print("Wiki Frontmatter Validation Report")
        print("=" * 40)
        for error in all_errors:
            print(f"- {error}")
        print(f"\nFAILED: {len(all_errors)} issue(s)")
        sys.exit(1)

    print(f"OK: validated {len(list(wiki_dir.rglob('*.md')))} wiki page(s)")


if __name__ == "__main__":
    main()
