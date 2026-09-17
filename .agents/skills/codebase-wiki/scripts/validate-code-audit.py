#!/usr/bin/env python3
"""Validate the structure and provenance of a persisted Codebase audit.

The validator does not inspect or execute the audited application.  It checks
that a report is internally consistent, that its current ``sources`` exist,
and that Git history claims have the evidence shape required by the audit
workflow.

Usage:
    python .agents/skills/codebase-wiki/scripts/validate-code-audit.py \
        wiki/synthesis/code-audit-all.md --repo-root .
"""

from __future__ import annotations

import argparse
import datetime as _datetime
import json
from pathlib import Path, PurePosixPath
import re
import sys
from typing import Any

from frontmatter import configure_utf8_stdio, parse_frontmatter_text


REQUIRED_FRONTMATTER = {
    "title",
    "type",
    "summary",
    "sources",
    "derived_from",
    "source_digest",
    "last_updated",
    "tags",
    "status",
    "notebooklm_role",
}
FINDING_HEADING = re.compile(
    r"(?m)^###\s+((?:BUG|RISK|BIZ)-[0-9]+)\s+[—-]\s+.+$"
)
FULL_SHA = re.compile(r"(?<![0-9a-f])[0-9a-f]{40}(?![0-9a-f])")
SOURCE_DIGEST = re.compile(r"^sha256:[0-9a-f]{64}$")
RELATIVE_SOURCE = re.compile(r"^[^/\\][^:]*$")
SUMMARY_COVERAGE = re.compile(
    r"入口覆蓋[^\n]*?checked\s*([0-9]+)[^\n]*?partial\s*([0-9]+)"
    r"[^\n]*?not checked\s*([0-9]+)",
    re.IGNORECASE,
)
SUMMARY_FINDINGS = re.compile(
    r"確定缺陷\s*[：:]\s*([0-9]+)\s*[；;，,]\s*"
    r"技術風險\s*[：:]\s*([0-9]+)\s*[；;，,]\s*"
    r"待確認業務疑點\s*[：:]\s*([0-9]+)",
)
TABLE_CELL = re.compile(r"^\|(.+)\|$")
PATH_REFERENCE = re.compile(
    r"`(?:[^`\n]+[/\\][^`\n]+|[A-Za-z0-9_.-]+\.[A-Za-z0-9_.-]+)(?::[0-9]+)?`"
)
HISTORY_AVAILABILITY = re.compile(
    r"歷史可用性\s*[：:]\s*`?(available|shallow|unavailable|not-a-repository)`?",
    re.IGNORECASE,
)
COVERAGE_STATUSES = {"checked", "partial", "not checked"}
CHECK_CATEGORY_STATUSES = {
    "checked",
    "partial",
    "not checked",
    "not applicable",
    "evidence-gap",
    "evidence insufficient",
    "insufficient evidence",
    "n/a",
    "已檢查",
    "部分檢查",
    "不適用",
    "證據不足",
    "證據缺口",
    "未檢查",
}
STATIC_CHECKS = (
    "Transactions and side effects",
    "Configuration references",
    "Logic and state contracts",
    "Change completeness",
)
STATIC_CHECK_ALIASES = {
    "交易與外部副作用": "Transactions and side effects",
    "交易／外部副作用": "Transactions and side effects",
    "設定引用": "Configuration references",
    "邏輯與狀態契約": "Logic and state contracts",
    "變更完整性": "Change completeness",
}

REQUIRED_SECTIONS = (
    "結果摘要",
    "檢查範圍與排除",
    "入口覆蓋",
    "Git 歷史與變更線索",
    "確定缺陷",
    "技術風險",
    "待確認業務疑點",
    "未完成工作與驗證建議",
    "相關頁面",
)

