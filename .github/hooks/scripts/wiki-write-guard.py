#!/usr/bin/env python3
"""wiki-write-guard.py — preToolUse hook，限制 wiki 代理的寫入邊界。

此腳本預期作為 repository-scoped hook 使用。它允許 wiki 維護流程寫入
`wiki/` 與 `.github/`，並拒絕其他路徑的寫入，避免知識維護代理誤改
raw sources。
"""

import json
import re
import sys


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
    payload = {"permissionDecision": decision}
    if reason:
        payload["permissionDecisionReason"] = reason
    print(json.dumps(payload, ensure_ascii=False))


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

    tool_input = parse_tool_args(payload)

    target_paths = extract_paths_from_tool_input(tool_name, tool_input)
    if not target_paths:
        respond(
            "deny",
            "wiki-write-guard 無法判定本次編輯的目標路徑。"
            "為保護 raw sources，請改用可明確標示路徑的編輯工具，且僅寫入 `wiki/` 或 `.github/`。",
        )
        return

    disallowed_paths = [path for path in target_paths if not is_allowed_path(path)]
    if disallowed_paths:
        summarized_paths = ", ".join(f"`{path}`" for path in disallowed_paths[:3])
        if len(disallowed_paths) > 3:
            summarized_paths += f" 等 {len(disallowed_paths)} 個路徑"
        respond(
            "deny",
            "Wiki 代理預設只應寫入 `wiki/` 與 `.github/`。"
            f"這次偵測到其他路徑：{summarized_paths}。",
        )
        return

    respond("allow")


if __name__ == "__main__":
    main()
