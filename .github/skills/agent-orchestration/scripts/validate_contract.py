#!/usr/bin/env python3
"""
Agent Communication Contract 驗證腳本

驗證 JSON 檔案是否符合多代理人編排系統的標準通訊 Envelope。
支援三種訊息型態：

- request 訊息（`payload.parameters`）
- response 訊息（`status` + `payload.result`）
- confirmation_required 訊息（`status` + `payload.pendingOperation`）

僅使用 Python 標準庫，無需安裝額外套件。

用法：
    python validate_contract.py <json-file>
    python validate_contract.py <json-file> --strict
"""

import json
import re
import sys
from pathlib import Path

UUID_V4_PATTERN = re.compile(
    r"^[0-9a-fA-F]{8}-[0-9a-fA-F]{4}-4[0-9a-fA-F]{3}-[89abAB][0-9a-fA-F]{3}-[0-9a-fA-F]{12}$"
)
SNAKE_CASE_PATTERN = re.compile(r"^[a-z][a-z0-9_]*$")
ISO8601_PATTERN = re.compile(
    r"^\d{4}-\d{2}-\d{2}T\d{2}:\d{2}:\d{2}(\.\d+)?(Z|[+-]\d{2}:\d{2})$"
)
VALID_STATUSES = {"completed", "failed", "confirmation_required", "partial"}
RESULT_STATUSES = {"completed", "failed", "partial"}


def is_non_empty_string(value: object) -> bool:
    return isinstance(value, str) and len(value.strip()) > 0


def is_non_negative_int(value: object) -> bool:
    return isinstance(value, int) and not isinstance(value, bool) and value >= 0


def validate_contract(data: dict, strict: bool = False) -> list[str]:
    """驗證單一 JSON Envelope 是否符合 Agent Communication Contract。"""
    errors: list[str] = []

    required_top = ["traceId", "sender", "target", "timestamp", "payload", "context"]
    for field in required_top:
        if field not in data:
            errors.append(
                f"缺少必要欄位 '{field}'。"
                f"期望的頂層欄位：{', '.join(required_top)}"
            )

    if errors:
        return errors

    trace_id = data["traceId"]
    if not isinstance(trace_id, str) or not UUID_V4_PATTERN.match(trace_id):
        errors.append(
            f"'traceId' 格式錯誤：'{trace_id}'。"
            "期望 UUID v4 格式，例如：'a1b2c3d4-e5f6-4890-ab34-56789abcdef0'"
        )

    for field in ["sender", "target"]:
        if not is_non_empty_string(data[field]):
            errors.append(f"'{field}' 必須為非空字串。收到：{repr(data[field])}")

    ts = data["timestamp"]
    if not isinstance(ts, str) or not ISO8601_PATTERN.match(ts):
        errors.append(
            f"'timestamp' 格式錯誤：'{ts}'。"
            "期望 ISO 8601 格式，例如：'2026-04-16T10:30:00Z'"
        )

    status = data.get("status")
    if status is not None and status not in VALID_STATUSES:
        errors.append(
            f"'status' 值無效：'{status}'。"
            f"允許的值：{', '.join(sorted(VALID_STATUSES))}"
        )

    payload = data["payload"]
    if not isinstance(payload, dict):
        errors.append(f"'payload' 必須為物件。收到類型：{type(payload).__name__}")
    else:
        action = payload.get("action")
        if action is None:
            errors.append(
                "'payload.action' 缺失。"
                "期望 snake_case 字串，例如：'generate_dapper_query'"
            )
        elif not isinstance(action, str) or not SNAKE_CASE_PATTERN.match(action):
            errors.append(
                f"'payload.action' 格式錯誤：'{action}'。"
                "期望 snake_case 格式（小寫字母開頭，僅含小寫字母、數字、底線）"
            )

        if status is None:
            if "parameters" not in payload:
                errors.append(
                    "'payload.parameters' 缺失。"
                    "請求訊息期望為物件（可以是空物件 {}）"
                )
            elif not isinstance(payload["parameters"], dict):
                errors.append(
                    f"'payload.parameters' 必須為物件。"
                    f"收到類型：{type(payload['parameters']).__name__}"
                )
        elif status == "confirmation_required":
            if "pendingOperation" not in payload:
                errors.append(
                    "'payload.pendingOperation' 缺失。"
                    "當 status = 'confirmation_required' 時，必須提供待授權操作資訊"
                )
            elif not isinstance(payload["pendingOperation"], dict):
                errors.append(
                    f"'payload.pendingOperation' 必須為物件。"
                    f"收到類型：{type(payload['pendingOperation']).__name__}"
                )
            else:
                pending_op = payload["pendingOperation"]
                for field in ["description", "impact", "reversibility"]:
                    if not is_non_empty_string(pending_op.get(field)):
                        errors.append(
                            f"'payload.pendingOperation.{field}' 必須為非空字串。"
                            f"收到：{repr(pending_op.get(field))}"
                        )

                suggested_alt = pending_op.get("suggestedAlternative")
                if suggested_alt is not None and not isinstance(suggested_alt, str):
                    errors.append(
                        "'payload.pendingOperation.suggestedAlternative' "
                        f"必須為字串或 null。收到：{repr(suggested_alt)}"
                    )
        elif status in RESULT_STATUSES:
            if "result" not in payload:
                errors.append(
                    "'payload.result' 缺失。"
                    "當 status 為 completed / failed / partial 時，必須提供結果物件"
                )
            elif not isinstance(payload["result"], dict):
                errors.append(
                    f"'payload.result' 必須為物件。"
                    f"收到類型：{type(payload['result']).__name__}"
                )

    context = data["context"]
    if not isinstance(context, dict):
        errors.append(f"'context' 必須為物件。收到類型：{type(context).__name__}")
    else:
        for field in ["retryCount", "maxRetries"]:
            if field not in context:
                errors.append(f"'context.{field}' 缺失。期望為非負整數")
            elif not is_non_negative_int(context[field]):
                errors.append(
                    f"'context.{field}' 必須為非負整數。收到：{context[field]}"
                )

        if (
            "retryCount" in context
            and "maxRetries" in context
            and is_non_negative_int(context["retryCount"])
            and is_non_negative_int(context["maxRetries"])
            and context["retryCount"] > context["maxRetries"]
        ):
            errors.append(
                f"'context.retryCount' ({context['retryCount']}) "
                f"大於 'context.maxRetries' ({context['maxRetries']})。"
                "retryCount 不應超過 maxRetries"
            )

        parent_trace = context.get("parentTraceId")
        if parent_trace is not None:
            if not isinstance(parent_trace, str) or not UUID_V4_PATTERN.match(parent_trace):
                errors.append(
                    f"'context.parentTraceId' 格式錯誤：'{parent_trace}'。"
                    "期望 UUID v4 或 null"
                )

        session_memory_path = context.get("sessionMemoryPath")
        if session_memory_path is not None and not isinstance(session_memory_path, str):
            errors.append(
                "'context.sessionMemoryPath' 必須為字串或 null。"
                f"收到：{repr(session_memory_path)}"
            )

        previous_error = context.get("previousError")
        if previous_error is not None:
            if not isinstance(previous_error, dict):
                errors.append(
                    f"'context.previousError' 必須為物件或 null。"
                    f"收到類型：{type(previous_error).__name__}"
                )
            else:
                for field in ["type", "message"]:
                    if not is_non_empty_string(previous_error.get(field)):
                        errors.append(
                            f"'context.previousError.{field}' 缺失或為空。"
                            "重試錯誤應包含 type 和 message 欄位"
                        )

                suggestion = previous_error.get("suggestion")
                if suggestion is not None and not isinstance(suggestion, str):
                    errors.append(
                        "'context.previousError.suggestion' 必須為字串或 null。"
                        f"收到：{repr(suggestion)}"
                    )

        for field in ["durationMs", "tokensUsed"]:
            if field in context and not is_non_negative_int(context[field]):
                errors.append(
                    f"'context.{field}' 必須為非負整數。收到：{context[field]}"
                )

        if strict and "sessionMemoryPath" not in context:
            errors.append(
                "[strict] 建議包含 'context.sessionMemoryPath' "
                "以支援跨代理狀態共享"
            )

    return errors


