#!/usr/bin/env python3
"""Deprecated compatibility wrapper for the capability parity check.

Usage:
    python .agents/skills/codebase-wiki/scripts/check-dual-entry-sync.py

The old byte-comparison model produced false drift on Windows line endings and
did not validate platform adapters. Use ``parity-check.py`` for the canonical
semantic check.
"""

from __future__ import annotations

from collections.abc import Callable
import pathlib
from typing import cast


REPO_ROOT = pathlib.Path(__file__).resolve().parents[4]


def main() -> None:
    """Compatibility entrypoint; parity-check is the canonical validator."""
    parity_script = REPO_ROOT / ".agents" / "skills" / "codebase-wiki" / "scripts" / "parity-check.py"
    namespace: dict[str, object] = {
        "__file__": str(parity_script),
        "__name__": "__parity_check__",
    }
    exec(compile(parity_script.read_text(encoding="utf-8"), str(parity_script), "exec"), namespace)
    result = cast(Callable[[], int], namespace["main"])
    raise SystemExit(result())


if __name__ == "__main__":
    main()
