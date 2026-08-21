#!/usr/bin/env python3
"""Plan and atomically install or upgrade Codebase LLM Wiki surfaces."""

from __future__ import annotations

import argparse
import datetime as dt
import hashlib
import json
import os
from pathlib import Path
import shutil
import tempfile
from typing import Any, Sequence


CONTRACT_VERSION = 3
REPO_ROOT = Path(__file__).resolve().parents[4]
COMMON_SURFACE_PATHS = ("AGENTS.md", ".agents/skills/codebase-wiki")
SURFACE_PATHS = {
    "codex": ("Codex.md", ".codex"),
    "copilot": (".github",),
}
WIKI_STARTER_PATH = ".agents/skills/codebase-wiki/assets/wiki-starter"
TARGET_AGENTS_BLOCK_PATH = ".agents/skills/codebase-wiki/assets/target-agents-block.md"
EXCLUDED_PARTS = {"__pycache__", "logs", ".venv", "cache"}
TARGET_MODE_CONFIGS = {".codex/config.toml", ".github/hooks/config.toml"}
MANAGED_BLOCK_PATHS = {"AGENTS.md", ".github/copilot-instructions.md"}
MANAGED_BEGIN = "<!-- codebase-wiki:managed:start -->"
MANAGED_END = "<!-- codebase-wiki:managed:end -->"
LEGACY_RUNTIME_PATH = ".codebase-wiki/"
VERSION_SOURCE_PATH = "VERSION"
INSTALLED_VERSION_PATH = ".agents/skills/codebase-wiki/VERSION"
INSTALL_STATE_PATH = ".agents/skills/codebase-wiki/install-state.json"
FRAMEWORK_ONLY_PATHS = {
    ".github/workflows/ci.yml",
    ".github/workflows/release.yml",
}


def _sha256(data: bytes) -> str:
    return hashlib.sha256(data).hexdigest()


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
        and path.relative_to(root).as_posix() != INSTALL_STATE_PATH
    ]


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
    unique: dict[str, Path] = {}
    for source, relative in files:
        unique[relative] = source
    return [(source, relative) for relative, source in sorted(unique.items())]


def _managed_block(source_root: Path, source: Path, relative: str) -> bytes:
    selected = source
    if relative == "AGENTS.md":
        target_asset = source_root / TARGET_AGENTS_BLOCK_PATH
        if target_asset.is_file():
            selected = target_asset
    text = selected.read_text(encoding="utf-8").strip()
    if MANAGED_BEGIN in text and MANAGED_END in text:
        text = text.split(MANAGED_BEGIN, 1)[1].split(MANAGED_END, 1)[0].strip()
    return (text + "\n").encode("utf-8")


def _render_managed_document(existing: bytes | None, block: bytes) -> bytes:
    current = existing.decode("utf-8") if existing is not None else ""
    managed = f"{MANAGED_BEGIN}\n{block.decode('utf-8').rstrip()}\n{MANAGED_END}"
    if MANAGED_BEGIN in current and MANAGED_END in current:
        before, remainder = current.split(MANAGED_BEGIN, 1)
        _, after = remainder.split(MANAGED_END, 1)
        return (before.rstrip() + "\n\n" + managed + after).encode("utf-8")
    if current.strip():
        return (current.rstrip() + "\n\n" + managed + "\n").encode("utf-8")
    return (managed + "\n").encode("utf-8")


def _target_bytes(
    source_root: Path,
    source: Path,
    relative: str,
    guard_mode: str,
    install_date: dt.date,
) -> bytes:
    data = source.read_bytes()
    if relative in TARGET_MODE_CONFIGS:
        text = data.decode("utf-8")
        text = text.replace('mode = "framework"', f'mode = "{guard_mode}"')
        text = text.replace('mode = "target"', f'mode = "{guard_mode}"')
        data = text.encode("utf-8")
    if relative.startswith("wiki/"):
        data = data.replace(b"2026-07-22", install_date.isoformat().encode("ascii"))
    return data