FINDING_FIELDS = {
    "BUG": (
        "狀態",
        "證據確定度",
        "影響程度",
        "受影響入口",
        "可達觸發條件",
        "呼叫路徑",
        "證據",
        "已核對防護／反證",
        "預期行為／明確規則",
        "實際行為與影響",
        "修正方向",
        "建議驗證案例",
    ),
    "RISK": (
        "狀態",
        "證據確定度",
        "影響程度",
        "受影響入口",
        "成立條件",
        "可疑呼叫路徑",
        "目前觀察",
        "已核對防護／反證",
        "缺少的證據",
        "確認方式",
        "修正方向",
        "建議驗證案例",
    ),
    "BIZ": (
        "狀態",
        "證據確定度",
        "可能影響程度",
        "受影響入口",
        "呼叫路徑",
        "目前行為",
        "已核對防護／反證",
        "推論依據",
        "尚未明確的預期政策",
        "需確認的業務問題",
        "確認不同答案可能造成的差異",
        "建議驗證案例",
    ),
}


def _section_body(text: str, title: str) -> str:
    """Return a section body, excluding the next level-2 heading."""

    match = re.search(rf"(?m)^##\s+{re.escape(title)}\s*$", text)
    if not match:
        return ""
    next_heading = re.search(r"(?m)^##\s+", text[match.end() :])
    end = match.end() + next_heading.start() if next_heading else len(text)
    return text[match.end() : end]


def _managed_body(text: str) -> str:
    start = "<!-- codebase-wiki:managed:start -->"
    end = "<!-- codebase-wiki:managed:end -->"
    if start not in text or end not in text:
        return text
    body = text.split(start, 1)[1]
    return body.split(end, 1)[0]


def _finding_blocks(text: str) -> list[tuple[str, str]]:
    matches = list(FINDING_HEADING.finditer(text))
    blocks: list[tuple[str, str]] = []
    for index, match in enumerate(matches):
        end = matches[index + 1].start() if index + 1 < len(matches) else len(text)
        blocks.append((match.group(1), text[match.end() : end]))
    return blocks


def _has_field(body: str, field: str) -> bool:
    """Match a labelled bullet, allowing the template's explanatory suffix."""

    return bool(
        re.search(
            rf"(?m)^\s*-\s*{re.escape(field)}(?:（[^\n：:]*）)?\s*[：:]",
            body,
        )
    )


def _field_value(body: str, field: str) -> str:
    """Return the first value of a labelled bullet, without the label."""

    match = re.search(
        rf"(?m)^\s*-\s*{re.escape(field)}(?:（[^\n：:]*）)?\s*[：:]\s*(.+)$",
        body,
    )
    return match.group(1).strip() if match else ""


def _normalise_status(value: str) -> str:
    return value.strip().strip("`").lower()


def _is_empty_value(value: str) -> bool:
    normalized = value.strip().strip("`").strip("。.;；")
    return normalized.lower() in {"", "無", "none", "n/a", "-"}


def _table_cells(line: str) -> list[str] | None:
    match = TABLE_CELL.match(line.strip())
    if not match:
        return None
    return [cell.strip() for cell in match.group(1).split("|")]


def _is_separator_row(cells: list[str]) -> bool:
    return bool(cells) and all(set(cell) <= {"-", " ", ":"} for cell in cells)


def _source_path(repo_root: Path, value: str) -> Path | None:
    normalized = value.replace("\\", "/")
    if not RELATIVE_SOURCE.fullmatch(normalized):
        return None
    pure = PurePosixPath(normalized)
    if pure.is_absolute() or ".." in pure.parts or not pure.parts:
        return None
    path = repo_root.joinpath(*pure.parts)
    try:
        path.resolve().relative_to(repo_root.resolve())
    except ValueError:
        return None
    return path


