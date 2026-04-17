#!/usr/bin/env python3
"""wiki-write-guard.py — preToolUse hook，攔截 wiki agent 對 wiki/ 外目錄的寫入。

當 wiki 相關 agent 活躍時，只允許寫入 wiki/ 和 .github/ 目錄。
非 wiki agent 的操作不受此 hook 影響。
"""

import json
import sys


def respond(decision: str, reason: str | None = None):
    payload = {"permissionDecision": decision}
    if reason:
        payload["reason"] = reason
    print(json.dumps(payload, ensure_ascii=False))


def main():
    try:
        payload = json.load(sys.stdin)
    except (json.JSONDecodeError, EOFError):
        respond("allow")
        return

    # 取得檔案路徑（從不同工具的參數中擷取）
    tool_input = payload.get("input", {})
    file_path = (
        tool_input.get("filePath", "")
        or tool_input.get("path", "")
        or ""
    )

    # 正規化路徑，統一使用 /
    file_path_normalized = file_path.replace("\\", "/").lower()

    # 檢查 agent context（若可取得）
    # 如果無法判斷是否為 wiki agent，則放行（避免誤攔正常操作）
    agent_name = payload.get("agentName", "") or ""
    is_wiki_agent = "wiki" in agent_name.lower()

    if not is_wiki_agent:
        respond("allow")
        return

    # Wiki agent 只能寫入 wiki/ 和 .github/ 目錄
    allowed_prefixes = ["wiki/", ".github/", "wiki\\", ".github\\"]

    # 嘗試從絕對路徑中擷取相對路徑
    for marker in ["/wiki/", "\\wiki\\", "/.github/", "\\.github\\"]:
        if marker in file_path_normalized:
            respond("allow")
            return

    # 檢查是否為相對路徑且在允許範圍
    for prefix in allowed_prefixes:
        if file_path_normalized.startswith(prefix):
            respond("allow")
            return

    # 若路徑不在允許範圍，詢問使用者
    respond(
        "ask",
        f"Wiki agent 正嘗試寫入 wiki/ 外的路徑: {file_path}。"
        f"Wiki agent 僅應寫入 wiki/ 目錄。是否允許？"
    )


if __name__ == "__main__":
    main()
