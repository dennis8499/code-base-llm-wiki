from __future__ import annotations

import argparse
import json
import sqlite3
import subprocess
import sys
import venv
from pathlib import Path
from typing import Sequence

from . import CONTRACT_VERSION, __version__
from .constants import DEFAULT_DB_PATH, SUPPORTED_LANGUAGES
from .indexer import build_index
from .installer import apply_install, plan_install
from .storage import IndexStore
from .structure import doctor_tree_sitter


def _json(payload: dict[str, object]) -> None:
    # ASCII escapes keep the machine-readable contract intact when Windows
    # PowerShell decodes redirected native-process output with a legacy code
    # page. Consumers still receive the original Unicode after JSON decoding.
    print(json.dumps(payload, ensure_ascii=True, sort_keys=True))


def _paths() -> tuple[Path, Path]:
    root = Path.cwd()
    return root, root / DEFAULT_DB_PATH


def _is_indexed_path(path: str) -> bool:
    normalized = path.replace("\\", "/").strip().strip('"\'')
    while normalized.startswith("./"):
        normalized = normalized[2:]
    if normalized.startswith("wiki/"):
        return normalized.lower().endswith(".md")
    return Path(normalized).suffix.lower() in SUPPORTED_LANGUAGES


def _index_stale(root: Path) -> bool:
    try:
        result = subprocess.run(
            # The index covers Wiki and source files. Git already excludes the
            # rebuildable cache/venv via .gitignore, so any remaining dirty
            # path can make an existing index stale.
            ["git", "-C", str(root), "status", "--porcelain", "--untracked-files=all"],
            capture_output=True,
            text=True,
            check=True,
        )
        dirty_paths: set[str] = set()
        for line in result.stdout.splitlines():
            if len(line) < 4:
                continue
            value = line[3:].strip()
            if " -> " in value:
                old_path, new_path = value.rsplit(" -> ", 1)
                dirty_paths.update((old_path, new_path))
            else:
                dirty_paths.add(value)
        return any(_is_indexed_path(path) for path in dirty_paths)
    except (OSError, subprocess.CalledProcessError):
        return False


def _doctor() -> dict[str, object]:
    languages = doctor_tree_sitter()
    fts5 = IndexStore.fts5_available()
    tree_sitter_ok = all(bool(item.get("ok")) for item in languages.values())
    return {
        "contract_version": CONTRACT_VERSION,
        "version": __version__,
        "ok": fts5 and tree_sitter_ok,
        "capabilities": {
            "fts5": fts5,
            "sqlite_version": sqlite3.sqlite_version,
            "tree_sitter": languages,
        },
    }


def build_parser() -> argparse.ArgumentParser:
    parser = argparse.ArgumentParser(prog="codebase-wiki")
    subparsers = parser.add_subparsers(dest="command", required=True)
    doctor = subparsers.add_parser("doctor")
    doctor.add_argument("--format", choices=("json", "text"), default="text")
    setup = subparsers.add_parser("setup")
    setup.add_argument("--no-install", action="store_true", help="Only create the cache directory")
    setup.add_argument("--format", choices=("json", "text"), default="text")
    install = subparsers.add_parser("install")
    install.add_argument("--target", type=Path, required=True)
    install.add_argument("--surface", choices=("copilot", "codex"), required=True)
    install.add_argument("--apply", action="store_true")
    install.add_argument("--format", choices=("json", "text"), default="text")
    upgrade = subparsers.add_parser("upgrade")
    upgrade.add_argument("--target", type=Path, required=True)
    upgrade.add_argument("--surface", choices=("copilot", "codex"), required=True)
    upgrade.add_argument("--apply", action="store_true")
    upgrade.add_argument("--format", choices=("json", "text"), default="text")
    index = subparsers.add_parser("index")
    index.add_argument("action", choices=("build", "update", "status", "check", "optimize"))
    index.add_argument("--scope", choices=("wiki", "source", "all"), default="all")
    index.add_argument("--format", choices=("json", "text"), default="text")
    search = subparsers.add_parser("search")
    search.add_argument("query")
    search.add_argument("--scope", choices=("wiki", "source", "all"), default="wiki")
    search.add_argument("--limit", type=int, default=20)
    search.add_argument("--format", choices=("json", "text"), default="text")
    show = subparsers.add_parser("show")
    show.add_argument("result_id")
    show.add_argument("--format", choices=("json", "text"), default="text")
    return parser