def validate_report(report_path: Path, repo_root: Path) -> list[str]:
    errors: list[str] = []
    try:
        text = report_path.read_text(encoding="utf-8")
    except (OSError, UnicodeError) as exc:
        return [f"cannot read report: {exc}"]

    frontmatter = parse_frontmatter_text(text)
    missing = sorted(REQUIRED_FRONTMATTER - set(frontmatter))
    if missing:
        errors.append("missing required frontmatter: " + ", ".join(missing))
    if frontmatter.get("type") != "synthesis":
        errors.append("type must be synthesis")
    if frontmatter.get("notebooklm_role") != "exclude":
        errors.append("notebooklm_role must be exclude")
    if not isinstance(frontmatter.get("title"), str) or not frontmatter["title"].strip():
        errors.append("title must be a non-empty string")
    if not isinstance(frontmatter.get("summary"), str) or not frontmatter["summary"].strip():
        errors.append("summary must be a non-empty string")
    last_updated = frontmatter.get("last_updated")
    if not isinstance(last_updated, str):
        errors.append("last_updated must be a YYYY-MM-DD date")
    else:
        try:
            parsed_date = _datetime.date.fromisoformat(last_updated)
        except ValueError:
            parsed_date = None
        if parsed_date is None or parsed_date.isoformat() != last_updated:
            errors.append("last_updated must be a YYYY-MM-DD date")
    tags = frontmatter.get("tags")
    if not isinstance(tags, list) or any(not isinstance(tag, str) or not tag.strip() for tag in tags):
        errors.append("tags must be an array of non-empty strings")
    status = frontmatter.get("status")
    if status not in {"active", "stale", "placeholder"}:
        errors.append("status must be active, stale, or placeholder")
    sources = frontmatter.get("sources")
    if not isinstance(sources, list):
        errors.append("sources must be an array")
        sources = []
    for source in sources:
        if not isinstance(source, str) or not source.strip():
            errors.append("every sources entry must be a non-empty relative path")
            continue
        normalized_source = source.replace("\\", "/")
        if PurePosixPath(normalized_source).parts and PurePosixPath(normalized_source).parts[0].lower() == "wiki":
            errors.append(f"sources must reference raw repository evidence; use derived_from for Wiki pages: {source}")
        path = _source_path(repo_root, source)
        if path is None:
            errors.append(f"source escapes repository or is malformed: {source!r}")
        elif not path.exists() and not path.is_dir():
            errors.append(f"source does not exist: {source}")
    digest = frontmatter.get("source_digest")
    if not isinstance(digest, str) or not SOURCE_DIGEST.fullmatch(digest):
        errors.append("source_digest must use sha256:<64 lowercase hex>")
    derived_from = frontmatter.get("derived_from")
    if not isinstance(derived_from, list) or not all(
        isinstance(item, str) and re.fullmatch(r"\[\[[^\[\]]+\]\]", item)
        for item in derived_from
    ):
        errors.append("derived_from must be an array of [[wiki-page]] links")

    managed = _managed_body(text)
    if "<!-- codebase-wiki:managed:start -->" not in text or "<!-- codebase-wiki:managed:end -->" not in text:
        errors.append("report must contain managed markers")
    if "<!-- codebase-wiki:user-notes:start -->" not in text or "<!-- codebase-wiki:user-notes:end -->" not in text:
        errors.append("report must contain user-notes markers")
    for section in REQUIRED_SECTIONS:
        if not re.search(rf"(?m)^##\s+{re.escape(section)}\s*$", managed):
            errors.append(f"missing required section: {section}")

    coverage_body = _section_body(managed, "入口覆蓋")
    coverage_counts = {"checked": 0, "partial": 0, "not checked": 0}
    coverage_entries: list[str] = []
    for line in coverage_body.splitlines():
        cells = _table_cells(line)
        if cells is None or not cells or _is_separator_row(cells):
            continue
        first = cells[0].strip().strip("`").lower()
        if first in {"入口", "entrypoint"}:
            continue
        if len(cells) < 3:
            errors.append("each 入口覆蓋 row must include an entry, type, and status")
            continue
        entry = cells[0].strip().strip("`")
        status = _normalise_status(cells[2])
        if status not in COVERAGE_STATUSES:
            errors.append(f"入口覆蓋 row has invalid status: {cells[2]}")
            continue
        coverage_entries.append(entry)
        coverage_counts[status] += 1
        if len(cells) < 9:
            errors.append(
                "each 入口覆蓋 row must include transaction/configuration/logic/history statuses, trace, and reason"
            )
            continue
        for index, label in ((0, "entry"), (1, "type"), (7, "trace"), (8, "reason")):
            if not cells[index].strip():
                errors.append(f"入口覆蓋 row is missing {label}")
        for category_cell in cells[3:7]:
            if _normalise_status(category_cell) not in CHECK_CATEGORY_STATUSES:
                errors.append(f"入口覆蓋 row has invalid category status: {category_cell}")
    summary_match = SUMMARY_COVERAGE.search(managed)
    if not summary_match:
        errors.append("結果摘要 must include checked/partial/not checked counts")
    else:
        declared = {
            "checked": int(summary_match.group(1)),
            "partial": int(summary_match.group(2)),
            "not checked": int(summary_match.group(3)),
        }
        if declared != coverage_counts:
            errors.append(
                "入口覆蓋 counts do not match the table: "
                f"declared={declared}, actual={coverage_counts}"
            )

    static_body = _section_body(managed, "靜態交叉檢查")
    static_seen: set[str] = set()
    for line in static_body.splitlines():
        cells = _table_cells(line)
        if cells is None or not cells or _is_separator_row(cells):
            continue
        category = cells[0].strip()
        if category in {"類別", "category"}:
            continue
        category = STATIC_CHECK_ALIASES.get(category, category)
        if category not in STATIC_CHECKS:
            continue
        static_seen.add(category)
        if len(cells) < 3:
            errors.append(f"static check row is missing a result: {category}")
        elif _normalise_status(cells[2]) not in CHECK_CATEGORY_STATUSES:
            errors.append(f"static check row has invalid result: {category}")
        if len(cells) < 4 or not cells[1].strip() or not cells[3].strip():
            errors.append(f"static check row is missing check content or evidence: {category}")
    for category in STATIC_CHECKS:
        if category not in static_seen:
            errors.append(f"static cross-check table missing category: {category}")

    findings = _finding_blocks(managed)
    ids = [finding_id for finding_id, _ in findings]
    duplicates = sorted({finding_id for finding_id in ids if ids.count(finding_id) > 1})
    if duplicates:
        errors.append("duplicate finding ID(s): " + ", ".join(duplicates))
    counts = {"BUG": 0, "RISK": 0, "BIZ": 0}
    for finding_id, body in findings:
        prefix = finding_id.split("-", 1)[0]
        counts[prefix] += 1
        for field in FINDING_FIELDS[prefix]:
            if not _has_field(body, field):
                errors.append(f"{finding_id} missing field: {field}")
        affected = _field_value(body, "受影響入口")
        if _is_empty_value(affected):
            errors.append(f"{finding_id} must name at least one affected entrypoint")
        elif coverage_entries and not any(entry.lower() in affected.lower() for entry in coverage_entries):
            errors.append(f"{finding_id} affected entrypoint is missing from 入口覆蓋")
        elif not coverage_entries:
            errors.append(f"{finding_id} cannot be linked because 入口覆蓋 has no rows")
        historical = _field_value(body, "歷史證據")
        if historical and not _is_empty_value(historical):
            if not FULL_SHA.search(historical):
                errors.append(f"{finding_id} historical evidence must include a full 40-character SHA")
            if not PATH_REFERENCE.search(historical):
                errors.append(f"{finding_id} historical evidence must name a path")
            if not re.search(r"diff|blame|hunk|:[0-9]+", historical, re.IGNORECASE):
                errors.append(f"{finding_id} historical evidence must name a diff/blame location")
    findings_summary = SUMMARY_FINDINGS.search(managed)
    if not findings_summary:
        errors.append("結果摘要 must include defect/risk/business-question counts")
    else:
        declared = {
            "BUG": int(findings_summary.group(1)),
            "RISK": int(findings_summary.group(2)),
            "BIZ": int(findings_summary.group(3)),
        }
        if declared != counts:
            errors.append(
                "finding counts do not match headings: "
                f"declared={declared}, actual={counts}"
            )
    if counts["BUG"] == 0 and "本次已檢查範圍未發現具體缺陷" not in _section_body(managed, "確定缺陷"):
        errors.append("clean defect results must use the required clean-result statement")
    if counts["RISK"] == 0 and "未發現需要技術風險確認的事項" not in _section_body(managed, "技術風險"):
        errors.append("empty risk results must state that no technical risks need confirmation")
    if counts["BIZ"] == 0 and "未發現需要業務確認的事項" not in _section_body(managed, "待確認業務疑點"):
        errors.append("empty business results must state that no business confirmation is needed")

    history = _section_body(managed, "Git 歷史與變更線索")
    for label in (
        "HEAD",
        "工作樹",
        "歷史可用性",
        "歷史查詢範圍",
        "使用的唯讀命令",
        "深入閱讀的 commits",
        "歷史索引限制",
    ):
        if not re.search(rf"(?m)^\s*-\s*{re.escape(label)}\s*[：:]", history):
            errors.append(f"Git history section missing field: {label}")
    availability = HISTORY_AVAILABILITY.search(history)
    if not availability:
        errors.append("Git history section must declare availability")
    elif availability.group(1).lower() in {"available", "shallow"}:
        head_match = re.search(r"(?m)^\s*-\s*HEAD\s*[：:].*?([0-9a-f]{40})", history, re.IGNORECASE)
        if not head_match:
            errors.append("available Git history requires a full 40-character HEAD")
    if availability and availability.group(1).lower() in {"available", "shallow"}:
        for command in ("git rev-parse", "git log", "git show", "git blame"):
            if command not in history:
                errors.append(f"available Git history must record use of {command}")
    elif availability and availability.group(1).lower() in {"unavailable", "not-a-repository"}:
        pass
    elif not any(command in history for command in ("git log", "git show", "git blame")):
        errors.append("Git history section must name a read-only history command or state why unavailable")
    in_commit_table = False
    commit_rows = 0
    for line in history.splitlines():
        cells = _table_cells(line)
        if cells is None:
            continue
        if not cells:
            continue
        first = cells[0].lower()
        if first.startswith(("commit", "sha")):
            in_commit_table = True
            continue
        if not in_commit_table or _is_separator_row(cells):
            continue
        sha = cells[0].strip("`")
        if not FULL_SHA.fullmatch(sha):
            errors.append("every listed historical commit must use a full 40-character SHA")
        commit_rows += 1
        if len(cells) < 5:
            errors.append("every listed historical commit must include intent, diff, and current-result fields")
            continue
        if not cells[1].strip():
            errors.append("every listed historical commit must name a path/diff location")
        elif not PATH_REFERENCE.search(cells[1]):
            errors.append("every listed historical commit must name a path and diff/blame location")
        elif not re.search(r"diff|blame|hunk|@@|:[0-9]+", cells[1], re.IGNORECASE):
            errors.append("every listed historical commit must name a path and diff/blame location")
        if any(not cell.strip() for cell in cells[2:5]):
            errors.append("every listed historical commit must preserve intent, diff, and current behavior")
    if availability and availability.group(1).lower() in {"available", "shallow"}:
        reviewed = _field_value(history, "深入閱讀的 commits").lower()
        if commit_rows == 0 and not _is_empty_value(reviewed):
            errors.append("深入閱讀的 commits must have a full-SHA history table or explicitly state none")
        if availability.group(1).lower() == "shallow" and not re.search(
            r"missing|incomplete|unreviewed|shallow clone|缺少|不完整|遺失|未完整", history, re.IGNORECASE
        ):
            errors.append("shallow Git history must state its missing-history limitation")
    worktree = _field_value(history, "工作樹").lower()
    if "dirty" in worktree and not re.search(
        r"未提交|uncommitted|modified|變更檔案", history, re.IGNORECASE
    ):
        errors.append("dirty worktree must list the uncommitted changes")

    return errors


def main(argv: list[str] | None = None) -> int:
    configure_utf8_stdio()
    parser = argparse.ArgumentParser(
        prog="validate-code-audit.py",
        description="Validate a persisted Codebase audit report without executing target code.",
    )
    parser.add_argument("report", type=Path)
    parser.add_argument("--repo-root", type=Path, default=Path("."))
    parser.add_argument("--format", choices=("text", "json"), default="text")
    args = parser.parse_args(argv)
    if not args.report.is_file():
        errors = [f"report not found: {args.report}"]
    else:
        errors = validate_report(args.report, args.repo_root)
    payload: dict[str, Any] = {"ok": not errors, "report": str(args.report), "issues": errors}
    if args.format == "json":
        print(json.dumps(payload, ensure_ascii=False, indent=2))
    elif errors:
        print("Codebase Audit Validation Report")
        print("=" * 40)
        for error in errors:
            print(f"- {error}")
        print(f"\nFAILED: {len(errors)} issue(s)")
    else:
        print(f"OK: validated Codebase audit report {args.report}")
    return 1 if errors else 0


if __name__ == "__main__":
    raise SystemExit(main())
