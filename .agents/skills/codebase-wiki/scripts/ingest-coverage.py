#!/usr/bin/env python3
"""Emit an inventory or validate a saved full-ingest ledger, without writing files."""
import argparse
import json
import subprocess
from pathlib import Path

from frontmatter import configure_utf8_stdio
from ingest_coverage import inventory, validate


def main() -> int:
    configure_utf8_stdio()
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("operation", choices=("inventory", "validate"))
    parser.add_argument("--root", type=Path, default=Path.cwd())
    parser.add_argument("--scope", choices=("repository", "group"), default="repository")
    parser.add_argument("--repo", action="append", dest="selected")
    parser.add_argument("--profile", choices=("target", "framework"), default="target")
    parser.add_argument("--ledger", type=Path)
    args = parser.parse_args()
    try:
        kwargs = {"scope": args.scope, "selected": args.selected, "profile": args.profile}
        if args.operation == "inventory":
            result = inventory(args.root, **kwargs)
        else:
            if args.ledger is None:
                raise ValueError("validate requires --ledger")
            result = validate(args.root, json.loads(args.ledger.read_text(encoding="utf-8")), **kwargs)
    except (OSError, ValueError, TypeError, KeyError, subprocess.SubprocessError) as exc:
        result = {"ok": False, "status": "partial", "errors": [str(exc)]}
    print(json.dumps(result, ensure_ascii=False, indent=2))
    return 0 if result.get("ok", True) else 1


if __name__ == "__main__":
    raise SystemExit(main())
