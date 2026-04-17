#!/usr/bin/env python3
"""check-stale.py — 比對 wiki frontmatter sources 與實際檔案，找出陳舊頁面。

用法：
    python .github/skills/codebase-wiki/scripts/check-stale.py [wiki_dir] [repo_root]

預設 wiki_dir 為 wiki/，repo_root 為當前目錄。
"""

import pathlib
import re
import sys
import yaml


def parse_frontmatter(filepath: pathlib.Path) -> dict:
    """解析 markdown 檔案的 YAML frontmatter。"""
    text = filepath.read_text(encoding="utf-8")
    match = re.match(r"^---\s*\n(.*?)\n---", text, re.DOTALL)
    if not match:
        return {}
    try:
        return yaml.safe_load(match.group(1)) or {}
    except yaml.YAMLError:
        return {}


def check_stale(wiki_dir: pathlib.Path, repo_root: pathlib.Path):
    """檢查每個 wiki 頁面的 sources 是否仍存在。"""
    md_files = sorted(wiki_dir.rglob("*.md"))
    results = {"critical": [], "warning": [], "ok": []}

    for fp in md_files:
        fm = parse_frontmatter(fp)
        sources = fm.get("sources", [])
        if not sources:
            continue

        title = fm.get("title", fp.stem)
        rel_path = fp.relative_to(wiki_dir)
        missing = []
        existing = []

        for src in sources:
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

        if missing and not existing:
            results["critical"].append({
                "page": str(rel_path),
                "title": title,
                "all_missing": missing,
            })
        elif missing:
            results["warning"].append({
                "page": str(rel_path),
                "title": title,
                "missing": missing,
                "existing": existing,
            })
        else:
            results["ok"].append(str(rel_path))

    return results


def main():
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
        print(f"\n🔴 CRITICAL — All sources missing ({len(results['critical'])} pages):\n")
        for item in results["critical"]:
            print(f"  {item['page']} ({item['title']})")
            for src in item["all_missing"]:
                print(f"    ✗ {src}")

    if results["warning"]:
        print(f"\n🟡 WARNING — Some sources missing ({len(results['warning'])} pages):\n")
        for item in results["warning"]:
            print(f"  {item['page']} ({item['title']})")
            for src in item["missing"]:
                print(f"    ✗ {src}")

    ok_count = len(results["ok"])
    total = ok_count + len(results["critical"]) + len(results["warning"])
    print(f"\n🟢 OK: {ok_count}/{total} pages have all sources intact.\n")

    if results["critical"] or results["warning"]:
        sys.exit(1)


if __name__ == "__main__":
    main()
