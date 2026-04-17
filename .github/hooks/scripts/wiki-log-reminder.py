#!/usr/bin/env python3
"""wiki-log-reminder.py — PostToolUse hook，提醒 wiki 維護代理補上 log.md。

此腳本預期作為自訂 Agent 的 agent-scoped hook 使用，只在相關 wiki 代理
完成檔案寫入後執行。當偵測到 `wiki/` 目錄下的 Markdown 頁面被建立或更新
（排除 `wiki/log.md` 本身）時，會以 systemMessage 與 additionalContext
提醒代理在收尾時追加 log 條目。
"""

import json
import re
import sys


EDIT_TOOL_NAMES = {
    "apply_patch",
    "create_file",
    "editFiles",
    "multi_replace_string_in_file",
    "replace_string_in_file",
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


def respond(message: str | None = None):
    payload: dict[str, object] = {}
    if message:
        payload["systemMessage"] = message
        payload["hookSpecificOutput"] = {
            "hookEventName": "PostToolUse",
            "additionalContext": message,
        }
    print(json.dumps(payload, ensure_ascii=False))


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

    tool_input = payload.get("tool_input")
    if tool_input is None:
        tool_input = payload.get("toolInput")

    changed_paths = extract_paths_from_tool_input(tool_name, tool_input)
    wiki_paths = [path for path in changed_paths if is_wiki_markdown(path) and not is_log_file(path)]

    if wiki_paths:
        summarized_paths = ", ".join(f"`{path}`" for path in wiki_paths[:3])
        if len(wiki_paths) > 3:
            summarized_paths += f" 等 {len(wiki_paths)} 個檔案"
        respond(
            "💡 已修改 wiki 頁面："
            f"{summarized_paths}。"
            "請在本次操作收尾時追加 `wiki/log.md` 條目（append-only）。"
        )
    else:
        respond()


if __name__ == "__main__":
    main()
