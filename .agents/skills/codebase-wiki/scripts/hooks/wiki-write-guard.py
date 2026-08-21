#!/usr/bin/env python3
"""Fail-closed write boundary shared by both platform adapters."""

from __future__ import annotations

import json
from pathlib import Path
import sys
from typing import Any

from common import (
    EDIT_TOOL_NAMES,
    configure_stdio,
    extract_paths,
    parse_platform,
    parse_tool_input,
    repo_relative_path,
    repo_root,
)


FRAMEWORK_PREFIXES = (
    "wiki/",
    ".codex/",
    ".agents/",
    ".github/",
    "docs/",
    "samples/",
    "tests/",
    "tools/",
)
FRAMEWORK_ROOT_FILES = {
    ".gitattributes",
    ".gitignore",
    "agents.md",
    "changelog.md",
    "codex.md",
    "license",
    "license.md",
    "readme.md",
    "version",
}


def read_guard_mode(platform: str) -> str:
    root = repo_root()
    config = (
        root / ".github" / "hooks" / "config.toml"
        if platform == "copilot"
        else root / ".codex" / "config.toml"
    )
    section = ""
    try:
        lines = config.read_text(encoding="utf-8").splitlines()
    except OSError:
        return "wiki-only"
    for raw in lines:
        line = raw.split("#", 1)[0].strip()
        if line.startswith("[") and line.endswith("]"):
            section = line.strip("[]").strip()
            continue
        if section != "wiki_guard" or "=" not in line:
            continue
        key, value = (part.strip().strip("\"'") for part in line.split("=", 1))
        if key == "mode":
            if value == "target":
                return "wiki-only"
            if value in {"wiki-only", "coexist", "framework"}:
                return value
    return "wiki-only"


def is_allowed_path(path: str, mode: str) -> bool:
    relative = repo_relative_path(path)
    if not relative:
        return False
    normalized = relative.lower()
    if mode == "target":
        mode = "wiki-only"
    if mode == "coexist":
        return True
    if mode == "framework":
        if "/" not in normalized and normalized in FRAMEWORK_ROOT_FILES:
            return True
        return any(
            normalized == prefix.rstrip("/") or normalized.startswith(prefix)
            for prefix in FRAMEWORK_PREFIXES
        )
    return normalized == "wiki" or normalized.startswith("wiki/")


def respond_allow(reason: str | None = None) -> None:
    if not reason:
        print("{}")
        return
    print(
        json.dumps(
            {
                "permissionDecision": "allow",
                "hookSpecificOutput": {
                    "hookEventName": "PreToolUse",
                    "permissionDecision": "allow",
                    "additionalContext": reason,
                },
            },
            ensure_ascii=False,
        )
    )


def respond_deny(reason: str) -> None:
    print(
        json.dumps(
            {
                "permissionDecision": "deny",
                "permissionDecisionReason": reason,
                "hookSpecificOutput": {
                    "hookEventName": "PreToolUse",
                    "permissionDecision": "deny",
                    "permissionDecisionReason": reason,
                },
            },
            ensure_ascii=False,
        )
    )


def main() -> None:
    configure_stdio()
    platform = parse_platform()
    try:
        payload: dict[str, Any] = json.load(sys.stdin)
    except (json.JSONDecodeError, EOFError):
        respond_deny("Write target could not be parsed; the Wiki guard failed closed.")
        return
    tool_name = str(payload.get("tool_name") or payload.get("toolName") or "")
    if tool_name and tool_name not in EDIT_TOOL_NAMES:
        print("{}")
        return
    paths = extract_paths(tool_name, parse_tool_input(payload))
    if not paths:
        respond_deny("Write target was absent; use an edit tool with explicit paths.")
        return
    mode = read_guard_mode(platform)
    blocked = [path for path in paths if not is_allowed_path(path, mode)]
    if blocked:
        respond_deny(
            f"Wiki guard mode `{mode}` blocked: "
            + ", ".join(f"`{path}`" for path in blocked[:3])
        )
        return
    if mode == "coexist" and any(
        not (repo_relative_path(path) or "").lower().startswith("wiki/")
        and (repo_relative_path(path) or "").lower() != "wiki"
        for path in paths
    ):
        respond_allow(
            "Coexist mode allowed an in-repository non-Wiki edit. The guard does not "
            "expand task authorization; raw sources remain read-only during Wiki tasks."
        )
        return
    respond_allow()


if __name__ == "__main__":
    main()
