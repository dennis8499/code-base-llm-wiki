#!/usr/bin/env python3
"""Cross-platform source launcher for the shared Codebase Wiki runtime."""

from __future__ import annotations

import sys
import os
import subprocess
from pathlib import Path


RUNTIME_ROOT = Path(__file__).resolve().parents[1]


def use_project_virtualenv() -> None:
    if os.environ.get("CODEBASE_WIKI_NO_REEXEC") == "1" or sys.prefix != sys.base_prefix:
        return
    executable = RUNTIME_ROOT.parent / ".venv" / ("Scripts/python.exe" if os.name == "nt" else "bin/python")
    if executable.exists():
        os.environ["CODEBASE_WIKI_NO_REEXEC"] = "1"
        result = subprocess.run([str(executable), str(Path(__file__).resolve()), *sys.argv[1:]], env=os.environ)
        raise SystemExit(result.returncode)


use_project_virtualenv()
sys.path.insert(0, str(RUNTIME_ROOT))

from codebase_wiki_runtime.cli import main  # noqa: E402


raise SystemExit(main())
