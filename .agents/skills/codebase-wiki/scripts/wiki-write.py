#!/usr/bin/env python3
"""Capture a Wiki preview snapshot or apply one bounded JSON write plan."""
import argparse
import json
from pathlib import Path
import sys
from wiki_transaction import commit, snapshot


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("operation", choices=("snapshot", "apply"))
    parser.add_argument("--root", type=Path, default=Path("."))
    parser.add_argument("--plan", type=Path)
    args = parser.parse_args()
    try:
        if args.operation == "snapshot":
            result = {"schema": "codebase-wiki-write/v1", "snapshot": snapshot(args.root)}
        else:
            if args.plan is None:
                parser.error("apply requires --plan")
            if args.plan.stat().st_size > 64 * 1024 * 1024:
                raise ValueError("Wiki write plan exceeds 64 MiB; split the authorized update")
            value = json.loads(args.plan.read_text(encoding="utf-8"))
            if not isinstance(value, dict) or value.get("schema") != "codebase-wiki-write/v1":
                raise ValueError("unsupported Wiki write plan")
            if (not isinstance(value.get("snapshot"), dict) or not isinstance(value.get("writes"), dict)
                or not all(isinstance(path, str) and isinstance(text, str) for path, text in value["writes"].items())
                or not isinstance(value.get("deletes", []), list)
                or not all(isinstance(path, str) for path in value.get("deletes", []))
                or not isinstance(value.get("log_append"), str)):
                raise ValueError("Wiki write plan requires a snapshot, UTF-8 text writes, deletion paths and log_append")
            writes = {path: text.encode("utf-8") for path, text in value["writes"].items()}
            for path in value.get("deletes", []):
                if path in writes:
                    raise ValueError("one path cannot be both written and deleted")
                writes[path] = None
            result = commit(args.root, writes, value["snapshot"], log_append=value["log_append"].encode("utf-8"))
        print(json.dumps(result, ensure_ascii=False, sort_keys=True))
        return 0
    except (OSError, ValueError, KeyError, TypeError) as exc:
        print(json.dumps({"ok": False, "error": str(exc)}, ensure_ascii=False), file=sys.stderr)
        return 2


if __name__ == "__main__":
    raise SystemExit(main())
