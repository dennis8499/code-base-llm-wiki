#!/usr/bin/env python3
"""Tree-sitter preflight helper for Codebase Wiki workflows.

The helper never writes source or wiki files. It scans a target tree to decide
which Tree-sitter packages are relevant, checks whether the core binding and
the required language parser modules are importable, and reports any missing
packages so the agent can ask the user before installing them.
"""

from __future__ import annotations

import argparse
import datetime as _datetime
import importlib
import json
from pathlib import Path
import sys
from typing import Any, Iterable


VERSION = "1.0"
SUPPORTED_EXTENSIONS = {
    ".ts": "typescript",
    ".tsx": "typescript",
    ".js": "javascript",
    ".jsx": "javascript",
    ".py": "python",
    ".cs": "csharp",
}
SKIP_DIRS = {
    ".git",
    ".hg",
    ".svn",
    ".venv",
    "venv",
    "node_modules",
    "__pycache__",
    "bin",
    "obj",
    "dist",
    "build",
}
CORE_PACKAGE = "tree_sitter"
LANGUAGE_REQUIREMENTS = {
    "python": {"package": "tree_sitter_python", "entrypoints": ("language",)},
    "javascript": {"package": "tree_sitter_javascript", "entrypoints": ("language",)},
    "typescript": {"package": "tree_sitter_typescript", "entrypoints": ("language_typescript", "language_tsx")},
    "csharp": {"package": "tree_sitter_c_sharp", "entrypoints": ("language",)},
}


def configure_utf8_stdio() -> None:
    for stream in (sys.stdout, sys.stderr):
        try:
            stream.reconfigure(encoding="utf-8")
        except Exception:
            pass


def utc_now() -> str:
    value = _datetime.datetime.now(_datetime.timezone.utc).replace(microsecond=0)
    return value.isoformat().replace("+00:00", "Z")


def repo_relative(path: Path, repo_root: Path) -> str:
    try:
        return path.resolve().relative_to(repo_root.resolve()).as_posix()
    except ValueError:
        try:
            return path.resolve().relative_to(Path.cwd().resolve()).as_posix()
        except ValueError:
            return path.as_posix()


def iter_source_files(target: Path) -> Iterable[Path]:
    if target.is_file():
        yield target
        return

    for path in sorted(target.rglob("*")):
        if not path.is_file():
            continue
        if any(part in SKIP_DIRS for part in path.parts):
            continue
        yield path


def detect_language(path: Path) -> str:
    return SUPPORTED_EXTENSIONS.get(path.suffix.lower(), "unsupported")


def discover_languages(target: Path) -> list[str]:
    languages: list[str] = []
    seen: set[str] = set()

    for path in iter_source_files(target):
        language = detect_language(path)
        if language == "unsupported" or language in seen:
            continue
        seen.add(language)
        languages.append(language)

    return languages


def inspect_module(module_name: str, entrypoints: tuple[str, ...], any_match: bool) -> dict[str, Any]:
    try:
        module = importlib.import_module(module_name)
    except Exception as exc:
        return {
            "package": module_name,
            "available": False,
            "entrypoints": {entrypoint: False for entrypoint in entrypoints},
            "error": str(exc),
        }

    entrypoint_status: dict[str, bool] = {}
    for entrypoint in entrypoints:
        entrypoint_status[entrypoint] = callable(getattr(module, entrypoint, None))

    available = any(entrypoint_status.values()) if any_match else all(entrypoint_status.values())
    error = "" if available else f"{module_name} is importable, but required entrypoint(s) are missing."
    return {
        "package": module_name,
        "available": available,
        "entrypoints": entrypoint_status,
        "error": error,
    }


def build_report(target: Path, repo_root: Path) -> dict[str, Any]:
    if not target.exists():
        return {
            "version": VERSION,
            "target_path": str(target),
            "generated_at": utc_now(),
            "status": "target_not_found",
            "languages": [],
            "checks": [],
            "missing_packages": [],
            "install_command": "",
            "ready": False,
            "user_prompt": f"Target path does not exist: {target}",
        }

    languages = discover_languages(target)
    checks: list[dict[str, Any]] = []
    missing_packages: list[str] = []

    if languages:
        core_check = inspect_module(CORE_PACKAGE, ("Language", "Parser"), any_match=False)
        core_check["kind"] = "core"
        checks.append(core_check)
        if not core_check["available"]:
            missing_packages.append(CORE_PACKAGE)

        for language in languages:
            requirement = LANGUAGE_REQUIREMENTS[language]
            check = inspect_module(
                requirement["package"],
                requirement["entrypoints"],
                any_match=language == "typescript",
            )
            check["kind"] = language
            checks.append(check)
            if not check["available"] and check["package"] not in missing_packages:
                missing_packages.append(check["package"])

    status = "ready"
    if not languages:
        status = "no_supported_sources"
    elif missing_packages:
        status = "needs_install"

    install_command = f"python -m pip install {' '.join(missing_packages)}" if missing_packages else ""
    if missing_packages:
        user_prompt = (
            "Missing Tree-sitter packages detected: "
            + ", ".join(missing_packages)
            + f". Install them now with `{install_command}`?"
        )
    elif not languages:
        user_prompt = "No supported source files were found, so Tree-sitter preflight is not required."
    else:
        user_prompt = "Tree-sitter preflight passed; optional structure-index.py can run with the current environment."

    return {
        "version": VERSION,
        "target_path": repo_relative(target, repo_root),
        "generated_at": utc_now(),
        "status": status,
        "languages": languages,
        "checks": checks,
        "missing_packages": missing_packages,
        "install_command": install_command,
        "ready": status in {"ready", "no_supported_sources"},
        "user_prompt": user_prompt,
    }


def parse_args(argv: list[str]) -> argparse.Namespace:
    parser = argparse.ArgumentParser(description="Emit a JSON Tree-sitter preflight report for wiki workflows.")
    parser.add_argument("target_path", help="Source file or directory to scan.")
    parser.add_argument("--format", choices=["json"], default="json", help="Output format. Only json is currently supported.")
    parser.add_argument("--repo-root", default=".", help="Repo root used for relative paths. Defaults to current directory.")
    return parser.parse_args(argv)


def main(argv: list[str] | None = None) -> int:
    configure_utf8_stdio()
    args = parse_args(argv or sys.argv[1:])
    repo_root = Path(args.repo_root).resolve()
    target = Path(args.target_path)
    if not target.is_absolute():
        target = (Path.cwd() / target).resolve()

    payload = build_report(target, repo_root)
    print(json.dumps(payload, ensure_ascii=False, indent=2))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
