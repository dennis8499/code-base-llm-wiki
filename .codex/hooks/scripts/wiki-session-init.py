#!/usr/bin/env python3
"""Codex SessionStart hook that summarizes current wiki state."""

from __future__ import annotations

import json
import pathlib
import sys
from typing import Any


REPO_ROOT = pathlib.Path(__file__).resolve().parents[3]
WIKI_ROOT = REPO_ROOT / "wiki"
INDEX_FILE = WIKI_ROOT / "index.md"
LOG_FILE = WIKI_ROOT / "log.md"
STATE_FILE_CANDIDATES = (
    REPO_ROOT / ".codex" / "hooks" / "logs" / "wiki-session-state.md",
    REPO_ROOT / ".codex-hook-logs" / "wiki-session-state.md",
)

INDEX_MAX_LINES = 60
LOG_TAIL_ENTRIES = 10


def configure_stdio() -> None:
    for stream in (sys.stdout, sys.stderr):
        try:
            stream.reconfigure(encoding="utf-8")
        except Exception:
            pass


def read_index_summary() -> str:
    if not INDEX_FILE.exists():
        return ""
    lines = INDEX_FILE.read_text(encoding="utf-8").splitlines()
    return "\n".join(lines[:INDEX_MAX_LINES])


def read_log_tail() -> str:
    if not LOG_FILE.exists():
        return ""
    content = LOG_FILE.read_text(encoding="utf-8")
    entries: list[str] = []
    current: list[str] = []
    for line in content.splitlines():
        if line.startswith("## ") and current:
            entries.append("\n".join(current))
            current = [line]
        else:
            current.append(line)
    if current:
        entries.append("\n".join(current))
    tail = entries[-LOG_TAIL_ENTRIES:] if len(entries) >= LOG_TAIL_ENTRIES else entries
    return "\n\n".join(tail)


def build_message(index_summary: str, log_tail: str) -> str:
    parts: list[str] = ["## Wiki 狀態摘要（Codex SessionStart）", ""]
    if not index_summary and not log_tail:
        parts += [
            "`wiki/index.md` 尚未建立。",
            "若要開始使用 wiki，請先要求 Codex 依 Codebase LLM Wiki ingest 流程攝入 codebase 模組。",
        ]
    else:
        if index_summary:
            parts += [
                "### 目前涵蓋範圍（wiki/index.md 前段）",
                "```",
                index_summary,
                "```",
                "",
            ]
        if log_tail:
            parts += [
                f"### 最近 {LOG_TAIL_ENTRIES} 筆操作紀錄（wiki/log.md）",
                "```",
                log_tail,
                "```",
                "",
            ]
        parts.append("操作 wiki 時請保持 raw sources 唯讀，並在 ingest、lint 或重大更新後追加 `wiki/log.md`。")
    return "\n".join(parts)


def respond(additional_context: str) -> None:
    print(
        json.dumps(
            {
                "hookSpecificOutput": {
                    "hookEventName": "SessionStart",
                    "additionalContext": additional_context,
                }
            },
            ensure_ascii=False,
        )
    )


def write_state_file(message: str) -> str | None:
    errors: list[str] = []
    for state_file in STATE_FILE_CANDIDATES:
        try:
            state_file.parent.mkdir(parents=True, exist_ok=True)
            state_file.write_text(message, encoding="utf-8")
            return None
        except OSError as exc:
            errors.append(f"`{state_file.relative_to(REPO_ROOT)}`: {exc}")
    return "；".join(errors)


def main() -> None:
    configure_stdio()
    try:
        sys.stdin.read()
    except Exception:
        pass

    message = build_message(read_index_summary(), read_log_tail())
    audit_error = write_state_file(message)
    if audit_error:
        message += f"\n\n> 無法寫入 Codex hook audit 檔：{audit_error}"
    respond(message)


if __name__ == "__main__":
    main()