def _load_state(target_root: Path) -> dict[str, Any] | None:
    path = target_root / INSTALL_STATE_PATH
    if not path.is_file():
        return None
    try:
        value = json.loads(path.read_text(encoding="utf-8"))
    except (OSError, json.JSONDecodeError):
        return None
    if not isinstance(value, dict) or not isinstance(value.get("files"), dict):
        return None
    return value


def _existing_bytes(path: Path) -> bytes | None:
    if path.is_file():
        return path.read_bytes()
    return None


def _block_fingerprint(data: bytes | None) -> str | None:
    if data is None:
        return None
    try:
        text = data.decode("utf-8")
    except UnicodeDecodeError:
        return None
    if MANAGED_BEGIN not in text or MANAGED_END not in text:
        return None
    block = text.split(MANAGED_BEGIN, 1)[1].split(MANAGED_END, 1)[0].strip()
    return _sha256((block + "\n").encode("utf-8"))


def _obsolete_paths(target_root: Path, state: dict[str, Any] | None, expected: set[str]) -> list[str]:
    values = [LEGACY_RUNTIME_PATH] if (target_root / LEGACY_RUNTIME_PATH).exists() else []
    if state:
        values.extend(
            sorted(
                path
                for path in set(state.get("files", {})) - expected
                if not path.startswith("wiki/")
            )
        )
    return sorted(set(values))


def _prepare_plan(
    source_root: Path,
    target_root: Path,
    surface: str,
    action: str,
    guard_mode: str,
    install_date: dt.date,
) -> tuple[dict[str, Any], dict[str, bytes], bytes]:
    if surface not in SURFACE_PATHS:
        raise ValueError(f"unknown surface: {surface}")
    if action not in {"install", "upgrade"}:
        raise ValueError(f"unknown action: {action}")
    if guard_mode not in {"wiki-only", "coexist"}:
        raise ValueError(f"unknown guard mode: {guard_mode}")

    state = _load_state(target_root)
    state_files = state.get("files", {}) if state else {}
    files: list[str] = []
    managed: list[str] = []
    preserved: list[str] = []
    conflicts: list[str] = []
    changes: list[str] = []
    writes: dict[str, bytes] = {}
    next_state_files: dict[str, dict[str, str]] = {}

    for source, relative in _surface_files(source_root, surface, action):
        files.append(relative)
        managed.append(relative)
        target = target_root / relative
        if target.exists() and not target.is_file():
            conflicts.append(relative)
            continue
        existing = _existing_bytes(target)
        kind = "managed_block" if relative in MANAGED_BLOCK_PATHS else "file"
        if kind == "managed_block":
            block = _managed_block(source_root, source, relative)
            expected = _render_managed_document(existing, block)
            expected_fingerprint = _sha256(block)
            actual_fingerprint = _block_fingerprint(existing)
        else:
            expected = _target_bytes(
                source_root, source, relative, guard_mode, install_date
            )
            expected_fingerprint = _sha256(expected)
            actual_fingerprint = _sha256(existing) if existing is not None else None

        baseline_entry = state_files.get(relative)
        baseline = (
            baseline_entry.get("sha256")
            if isinstance(baseline_entry, dict) and baseline_entry.get("kind") == kind
            else None
        )
        if baseline is None:
            if kind == "managed_block":
                local_changed = False
                upstream_changed = True
            else:
                local_changed = existing is not None and actual_fingerprint != expected_fingerprint
                upstream_changed = True
        else:
            local_changed = actual_fingerprint != baseline
            upstream_changed = expected_fingerprint != baseline

        if local_changed and upstream_changed:
            conflicts.append(relative)
        elif local_changed:
            preserved.append(relative)
        elif existing != expected:
            changes.append(relative)
            writes[relative] = expected
        next_state_files[relative] = {
            "kind": kind,
            "sha256": expected_fingerprint,
        }

    expected_paths = set(files)
    state_payload = {
        "contract_version": CONTRACT_VERSION,
        "framework_version": _framework_version(source_root),
        "surface": surface,
        "guard_mode": guard_mode,
        "files": dict(sorted(next_state_files.items())),
    }
    state_bytes = (
        json.dumps(state_payload, ensure_ascii=False, indent=2, sort_keys=True) + "\n"
    ).encode("utf-8")
    state_existing = _existing_bytes(target_root / INSTALL_STATE_PATH)
    if not conflicts and state_existing != state_bytes:
        writes[INSTALL_STATE_PATH] = state_bytes
        changes.append(INSTALL_STATE_PATH)

    plan = {
        "surface": surface,
        "guard_mode": guard_mode,
        "framework_version": _framework_version(source_root),
        "files": sorted(set(files) | {INSTALL_STATE_PATH}),
        "managed": sorted(set(managed)),
        "changes": sorted(set(changes)),
        "preserved": sorted(set(preserved)),
        "conflicts": sorted(set(conflicts)),
        "obsolete_paths": _obsolete_paths(target_root, state, expected_paths),
    }
    return plan, writes, state_bytes


