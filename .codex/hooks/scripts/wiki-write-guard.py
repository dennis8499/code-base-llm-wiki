#!/usr/bin/env python3
"""PreToolUse hook that keeps wiki work inside the configured write boundary."""

from __future__ import annotations

import json
from pathlib import Path
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

REPO_ROOT = Path(__file__).resolve().parents[3]
FRAMEWORK_PREFIXES = ("wiki/", ".codex/", ".agents/", ".github/")
TARGET_PREFIXES = ("wiki/",)
FRAMEWORK_ROOT_FILES = {
    "agents.md",
    "readme.md",
    "changelog.md",
    "codex.md",
    "llm-wiki.md",
    "prompt.txt",
}


def configure_stdio() -> None:
    for stream in (sys.stdout, sys.stderr):
        try:
            stream.reconfigure(encoding="utf-8")
        except Exception:
            pass


def normalize_path(value: str) -> str:
    return value.replace("\\", "/").strip().strip("\"'")


def current_platform() -> str:
    parts = {part.lower() for part in Path(__file__).resolve().parts}
    if ".github" in parts:
        return "github"
    if ".codex" in parts:
        return "codex"
    return "unknown"


def config_candidates() -> list[Path]:
    github_config = REPO_ROOT / ".github" / "hooks" / "config.toml"
    codex_config = REPO_ROOT / ".codex" / "config.toml"
    if current_platform() == "github":
        return [github_config, codex_config]
    return [codex_config, github_config]


def read_guard_mode() -> str:
    """Read wiki_guard.mode from config.toml, failing closed to target mode."""
    for config_path in config_candidates():
        if not config_path.exists():
            continue
        section = ""
        try:
            lines = config_path.read_text(encoding="utf-8").splitlines()
        except OSError:
            continue
        for raw_line in lines:
            line = raw_line.split("#", 1)[0].strip()
            if not line:
                continue
            if line.startswith("[") and line.endswith("]"):
                section = line.strip("[]").strip()
                continue
            if "=" not in line:
                continue
            key, value = line.split("=", 1)
            key = key.strip()
            value = value.strip().strip("\"'")
            if section == "wiki_guard" and key == "mode" and value in {"target", "framework"}:
                return value
            if section == "wiki" and key == "guard_mode" and value in {"target", "framework"}:
                return value
    return "target"


def repo_relative_path(path: str) -> str | None:
    normalized = normalize_path(path)
    while normalized.startswith("./"):
        normalized = normalized[2:]
    try:
        candidate = Path(normalized)
        if not candidate.is_absolute():
            candidate = REPO_ROOT / candidate
        resolved = candidate.resolve(strict=False)
        rel = resolved.relative_to(REPO_ROOT.resolve(strict=False))
    except Exception:
        return None
    return rel.as_posix().lower()


def is_allowed_root_file(rel_path: str) -> bool:
    return "/" not in rel_path and rel_path in FRAMEWORK_ROOT_FILES


def is_allowed_path(path: str, mode: str) -> bool:
    rel_path = repo_relative_path(path)
    if not rel_path:
        return False
    prefixes = FRAMEWORK_PREFIXES if mode == "framework" else TARGET_PREFIXES
    if mode == "framework" and is_allowed_root_file(rel_path):
        return True
    return any(rel_path == prefix.rstrip("/") or rel_path.startswith(prefix) for prefix in prefixes)


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
    try:
        payload = json.load(sys.stdin)
    except (json.JSONDecodeError, EOFError):
        respond_deny("wiki-write-guard 無法解析 hook 輸入，依 fail-safe 政策拒絕本次寫入。")
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

    mode = read_guard_mode()
    disallowed_paths = [path for path in target_paths if not is_allowed_path(path, mode)]
    if disallowed_paths:
        summarized_paths = ", ".join(f"`{path}`" for path in disallowed_paths[:3])
        if len(disallowed_paths) > 3:
            summarized_paths += f" 等 {len(disallowed_paths)} 個路徑"
        allowed_summary = "`wiki/`" if mode == "target" else "`wiki/` 與框架 schema/docs 路徑"
        respond_deny(
            f"Codebase LLM Wiki write guard 目前為 `{mode}` 模式，只允許寫入 {allowed_summary}。"
            f"這次偵測到其他路徑：{summarized_paths}。"
        )
        return

    respond_allow()


if __name__ == "__main__":
    main()