def validate_file(file_path: str, strict: bool = False) -> bool:
    """驗證 JSON 檔案。"""
    path = Path(file_path)

    if not path.exists():
        print(f"[ERROR] 檔案不存在：{file_path}")
        return False

    try:
        with open(path, encoding="utf-8") as f:
            raw = json.load(f)
    except json.JSONDecodeError as e:
        print(f"[ERROR] JSON 解析錯誤：{e}")
        print(f"   位置：第 {e.lineno} 行，第 {e.colno} 欄")
        return False

    if "$schema" in raw and "examples" in raw:
        print(f"[INFO] 偵測到 JSON Schema 模板檔案：{path.name}")
        print(f"   驗證 {len(raw['examples'])} 個範例...\n")

        all_pass = True
        for i, example in enumerate(raw["examples"]):
            example_to_validate = dict(example)
            comment = example_to_validate.pop("_comment", f"範例 {i + 1}")
            print(f"   --- {comment} ---")
            errors = validate_contract(example_to_validate, strict=strict)
            if errors:
                all_pass = False
                for err in errors:
                    print(f"   [ERROR] {err}")
            else:
                print("   [OK] 驗證通過")
            print()
        return all_pass

    errors = validate_contract(raw, strict=strict)
    if errors:
        print(f"[ERROR] 驗證失敗：{path.name}")
        print(f"   發現 {len(errors)} 個問題：\n")
        for i, err in enumerate(errors, 1):
            print(f"   {i}. {err}")
        return False

    print(f"[OK] 驗證通過：{path.name}")
    return True


def main() -> None:
    if len(sys.argv) < 2:
        print("用法：python validate_contract.py <json-file> [--strict]")
        print()
        print("範例：")
        print("  python validate_contract.py contract.json")
        print("  python validate_contract.py contract.json --strict")
        sys.exit(1)

    file_path = sys.argv[1]
    strict = "--strict" in sys.argv

    success = validate_file(file_path, strict=strict)
    sys.exit(0 if success else 1)


if __name__ == "__main__":
    main()
