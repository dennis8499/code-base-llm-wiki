# Hook Specification

This file documents the three Codebase LLM Wiki hooks shared by the Copilot and
Codex entrypoints. Hook scripts should stay mirrored across entrypoints; platform
differences belong in hook configuration and this specification.

## Hooks

| Hook | Event | Script | Purpose | Side effect |
| --- | --- | --- | --- | --- |
| `wiki-session-init` | Session start | `wiki-session-init.py` | Summarize `wiki/index.md` and recent `wiki/log.md` for audit/context. | Writes a session state Markdown file. |
| `wiki-write-guard` | Before edit tools | `wiki-write-guard.py` | Deny writes outside the configured wiki/framework boundary. | No persistent state. |
| `wiki-log-reminder` | After edit tools | `wiki-log-reminder.py` | Detect wiki page edits that may require a `wiki/log.md` entry. | Appends a JSONL audit entry. |

## Platform Configuration

| Platform | Configuration | Event names | Script location |
| --- | --- | --- | --- |
| GitHub Copilot | `.github/hooks/*.json` | `sessionStart`, `preToolUse`, `postToolUse` | `.github/hooks/scripts/` |
| OpenAI Codex | `.codex/hooks.json` | `SessionStart`, `PreToolUse`, `PostToolUse` | `.codex/hooks/scripts/` |

## Matched Edit Tools

Both platforms should route these edit tools to write guard and log reminder
when the platform supports matcher filters:

```text
apply_patch|Edit|Write|create|create_file|edit|editFiles|str_replace|str_replace_editor|multi_replace_string_in_file|replace_string_in_file|write
```

## Input Contract

Scripts accept JSON from stdin. They support these payload shapes:

- Codex-style `tool_name` / `tool_input`.
- Copilot-style `toolName` / `toolInput`.
- Serialized `toolArgs` as an object or JSON string.

Path extraction checks `filePath`, `file_path`, `path`, `targetPath`,
`target_path`, `files`, and file paths embedded in `apply_patch` text.

## Output Contract

- Allow decisions may output `{}` or `{"permissionDecision": "allow"}`.
- Deny decisions include top-level `permissionDecision` fields for Copilot and
  `hookSpecificOutput` for Codex.
- Context messages include `hookSpecificOutput.additionalContext` when the
  platform can consume it. Audit files are still written because not every
  platform injects hook output into the agent context.

## Audit Paths

| Platform | Primary path | Fallback path |
| --- | --- | --- |
| GitHub Copilot | `.github/hooks/logs/` | `.github-hook-logs/` |
| OpenAI Codex | `.codex/hooks/logs/` | `.codex-hook-logs/` |

## Write Guard Modes

`wiki-write-guard.py` reads `wiki_guard.mode` from the entrypoint config:

- Codex: `.codex/config.toml`
- Copilot: `.github/hooks/config.toml`

Allowed values:

- `target`: allow wiki writes only. This is the safe mode for installed target
  codebases.
- `framework`: allow `wiki/`, `.codex/`, `.agents/`, `.github/`, `docs/`,
  `samples/`, `tests/`, and approved root entrypoints (`AGENTS.md`, `README.md`,
  `ChangeLog.md`, `Codex.md`). Use this only when maintaining the Codebase LLM
  Wiki framework repository itself.

If the config is missing or invalid, the guard fails closed to `target`.
