#!/usr/bin/env python3
"""wiki-log-reminder.py — postToolUse hook，記錄 wiki 頁面異動線索。

postToolUse hook 的輸出不會被注入 agent context，因此此腳本改為把異動線索
寫到 `.github/hooks/logs/wiki-log-reminder.jsonl`，供稽核或後續人工檢查。
"""

import json
import pathlib
import re
import sys
import time


EDIT_TOOL_NAMES = {
    "apply_patch",
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


def extract_paths_from_tool_input(tool_name: str, tool_input) -> list[str]:
    paths: list[str] = []
    patch_text = ""

    if isinstance(tool_input, dict):
        for key in ("filePath", "path"):
            value = tool_input.get(key)
            if isinstance(value, str) and value.strip():
                paths.append(value)

        files = tool_input.get("files")
        if isinstance(files, list):
            for item in files:
                if isinstance(item, str) and item.strip():
                    paths.append(item)
                elif isinstance(item, dict):
                    for key in ("filePath", "path"):
                        value = item.get(key)
                        if isinstance(value, str) and value.strip():
                            paths.append(value)

        for key in ("input", "patch"):
            value = tool_input.get(key)
            if isinstance(value, str) and value.strip():
                patch_text = value
                break
    elif isinstance(tool_input, str):
        patch_text = tool_input

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


def parse_tool_args(payload: dict) -> object:
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


def append_audit_entry(paths: list[str]):
    log_dir = pathlib.Path(".github/hooks/logs")
    log_dir.mkdir(parents=True, exist_ok=True)
    entry = {
        "timestamp": int(time.time() * 1000),
        "event": "wiki_page_changed",
        "paths": paths,
        "reminder": "Append an entry to wiki/log.md for ingest, lint, query save, or major wiki updates.",
    }
    with (log_dir / "wiki-log-reminder.jsonl").open("a", encoding="utf-8") as fh:
        fh.write(json.dumps(entry, ensure_ascii=False) + "\n")


def respond():
    print("{}")


def main():
    try:
        payload = json.load(sys.stdin)
    except (json.JSONDecodeError, EOFError):
        respond()
        return

    tool_name = str(payload.get("tool_name") or payload.get("toolName") or "")
    if tool_name and tool_name not in EDIT_TOOL_NAMES:
        respond()
        return

    tool_input = parse_tool_args(payload)

    changed_paths = extract_paths_from_tool_input(tool_name, tool_input)
    wiki_paths = [path for path in changed_paths if is_wiki_markdown(path) and not is_log_file(path)]

    if wiki_paths:
        append_audit_entry(wiki_paths)
    respond()


if __name__ == "__main__":
    main()
