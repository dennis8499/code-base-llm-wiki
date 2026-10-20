#!/usr/bin/env python3
"""Read local Git evidence without lazy fetch, with bounded time and output."""
import argparse
from pathlib import Path
import subprocess
import sys
from offline_git import ProcessLimitError, run_git


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--root", type=Path, required=True)
    parser.add_argument("--timeout", type=float, default=30)
    parser.add_argument("--max-output-bytes", type=int, default=8 * 1024 * 1024)
    parser.add_argument("args", nargs=argparse.REMAINDER)
    args = parser.parse_args()
    command = args.args[1:] if args.args[:1] == ["--"] else args.args
    try:
        result = run_git(args.root, *command, timeout=args.timeout, max_output_bytes=args.max_output_bytes, check=False)
        sys.stdout.write(result.stdout)
        sys.stderr.write(result.stderr)
        return result.returncode
    except (OSError, ValueError, subprocess.SubprocessError) as exc:
        print(f"Git evidence unavailable: {exc}", file=sys.stderr)
        return 2


if __name__ == "__main__":
    raise SystemExit(main())
