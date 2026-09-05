#!/usr/bin/env python3
"""Validate the shared Copilot/Codex capability surface without byte mirroring."""

from __future__ import annotations

import json
from collections.abc import Callable
from pathlib import Path
import re
import tomllib
from typing import cast


EXPECTED_OPERATIONS = {
    "install",
    "ingest",
    "query",
    "lint",
    "archaeology",
    "adr",
    "synthesis",
    "business_analysis",
    "system_analysis",
    "system_design",
    "notebooklm_export",
}
EXPECTED_INTENT_CONTRACT = {
    "install": (False, True, "apply_flag"),
    "ingest": (False, True, "interactive_preview_or_explicit_batch"),
    "query": (False, False, "read_only"),
    "lint": (False, True, "confirm_repairs"),
    "archaeology": (False, True, "explicit_persist"),
    "adr": (True, False, "explicit_request"),
    "synthesis": (True, False, "explicit_request"),
    "business_analysis": (True, False, "explicit_request"),
    "system_analysis": (True, False, "explicit_request"),
    "system_design": (True, False, "explicit_request"),
    "notebooklm_export": (False, True, "preview_then_confirm"),
}
EXPECTED_GROUPS = {
    "install_setup": ["install"],
    "ingest": ["ingest"],
    "query": ["query"],
    "lint": ["lint"],
    "adr": ["adr"],
    "synthesis": ["synthesis"],
    "business_analysis": ["business_analysis"],
    "system_analysis": ["system_analysis"],
    "system_design": ["system_design"],
    "notebooklm_export": ["notebooklm_export"],
    "archaeology": ["archaeology"],
}
CANONICAL_HOOK_ROOT = ".agents/skills/codebase-wiki/scripts/hooks/"
CODEX_SESSION_SOURCES = "startup|resume|clear|compact"
FOLLOW_UP_REFERENCE = ".agents/skills/codebase-wiki/references/follow-up-actions.md"
FOLLOW_UP_ADAPTERS = (
    ".github/prompts/query-wiki.prompt.md",
    ".github/prompts/lint-wiki.prompt.md",
    "Codex.md",
)
REMOVED_ACTIVE_PATHS = (
    ".agents/skills/codebase-wiki/references/guide-workflow.md",
    ".agents/skills/codebase-wiki/assets/guide-template.md",
    ".github/prompts/onboarding-guide.prompt.md",
    ".github/prompts/save-guide.prompt.md",
    ".github/agents/wiki-archaeologist.agent.md",
    ".github/agents/wiki-ingest.agent.md",
    ".github/agents/wiki-keeper.agent.md",
    ".github/agents/wiki-lint.agent.md",
    ".github/agents/wiki-query.agent.md",
    ".codex/agents/wiki-archaeologist.toml",
    ".codex/agents/wiki-ingest.toml",
    ".codex/agents/wiki-keeper.toml",
    ".codex/agents/wiki-lint.toml",
    ".codex/agents/wiki-query.toml",
)
REMOVED_CODEX_FANOUT_CONFIG = {
    "max_concurrent_threads_per_session": 6,
    "max_depth": 1,
}
REMOVED_LIVE_DATABASE_REFERENCE = (
    ".agents/skills/codebase-wiki/references/mssql-evidence-rules.md"
)
LIVE_DATABASE_CONTRACT_PATHS = (
    ".agents/skills/codebase-wiki/SKILL.md",
    ".agents/skills/codebase-wiki/references/intent-routing.md",
    ".agents/skills/codebase-wiki/references/query-workflow.md",
    ".agents/skills/codebase-wiki/references/synthesis-workflow.md",
    ".agents/skills/codebase-wiki/references/business-analysis-workflow.md",
    ".agents/skills/codebase-wiki/references/system-analysis-workflow.md",
    ".agents/skills/codebase-wiki/references/system-design-workflow.md",
    ".github/prompts/query-wiki.prompt.md",
    ".github/prompts/business-analysis-doc.prompt.md",
    ".github/prompts/system-analysis-doc.prompt.md",
    ".github/prompts/system-design-doc.prompt.md",
)
LIVE_DATABASE_ENABLEMENT_TOKENS = (
    "mssql",
    "sql server live evidence",
    "sql query",
    "sql queries",
    "bounded read-only `select`",
    "db live evidence",
    "db evidence",
    "database evidence block",
    "database evidence is needed",
    "exposes sql server",
    "schema discovery",
    "metadata discovery",
)
QUERY_DATABASE_BOUNDARIES = {
    ".agents/skills/codebase-wiki/references/query-workflow.md": (
        "must not connect to",
        "current database state",
    ),
}
COPILOT_PROMPT_CONTRACT = {
    "ingest-module.prompt.md": (
        "references/ingest-workflow.md",
        "等待確認",
        "確認前不得寫檔",
        "wiki/index.md",
        "wiki/log.md",
    ),
    "ingest-batch.prompt.md": (
        "references/ingest-workflow.md",
        "明確授權",
        "不需要再次要求",
        "指定 scope",
        "wiki/index.md",
        "wiki/log.md",
    ),
    "query-wiki.prompt.md": (
        "references/query-workflow.md",
        "1–5",
        "零寫入",
    ),
    "lint-wiki.prompt.md": (
        "references/lint-checklist.md",
        "references/follow-up-actions.md",
        "先回報",
        "未經確認不得修復",
        "一筆 lint log",
    ),
    "code-archaeology.prompt.md": (
        "references/code-archaeology-workflow.md",
        "Git evidence",
        "預設零寫入",
        "明確要求保存",
        "語意 inbound",
        "wiki/index.md",
        "wiki/log.md",
    ),
    "business-analysis-doc.prompt.md": (
        "references/business-analysis-workflow.md",
        "assets/business-analysis-template.md",
        "business-analysis-aligned-v1",
        "wiki/index.md",
        "wiki/log.md",
    ),
    "system-analysis-doc.prompt.md": (
        "references/system-analysis-workflow.md",
        "assets/system-analysis-template.md",
        "system-analysis-aligned-v1",
        "solution-neutral",
        "wiki/index.md",
        "wiki/log.md",
    ),
    "system-design-doc.prompt.md": (
        "references/system-design-workflow.md",
        "assets/system-design-template.md",
        "system-design-aligned-v1",
        "wiki/index.md",
        "wiki/log.md",
    ),
}


