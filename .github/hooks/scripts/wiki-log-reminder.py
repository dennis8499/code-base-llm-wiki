#!/usr/bin/env python3
"""wiki-log-reminder.py — postToolUse hook，wiki 檔案被修改後提醒更新 log.md。

當偵測到 wiki/ 目錄下的 .md 檔案被修改（排除 log.md 本身），
輸出提醒訊息要求 agent 更新 wiki/log.md。
"""

import json
import sys


def respond(message: str | None = None):
    payload = {}
    if message:
        payload["message"] = message
    print(json.dumps(payload, ensure_ascii=False))


def main():
    try:
        payload = json.load(sys.stdin)
    except (json.JSONDecodeError, EOFError):
        respond()
        return

    # 取得被修改的檔案路徑
    tool_input = payload.get("input", {})
    file_path = (
        tool_input.get("filePath", "")
        or tool_input.get("path", "")
        or ""
    )

    file_path_normalized = file_path.replace("\\", "/").lower()

    # 只在修改 wiki/ 下的 .md 檔案（且非 log.md）時提醒
    is_wiki_file = "wiki/" in file_path_normalized or "wiki\\" in file_path_normalized
    is_md_file = file_path_normalized.endswith(".md")
    is_log_file = file_path_normalized.endswith("log.md")

    if is_wiki_file and is_md_file and not is_log_file:
        respond(
            f"💡 提醒：wiki 檔案 {file_path} 已被修改。"
            f"請確保在操作完成後更新 wiki/log.md（append-only）。"
        )
    else:
        respond()


if __name__ == "__main__":
    main()
