#!/usr/bin/env python3
"""Install or upgrade Codebase LLM Wiki framework surfaces.

The installer is intentionally dependency-free. It plans changes by default and
only writes to the target repository when ``--apply`` is supplied and no
conflicting target files are present.
"""

from __future__ import annotations

import argparse
import hashlib
import json
from pathlib import Path
from typing import Sequence


CONTRACT_VERSION = 2
REPO_ROOT = Path(__file__).resolve().parents[4]
COMMON_SURFACE_PATHS = ("AGENTS.md", ".agents/skills/codebase-wiki")
SURFACE_PATHS = {
    "codex": ("Codex.md", ".codex"),
    "copilot": (".github",),
}
WIKI_STARTER_PATH = ".agents/skills/codebase-wiki/assets/wiki-starter"
EXCLUDED_PARTS = {"__pycache__", "logs", ".venv", "cache"}
TARGET_MODE_CONFIGS = {".codex/config.toml", ".github/hooks/config.toml"}
LEGACY_RUNTIME_PATH = ".codebase-wiki/"
VERSION_SOURCE_PATH = "VERSION"
INSTALLED_VERSION_PATH = ".agents/skills/codebase-wiki/VERSION"
FRAMEWORK_ONLY_PATHS = {".github/workflows/release.yml"}


def _files(root: Path, relative_root: str) -> list[tuple[Path, str]]:
    source = root / relative_root
    if source.is_file():
        return [(source, relative_root.replace("\\", "/"))]
    if not source.exists():
        return []
    return [
        (path, path.relative_to(root).as_posix())
        for path in sorted(source.rglob("*"))
        if path.is_file()
        and not any(part in EXCLUDED_PARTS for part in path.relative_to(root).parts)
        and path.suffix != ".pyc"
    ]


def _target_bytes(source: Path, relative: str) -> bytes:
    data = source.read_bytes()
    if relative in TARGET_MODE_CONFIGS:
        data = data.replace(b'mode = "framework"', b'mode = "target"')
    return data


def _framework_version(root: Path) -> str | None:
    version_path = root / VERSION_SOURCE_PATH
    if not version_path.is_file():
        return None
    return version_path.read_text(encoding="utf-8").strip()


def _surface_files(root: Path, surface: str, action: str = "install") -> list[tuple[Path, str]]:
    files: list[tuple[Path, str]] = []
    for relative_root in (*COMMON_SURFACE_PATHS, *SURFACE_PATHS[surface]):
        files.extend(
            (source, relative)
            for source, relative in _files(root, relative_root)
            if relative not in FRAMEWORK_ONLY_PATHS
        )
    if (root / VERSION_SOURCE_PATH).is_file():
        files.append((root / VERSION_SOURCE_PATH, INSTALLED_VERSION_PATH))
    if action == "install":
        for source, relative in _files(root, WIKI_STARTER_PATH):
            starter_relative = Path(relative).relative_to(WIKI_STARTER_PATH)
            files.append((source, (Path("wiki") / starter_relative).as_posix()))
    return files


def _obsolete_paths(target_root: Path) -> list[str]:
    return [LEGACY_RUNTIME_PATH] if (target_root / LEGACY_RUNTIME_PATH).exists() else []


def plan_install(
    source_root: Path,
    target_root: Path,
    surface: str,
    action: str = "install",
) -> dict[str, object]:
    if surface not in SURFACE_PATHS:
        raise ValueError(f"unknown surface: {surface}")
    if action not in {"install", "upgrade"}:
        raise ValueError(f"unknown action: {action}")
    files: list[str] = []
    conflicts: list[str] = []
    for source, relative in _surface_files(source_root, surface, action):
        files.append(relative)
        target = target_root / relative
        expected = _target_bytes(source, relative)
        if target.is_dir() or (
            target.exists()
            and hashlib.sha256(expected).digest() != hashlib.sha256(target.read_bytes()).digest()
        ):
            conflicts.append(relative)
    return {
        "surface": surface,
        "framework_version": _framework_version(source_root),
        "files": sorted(set(files)),
        "conflicts": sorted(set(conflicts)),
        "obsolete_paths": _obsolete_paths(target_root),
    }


def apply_install(
    source_root: Path,
    target_root: Path,
    surface: str,
    action: str = "install",
) -> dict[str, object]:
    plan = plan_install(source_root, target_root, surface, action)
    if plan["conflicts"]:
        raise FileExistsError("Installation conflicts: " + ", ".join(plan["conflicts"]))
    for source, relative in _surface_files(source_root, surface, action):
        destination = target_root / relative
        destination.parent.mkdir(parents=True, exist_ok=True)
        destination.write_bytes(_target_bytes(source, relative))
    return plan


def build_parser() -> argparse.ArgumentParser:
    parser = argparse.ArgumentParser(prog="install-framework.py")
    subparsers = parser.add_subparsers(dest="action", required=True)
    for action in ("install", "upgrade"):
        command = subparsers.add_parser(action)
        command.add_argument("--target", type=Path, required=True)
        command.add_argument("--surface", choices=tuple(SURFACE_PATHS), required=True)
        command.add_argument("--apply", action="store_true")
        command.add_argument("--format", choices=("json", "text"), default="text")
    return parser


def main(argv: Sequence[str] | None = None) -> int:
    args = build_parser().parse_args(argv)
    target_root = args.target.resolve()
    plan = plan_install(REPO_ROOT, target_root, args.surface, args.action)
    applied = False
    if args.apply and not plan["conflicts"]:
        apply_install(REPO_ROOT, target_root, args.surface, args.action)
        applied = True

    payload = {
        "contract_version": CONTRACT_VERSION,
        "framework_version": plan.get("framework_version"),
        "ok": not bool(plan["conflicts"]),
        "action": args.action,
        **plan,
        "applied": applied,
    }
    if args.format == "json":
        print(json.dumps(payload, ensure_ascii=True, sort_keys=True))
    else:
        print(json.dumps(payload, ensure_ascii=False, indent=2))
    return 0 if payload["ok"] else 2


if __name__ == "__main__":
    raise SystemExit(main())
