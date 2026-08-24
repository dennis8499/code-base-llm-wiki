#!/usr/bin/env python3
"""check-stale.py — 比對 wiki frontmatter sources 與實際檔案，找出陳舊頁面。

用法：
    python .agents/skills/codebase-wiki/scripts/check-stale.py [wiki_dir] [repo_root]

預設 wiki_dir 為 wiki/，repo_root 為當前目錄。
"""

import argparse
import pathlib
import datetime as _datetime
import hashlib
import re
import subprocess
import sys
from typing import Any

from frontmatter import configure_utf8_stdio, parse_frontmatter_text, validate_regular_tree


DIGEST_EXCLUDED_PARTS = {
    ".bundle",
    ".git",
    ".gradle",
    ".m2",
    ".notebooklm",
    ".nuget",
    ".pnpm-store",
    ".venv",
    ".yarn",
    "__pycache__",
    "bin",
    "build",
    "cache",
    "coverage",
    "dist",
    "logs",
    "node_modules",
    "obj",
    "target",
    "vendor",
    "wiki",
}


def parse_frontmatter(filepath: pathlib.Path) -> dict:
    """解析 markdown 檔案的 YAML frontmatter。"""
    return parse_frontmatter_text(filepath.read_text(encoding="utf-8"))


def git_dirty_paths(repo_root: pathlib.Path) -> set[str]:
    try:
        result = subprocess.run(
            ["git", "-C", str(repo_root), "status", "--porcelain", "--untracked-files=all"],
            check=True,
            capture_output=True,
            text=True,
            encoding="utf-8",
        )
    except (OSError, subprocess.CalledProcessError):
        return set()
    paths: set[str] = set()
    for line in result.stdout.splitlines():
        if len(line) < 4:
            continue
        value = line[3:].strip()
        if " -> " in value:
            value = value.rsplit(" -> ", 1)[1]
        paths.add(value.replace("\\", "/"))
    return paths


def latest_source_date(repo_root: pathlib.Path, source: str) -> _datetime.date | None:
    try:
        result = subprocess.run(
            ["git", "-C", str(repo_root), "log", "-1", "--format=%cs", "--", source],
            check=True,
            capture_output=True,
            text=True,
            encoding="utf-8",
        )
        value = result.stdout.strip()
        return _datetime.date.fromisoformat(value) if value else None
    except (OSError, subprocess.CalledProcessError, ValueError):
        return None


def _source_path(repo_root: pathlib.Path, source: str) -> pathlib.Path:
    """Resolve a validated repo-relative source independent of host separators."""

    normalized = source.replace("\\", "/").rstrip("/")
    pure = pathlib.PurePosixPath(normalized)
    return repo_root.joinpath(*pure.parts)


def _source_files(repo_root: pathlib.Path, source: str) -> list[pathlib.Path]:
    source_path = _source_path(repo_root, source).resolve()
    try:
        source_path.relative_to(repo_root.resolve())
    except ValueError:
        return []
    if source_path.is_file():
        return [source_path]
    if not source_path.is_dir():
        return []

    relative_source = source_path.relative_to(repo_root.resolve()).as_posix()
    try:
        result = subprocess.run(
            [
                "git",
                "-C",
                str(repo_root),
                "ls-files",
                "--cached",
                "--others",
                "--exclude-standard",
                "-z",
                "--",
                relative_source,
            ],
            check=True,
            capture_output=True,
        )
        candidates = [
            repo_root / value.decode("utf-8", errors="surrogateescape")
            for value in result.stdout.split(b"\0")
            if value
        ]
    except (OSError, subprocess.CalledProcessError):
        candidates = list(source_path.rglob("*"))

    files: list[pathlib.Path] = []
    for path in candidates:
        if not path.is_file():
            continue
        try:
            relative = path.resolve().relative_to(repo_root.resolve())
        except ValueError:
            continue
        if set(relative.parts) & DIGEST_EXCLUDED_PARTS:
            continue
        files.append(path)
    return sorted(set(files), key=lambda item: item.resolve().as_posix())


def compute_source_digest(repo_root: pathlib.Path, sources: list[str]) -> str:
    """Return the stable aggregate digest for existing raw source files."""

    records: dict[str, str] = {}
    for source in sources:
        for path in _source_files(repo_root, source):
            relative = path.resolve().relative_to(repo_root.resolve()).as_posix()
            records[relative] = hashlib.sha256(path.read_bytes()).hexdigest()
    aggregate = hashlib.sha256()
    for relative, digest in sorted(records.items()):
        aggregate.update(relative.encode("utf-8"))
        aggregate.update(b"\0")
        aggregate.update(digest.encode("ascii"))
        aggregate.update(b"\n")
    return f"sha256:{aggregate.hexdigest()}"


