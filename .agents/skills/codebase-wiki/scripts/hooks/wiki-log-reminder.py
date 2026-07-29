#!/usr/bin/env python3
"""Record Wiki page edits that may require an append-only log entry."""

from __future__ import annotations

import json
import sys
import time
from typing import Any

from common import (
    EDIT_TOOL_NAMES,
    audit_candidates,
    configure_stdio,
    extract_paths,
    parse_platform,
    parse_tool_input,
    repo_relative_path,
)


def append_audit(platform: str, paths: list[str]) -> str | None:
    entry = {
        "timestamp": int(time.time() * 1000),
        "event": "wiki_page_changed",
        "paths": paths,
        "reminder": "Append one valid wiki/log.md operation for durable Wiki changes.",
    }
    errors: list[str] = []
    for target in audit_candidates(platform, "wiki-log-reminder.jsonl"):
        try:
            target.parent.mkdir(parents=True, exist_ok=True)
            with target.open("a", encoding="utf-8") as handle:
                handle.write(json.dumps(entry, ensure_ascii=False) + "\n")
            return None
        except OSError as exc:
            errors.append(str(exc))
    return "; ".join(errors)


def main() -> None:
    configure_stdio()
    platform = parse_platform()
    try:
        payload: dict[str, Any] = json.load(sys.stdin)
    except (json.JSONDecodeError, EOFError):
        print("{}")
        return
    tool_name = str(payload.get("tool_name") or payload.get("toolName") or "")
    if tool_name and tool_name not in EDIT_TOOL_NAMES:
        print("{}")
        return
    wiki_paths: list[str] = []
    for value in extract_paths(tool_name, parse_tool_input(payload)):
        relative = repo_relative_path(value)
        if relative and relative.lower().startswith("wiki/") and relative.lower().endswith(".md"):
            if relative.lower() != "wiki/log.md":
                wiki_paths.append(relative)
    if not wiki_paths:
        print("{}")
        return
    error = append_audit(platform, wiki_paths)
    message = "Wiki pages changed; append one log operation if the update is durable."
    if error:
        message += f" Audit write failed: {error}"
    print(
        json.dumps(
            {
                "additionalContext": message,
                "hookSpecificOutput": {
                    "hookEventName": "PostToolUse",
                    "additionalContext": message,
                },
            },
            ensure_ascii=False,
        )
    )


if __name__ == "__main__":
    main()
