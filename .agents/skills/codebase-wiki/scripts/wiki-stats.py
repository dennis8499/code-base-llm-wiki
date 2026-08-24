#!/usr/bin/env python3
"""wiki-stats.py — Wiki 統計報告：頁面數、覆蓋率、更新狀態。

用法：
    python .agents/skills/codebase-wiki/scripts/wiki-stats.py [wiki_dir]

預設 wiki_dir 為 wiki/。
"""

import argparse
import datetime
import pathlib
import re
import sys

from frontmatter import configure_utf8_stdio, parse_frontmatter_text, validate_regular_tree


def parse_frontmatter(filepath: pathlib.Path) -> dict:
    """解析 markdown 檔案的 YAML frontmatter。"""
    return parse_frontmatter_text(filepath.read_text(encoding="utf-8"))


def count_wikilinks(filepath: pathlib.Path) -> int:
    """計算檔案中 [[wikilink]] 的數量。"""
    text = filepath.read_text(encoding="utf-8")
    return len(re.findall(r"\[\[([^\]]+)\]\]", text))


def wiki_stats(wiki_dir: pathlib.Path):
    """產出 wiki 統計報告。"""
    validate_regular_tree(wiki_dir)
    md_files = sorted(wiki_dir.rglob("*.md"))
    today = datetime.date.today()
    thirty_days_ago = today - datetime.timedelta(days=30)

    type_counts: dict[str, int] = {}
    status_counts: dict[str, int] = {}
    total_sources = 0
    total_wikilinks = 0
    stale_count = 0
    pages_with_sources = 0

    skip = {"index.md", "log.md"}

    for fp in md_files:
        if fp.name in skip:
            continue

        fm = parse_frontmatter(fp)
        page_type = fm.get("type", "unknown")
        status = fm.get("status", "unknown")
        sources = fm.get("sources", [])
        last_updated = fm.get("last_updated", "")

        type_counts[page_type] = type_counts.get(page_type, 0) + 1
        status_counts[status] = status_counts.get(status, 0) + 1

        if sources:
            total_sources += len(sources)
            pages_with_sources += 1

        total_wikilinks += count_wikilinks(fp)

        # 檢查是否在 30 天內更新
        if last_updated:
            try:
                updated_date = datetime.date.fromisoformat(last_updated)
                if updated_date < thirty_days_ago:
                    stale_count += 1
            except ValueError:
                pass

    total_pages = sum(type_counts.values())
    avg_sources = total_sources / max(pages_with_sources, 1)

    # 輸出報告
    print("=" * 60)
    print(f"Wiki Statistics Report — {today.isoformat()}")
    print("=" * 60)

    print(f"\n📊 總頁面數: {total_pages}")
    print("   (不含 index.md, log.md)")

    print("\n📁 各類型頁面數:")
    for t, c in sorted(type_counts.items(), key=lambda x: -x[1]):
        print(f"   {t:20s} {c}")

    print("\n📋 狀態分佈:")
    for s, c in sorted(status_counts.items(), key=lambda x: -x[1]):
        print(f"   {s:20s} {c}")

    print(f"\n🔗 Wikilink 總數: {total_wikilinks}")
    print(f"   平均每頁: {total_wikilinks / max(total_pages, 1):.1f}")

    print("\n📎 Source 引用:")
    print(f"   總引用數: {total_sources}")
    print(f"   有 source 的頁面: {pages_with_sources}/{total_pages}")
    print(f"   平均每頁: {avg_sources:.1f}")

    print(f"\n⏰ 30 天內未更新: {stale_count} 頁面")

    print()


def main(argv: list[str] | None = None):
    configure_utf8_stdio()
    parser = argparse.ArgumentParser(
        prog="wiki-stats.py",
        description="Print page, source, link, and update statistics for a Wiki.",
    )
    parser.add_argument("wiki_dir", nargs="?", type=pathlib.Path, default=pathlib.Path("wiki"))
    args = parser.parse_args(argv)
    wiki_dir = args.wiki_dir
    if not wiki_dir.is_dir():
        print(f"Error: wiki directory not found: {wiki_dir}", file=sys.stderr)
        sys.exit(1)
    try:
        wiki_stats(wiki_dir)
    except (OSError, UnicodeError) as exc:
        print(f"Error: {exc}", file=sys.stderr)
        sys.exit(2)


if __name__ == "__main__":
    main()
