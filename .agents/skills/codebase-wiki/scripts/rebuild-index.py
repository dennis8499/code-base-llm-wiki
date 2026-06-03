#!/usr/bin/env python3
"""rebuild-index.py — 掃描 wiki/ 目錄，重建 index.md。

用法：
    python .github/skills/codebase-wiki/scripts/rebuild-index.py [wiki_dir]

預設 wiki_dir 為當前目錄下的 wiki/。
"""

import pathlib
import re
import sys

from frontmatter import configure_utf8_stdio, parse_frontmatter_text


def parse_frontmatter(filepath: pathlib.Path) -> dict:
    """解析 markdown 檔案的 YAML frontmatter。"""
    return parse_frontmatter_text(filepath.read_text(encoding="utf-8"))


def extract_first_sentence(filepath: pathlib.Path) -> str:
    """擷取第一個非 frontmatter、非標題的文字段落作為摘要。"""
    text = filepath.read_text(encoding="utf-8")
    # 移除 frontmatter
    text = re.sub(r"^---\s*\n.*?\n---\s*\n?", "", text, count=1, flags=re.DOTALL)
    for line in text.splitlines():
        line = line.strip()
        if not line or line.startswith("#") or line.startswith(">") or line.startswith("|") or line.startswith("-"):
            continue
        # 取第一句
        sentence = re.split(r"[。.\n]", line)[0].strip()
        if sentence:
            return sentence
    return ""


# 頁面類型對應的 index 分類
TYPE_SECTIONS = {
    "overview": "Overview",
    "architecture": "Architecture",
    "module": "Modules",
    "entity": "Entities",
    "pattern": "Patterns",
    "decision": "Decisions",
    "dependency": "Dependencies",
    "guide": "Guides",
    "synthesis": "Synthesis",
}

SKIP_FILES = {"index.md", "log.md"}


def rebuild_index(wiki_dir: pathlib.Path) -> str:
    """掃描 wiki 目錄，產出 index.md 內容。"""
    sections: dict[str, list[str]] = {s: [] for s in TYPE_SECTIONS.values()}

    # 收集所有 .md 檔案
    md_files = sorted(wiki_dir.rglob("*.md"))

    for fp in md_files:
        if fp.name in SKIP_FILES:
            continue
        rel = fp.relative_to(wiki_dir)
        fm = parse_frontmatter(fp)
        title = fm.get("title", fp.stem)
        page_type = fm.get("type", "")
        status = fm.get("status", "active")
        page_name = fp.stem  # 用於 wikilink

        summary = extract_first_sentence(fp) or f"({status})"
        section_name = TYPE_SECTIONS.get(page_type)
        if not section_name:
            continue

        sections[section_name].append(f"| [[{page_name}]] | {summary} |")

    # 組裝 index
    lines = [
        "---",
        "title: Wiki Index",
        "type: index",
        "sources: []",
        f"last_updated: {__import__('datetime').date.today().isoformat()}",
        "tags: [index]",
        "status: active",
        "---",
        "",
        "# Codebase Wiki — 索引",
        "",
        "> 此索引由 `rebuild-index.py` 自動產生。",
        "",
        "---",
        "",
    ]

    for section_name in TYPE_SECTIONS.values():
        lines.append(f"## {section_name}")
        lines.append("")
        entries = sections[section_name]
        if entries:
            lines.append("| 頁面 | 摘要 |")
            lines.append("|------|------|")
            lines.extend(entries)
        else:
            lines.append("_（尚無頁面）_")
        lines.append("")

    return "\n".join(lines)


def main():
    configure_utf8_stdio()
    wiki_dir = pathlib.Path(sys.argv[1]) if len(sys.argv) > 1 else pathlib.Path("wiki")
    if not wiki_dir.is_dir():
        print(f"Error: wiki directory not found: {wiki_dir}", file=sys.stderr)
        sys.exit(1)

    content = rebuild_index(wiki_dir)
    index_path = wiki_dir / "index.md"
    index_path.write_text(content, encoding="utf-8")
    print(f"✅ index.md rebuilt at {index_path}")


if __name__ == "__main__":
    main()
