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
SURFACE_PATHS = {
    "codex": ("AGENTS.md", "Codex.md", ".agents", ".codex", "wiki"),
    "copilot": ("AGENTS.md", ".agents", ".github", "wiki"),
}
EXCLUDED_PARTS = {"__pycache__", "logs", ".venv", "cache"}
TARGET_MODE_CONFIGS = {".codex/config.toml", ".github/hooks/config.toml"}
LEGACY_RUNTIME_PATH = ".codebase-wiki/"


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


def _obsolete_paths(target_root: Path) -> list[str]:
    return [LEGACY_RUNTIME_PATH] if (target_root / LEGACY_RUNTIME_PATH).exists() else []


def plan_install(source_root: Path, target_root: Path, surface: str) -> dict[str, object]:
    if surface not in SURFACE_PATHS:
        raise ValueError(f"unknown surface: {surface}")
    files: list[str] = []
    conflicts: list[str] = []
    for relative_root in SURFACE_PATHS[surface]:
        for source, relative in _files(source_root, relative_root):
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
        "files": sorted(set(files)),
        "conflicts": sorted(set(conflicts)),
        "obsolete_paths": _obsolete_paths(target_root),
    }


def apply_install(source_root: Path, target_root: Path, surface: str) -> dict[str, object]:
    plan = plan_install(source_root, target_root, surface)
    if plan["conflicts"]:
        raise FileExistsError("Installation conflicts: " + ", ".join(plan["conflicts"]))
    for relative_root in SURFACE_PATHS[surface]:
        for source, relative in _files(source_root, relative_root):
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
    plan = plan_install(REPO_ROOT, target_root, args.surface)
    applied = False
    if args.apply and not plan["conflicts"]:
        apply_install(REPO_ROOT, target_root, args.surface)
        applied = True

    payload = {
        "contract_version": CONTRACT_VERSION,
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
