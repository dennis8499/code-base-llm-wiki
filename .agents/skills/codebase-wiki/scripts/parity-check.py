#!/usr/bin/env python3
"""Validate the shared Copilot/Codex capability surface without byte mirroring."""

from __future__ import annotations

import json
from pathlib import Path
import sys


EXPECTED_OPERATIONS = {
    "install",
    "ingest",
    "query",
    "lint",
    "archaeology",
    "adr",
    "guide",
    "synthesis",
    "system_analysis",
    "notebooklm_export",
    "delegation",
}
EXPECTED_INTENT_CONTRACT = {
    "install": (False, True, "apply_flag"),
    "ingest": (False, True, "interactive_preview_or_explicit_batch"),
    "query": (False, False, "read_only"),
    "lint": (False, True, "confirm_repairs"),
    "archaeology": (False, True, "explicit_persist"),
    "adr": (True, False, "explicit_request"),
    "guide": (True, False, "explicit_request"),
    "synthesis": (True, False, "explicit_request"),
    "system_analysis": (True, False, "explicit_request"),
    "notebooklm_export": (False, True, "preview_then_confirm"),
    "delegation": (False, False, "explicit_delegation"),
}
EXPECTED_GROUPS = {
    "install_setup": ["install"],
    "ingest": ["ingest"],
    "query": ["query"],
    "lint": ["lint"],
    "adr": ["adr"],
    "synthesis_guide": ["synthesis", "guide"],
    "system_analysis": ["system_analysis"],
    "notebooklm_export": ["notebooklm_export"],
    "archaeology": ["archaeology"],
    "delegation": ["delegation"],
}
CANONICAL_HOOK_ROOT = ".agents/skills/codebase-wiki/scripts/hooks/"


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

    intents = manifest.get("intents", {})
    if not isinstance(intents, dict) or set(intents) != EXPECTED_OPERATIONS:
        issues.append("manifest intents must define the eleven canonical operations")
        intents = {}
    for operation, expected in EXPECTED_INTENT_CONTRACT.items():
        contract = intents.get(operation, {})
        actual = (
            contract.get("writes_by_default"),
            contract.get("requires_confirmation"),
            contract.get("authorization_policy"),
        )
        if actual != expected:
            issues.append(f"authorization drift: {operation}")

    groups = manifest.get("intent_groups", {})
    if groups != EXPECTED_GROUPS:
        issues.append("manifest must define the exact ten user-facing intent groups")
        groups = {}
    grouped = [operation for values in groups.values() if isinstance(values, list) for operation in values]
    if len(grouped) != len(set(grouped)) or set(grouped) != EXPECTED_OPERATIONS:
        issues.append("intent_groups must cover each canonical operation exactly once")

    entrypoints = manifest.get("entrypoints", {})
    copilot_entrypoints = entrypoints.get("copilot", {}) if isinstance(entrypoints, dict) else {}
    if set(copilot_entrypoints) != EXPECTED_OPERATIONS:
        issues.append("Copilot entrypoint mapping must cover every operation")
    else:
        for operation, filenames in copilot_entrypoints.items():
            if not isinstance(filenames, list):
                issues.append(f"Copilot entrypoints must be arrays: {operation}")
                continue
            for filename in filenames:
                if not (root / ".github" / "prompts" / filename).is_file():
                    issues.append(f"missing Copilot prompt: {filename}")
    recipe_document = entrypoints.get("codex", {}).get("recipe_document", "")
    if recipe_document != "Codex.md" or not (root / recipe_document).is_file():
        issues.append("Codex recipe document must be Codex.md")

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

    for hook_name in ("wiki-session-init.py", "wiki-write-guard.py", "wiki-log-reminder.py"):
        if not (root / CANONICAL_HOOK_ROOT / hook_name).is_file():
            issues.append(f"missing canonical hook: {hook_name}")
    for legacy_root in (
        root / ".codex" / "hooks" / "scripts",
        root / ".github" / "hooks" / "scripts",
    ):
        if legacy_root.is_dir() and any(legacy_root.glob("*.py")):
            issues.append(f"legacy hook mirrors remain: {legacy_root.relative_to(root)}")
    hook_configs = {
        root / ".codex" / "hooks.json": "--platform codex",
        root / ".github" / "hooks" / "wiki-session-init.json": "--platform copilot",
        root / ".github" / "hooks" / "wiki-write-guard.json": "--platform copilot",
        root / ".github" / "hooks" / "wiki-log-reminder.json": "--platform copilot",
    }
    for path, platform_argument in hook_configs.items():
        text = path.read_text(encoding="utf-8") if path.is_file() else ""
        if CANONICAL_HOOK_ROOT not in text.replace("\\", "/") or platform_argument not in text:
            issues.append(f"hook config does not use canonical implementation: {path.relative_to(root)}")

    for directory in (root / ".codex" / "agents", root / ".github" / "agents"):
        for path in directory.iterdir() if directory.is_dir() else ():
            if path.is_file() and "Explicit delegation only." not in path.read_text(
                encoding="utf-8"
            ):
                issues.append(f"agent is missing explicit-delegation marker: {path.relative_to(root)}")

    installer_namespace: dict[str, object] = {
        "__file__": str(root / ".agents/skills/codebase-wiki/scripts/install-framework.py"),
        "__name__": "__installer_parity__",
    }
    installer_path = root / ".agents/skills/codebase-wiki/scripts/install-framework.py"
    exec(compile(installer_path.read_text(encoding="utf-8"), str(installer_path), "exec"), installer_namespace)
    surface_files = installer_namespace["_surface_files"]
    for surface in ("copilot", "codex"):
        planned = [relative for _, relative in surface_files(root, surface, "install")]
        leaked = [
            path
            for path in planned
            if path.startswith(".agents/skills/")
            and not path.startswith(".agents/skills/codebase-wiki/")
        ]
        if leaked:
            issues.append(f"{surface} installer leaks unrelated Skills: {', '.join(leaked)}")

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