def plan_install(
    source_root: Path,
    target_root: Path,
    surface: str,
    action: str = "install",
    guard_mode: str = "wiki-only",
    install_date: dt.date | None = None,
) -> dict[str, object]:
    plan, _, _ = _prepare_plan(
        source_root,
        target_root,
        surface,
        action,
        guard_mode,
        install_date or dt.date.today(),
    )
    return plan


def _atomic_write(target_root: Path, writes: dict[str, bytes]) -> None:
    target_root.mkdir(parents=True, exist_ok=True)
    stage = Path(tempfile.mkdtemp(prefix="codebase-wiki-stage-", dir=target_root.parent))
    backup = Path(tempfile.mkdtemp(prefix="codebase-wiki-backup-", dir=target_root.parent))
    replaced: list[str] = []
    created: list[str] = []
    try:
        for relative, data in writes.items():
            staged = stage / relative
            staged.parent.mkdir(parents=True, exist_ok=True)
            staged.write_bytes(data)
        for relative in sorted(writes):
            destination = target_root / relative
            destination.parent.mkdir(parents=True, exist_ok=True)
            if destination.exists():
                saved = backup / relative
                saved.parent.mkdir(parents=True, exist_ok=True)
                os.replace(destination, saved)
                replaced.append(relative)
            else:
                created.append(relative)
            os.replace(stage / relative, destination)
    except OSError:
        for relative in reversed(created):
            destination = target_root / relative
            if destination.is_file():
                destination.unlink()
        for relative in reversed(replaced):
            destination = target_root / relative
            saved = backup / relative
            if destination.is_file():
                destination.unlink()
            if saved.exists():
                destination.parent.mkdir(parents=True, exist_ok=True)
                os.replace(saved, destination)
        raise
    finally:
        shutil.rmtree(stage, ignore_errors=True)
        shutil.rmtree(backup, ignore_errors=True)


def apply_install(
    source_root: Path,
    target_root: Path,
    surface: str,
    action: str = "install",
    guard_mode: str = "wiki-only",
    install_date: dt.date | None = None,
) -> dict[str, object]:
    plan, writes, _ = _prepare_plan(
        source_root,
        target_root,
        surface,
        action,
        guard_mode,
        install_date or dt.date.today(),
    )
    if plan["conflicts"]:
        raise FileExistsError("Installation conflicts: " + ", ".join(plan["conflicts"]))
    _atomic_write(target_root, writes)
    return plan


def build_parser() -> argparse.ArgumentParser:
    parser = argparse.ArgumentParser(prog="install-framework.py")
    subparsers = parser.add_subparsers(dest="action", required=True)
    for action in ("install", "upgrade"):
        command = subparsers.add_parser(action)
        command.add_argument("--target", type=Path, required=True)
        command.add_argument("--surface", choices=tuple(SURFACE_PATHS), required=True)
        command.add_argument(
            "--guard-mode", choices=("wiki-only", "coexist"), default="wiki-only"
        )
        command.add_argument("--apply", action="store_true")
        command.add_argument("--format", choices=("json", "text"), default="text")
    return parser


def main(argv: Sequence[str] | None = None) -> int:
    args = build_parser().parse_args(argv)
    target_root = args.target.resolve()
    plan = plan_install(
        REPO_ROOT, target_root, args.surface, args.action, args.guard_mode
    )
    applied = False
    if args.apply and not plan["conflicts"]:
        apply_install(
            REPO_ROOT, target_root, args.surface, args.action, args.guard_mode
        )
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
