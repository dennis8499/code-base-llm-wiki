#!/usr/bin/env python3
"""wiki-write-guard.py — PreToolUse hook，限制 wiki 代理的寫入邊界。

此腳本預期作為自訂 Agent 的 agent-scoped hook 使用，只在 wiki 相關代理
活躍時觸發。它允許這些代理寫入 `wiki/` 與 `.github/`，並在偵測到其餘
路徑時要求使用者確認，避免知識維護代理誤改原始碼。
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


def is_allowed_path(path: str) -> bool:
    normalized = normalize_path(path).lower()
    return (
        normalized.startswith("wiki/")
        or normalized.startswith(".github/")
        or "/wiki/" in normalized
        or "/.github/" in normalized
    )


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


def respond(decision: str, reason: str | None = None):
    payload = {
        "hookSpecificOutput": {
            "hookEventName": "PreToolUse",
            "permissionDecision": decision,
        }
    }
    if reason:
        payload["hookSpecificOutput"]["permissionDecisionReason"] = reason
    print(json.dumps(payload, ensure_ascii=False))


def main():
    try:
        payload = json.load(sys.stdin)
    except (json.JSONDecodeError, EOFError):
        respond("deny", "wiki-write-guard 無法解析 hook 輸入，依 fail-safe 政策拒絕本次寫入。")
        return

    tool_name = str(payload.get("tool_name") or payload.get("toolName") or "")
    if tool_name and tool_name not in EDIT_TOOL_NAMES:
        respond("allow")
        return

    tool_input = payload.get("tool_input")
    if tool_input is None:
        tool_input = payload.get("toolInput")

    target_paths = extract_paths_from_tool_input(tool_name, tool_input)
    if not target_paths:
        respond(
            "ask",
            "wiki-write-guard 無法判定本次編輯的目標路徑。"
            "請確認這次寫入僅影響 `wiki/` 或 `.github/` 後再繼續。",
        )
        return

    disallowed_paths = [path for path in target_paths if not is_allowed_path(path)]
    if disallowed_paths:
        summarized_paths = ", ".join(f"`{path}`" for path in disallowed_paths[:3])
        if len(disallowed_paths) > 3:
            summarized_paths += f" 等 {len(disallowed_paths)} 個路徑"
        respond(
            "ask",
            "Wiki 代理預設只應寫入 `wiki/` 與 `.github/`。"
            f"這次偵測到其他路徑：{summarized_paths}。若確實需要，請明確確認。",
        )
        return

    respond("allow")


if __name__ == "__main__":
    main()
