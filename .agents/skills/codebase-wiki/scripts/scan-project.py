#!/usr/bin/env python3
"""Standalone source-first inventory for Code Audit and NotebookLM workflows."""

from __future__ import annotations

import sys
from pathlib import Path

# The script is intentionally executable from any current working directory.
SCRIPT_DIR = Path(__file__).resolve().parent
if str(SCRIPT_DIR) not in sys.path:
    sys.path.insert(0, str(SCRIPT_DIR))

from project_scanner import main  # noqa: E402


if __name__ == "__main__":
    raise SystemExit(main())
