#!/usr/bin/env python3
"""rebuild-index.py — 掃描 wiki/ 目錄，重建或唯讀檢查 index.md。

用法：
    python .agents/skills/codebase-wiki/scripts/rebuild-index.py [wiki_dir]
    python .agents/skills/codebase-wiki/scripts/rebuild-index.py [wiki_dir] --check

預設 wiki_dir 為當前目錄下的 wiki/。
"""

import argparse
from collections import defaultdict
import os
import pathlib
import re
import stat
import sys
from typing import TypedDict

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
    "business-process": "Business Processes",
    "business-rule": "Business Rules",
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
MANAGED_START = "<!-- codebase-wiki:index:start -->"
MANAGED_END = "<!-- codebase-wiki:index:end -->"


def _is_reparse_point(path: pathlib.Path) -> bool:
    """Detect symlinks and Windows junction/reparse points without following them."""

    if path.is_symlink():
        return True
    if os.name != "nt":
        return False
    try:
        attributes = os.stat(path, follow_symlinks=False).st_file_attributes
    except FileNotFoundError:
        return False
    except OSError:
        return True
    return bool(attributes & getattr(stat, "FILE_ATTRIBUTE_REPARSE_POINT", 0x400))


def validate_wiki_tree(wiki_dir: pathlib.Path) -> None:
    """Reject a Wiki tree that could make index reads or writes escape it."""

    if _is_reparse_point(wiki_dir):
        raise OSError(f"Wiki directory must not be a symlink or reparse point: {wiki_dir}")
    if not wiki_dir.is_dir():
        raise OSError(f"Wiki directory is not a directory: {wiki_dir}")
    for path in wiki_dir.rglob("*"):
        if _is_reparse_point(path):
            raise OSError(f"Wiki tree must not contain symlink or reparse point: {path}")


class WrongSection(TypedDict):
    expected: str
    actual: list[str]


class IndexDifferences(TypedDict):
    missing: set[str]
    unknown: set[str]
    wrong_section: dict[str, WrongSection]
    duplicates: dict[str, list[str]]


def expected_index_entries(wiki_dir: pathlib.Path) -> dict[str, str]:
    validate_wiki_tree(wiki_dir)
    expected: dict[str, str] = {}
    for path in sorted(wiki_dir.rglob("*.md")):
        if path.name in SKIP_FILES:
            continue
        section = TYPE_SECTIONS.get(str(parse_frontmatter(path).get("type", "")))
        if section:
            expected[path.stem] = section
    return expected


def actual_index_entries(text: str) -> dict[str, list[str]]:
    if MANAGED_START in text and MANAGED_END in text:
        text = text.split(MANAGED_START, 1)[1].split(MANAGED_END, 1)[0]
    visible = re.sub(r"```.*?```", "", text, flags=re.DOTALL)
    visible = re.sub(r"`[^`\n]*`", "", visible)
    entries: dict[str, list[str]] = defaultdict(list)
    section = ""
    valid_sections = set(TYPE_SECTIONS.values())
    for line in visible.splitlines():
        if line.startswith("## "):
            section = line[3:].strip()
            continue
        if section not in valid_sections:
            continue
        for raw in re.findall(r"\[\[([^\]]+)\]\]", line):
            target = raw.split("|", 1)[0].split("#", 1)[0].strip().replace("\\", "/")
            if target:
                entries[pathlib.PurePosixPath(target).stem].append(section)
    return dict(entries)


def check_index(wiki_dir: pathlib.Path) -> IndexDifferences:
    validate_wiki_tree(wiki_dir)
    expected = expected_index_entries(wiki_dir)
    index_path = wiki_dir / "index.md"
    actual = (
        actual_index_entries(index_path.read_text(encoding="utf-8"))
        if index_path.is_file()
        else {}
    )
    wrong_section: dict[str, WrongSection] = {
        target: {"expected": expected[target], "actual": list(sections)}
        for target, sections in actual.items()
        if target in expected and any(section != expected[target] for section in sections)
    }
    duplicates = {
        target: sections for target, sections in actual.items() if len(sections) > 1
    }
    return {
        "missing": set(expected) - set(actual),
        "unknown": set(actual) - set(expected),
        "wrong_section": wrong_section,
        "duplicates": duplicates,
    }