def main(argv: Sequence[str] | None = None) -> int:
    args = build_parser().parse_args(argv)
    if args.command == "doctor":
        payload = _doctor()
        if args.format == "json":
            _json(payload)
        else:
            print(f"FTS5: {'yes' if payload['capabilities']['fts5'] else 'no'}")
            tree_sitter = payload["capabilities"]["tree_sitter"]
            tree_sitter_ok = bool(tree_sitter) and all(bool(item.get("ok")) for item in tree_sitter.values())
            print(f"Tree-sitter: {'yes' if tree_sitter_ok else 'no'}")
        return 0 if payload["ok"] else 3

    root, database = _paths()
    if args.command == "setup":
        (root / ".codebase-wiki" / "cache").mkdir(parents=True, exist_ok=True)
        virtualenv = root / ".codebase-wiki" / ".venv"
        if not args.no_install and not virtualenv.exists():
            venv.EnvBuilder(with_pip=True, clear=False).create(virtualenv)
        if not args.no_install:
            python_executable = virtualenv / ("Scripts/python.exe" if sys.platform == "win32" else "bin/python")
            requirements = root / ".codebase-wiki" / "runtime" / "requirements.lock"
            if requirements.exists():
                subprocess.run(
                    [str(python_executable), "-m", "pip", "install", "--disable-pip-version-check", "-r", str(requirements)],
                    check=True,
                )
        payload = {
            "contract_version": CONTRACT_VERSION,
            "ok": True,
            "database": str(database),
            "virtualenv": str(virtualenv),
            "installed": not args.no_install,
        }
        if args.format == "json":
            _json(payload)
        else:
            print(f"Runtime cache ready: {database}")
        return 0

    if args.command in {"install", "upgrade"}:
        source_root = root
        target_root = args.target.resolve()
        plan = plan_install(source_root, target_root, args.surface)
        if args.apply and not plan["conflicts"]:
            apply_install(source_root, target_root, args.surface)
            plan["applied"] = True
        else:
            plan["applied"] = False
        payload = {"contract_version": CONTRACT_VERSION, "ok": not bool(plan["conflicts"]), **plan}
        if args.format == "json":
            _json(payload)
        else:
            print(json.dumps(payload, ensure_ascii=False, indent=2))
        return 0 if payload["ok"] else 2

    if args.command == "index":
        if args.action in {"status", "check"}:
            payload = {
                "contract_version": CONTRACT_VERSION,
                "ok": database.exists(),
                "database": str(database),
                "generation": IndexStore(database).generation() if database.exists() else 0,
                "stale": _index_stale(root) if database.exists() else True,
            }
            if args.format == "json":
                _json(payload)
            else:
                print(json.dumps(payload, ensure_ascii=False, indent=2))
            return 0 if payload["ok"] else 4
        if args.action == "optimize":
            if not database.exists():
                payload = {"contract_version": CONTRACT_VERSION, "ok": False, "error": {"code": "index_missing"}}
                _json(payload) if args.format == "json" else print("Index is missing")
                return 4
            with sqlite3.connect(database) as connection:
                connection.execute("INSERT INTO documents_fts(documents_fts) VALUES ('optimize')")
            payload = {"contract_version": CONTRACT_VERSION, "ok": True}
        else:
            result = build_index(root, database, args.scope)
            payload = {"contract_version": CONTRACT_VERSION, "ok": True, **result}
        if args.format == "json":
            _json(payload)
        else:
            print(json.dumps(payload, ensure_ascii=False, indent=2))
        return 0

    if args.command == "search":
        if not database.exists():
            payload = {
                "contract_version": CONTRACT_VERSION,
                "ok": False,
                "error": {"code": "index_missing", "message": "Run index update first."},
            }
            _json(payload) if args.format == "json" else print(payload["error"]["message"])
            return 4
        kind = "wiki_section" if args.scope == "wiki" else "symbol" if args.scope == "source" else None
        results = IndexStore(database).search(args.query, args.limit, kind=kind)
        payload = {
            "contract_version": CONTRACT_VERSION,
            "ok": True,
            "stale": _index_stale(root),
            "scope": args.scope,
            "results": results,
        }
        if args.format == "json":
            _json(payload)
        else:
            for item in results:
                print(f"{item['path']}:{item['line_start']} {item['title']}")
        return 0

    if args.command == "show":
        item = IndexStore(database).get(args.result_id)
        if item is None:
            payload = {
                "contract_version": CONTRACT_VERSION,
                "ok": False,
                "error": {"code": "result_missing", "message": "Result does not exist in the current index."},
            }
            _json(payload) if args.format == "json" else print(payload["error"]["message"])
            return 4
        payload = {"contract_version": CONTRACT_VERSION, "ok": True, "result": item}
        if args.format == "json":
            _json(payload)
        else:
            print(f"{item['path']}:{item['line_start']} {item['title']}")
            print(item["body"])
        return 0

    return 2
