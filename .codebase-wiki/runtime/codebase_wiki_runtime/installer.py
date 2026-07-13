from __future__ import annotations

import hashlib
from pathlib import Path


SURFACE_PATHS = {
    "codex": ["AGENTS.md", "Codex.md", ".agents", ".codex", ".codebase-wiki", "wiki"],
    "copilot": ["AGENTS.md", ".agents", ".github", ".codebase-wiki", "wiki"],
}


def _files(root: Path, relative_root: str) -> list[tuple[Path, str]]:
    source = root / relative_root
    if source.is_file():
        return [(source, relative_root.replace("\\", "/"))]
    if not source.exists():
        return []
    return [
        (path, path.relative_to(root).as_posix())
        for path in source.rglob("*")
        if path.is_file()
        and "__pycache__" not in path.parts
        and "logs" not in path.parts
        and ".venv" not in path.parts
        and "cache" not in path.parts
    ]


def _target_bytes(source: Path, relative: str) -> bytes:
    data = source.read_bytes()
    if relative in {".codex/config.toml", ".github/hooks/config.toml", ".codebase-wiki/config.toml"}:
        data = data.replace(b'mode = "framework"', b'mode = "target"')
    return data


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
            if target.is_dir() or (target.exists() and hashlib.sha256(expected).digest() != hashlib.sha256(target.read_bytes()).digest()):
                conflicts.append(relative)
    return {"surface": surface, "files": sorted(set(files)), "conflicts": sorted(set(conflicts))}


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