def check_stale(wiki_dir: pathlib.Path, repo_root: pathlib.Path):
    """檢查每個 wiki 頁面的 sources 是否仍存在。"""
    validate_regular_tree(wiki_dir)
    md_files = sorted(wiki_dir.rglob("*.md"))
    results: dict[str, list[Any]] = {"critical": [], "warning": [], "ok": []}

    dirty_paths = git_dirty_paths(repo_root)
    for fp in md_files:
        fm = parse_frontmatter(fp)
        sources = fm.get("sources", [])
        if not sources:
            continue

        title = fm.get("title", fp.stem)
        rel_path = fp.relative_to(wiki_dir)
        try:
            repo_page_path = fp.resolve().relative_to(repo_root.resolve()).as_posix()
        except ValueError:
            repo_page_path = ""
        page_is_dirty = repo_page_path in dirty_paths
        missing = []
        existing = []
        stale = []
        invalid = []
        digest_mismatch = None

        if not isinstance(sources, list):
            results["critical"].append({"page": str(rel_path), "title": title, "invalid_sources": "sources must be a list"})
            continue
        page_date = None
        try:
            page_date = _datetime.date.fromisoformat(str(fm.get("last_updated", "")))
        except ValueError:
            pass

        for src in sources:
            normalized_source = src.replace("\\", "/") if isinstance(src, str) else ""
            pure_source = pathlib.PurePath(normalized_source) if isinstance(src, str) else None
            if (
                not isinstance(src, str)
                or not src.strip()
                or pure_source is None
                or pure_source.is_absolute()
                or ".." in pure_source.parts
                or re.fullmatch(r"[A-Za-z]:.*", normalized_source)
            ):
                invalid.append(src)
                continue
            src_path = _source_path(repo_root, src)
            try:
                src_path.resolve(strict=False).relative_to(repo_root.resolve())
            except ValueError:
                invalid.append(src)
                continue
            # 檢查檔案或目錄是否存在
            if src_path.exists() or src_path.is_dir():
                existing.append(src)
            else:
                # 若路徑以 / 結尾，也嘗試不帶 / 的目錄
                if src_path.exists():
                    existing.append(src)
                else:
                    missing.append(src)
                    continue
            normalized = src.rstrip("/").replace("\\", "/")
            dirty = not page_is_dirty and (
                normalized in dirty_paths
                or any(item.startswith(normalized + "/") for item in dirty_paths)
            )
            changed_after_page = bool(page_date and (latest := latest_source_date(repo_root, normalized)) and latest > page_date)
            if dirty or changed_after_page:
                stale.append(src)

        declared_digest = fm.get("source_digest")
        if isinstance(declared_digest, str) and existing and not missing and not invalid:
            current_digest = compute_source_digest(repo_root, existing)
            if declared_digest != current_digest:
                digest_mismatch = {
                    "declared": declared_digest,
                    "current": current_digest,
                }
            else:
                # A matching content fingerprint is stronger evidence than Git
                # commit dates or dirty-path heuristics.
                stale = []

        if invalid:
            results["critical"].append({"page": str(rel_path), "title": title, "invalid_sources": invalid})
        elif missing and not existing:
            results["critical"].append({
                "page": str(rel_path),
                "title": title,
                "all_missing": missing,
            })
        elif missing or stale or digest_mismatch:
            warning = {
                "page": str(rel_path),
                "title": title,
                "missing": missing,
                "existing": existing,
                "stale": stale,
            }
            if digest_mismatch:
                warning["digest_mismatch"] = digest_mismatch
            results["warning"].append(warning)
        else:
            results["ok"].append(str(rel_path))

    return results


def main(argv: list[str] | None = None):
    configure_utf8_stdio()
    parser = argparse.ArgumentParser(
        prog="check-stale.py",
        description="Check Wiki sources for missing or stale raw files.",
    )
    parser.add_argument("wiki_dir", nargs="?", type=pathlib.Path, default=pathlib.Path("wiki"))
    parser.add_argument("repo_root", nargs="?", type=pathlib.Path, default=pathlib.Path("."))
    args = parser.parse_args(argv)
    wiki_dir = args.wiki_dir
    repo_root = args.repo_root

    if not wiki_dir.is_dir():
        print(f"Error: wiki directory not found: {wiki_dir}", file=sys.stderr)
        sys.exit(1)

    try:
        results = check_stale(wiki_dir, repo_root)
    except (OSError, UnicodeError) as exc:
        print(f"Error: {exc}", file=sys.stderr)
        sys.exit(2)

    print("=" * 60)
    print("Wiki Stale Check Report")
    print("=" * 60)

    if results["critical"]:
        print(f"\n🔴 CRITICAL — Invalid or missing sources ({len(results['critical'])} pages):\n")
        for item in results["critical"]:
            print(f"  {item['page']} ({item['title']})")
            if "invalid_sources" in item:
                invalid = item["invalid_sources"]
                values = invalid if isinstance(invalid, list) else [invalid]
                for src in values:
                    print(f"    invalid: {src}")
            for src in item.get("all_missing", []):
                print(f"    missing: {src}")

    if results["warning"]:
        print(f"\n🟡 WARNING — Some sources missing or stale ({len(results['warning'])} pages):\n")
        for item in results["warning"]:
            print(f"  {item['page']} ({item['title']})")
            if item.get("missing"):
                print(f"    missing: {', '.join(item['missing'])}")
            if item.get("stale"):
                print(f"    stale: {', '.join(item['stale'])}")
            if item.get("digest_mismatch"):
                mismatch = item["digest_mismatch"]
                print(f"    source_digest: {mismatch['declared']} -> {mismatch['current']}")
            for src in item["missing"]:
                print(f"    ✗ {src}")

    ok_count = len(results["ok"])
    total = ok_count + len(results["critical"]) + len(results["warning"])
    print(f"\n🟢 OK: {ok_count}/{total} pages have no missing or stale sources.\n")

    if results["critical"] or results["warning"]:
        sys.exit(1)


if __name__ == "__main__":
    main()
