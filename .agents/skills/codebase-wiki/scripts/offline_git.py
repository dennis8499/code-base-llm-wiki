"""Bounded local Git evidence. Missing promisor objects stay evidence gaps."""
from __future__ import annotations

import os
from pathlib import Path
from bounded_process import ProcessLimitError, run_bounded


READ_COMMANDS = frozenset({"status", "log", "show", "blame", "rev-parse", "ls-files", "ls-tree", "cat-file", "diff", "rev-list", "merge-base"})


def run_git(repo: Path, *args: str, check=True, text=True, encoding="utf-8",
            timeout=30, max_output_bytes=8 * 1024 * 1024):
    if not args or args[0] not in READ_COMMANDS:
        raise ValueError("offline Git accepts only local evidence commands")
    if any(arg in {"--filters", "--textconv", "--ext-diff"} for arg in args):
        raise ValueError("offline evidence does not execute source filters or diff helpers")
    env = dict(os.environ, GIT_NO_LAZY_FETCH="1", GIT_OPTIONAL_LOCKS="0",
               GIT_TERMINAL_PROMPT="0", GCM_INTERACTIVE="never", GIT_ALLOW_PROTOCOL="")
    if args[0] in {"diff", "log", "show"}:
        args = (args[0], "--no-ext-diff", "--no-textconv", *args[1:])
    return run_bounded(["git", "--no-pager", "-c", f"safe.directory={Path(repo).resolve()}",
                        "-c", "core.fsmonitor=false", "-C", str(repo), *args], env=env, timeout=timeout,
                       max_output_bytes=max_output_bytes, check=check, text=text, encoding=encoding)
