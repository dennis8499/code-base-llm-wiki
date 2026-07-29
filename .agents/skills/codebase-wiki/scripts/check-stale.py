#!/usr/bin/env python3
"""check-stale.py — 比對 wiki frontmatter sources 與實際檔案，找出陳舊頁面。

用法：
    python .agents/skills/codebase-wiki/scripts/check-stale.py [wiki_dir] [repo_root]

預設 wiki_dir 為 wiki/，repo_root 為當前目錄。
"""

import pathlib
import datetime as _datetime
import subprocess
import sys

from frontmatter import configure_utf8_stdio, parse_frontmatter_text


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


def check_stale(wiki_dir: pathlib.Path, repo_root: pathlib.Path):
    """檢查每個 wiki 頁面的 sources 是否仍存在。"""
    md_files = sorted(wiki_dir.rglob("*.md"))
    results = {"critical": [], "warning": [], "ok": []}

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

        if not isinstance(sources, list):
            results["critical"].append({"page": str(rel_path), "title": title, "invalid_sources": "sources must be a list"})
            continue
        page_date = None
        try:
            page_date = _datetime.date.fromisoformat(str(fm.get("last_updated", "")))
        except ValueError:
            pass

        for src in sources:
            pure_source = pathlib.PurePath(src.replace("\\", "/")) if isinstance(src, str) else None
            if (
                not isinstance(src, str)
                or not src.strip()
                or pure_source is None
                or pure_source.is_absolute()
                or ".." in pure_source.parts
            ):
                invalid.append(src)
                continue
            src_path = repo_root / src.rstrip("/")
            # 檢查檔案或目錄是否存在
            if src_path.exists() or src_path.is_dir():
                existing.append(src)
            else:
                # 若路徑以 / 結尾，也嘗試不帶 / 的目錄
                if (repo_root / src).exists():
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

        if invalid:
            results["critical"].append({"page": str(rel_path), "title": title, "invalid_sources": invalid})
        elif missing and not existing:
            results["critical"].append({
                "page": str(rel_path),
                "title": title,
                "all_missing": missing,
            })
        elif missing or stale:
            results["warning"].append({
                "page": str(rel_path),
                "title": title,
                "missing": missing,
                "existing": existing,
                "stale": stale,
            })
        else:
            results["ok"].append(str(rel_path))

    return results


def main():
    configure_utf8_stdio()
    wiki_dir = pathlib.Path(sys.argv[1]) if len(sys.argv) > 1 else pathlib.Path("wiki")
    repo_root = pathlib.Path(sys.argv[2]) if len(sys.argv) > 2 else pathlib.Path(".")

    if not wiki_dir.is_dir():
        print(f"Error: wiki directory not found: {wiki_dir}", file=sys.stderr)
        sys.exit(1)

    results = check_stale(wiki_dir, repo_root)

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
            for src in item["missing"]:
                print(f"    ✗ {src}")

    ok_count = len(results["ok"])
    total = ok_count + len(results["critical"]) + len(results["warning"])
    print(f"\n🟢 OK: {ok_count}/{total} pages have no missing or stale sources.\n")

    if results["critical"] or results["warning"]:
        sys.exit(1)


if __name__ == "__main__":
    main()
