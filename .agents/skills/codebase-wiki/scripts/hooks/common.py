"""Shared helpers for Copilot and Codex Wiki hooks."""

from __future__ import annotations

import argparse
import json
import os
from pathlib import Path
import re
import stat
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
DRIVE_PATH_PATTERN = re.compile(r"^[A-Za-z]:")


def configure_stdio() -> None:
    for stream in (sys.stdout, sys.stderr):
        if hasattr(stream, "reconfigure"):
            stream.reconfigure(encoding="utf-8", errors="replace")


def parse_platform() -> str:
    parser = argparse.ArgumentParser(add_help=False)
    parser.add_argument("--platform", choices=("codex", "copilot"), required=True)
    args, _ = parser.parse_known_args()
    return str(args.platform)


def repo_root() -> Path:
    for parent in Path(__file__).resolve().parents:
        skill = parent / ".agents" / "skills" / "codebase-wiki"
        if (parent / "AGENTS.md").is_file() and skill.is_dir():
            return parent
    raise RuntimeError("Codebase LLM Wiki repository root not found")


def audit_candidates(platform: str, filename: str) -> tuple[Path, ...]:
    root = repo_root()
    if platform == "copilot":
        return (
            root / ".github" / "hooks" / "logs" / filename,
            root / ".github-hook-logs" / filename,
        )
    return (
        root / ".codex" / "hooks" / "logs" / filename,
        root / ".codex-hook-logs" / filename,
    )


def _is_reparse_point(path: Path) -> bool:
    """Detect symlinks and Windows junction/reparse points without following them."""

    if path.is_symlink():
        return True
    if os.name != "nt":
        return False
    try:
        attributes = os.stat(path, follow_symlinks=False).st_file_attributes
    except FileNotFoundError:
        return False
    except OSError:
        return True
    return bool(attributes & getattr(stat, "FILE_ATTRIBUTE_REPARSE_POINT", 0x400))


def audit_path_is_safe(path: Path) -> bool:
    """Return whether an audit file stays inside the repository boundary."""

    root = repo_root().resolve(strict=False)
    lexical_root = Path(os.path.abspath(root))
    lexical_path = Path(os.path.abspath(path))
    try:
        relative = lexical_path.relative_to(lexical_root)
    except ValueError:
        return False
    current = lexical_root
    for component in relative.parts:
        current /= component
        if _is_reparse_point(current):
            return False
    try:
        lexical_path.resolve(strict=False).relative_to(root)
    except (OSError, RuntimeError, ValueError):
        return False
    return True


def normalize_path(value: str) -> str:
    return value.replace("\\", "/").strip().strip("\"'")


def repo_relative_path(value: str) -> str | None:
    normalized = normalize_path(value)
    if DRIVE_PATH_PATTERN.match(normalized):
        return None
    while normalized.startswith("./"):
        normalized = normalized[2:]
    try:
        candidate = Path(normalized)
        if not candidate.is_absolute():
            candidate = repo_root() / candidate
        return candidate.resolve(strict=False).relative_to(
            repo_root().resolve(strict=False)
        ).as_posix()
    except (OSError, ValueError):
        return None


def parse_tool_input(payload: dict[str, Any]) -> Any:
    if "tool_input" in payload:
        return payload.get("tool_input")
    if "toolInput" in payload:
        return payload.get("toolInput")
    value = payload.get("toolArgs")
    if isinstance(value, str) and value.strip():
        try:
            return json.loads(value)
        except json.JSONDecodeError:
            return value
    return value


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


def extract_paths(tool_name: str, tool_input: Any) -> list[str]:
    paths: list[str] = []
    if isinstance(tool_input, dict):
        for key in ("filePath", "file_path", "path", "targetPath", "target_path"):
            value = tool_input.get(key)
            if isinstance(value, str) and value.strip():
                paths.append(value)
        files = tool_input.get("files")
        if isinstance(files, list):
            for item in files:
                if isinstance(item, str):
                    paths.append(item)
                elif isinstance(item, dict):
                    for key in ("filePath", "file_path", "path"):
                        value = item.get(key)
                        if isinstance(value, str) and value.strip():
                            paths.append(value)
    patch_text = extract_patch_text(tool_input)
    if tool_name == "apply_patch" or patch_text:
        paths.extend(match.group(1) for match in PATCH_FILE_PATTERN.finditer(patch_text))
    return list(dict.fromkeys(filter(None, (normalize_path(path) for path in paths))))
