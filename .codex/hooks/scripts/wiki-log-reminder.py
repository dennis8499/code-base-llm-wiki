#!/usr/bin/env python3
"""Codex PostToolUse hook that records wiki edits needing wiki/log.md entries."""

from __future__ import annotations

import json
import pathlib
import re
import sys
import time
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

REPO_ROOT = pathlib.Path(__file__).resolve().parents[3]
LOG_DIR = REPO_ROOT / ".codex" / "hooks" / "logs"


def configure_stdio() -> None:
    for stream in (sys.stdout, sys.stderr):
        try:
            stream.reconfigure(encoding="utf-8")
        except Exception:
            pass


def normalize_path(value: str) -> str:
    return value.replace("\\", "/").strip()


def is_wiki_markdown(path: str) -> bool:
    normalized = normalize_path(path).lower()
    return normalized.endswith(".md") and (
        normalized.startswith("wiki/") or "/wiki/" in normalized
    )


def is_log_file(path: str) -> bool:
    normalized = normalize_path(path).lower()
    return normalized.endswith("wiki/log.md") or normalized.endswith("/wiki/log.md")


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


def append_audit_entry(paths: list[str]) -> str | None:
    entry = {
        "timestamp": int(time.time() * 1000),
        "event": "wiki_page_changed",
        "paths": paths,
        "reminder": "Append an entry to wiki/log.md for ingest, lint, query save, or major wiki updates.",
    }
    try:
        LOG_DIR.mkdir(parents=True, exist_ok=True)
        with (LOG_DIR / "wiki-log-reminder.jsonl").open("a", encoding="utf-8") as fh:
            fh.write(json.dumps(entry, ensure_ascii=False) + "\n")
    except OSError as exc:
        return f"無法寫入 `.codex/hooks/logs/wiki-log-reminder.jsonl`：{exc}"
    return None


def respond(additional_context: str | None = None) -> None:
    payload: dict[str, Any] = {}
    if additional_context:
        payload["hookSpecificOutput"] = {
            "hookEventName": "PostToolUse",
            "additionalContext": additional_context,
        }
    print(json.dumps(payload, ensure_ascii=False))


def main() -> None:
    configure_stdio()
    try:
        payload = json.load(sys.stdin)
    except (json.JSONDecodeError, EOFError):
        respond()
        return

    tool_name = str(payload.get("tool_name") or payload.get("toolName") or "")
    if tool_name and tool_name not in EDIT_TOOL_NAMES:
        respond()
        return

    changed_paths = extract_paths_from_tool_input(tool_name, parse_tool_input(payload))
    wiki_paths = [path for path in changed_paths if is_wiki_markdown(path) and not is_log_file(path)]

    if wiki_paths:
        audit_error = append_audit_entry(wiki_paths)
        joined_paths = ", ".join(f"`{path}`" for path in wiki_paths[:5])
        if len(wiki_paths) > 5:
            joined_paths += f" 等 {len(wiki_paths)} 個路徑"
        message = f"已偵測 wiki 頁面變更：{joined_paths}。若這是 ingest、lint 或重大更新，請追加 `wiki/log.md`。"
        if audit_error:
            message += f"（{audit_error}）"
        respond(message)
        return

    respond()


if __name__ == "__main__":
    main()
