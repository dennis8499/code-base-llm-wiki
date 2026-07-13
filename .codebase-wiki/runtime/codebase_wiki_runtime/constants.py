from __future__ import annotations

from pathlib import Path


SUPPORTED_LANGUAGES = {
    ".py": "python",
    ".js": "javascript",
    ".jsx": "jsx",
    ".ts": "typescript",
    ".tsx": "tsx",
    ".cs": "csharp",
}

DEFAULT_EXCLUDES = {
    ".git",
    ".hg",
    ".svn",
    ".codebase-wiki",
    ".venv",
    "venv",
    "node_modules",
    "__pycache__",
    "bin",
    "obj",
    "dist",
    "build",
    "coverage",
}
DEFAULT_MAX_FILE_BYTES = 1024 * 1024
DEFAULT_DB_PATH = Path(".codebase-wiki/cache/index.sqlite3")
