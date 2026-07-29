#!/usr/bin/env python3
"""Emit a bounded Wiki state summary at session start."""

from __future__ import annotations

from collections import Counter
import json
from pathlib import Path
import sys

sys.path.insert(0, str(Path(__file__).resolve().parents[1]))
from frontmatter import parse_frontmatter_text  # noqa: E402
from common import audit_candidates, configure_stdio, parse_platform, repo_root  # noqa: E402


MAX_LINES = 30
MAX_BYTES = 4 * 1024
RECENT_OPERATIONS = 3
GAP_PAGES = 5


def recent_log_headings(log_path: Path) -> list[str]:
    if not log_path.is_file():
        return []
    headings = [
        line.strip()
        for line in log_path.read_text(encoding="utf-8").splitlines()
        if line.startswith("## [")
    ]
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
    for path in pages:
        fm = parse_frontmatter_text(path.read_text(encoding="utf-8"))
        page_type = str(fm.get("type", "unknown"))
        status = str(fm.get("status", "unknown"))
        types[page_type] += 1
        statuses[status] += 1
        if status in {"stale", "placeholder"} and len(gaps) < GAP_PAGES:
            gaps.append(path.relative_to(wiki).as_posix())

    lines = [
        "## Wiki state",
        f"- Pages: {len(pages)}",
        "- Types: " + (", ".join(f"{key}={value}" for key, value in sorted(types.items())) or "none"),
        "- Statuses: "
        + (", ".join(f"{key}={value}" for key, value in sorted(statuses.items())) or "none"),
    ]
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
