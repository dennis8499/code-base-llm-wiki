#!/usr/bin/env python3
"""Validate the shared Copilot/Codex capability surface without byte mirroring."""

from __future__ import annotations

import json
from pathlib import Path
import sys


def main() -> int:
    root = Path(__file__).resolve().parents[4]
    manifest_path = root / ".agents" / "skills" / "codebase-wiki" / "capabilities.json"
    issues: list[str] = []
    if not manifest_path.exists():
        issues.append("missing capabilities.json")
        manifest = {}
    else:
        manifest = json.loads(manifest_path.read_text(encoding="utf-8"))
    for surface in ("copilot", "codex"):
        if surface not in manifest.get("surfaces", []):
            issues.append(f"manifest missing surface: {surface}")
    if manifest.get("contract_version") != 2:
        issues.append("manifest contract_version must be 2")
    cli = manifest.get("cli", {})
    if not isinstance(cli, dict):
        issues.append("manifest cli must be an object")
        cli = {}
    for action in ("install", "upgrade"):
        command = cli.get(action, "")
        if not isinstance(command, str) or f"install-framework.py {action}" not in command:
            issues.append(f"manifest missing installer command: {action}")
    stale_runtime_commands = sorted(set(cli) & {"setup", "doctor", "index", "search", "show"})
    if stale_runtime_commands:
        issues.append("manifest retains removed runtime commands: " + ", ".join(stale_runtime_commands))
    for path in (
        root / ".agents" / "skills" / "codebase-wiki" / "SKILL.md",
        root / ".agents" / "skills" / "codebase-wiki" / "scripts" / "install-framework.py",
        root / ".github" / "copilot-instructions.md",
        root / "AGENTS.md",
    ):
        if not path.exists():
            issues.append(f"missing required surface: {path.relative_to(root).as_posix()}")
    for directory in (root / ".github", root / ".codex"):
        for path in directory.rglob("*") if directory.exists() else ():
            if path.is_file() and path.suffix in {".md", ".toml", ".json", ".py"}:
                # Hook audit logs are generated state, not executable entrypoint
                # instructions. They may retain historical references and must
                # not make the current surface parity check fail.
                relative_parts = path.relative_to(root).parts
                if "logs" in relative_parts:
                    continue
                text = path.read_text(encoding="utf-8", errors="replace")
                if ".github/skills" in text or ".github\\skills" in text:
                    issues.append(f"stale mirrored skill reference: {path.relative_to(root).as_posix()}")
    payload = {"ok": not issues, "contract_version": manifest.get("contract_version", 0), "issues": issues}
    print(json.dumps(payload, ensure_ascii=False, indent=2))
    return 0 if not issues else 1


if __name__ == "__main__":
    raise SystemExit(main())
