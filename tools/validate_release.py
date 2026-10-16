#!/usr/bin/env python3
"""Run release checks once, retaining each standalone gate's exit semantics.

The interpreter's unittest suite runs separately. No release assets are built.
"""
from __future__ import annotations

import argparse
import importlib.util
import json
from pathlib import Path
import subprocess
import sys
import time

ROOT = Path(__file__).resolve().parents[1]
SCRIPTS = ROOT / ".agents/skills/codebase-wiki/scripts"
sys.path.insert(0, str(SCRIPTS))


def wiki_checks(wiki: Path, root: Path) -> list[dict]:
    spec = importlib.util.spec_from_file_location("release_wiki_lint", SCRIPTS / "lint-wiki.py")
    lint = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(lint)
    frontmatter = lint.load_script("release_frontmatter", "validate-frontmatter.py")
    stale = lint.load_script("release_stale", "check-stale.py")
    log = lint.load_script("release_log", "validate-log.py")
    components, rows = {}, []

    def capture(name, operation, exit_code):
        started = time.perf_counter()
        try:
            value = operation()
            components[name] = value
            row = {"check": name, "exit_code": exit_code(value), "result": value}
        except (OSError, UnicodeError, RuntimeError, ValueError) as error:
            row = {"check": name, "exit_code": 2, "error": str(error)}
        row["seconds"] = round(time.perf_counter() - started, 6)
        rows.append(row)

    def validate_frontmatter():
        frontmatter.validate_regular_tree(wiki)
        by_page = {path.relative_to(wiki).as_posix(): frontmatter.validate_page(path, wiki)
                   for path in sorted(wiki.rglob("*.md"))}
        return {"errors": [error for errors in by_page.values() for error in errors],
                "by_page": by_page, "pages": len(by_page)}

    if wiki.is_dir():
        capture("frontmatter", validate_frontmatter, lambda value: 1 if value["errors"] else 0)
        capture("stale", lambda: stale.check_stale(wiki, root),
                lambda value: 1 if value["critical"] or value["warning"] else 0)
    else:
        rows.extend({"check": name, "exit_code": 1, "error": f"Wiki directory not found: {wiki}", "seconds": 0}
                    for name in ("frontmatter", "stale"))
    capture("log", lambda: log.validate_log(wiki / "log.md", root), lambda value: 0 if value["ok"] else 2)
    if wiki.is_dir():
        capture("lint", lambda: lint.lint_wiki(wiki, root,
                precomputed=components if all(name in components for name in ("frontmatter", "stale", "log")) else None),
                lambda value: 2 if value["summary"]["critical"] else 1 if value["summary"]["warning"] else 0)
    else:
        rows.append({"check": "lint", "exit_code": 2, "error": f"Wiki directory not found: {wiki}", "seconds": 0})
    return rows


def validate(root: Path, tag: str | None = None) -> dict:
    started = time.perf_counter()
    checks = []
    commands = [("compile", ["-m", "compileall", "-q", ".agents/skills/codebase-wiki/scripts", "tools", "tests"]),
                ("parity", [str(SCRIPTS / "parity-check.py")]),
                ("stats", [str(SCRIPTS / "wiki-stats.py"), "wiki"]),
                ("index", [str(SCRIPTS / "rebuild-index.py"), "wiki", "--check"]),
                ("scan", [str(SCRIPTS / "scan-project.py"), "--root", ".", "--profile", "framework", "--format", "json"])]
    if tag is not None:
        commands.append(("release-validate", [str(ROOT / "tools/release.py"), "validate", "--tag", tag]))
    for name, arguments in commands:
        command = [sys.executable, "-X", "utf8", "-B", *arguments]
        check_started = time.perf_counter()
        process = subprocess.run(command, cwd=root, stdout=subprocess.PIPE, stderr=subprocess.STDOUT,
                                 text=True, encoding="utf-8", errors="replace")
        checks.append({"check": name, "command": command, "exit_code": process.returncode,
                       "seconds": round(time.perf_counter() - check_started, 6), "output": process.stdout})
    checks.extend(wiki_checks(root / "wiki", root))
    return {"schema": "codebase-wiki-release-validation/v1", "ok": all(row["exit_code"] == 0 for row in checks),
            "python": sys.version, "checks": checks, "seconds": round(time.perf_counter() - started, 6)}


def main(argv=None) -> int:
    from frontmatter import configure_utf8_stdio
    configure_utf8_stdio()
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--format", choices=("text", "json"), default="text")
    parser.add_argument("--tag", help="Also validate VERSION, tag and release readiness")
    args = parser.parse_args(argv)
    try:
        report = validate(ROOT, args.tag)
    except (OSError, ValueError, RuntimeError) as error:
        report = {"ok": False, "error": str(error), "checks": []}
    if args.format == "json":
        print(json.dumps(report, ensure_ascii=False, indent=2))
    else:
        for row in report["checks"]:
            print(f"{row['check']}: exit={row['exit_code']} ({row['seconds']:.3f}s)")
            if row["exit_code"]:
                print(row.get("output", row.get("error", json.dumps(row.get("result"), ensure_ascii=False))))
        if "error" in report:
            print(report["error"], file=sys.stderr)
    # Preserve operational/input errors as 2 and ordinary gate failures as 1.
    return 0 if report["ok"] else 2 if "error" in report or any(row["exit_code"] >= 2 for row in report["checks"]) else 1


if __name__ == "__main__":
    raise SystemExit(main())