def markdown_frontmatter(text: str) -> dict[str, str] | None:
    """Parse scalar values from the small Markdown frontmatter adapters."""

    match = re.match(r"\A---\s*\n(.*?)\n---\s*\n", text, flags=re.DOTALL)
    if not match:
        return None
    values: dict[str, str] = {}
    for line in match.group(1).splitlines():
        field = re.match(r"^([A-Za-z][A-Za-z0-9_-]*):\s*(.*?)\s*$", line)
        if field and field.group(2):
            values[field.group(1)] = field.group(2).strip().strip("\"'")
    return values


def main() -> int:
    root = Path(__file__).resolve().parents[4]
    manifest_path = root / ".agents" / "skills" / "codebase-wiki" / "capabilities.json"
    issues: list[str] = []
    if not manifest_path.exists():
        issues.append("missing capabilities.json")
        manifest = {}
    else:
        manifest = json.loads(manifest_path.read_text(encoding="utf-8"))

    for relative in REMOVED_ACTIVE_PATHS:
        if (root / relative).exists():
            issues.append(f"removed active capability path is still present: {relative}")

    removed_reference = root / REMOVED_LIVE_DATABASE_REFERENCE
    if removed_reference.exists():
        issues.append(
            f"removed live-database reference is still present: {REMOVED_LIVE_DATABASE_REFERENCE}"
        )
    for relative in LIVE_DATABASE_CONTRACT_PATHS:
        path = root / relative
        if not path.is_file():
            issues.append(f"missing live-database contract surface: {relative}")
            continue
        text = path.read_text(encoding="utf-8").lower()
        for token in LIVE_DATABASE_ENABLEMENT_TOKENS:
            if token in text:
                issues.append(f"live-database query capability remains in {relative}: {token}")
    for relative, required_tokens in QUERY_DATABASE_BOUNDARIES.items():
        path = root / relative
        text = path.read_text(encoding="utf-8").lower() if path.is_file() else ""
        for token in required_tokens:
            if token.lower() not in text:
                issues.append(f"query live-database boundary missing in {relative}: {token}")

    for surface in ("copilot", "codex"):
        if surface not in manifest.get("surfaces", []):
            issues.append(f"manifest missing surface: {surface}")
    if manifest.get("contract_version") != 5:
        issues.append("manifest contract_version must be 5")
    guard_modes = manifest.get("guard_modes", {})
    if guard_modes.get("default") != "wiki-only" or guard_modes.get("installed") != [
        "wiki-only",
        "coexist",
    ]:
        issues.append("manifest guard mode contract is incomplete")

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
        issues.append("manifest must define the exact eleven user-facing intent groups")
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
    for path in (root / ".github" / "prompts").glob("*.prompt.md"):
        relative = path.relative_to(root).as_posix()
        text = path.read_text(encoding="utf-8")
        frontmatter = markdown_frontmatter(text)
        if frontmatter is None:
            issues.append(f"Copilot prompt has no parseable frontmatter: {relative}")
            continue
        expected_name = path.name.removesuffix(".prompt.md")
        if frontmatter.get("name") != expected_name:
            issues.append(f"Copilot prompt name must match filename: {relative}")
        for field in ("description", "agent", "argument-hint"):
            if not frontmatter.get(field):
                issues.append(f"Copilot prompt missing {field}: {relative}")
        agent = frontmatter.get("agent", "")
        if agent and agent != "agent":
            issues.append(f"Copilot prompt must use built-in agent: {relative}")
    for filename, required_tokens in COPILOT_PROMPT_CONTRACT.items():
        path = root / ".github" / "prompts" / filename
        text = path.read_text(encoding="utf-8") if path.is_file() else ""
        for token in required_tokens:
            if token not in text:
                issues.append(f"Copilot workflow contract missing {token}: {filename}")
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

    follow_up_reference = root / FOLLOW_UP_REFERENCE
    if not follow_up_reference.is_file():
        issues.append(f"missing shared follow-up contract: {FOLLOW_UP_REFERENCE}")
    for relative in FOLLOW_UP_ADAPTERS:
        path = root / relative
        text = path.read_text(encoding="utf-8") if path.is_file() else ""
        if FOLLOW_UP_REFERENCE not in text.replace("\\", "/"):
            issues.append(f"surface missing follow-up contract: {relative}")

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

    codex_hooks_path = root / ".codex" / "hooks.json"
    if codex_hooks_path.is_file():
        try:
            codex_hooks = json.loads(codex_hooks_path.read_text(encoding="utf-8"))
        except json.JSONDecodeError as exc:
            issues.append(f"invalid Codex hooks JSON: {exc}")
            codex_hooks = {}
        for event_name in ("SessionStart", "PreToolUse", "PostToolUse"):
            groups = codex_hooks.get("hooks", {}).get(event_name, [])
            for group in groups:
                for handler in group.get("hooks", []):
                    command = handler.get("command", "")
                    if not command.startswith('python "$(git rev-parse --show-toplevel'):
                        issues.append(
                            f"Codex {event_name} command must resolve the Git root"
                        )
                    if "2>/dev/null || pwd" not in command:
                        issues.append(f"Codex {event_name} command must fall back to pwd")
                    command_windows = handler.get("commandWindows", "")
                    if not command_windows.startswith(
                        "powershell.exe -NoProfile -NonInteractive -Command"
                    ):
                        issues.append(
                            f"Codex {event_name} commandWindows must use the PowerShell wrapper"
                        )
                    for token in (
                        "$wikiRoot",
                        "git rev-parse --show-toplevel",
                        "Get-Location",
                        "Join-Path",
                    ):
                        if token not in command_windows:
                            issues.append(
                                f"Codex {event_name} commandWindows missing root resolver: {token}"
                            )
                    if CANONICAL_HOOK_ROOT not in command_windows.replace("\\", "/"):
                        issues.append(
                            f"Codex {event_name} commandWindows must use the canonical hook"
                        )
        session_groups = codex_hooks.get("hooks", {}).get("SessionStart", [])
        session_matchers = {str(group.get("matcher", "")) for group in session_groups}
        if CODEX_SESSION_SOURCES not in session_matchers:
            issues.append(
                "Codex SessionStart matcher must cover startup, resume, clear, and compact"
            )

    config_path = root / ".codex" / "config.toml"
    try:
        codex_config = tomllib.loads(config_path.read_text(encoding="utf-8"))
    except (OSError, tomllib.TOMLDecodeError) as exc:
        issues.append(f"invalid Codex config: {exc}")
        codex_config = {}
    agents_config = codex_config.get("agents", {})
    if isinstance(agents_config, dict) and all(
        agents_config.get(key) == value
        for key, value in REMOVED_CODEX_FANOUT_CONFIG.items()
    ):
        issues.append("removed framework Codex agent fan-out config is still present")

    # The exact ten retired Wiki profiles are already enforced through
    # REMOVED_ACTIVE_PATHS. Other names belong to the platform-native extension
    # surface and are deliberately outside this framework removal.

    installer_namespace: dict[str, object] = {
        "__file__": str(root / ".agents/skills/codebase-wiki/scripts/install-framework.py"),
        "__name__": "__installer_parity__",
    }
    installer_path = root / ".agents/skills/codebase-wiki/scripts/install-framework.py"
    exec(compile(installer_path.read_text(encoding="utf-8"), str(installer_path), "exec"), installer_namespace)
    surface_files = cast(
        Callable[..., list[tuple[Path, str]]], installer_namespace["_surface_files"]
    )
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
    workflow_root = root / ".github" / "workflows"
    workflows = sorted(
        path.relative_to(root).as_posix()
        for suffix in ("*.yml", "*.yaml")
        for path in workflow_root.glob(suffix)
    )
    if workflows:
        issues.append("GitHub workflow files must be absent: " + ", ".join(workflows))
    payload = {"ok": not issues, "contract_version": manifest.get("contract_version", 0), "issues": issues}
    print(json.dumps(payload, ensure_ascii=False, indent=2))
    return 0 if not issues else 1


if __name__ == "__main__":
    raise SystemExit(main())