def rebuild_index(wiki_dir: pathlib.Path) -> str:
    """更新受管索引區段，保留 frontmatter、前言與人工區段。"""
    validate_wiki_tree(wiki_dir)
    sections: dict[str, list[str]] = {s: [] for s in TYPE_SECTIONS.values()}

    # 收集所有 .md 檔案
    md_files = sorted(wiki_dir.rglob("*.md"))

    for fp in md_files:
        if fp.name in SKIP_FILES:
            continue
        fm = parse_frontmatter(fp)
        page_type = fm.get("type", "")
        status = fm.get("status", "active")
        page_name = fp.stem  # 用於 wikilink

        summary = fm.get("summary") or extract_first_sentence(fp) or f"({status})"
        section_name = TYPE_SECTIONS.get(page_type)
        if not section_name:
            continue

        sections[section_name].append(f"| [[{page_name}]] | {summary} |")

    managed_lines = [MANAGED_START, ""]

    for section_name in TYPE_SECTIONS.values():
        managed_lines.append(f"## {section_name}")
        managed_lines.append("")
        entries = sections[section_name]
        if entries:
            managed_lines.append("| 頁面 | 摘要 |")
            managed_lines.append("|------|------|")
            managed_lines.extend(entries)
        else:
            managed_lines.append("_（尚無頁面）_")
        managed_lines.append("")
    managed_lines.append(MANAGED_END)
    managed = "\n".join(managed_lines)

    index_path = wiki_dir / "index.md"
    if index_path.is_file():
        current = index_path.read_text(encoding="utf-8")
        current = re.sub(
            r"(?m)^last_updated:\s*\d{4}-\d{2}-\d{2}\s*$",
            f"last_updated: {__import__('datetime').date.today().isoformat()}",
            current,
            count=1,
        )
        if MANAGED_START in current and MANAGED_END in current:
            before, remainder = current.split(MANAGED_START, 1)
            _, after = remainder.split(MANAGED_END, 1)
            return before.rstrip() + "\n\n" + managed + after
        return current.rstrip() + "\n\n" + managed + "\n"

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
        "> 此索引的受管區段由 `rebuild-index.py` 維護；標記外內容會保留。",
        "",
        managed,
        "",
    ]
    return "\n".join(lines)


def main(argv: list[str] | None = None) -> int:
    configure_utf8_stdio()
    parser = argparse.ArgumentParser()
    parser.add_argument("wiki_dir", nargs="?", type=pathlib.Path, default=pathlib.Path("wiki"))
    parser.add_argument("--check", action="store_true")
    args = parser.parse_args(argv)
    wiki_dir = args.wiki_dir
    if not wiki_dir.is_dir():
        print(f"Error: wiki directory not found: {wiki_dir}", file=sys.stderr)
        return 1

    try:
        if args.check:
            differences = check_index(wiki_dir)
            if any(differences.values()):
                missing = differences["missing"]
                unknown = differences["unknown"]
                wrong_section = differences["wrong_section"]
                duplicates = differences["duplicates"]
                if missing:
                    print("Missing from index: " + ", ".join(sorted(missing)))
                if unknown:
                    print("Index targets without pages: " + ", ".join(sorted(unknown)))
                for target, wrong in sorted(wrong_section.items()):
                    print(
                        f"Wrong section for {target}: expected {wrong['expected']}; "
                        f"found {', '.join(wrong['actual'])}"
                    )
                for target, duplicate_sections in sorted(duplicates.items()):
                    print(
                        f"Duplicate index entry for {target}: {', '.join(duplicate_sections)}"
                    )
                return 1
            print(f"OK: {wiki_dir / 'index.md'} matches expected page/type entries")
            return 0

        content = rebuild_index(wiki_dir)
        index_path = wiki_dir / "index.md"
        index_path.write_text(content, encoding="utf-8")
        print(f"✅ index.md rebuilt at {index_path}")
        return 0
    except (OSError, UnicodeError) as exc:
        print(f"Error: {exc}", file=sys.stderr)
        return 2


if __name__ == "__main__":
    raise SystemExit(main())
