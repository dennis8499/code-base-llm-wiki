#!/usr/bin/env python3
"""Emit a bounded Wiki state summary at session start."""

from __future__ import annotations

from collections import Counter
import json
from pathlib import Path
import sys

sys.path.insert(0, str(Path(__file__).resolve().parents[1]))
from frontmatter import parse_frontmatter_text  # noqa: E402
from common import (  # noqa: E402
    audit_candidates,
    audit_path_is_safe,
    configure_stdio,
    parse_platform,
    repo_root,
)


MAX_LINES = 30
MAX_BYTES = 4 * 1024
RECENT_OPERATIONS = 3
GAP_PAGES = 5


def recent_log_headings(log_path: Path) -> list[str]:
    if not log_path.is_file():
        return []
    if not audit_path_is_safe(log_path):
        return []
    try:
        text = log_path.read_text(encoding="utf-8")
    except (OSError, UnicodeDecodeError):
        return []
    headings = [line.strip() for line in text.splitlines() if line.startswith("## [")]
    return headings[-RECENT_OPERATIONS:]


def bounded_message(lines: list[str]) -> str:
    message = "\n".join(lines[:MAX_LINES])
    encoded = message.encode("utf-8")
    if len(encoded) <= MAX_BYTES:
        return message
    return encoded[:MAX_BYTES].decode("utf-8", errors="ignore")


def build_message(root: Path) -> str:
    wiki = root / "wiki"
    pages = sorted(wiki.rglob("*.md")) if wiki.is_dir() else []
    types: Counter[str] = Counter()
    statuses: Counter[str] = Counter()
    gaps: list[str] = []
    readable_pages = 0
    skipped_pages = 0
    for path in pages:
        if not audit_path_is_safe(path):
            skipped_pages += 1
            continue
        try:
            text = path.read_text(encoding="utf-8")
        except (OSError, UnicodeDecodeError):
            skipped_pages += 1
            continue
        readable_pages += 1
        fm = parse_frontmatter_text(text)
        page_type = str(fm.get("type", "unknown"))
        status = str(fm.get("status", "unknown"))
        types[page_type] += 1
        statuses[status] += 1
        if status in {"stale", "placeholder"} and len(gaps) < GAP_PAGES:
            gaps.append(path.relative_to(wiki).as_posix())

    lines = [
        "## Wiki state",
        f"- Pages: {readable_pages}",
        "- Types: " + (", ".join(f"{key}={value}" for key, value in sorted(types.items())) or "none"),
        "- Statuses: "
        + (", ".join(f"{key}={value}" for key, value in sorted(statuses.items())) or "none"),
    ]
    if skipped_pages:
        lines.append(f"- Skipped unsafe/unreadable pages: {skipped_pages}")
    if gaps:
        lines.append("- Stale/placeholders: " + ", ".join(gaps))
    recent = recent_log_headings(wiki / "log.md")
    if recent:
        lines.append("- Recent operations:")
        lines.extend(f"  - {heading[3:]}" for heading in recent)
    lines.append("- Navigation: read `wiki/index.md` when a Wiki task begins.")
    return bounded_message(lines)


def write_audit(platform: str, message: str) -> str | None:
    errors: list[str] = []
    for target in audit_candidates(platform, "wiki-session-state.md"):
        if not audit_path_is_safe(target):
            errors.append(f"unsafe audit path: {target}")
            continue
        try:
            target.parent.mkdir(parents=True, exist_ok=True)
            target.write_text(message, encoding="utf-8")
            return None
        except OSError as exc:
            errors.append(str(exc))
    return "; ".join(errors)


def main() -> None:
    configure_stdio()
    platform = parse_platform()
    sys.stdin.read()
    message = build_message(repo_root())
    error = write_audit(platform, message)
    if error:
        message = bounded_message([*message.splitlines(), f"- Audit write failed: {error}"])
    print(
        json.dumps(
            {
                "additionalContext": message,
                "hookSpecificOutput": {
                    "hookEventName": "SessionStart",
                    "additionalContext": message,
                },
            },
            ensure_ascii=False,
        )
    )


if __name__ == "__main__":
    main()
