#!/usr/bin/env python3
"""Codex PreToolUse hook that keeps wiki work inside wiki/schema paths."""

from __future__ import annotations

import json
import re
import sys
from typing import Any


EDIT_TOOL_NAMES = {
    "apply_patch",
    "Edit",
    "Write",
    "create",
    "create_file",
    "edit",
    "editFiles",
    "str_replace",
    "str_replace_editor",
    "multi_replace_string_in_file",
    "replace_string_in_file",
    "write",
}

PATCH_FILE_PATTERN = re.compile(
    r"^\*\*\* (?:Add|Update|Delete) File:\s*(.+)$",
    re.MULTILINE,
)

ALLOWED_PREFIXES = ("wiki/", ".codex/", ".agents/", ".github/")


def configure_stdio() -> None:
    for stream in (sys.stdout, sys.stderr):
        try:
            stream.reconfigure(encoding="utf-8")
        except Exception:
            pass


def normalize_path(value: str) -> str:
    return value.replace("\\", "/").strip()


def is_allowed_path(path: str) -> bool:
    normalized = normalize_path(path).lower()
    while normalized.startswith("./"):
        normalized = normalized[2:]
    return (
        normalized == "agents.md"
        or normalized.endswith("/agents.md")
        or normalized.startswith(ALLOWED_PREFIXES)
        or any(f"/{prefix}" in normalized for prefix in ALLOWED_PREFIXES)
    )


def extract_patch_text(tool_input: Any) -> str:
    if isinstance(tool_input, str):
        return tool_input
    if not isinstance(tool_input, dict):
        return ""
    for key in ("command", "input", "patch", "content"):
        value = tool_input.get(key)
        if isinstance(value, str) and value.strip():
            return value
    return ""


def extract_paths_from_tool_input(tool_name: str, tool_input: Any) -> list[str]:
    paths: list[str] = []

    if isinstance(tool_input, dict):
        for key in ("filePath", "file_path", "path", "targetPath", "target_path"):
            value = tool_input.get(key)
            if isinstance(value, str) and value.strip():
                paths.append(value)

        files = tool_input.get("files")
        if isinstance(files, list):
            for item in files:
                if isinstance(item, str) and item.strip():
                    paths.append(item)
                elif isinstance(item, dict):
                    for key in ("filePath", "file_path", "path"):
                        value = item.get(key)
                        if isinstance(value, str) and value.strip():
                            paths.append(value)

    patch_text = extract_patch_text(tool_input)
    if tool_name == "apply_patch" or patch_text:
        paths.extend(match.group(1).strip() for match in PATCH_FILE_PATTERN.finditer(patch_text))

    deduped: list[str] = []
    seen: set[str] = set()
    for path in paths:
        normalized = normalize_path(path)
        if normalized and normalized not in seen:
            seen.add(normalized)
            deduped.append(normalized)
    return deduped


def parse_tool_input(payload: dict[str, Any]) -> Any:
    if "tool_input" in payload:
        return payload.get("tool_input")
    if "toolInput" in payload:
        return payload.get("toolInput")
    tool_args = payload.get("toolArgs")
    if isinstance(tool_args, str) and tool_args.strip():
        try:
            return json.loads(tool_args)
        except json.JSONDecodeError:
            return tool_args
    return tool_args


def respond_allow() -> None:
    print("{}")


def respond_deny(reason: str) -> None:
    print(
        json.dumps(
            {
                "hookSpecificOutput": {
                    "hookEventName": "PreToolUse",
                    "permissionDecision": "deny",
                    "permissionDecisionReason": reason,
                }
            },
            ensure_ascii=False,
        )
    )


def main() -> None:
    configure_stdio()
    try:
        payload = json.load(sys.stdin)
    except (json.JSONDecodeError, EOFError):
        respond_deny("wiki-write-guard 無法解析 Codex hook 輸入，依 fail-safe 政策拒絕本次寫入。")
        return

    tool_name = str(payload.get("tool_name") or payload.get("toolName") or "")
    if tool_name and tool_name not in EDIT_TOOL_NAMES:
        respond_allow()
        return

    target_paths = extract_paths_from_tool_input(tool_name, parse_tool_input(payload))
    if not target_paths:
        respond_deny(
            "wiki-write-guard 無法判定本次編輯的目標路徑。"
            "為保護 raw sources，請改用可明確標示路徑的編輯工具。"
        )
        return

    disallowed_paths = [path for path in target_paths if not is_allowed_path(path)]
    if disallowed_paths:
        summarized_paths = ", ".join(f"`{path}`" for path in disallowed_paths[:3])
        if len(disallowed_paths) > 3:
            summarized_paths += f" 等 {len(disallowed_paths)} 個路徑"
        respond_deny(
            "Codebase LLM Wiki 任務預設只應寫入 `wiki/`、`.codex/`、"
            "`.agents/`、`.github/` 或根目錄 `AGENTS.md`。"
            f"這次偵測到其他路徑：{summarized_paths}。"
        )
        return

    respond_allow()


if __name__ == "__main__":
    main()
