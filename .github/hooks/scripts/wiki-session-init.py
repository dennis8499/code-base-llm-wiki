#!/usr/bin/env python3
"""wiki-session-init.py — sessionStart hook，快取 wiki 當前狀態摘要。

sessionStart hook 的輸出不會被注入 agent context，因此此腳本把
wiki/index.md 前半部與 wiki/log.md 最近條目寫入
`.github/hooks/logs/wiki-session-state.md`，供稽核或人工查看。

若 wiki/ 尚未初始化（index.md 不存在），輸出引導訊息提示使用者先執行 ingest。
"""

import pathlib
import sys


WIKI_ROOT = pathlib.Path("wiki")
INDEX_FILE = WIKI_ROOT / "index.md"
LOG_FILE = WIKI_ROOT / "log.md"
STATE_FILE = pathlib.Path(".github/hooks/logs/wiki-session-state.md")

INDEX_MAX_LINES = 60   # 只取 index.md 前 60 行（目錄摘要部分）
LOG_TAIL_ENTRIES = 10  # 取 log.md 最後 N 個 ## 條目


def read_index_summary() -> str:
    if not INDEX_FILE.exists():
        return ""
    lines = INDEX_FILE.read_text(encoding="utf-8").splitlines()
    return "\n".join(lines[:INDEX_MAX_LINES])


def read_log_tail() -> str:
    if not LOG_FILE.exists():
        return ""
    content = LOG_FILE.read_text(encoding="utf-8")
    # 取最後 N 個以 "## " 開頭的條目區塊
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
    parts: list[str] = [
        "## Wiki 狀態摘要（Session 啟動自動載入）",
        "",
    ]
    if not index_summary and not log_tail:
        parts += [
            "⚠️ `wiki/index.md` 尚未建立。",
            "若要開始使用 wiki，請先執行 `/ingest-module` 或 `/ingest-batch` 攝入 codebase 模組。",
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
        parts.append(
            "若要開始操作，可使用 `/ingest-module`、`/query-wiki`、`/lint-wiki` 等指令，"
            "或直接描述需求讓 `wiki-keeper` 為你路由。"
        )
    return "\n".join(parts)


def main():
    # sessionStart hook 不需要讀取 stdin，但仍嘗試消耗以避免 broken pipe
    try:
        sys.stdin.read()
    except Exception:
        pass

    index_summary = read_index_summary()
    log_tail = read_log_tail()
    message = build_message(index_summary, log_tail)

    STATE_FILE.parent.mkdir(parents=True, exist_ok=True)
    STATE_FILE.write_text(message, encoding="utf-8")
    print("{}")


if __name__ == "__main__":
    main()
