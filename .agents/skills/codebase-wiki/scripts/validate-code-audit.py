#!/usr/bin/env python3
"""Validate a persisted Codebase audit against the current scanner inventory.

The v4 contract also validates plain-language finding cases.

The validator does not inspect or execute the audited application.  It checks
that a report is internally consistent, that its current ``sources`` exist,
and, for v3/v4 reports, that the recorded scan profile, snapshot, file paths,
categories, and dispositions still match a fresh read-only scanner run.  Git
history claims must also have the evidence shape required by the audit
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

# Keep the v3/v4 report contract aligned with the canonical source-first scanner
# instead of maintaining a second inventory or allowlist here.
from project_scanner import (  # noqa: E402
    EXCLUSION_REASON_TO_CATEGORY,
    REPORT_CATEGORIES,
    ScanError,
    load_scan_settings,
    scan_project,
)


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
    r"(?m)^###\s+((?:BUG|RISK|BIZ)-[0-9]+)\s+[—-]\s+"
    r"(?:\[(P[0-3])\]\s+)?(.+)$"
)
FUNCTION_ID = re.compile(
    r"(?<![A-Za-z0-9._-])FUNC-[A-Za-z0-9][A-Za-z0-9._-]*(?![A-Za-z0-9._-])"
)
RERUN_STATES = {
    "new",
    "still-present",
    "rechecked-no-longer-observed",
    "not-rechecked",
}
FULL_SHA = re.compile(r"(?<![0-9a-f])[0-9a-f]{40}(?![0-9a-f])")
SOURCE_DIGEST = re.compile(r"^sha256:[0-9a-f]{64}$")
SCAN_SNAPSHOT_ID = re.compile(r"^sha256:[0-9a-f]{64}$")
SCAN_PROFILES = {"target", "framework"}
SEVERITY_LEVELS = {"P0": 0, "P1": 1, "P2": 2, "P3": 3}
LEGACY_SEVERITIES = {"high", "medium", "low"}
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
SUMMARY_FUNCTION_COVERAGE = re.compile(
    r"功能覆蓋[^\n]*?checked\s*([0-9]+)[^\n]*?partial\s*([0-9]+)"
    r"[^\n]*?not checked\s*([0-9]+)",
    re.IGNORECASE,
)
SUMMARY_RERUN = re.compile(
    r"finding\s*重跑狀態[^\n]*?new\s*([0-9]+)"
    r"[^\n]*?still-present\s*([0-9]+)"
    r"[^\n]*?rechecked-no-longer-observed\s*([0-9]+)"
    r"[^\n]*?not-rechecked\s*([0-9]+)",
    re.IGNORECASE,
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
V2_REQUIRED_SECTIONS = ("功能 Review",)
V3_REQUIRED_SECTIONS = ("功能 Review", "檔案處置")
FILE_DISPOSITIONS = {"included", "excluded", "read-issue", "analysis-gap", "not-reviewed"}
SCAN_CATEGORIES = REPORT_CATEGORIES

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


def _finding_headings(text: str) -> list[tuple[str, str | None]]:
    """Return finding IDs and optional v4 P0-P3 heading severities."""

    return [(match.group(1), match.group(2)) for match in FINDING_HEADING.finditer(text)]


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


def _has_any_field(body: str, fields: tuple[str, ...]) -> bool:
    return any(_has_field(body, field) for field in fields)


def _cell_value(value: str) -> str:
    """Normalise a Markdown table cell for stable contract checks."""

    return value.strip().strip("`").strip()


def _function_ids(value: str) -> list[str]:
    """Return stable function references from a table cell or finding field."""

    return FUNCTION_ID.findall(value)


def _finding_ids(value: str) -> list[str]:
    return re.findall(r"(?:BUG|RISK|BIZ)-[0-9]+", value)


def _entrypoint_refs(value: str) -> list[str]:
    """Extract one or more entrypoint labels from a function table cell."""

    refs = [item.strip() for item in re.findall(r"`([^`]+)`", value) if item.strip()]
    if not refs:
        refs = [item.strip() for item in re.split(r"[；;,]", value) if item.strip()]
    return [
        item
        for item in refs
        if item.lower() not in {"無", "none", "n/a", "-"}
    ]


def _validate_functional_v2(
    managed: str,
    findings: list[tuple[str, str]],
) -> list[str]:
    """Validate the version-2 function/entrypoint and rerun contract.

    Legacy reports intentionally bypass this function so existing persisted
    reports remain readable and can be upgraded on their next audit run.
    """

    errors: list[str] = []
    function_body = _section_body(managed, "功能 Review")
    function_ids: list[str] = []
    function_rows: list[tuple[str, list[str]]] = []
    for line in function_body.splitlines():
        cells = _table_cells(line)
        if cells is None or not cells or _is_separator_row(cells):
            continue
        if _cell_value(cells[0]).lower() in {"功能 id", "function id"}:
            continue
        if len(cells) < 7:
            errors.append("each 功能 Review row must include ID, entrypoints, status, scenarios, findings, and limits")
            continue
        function_id = _cell_value(cells[0])
        if not FUNCTION_ID.fullmatch(function_id):
            errors.append(f"功能 Review row has invalid function ID: {cells[0]}")
            continue
        if function_id in function_ids:
            errors.append(f"duplicate function ID: {function_id}")
        function_ids.append(function_id)
        status = _normalise_status(cells[3])
        if status not in COVERAGE_STATUSES:
            errors.append(f"功能 Review row has invalid status: {cells[3]}")
        if not _cell_value(cells[1]):
            errors.append(f"功能 Review row is missing a name: {function_id}")
        related_entries = _entrypoint_refs(cells[2])
        if not related_entries:
            errors.append(f"功能 Review row is missing related entrypoints: {function_id}")
        if not _cell_value(cells[4]):
            errors.append(f"功能 Review row is missing checked scenarios: {function_id}")
        referenced_findings = _finding_ids(cells[5])
        function_rows.append((function_id, related_entries))
        if not _cell_value(cells[5]):
            errors.append(f"功能 Review row is missing finding value: {function_id}")
        elif _cell_value(cells[5]).lower() not in {"無", "none", "n/a", "-"}:
            if not referenced_findings:
                errors.append(f"功能 Review row has invalid finding references: {function_id}")
        if not _cell_value(cells[6]):
            errors.append(f"功能 Review row is missing a limitation value: {function_id}")

    function_counts = {"checked": 0, "partial": 0, "not checked": 0}
    for line in function_body.splitlines():
        cells = _table_cells(line)
        if cells is None or len(cells) < 4 or _is_separator_row(cells):
            continue
        if _cell_value(cells[0]).lower() in {"功能 id", "function id"}:
            continue
        status = _normalise_status(cells[3])
        if status in function_counts:
            function_counts[status] += 1
    declared_functions = SUMMARY_FUNCTION_COVERAGE.search(managed)
    if not declared_functions:
        errors.append("結果摘要 must include 功能覆蓋 checked/partial/not checked counts")
    else:
        declared = {
            "checked": int(declared_functions.group(1)),
            "partial": int(declared_functions.group(2)),
            "not checked": int(declared_functions.group(3)),
        }
        if declared != function_counts:
            errors.append(
                "功能覆蓋 counts do not match the table: "
                f"declared={declared}, actual={function_counts}"
            )

    coverage_body = _section_body(managed, "入口覆蓋")
    entrypoints: list[str] = []
    entry_function_refs: dict[str, set[str]] = {}
    for line in coverage_body.splitlines():
        cells = _table_cells(line)
        if cells is None or not cells or _is_separator_row(cells):
            continue
        if _cell_value(cells[0]).lower() in {"功能 id", "function id"}:
            continue
        if len(cells) < 10:
            errors.append("v2 入口覆蓋 rows must include a function ID and all trace columns")
            continue
        refs = _function_ids(cells[0])
        if not refs or any(ref not in function_ids for ref in refs):
            errors.append(f"入口覆蓋 row references an unknown function ID: {cells[0]}")
        entry = _cell_value(cells[1])
        if not entry:
            errors.append("入口覆蓋 row is missing an entrypoint")
            continue
        entrypoints.append(entry)
        entry_function_refs.setdefault(entry, set()).update(refs)
        for category_cell in cells[4:8]:
            if _normalise_status(category_cell) not in CHECK_CATEGORY_STATUSES:
                errors.append(f"入口覆蓋 row has invalid category status: {category_cell}")

    for function_id, related_entries in function_rows:
        for related_entry in related_entries:
            normalized = _cell_value(related_entry)
            if normalized.lower() in {"無", "none", "n/a", "-"}:
                continue
            matching_entries = [
                entry
                for entry in entrypoints
                if normalized == entry or normalized in entry or entry in normalized
            ]
            if not matching_entries:
                errors.append(
                    f"功能 Review entrypoint is missing from 入口覆蓋: {function_id} -> {normalized}"
                )
            elif not any(
                function_id in entry_function_refs.get(entry, set())
                for entry in matching_entries
            ):
                errors.append(
                    "功能 Review function/entrypoint association is missing: "
                    f"{function_id} -> {normalized}"
                )
    for entry, refs in entry_function_refs.items():
        if not refs:
            errors.append(f"入口覆蓋 entrypoint has no function association: {entry}")

    finding_ids = {finding_id for finding_id, _ in findings}
    rerun_counts = {state: 0 for state in RERUN_STATES}
    for finding_id, body in findings:
        rerun_state = _normalise_status(_field_value(body, "重跑狀態"))
        if rerun_state not in RERUN_STATES:
            errors.append(f"{finding_id} has invalid or missing 重跑狀態")
        else:
            rerun_counts[rerun_state] += 1
        affected_functions = _function_ids(_field_value(body, "受影響功能"))
        if not affected_functions:
            errors.append(f"{finding_id} must name at least one affected function")
        elif any(function_id not in function_ids for function_id in affected_functions):
            errors.append(f"{finding_id} affected function is missing from 功能 Review")
        affected_entries = _field_value(body, "受影響入口")
        if not _is_empty_value(affected_entries):
            affected_entry_matches = [
                entry for entry in entrypoints if entry.lower() in affected_entries.lower()
            ]
            if entrypoints and not affected_entry_matches:
                errors.append(f"{finding_id} affected entrypoint is missing from 入口覆蓋")
            for function_id in affected_functions:
                if affected_entry_matches and not any(
                    function_id in entry_function_refs.get(entry, [])
                    for entry in affected_entry_matches
                ):
                    errors.append(
                        f"{finding_id} affected function/entrypoint association is missing: "
                        f"{function_id}"
                    )
        else:
            errors.append(f"{finding_id} must name at least one affected entrypoint")

    rerun_summary = SUMMARY_RERUN.search(managed)
    if not rerun_summary:
        errors.append("結果摘要 must include finding rerun-state counts")
    else:
        declared = {
            "new": int(rerun_summary.group(1)),
            "still-present": int(rerun_summary.group(2)),
            "rechecked-no-longer-observed": int(rerun_summary.group(3)),
            "not-rechecked": int(rerun_summary.group(4)),
        }
        if declared != rerun_counts:
            errors.append(
                "finding rerun-state counts do not match headings: "
                f"declared={declared}, actual={rerun_counts}"
            )

    # Ensure function rows do not point at findings that are absent from the report.
    for function_id, _ in function_rows:
        row_text = next(
            (
                line
                for line in function_body.splitlines()
                if line.startswith("|") and function_id in line
            ),
            "",
        )
        for referenced in _finding_ids(row_text):
            if referenced not in finding_ids:
                errors.append(f"{function_id} references unknown finding ID: {referenced}")

    return errors


def _validate_v4_findings(
    managed: str,
    findings: list[tuple[str, str]],
) -> list[str]:
    """Validate the MergeReviewer-inspired evidence and severity contract."""

    errors: list[str] = []
    headings = _finding_headings(managed)
    if len(headings) != len(findings):
        errors.append("v4 finding headings and finding blocks do not match")
        return errors

    by_class: dict[str, list[tuple[int, str, str | None, str]]] = {
        "BUG": [],
        "RISK": [],
        "BIZ": [],
    }
    for (finding_id, body), (heading_id, severity) in zip(findings, headings):
        if finding_id != heading_id:
            errors.append(f"v4 finding heading does not match block: {finding_id}")
            continue
        prefix = finding_id.split("-", 1)[0]
        rerun_state = _normalise_status(_field_value(body, "重跑狀態"))
        carried_forward = rerun_state == "not-rechecked"
        if severity is None:
            if not carried_forward:
                errors.append(
                    f"{finding_id} must include a [P0], [P1], [P2], or [P3] heading severity"
                )
            # A carried-forward v3 finding may retain high/medium/low text.
            legacy_impact = _field_value(body, "影響程度") or _field_value(body, "可能影響程度")
            if carried_forward and not any(
                level in legacy_impact.lower() for level in LEGACY_SEVERITIES
            ):
                errors.append(f"{finding_id} retained finding must preserve its legacy severity")
            by_class[prefix].append((99, finding_id, None, rerun_state))
        else:
            impact_field = "可能影響程度" if prefix == "BIZ" else "影響程度"
            impact = _field_value(body, impact_field)
            if not re.search(rf"\b{re.escape(severity)}\b", impact):
                errors.append(
                    f"{finding_id} heading severity {severity} must agree with {impact_field}"
                )
            rank = 99 if carried_forward else SEVERITY_LEVELS[severity]
            by_class[prefix].append((rank, finding_id, severity, rerun_state))

        # Historical findings that were not rechecked retain their original
        # text and severity.  Do not force a newly invented example onto them.
        if carried_forward:
            continue

        certainty = _normalise_status(_field_value(body, "證據確定度"))
        expected_certainty = "confirmed" if prefix == "BUG" else "unresolved"
        if expected_certainty not in certainty:
            errors.append(
                f"{finding_id} {prefix} finding must preserve evidence certainty {expected_certainty}"
            )

        if not _has_field(body, "白話說明"):
            errors.append(f"{finding_id} missing field: 白話說明")
        if not _has_field(body, "具體案例"):
            errors.append(f"{finding_id} missing field: 具體案例")

        # Every case distinguishes what was supplied, what should happen, and
        # what the current source can produce. RISK/BIZ use conditional wording.
        if not _has_any_field(body, ("操作／輸入", "操作或輸入", "情境／輸入", "前提／輸入")):
            errors.append(f"{finding_id} missing case input/operation field")
        if not _has_any_field(body, ("預期結果", "條件式預期結果", "預期行為")):
            errors.append(f"{finding_id} missing case expected-result field")
        result_fields = ("可能結果", "實際結果", "政策差異") if prefix != "BUG" else ("實際結果",)
        if not _has_any_field(body, result_fields):
            errors.append(f"{finding_id} missing case result field")
        if not re.search(
            r"具體案例[^\n]*?(?:未實際執行|依程式推導|示意)",
            body,
        ):
            errors.append(
                f"{finding_id} 具體案例 must state that it is code-derived or not executed"
            )
        if prefix == "RISK" and not _has_field(body, "成立條件"):
            errors.append(f"{finding_id} missing field: 成立條件")
        if prefix == "RISK":
            if not re.search(
                r"(?m)^\s*-\s*(?:預期結果|條件式預期結果)[^\n]*(?:條件|不成立)",
                body,
            ):
                errors.append(f"{finding_id} RISK case must state a conditional expected result")
            if not re.search(r"(?m)^\s*-\s*可能結果[^\n]*(?:條件|成立)", body):
                errors.append(f"{finding_id} RISK case must state a conditional possible result")
        if prefix == "BIZ" and not _has_field(body, "確認不同答案可能造成的差異"):
            errors.append(f"{finding_id} missing field: 確認不同答案可能造成的差異")
        if prefix == "BIZ":
            if not re.search(r"(?m)^\s*-\s*預期結果[^\n]*政策答案\s*A", body):
                errors.append(f"{finding_id} BIZ case must state policy answer A")
            if not re.search(r"(?m)^\s*-\s*(?:政策差異|預期結果)[^\n]*政策答案\s*B", body):
                errors.append(f"{finding_id} BIZ case must state policy answer B")

    for prefix, entries in by_class.items():
        previous = -1
        for rank, finding_id, severity, _ in entries:
            if rank < previous:
                errors.append(
                    f"{prefix} findings must be ordered P0 to P3; {finding_id} is out of order"
                )
            previous = rank
    return errors


# v4 reports document a merge commit parent review in the Git-history section;
# the marker is intentionally explicit so a reviewer can distinguish it from a
# generic commit table.


def _validate_merge_parent_review(history: str) -> list[str]:
    """Validate merge-parent rows when a v4 report records any merge commit."""

    errors: list[str] = []
    if re.search(r"沒有 merge commit|no merge commit", history, re.IGNORECASE):
        return errors
    marker = re.search(r"(?im)^###\s+Merge parent 核對\s*$", history)
    if not marker:
        return errors
    review = history[marker.end() :]
    rows_seen = 0
    for line in review.splitlines():
        cells = _table_cells(line)
        if cells is None or not cells or _is_separator_row(cells):
            continue
        if cells[0].strip().lower().startswith("merge commit"):
            continue
        if len(cells) < 7:
            errors.append("Merge parent 核對 rows must include merge SHA, every parent, path, side behavior, merge result, and current-source result")
            continue
        rows_seen += 1
        for index, label in ((0, "merge"), (1, "parent-1")):
            if not FULL_SHA.fullmatch(cells[index].strip().strip("`")):
                errors.append(f"Merge parent 核對 {label} must use a full 40-character SHA")
        # Parent-2 may contain additional parent SHAs in the same cell.
        if not FULL_SHA.search(cells[2]):
            errors.append("Merge parent 核對 parent-2 must list at least one full 40-character SHA")
        if not cells[3].strip() or not PATH_REFERENCE.search(cells[3]):
            errors.append("Merge parent 核對 must name an affected path and diff/blame location")
        if any(not cell.strip() for cell in cells[4:7]):
            errors.append("Merge parent 核對 must preserve both-side behavior, merge result, and current-source result")
    if rows_seen == 0:
        errors.append("Merge parent 核對 must contain a merge row or explicitly state no merge commit")
    return errors


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


def _parse_file_disposition_rows(body: str) -> tuple[list[dict[str, str]], list[str]]:
    rows: list[dict[str, str]] = []
    errors: list[str] = []
    seen_paths: set[str] = set()
    for line in body.splitlines():
        cells = _table_cells(line)
        if cells is None or not cells or _is_separator_row(cells):
            continue
        if cells[0].strip().lower() in {"path", "檔案", "路徑"}:
            continue
        if len(cells) < 4:
            errors.append(
                "檔案處置 row must include path, category, disposition, and function/process link"
            )
            continue
        path_value = _cell_value(cells[0])
        normalized_path = path_value.replace("\\", "/")
        if normalized_path in seen_paths:
            errors.append(f"檔案處置 contains duplicate path: {normalized_path}")
        seen_paths.add(normalized_path)
        category = _cell_value(cells[1])
        if category not in SCAN_CATEGORIES:
            errors.append(f"檔案處置 row has invalid scanner category: {cells[1]}")
        disposition = _normalise_status(cells[2])
        if disposition not in FILE_DISPOSITIONS:
            errors.append(f"檔案處置 row has invalid disposition: {cells[2]}")
        if not path_value or not category or not _cell_value(cells[3]):
            errors.append("檔案處置 row is missing path, category, or function/process link")
        rows.append(
            {
                "path": normalized_path,
                "category": category,
                "disposition": disposition,
                "association": _cell_value(cells[3]),
            }
        )
    if not rows:
        errors.append("檔案處置 must contain at least one file row")
    return rows, errors


def _scanner_bound_errors(
    repo_root: Path,
    scan_profile: str,
    expected_snapshot_id: str,
    rows: list[dict[str, str]],
) -> list[str]:
    try:
        settings = load_scan_settings(repo_root, scan_profile)
        scan = scan_project(repo_root, settings, ())
    except (OSError, ScanError, UnicodeError) as exc:
        return [f"unable to rebuild scanner inventory: {exc}"]

    errors: list[str] = []
    actual_by_path: dict[str, dict[str, str]] = {}
    for row in rows:
        path = row["path"]
        if _source_path(repo_root, path) is None:
            errors.append(f"檔案處置 row has an unsafe or invalid path: {path}")
            continue
        actual_by_path[path] = row

    expected_by_path: dict[str, dict[str, str]] = {}
    for item in scan["included"]:
        expected_by_path[item["path"]] = {
            "category": item["category"],
            "kind": "included",
        }
    for item in scan["excluded"]:
        path = item["path"]
        category = EXCLUSION_REASON_TO_CATEGORY.get(item["reason"])
        if category is None:
            errors.append(f"scanner returned an unknown exclusion reason: {item['reason']}")
            continue
        expected_by_path[path] = {
            "category": category,
            "kind": "excluded",
        }

    expected_paths = set(expected_by_path)
    actual_paths = set(actual_by_path)
    missing = sorted(expected_paths - actual_paths)
    extra = sorted(actual_paths - expected_paths)
    if missing:
        suffix = " ..." if len(missing) > 10 else ""
        errors.append(
            "檔案處置 is missing scanner file rows: "
            + ", ".join(missing[:10])
            + suffix
        )
    if extra:
        suffix = " ..." if len(extra) > 10 else ""
        errors.append(
            "檔案處置 contains paths absent from scanner inventory: "
            + ", ".join(extra[:10])
            + suffix
        )

    for path in sorted(expected_paths & actual_paths):
        expected = expected_by_path[path]
        actual = actual_by_path[path]
        if actual["category"] != expected["category"]:
            errors.append(
                f"檔案處置 category mismatch for {path}: "
                f"expected {expected['category']}, got {actual['category']}"
            )
        allowed = (
            {"included", "analysis-gap", "not-reviewed"}
            if expected["kind"] == "included"
            else {"excluded", "read-issue"}
        )
        if actual["disposition"] not in allowed:
            errors.append(
                f"檔案處置 disposition mismatch for {path}: "
                f"expected one of {sorted(allowed)}, got {actual['disposition']}"
            )

    actual_scan_profile = scan.get("scan_profile")
    if actual_scan_profile != scan_profile:
        errors.append(
            f"scanner profile mismatch: expected {scan_profile}, got {actual_scan_profile}"
        )
    actual_snapshot_id = scan.get("snapshot_id")
    if actual_snapshot_id != expected_snapshot_id:
        errors.append(
            "scan_snapshot_id does not match the current scanner inventory: "
            f"expected {actual_snapshot_id}, got {expected_snapshot_id}"
        )
    return errors


def validate_report(report_path: Path, repo_root: Path) -> list[str]:
    errors: list[str] = []
    try:
        text = report_path.read_text(encoding="utf-8")
    except (OSError, UnicodeError) as exc:
        return [f"cannot read report: {exc}"]

    frontmatter = parse_frontmatter_text(text)
    report_version = frontmatter.get("audit_report_version")
    version_text = str(report_version).strip() if report_version is not None else ""
    is_v4 = version_text == "4"
    is_v3 = version_text in {"3", "4"}
    is_v2 = version_text in {"2", "3", "4"}
    scan_profile: str | None = None
    scan_snapshot_id: str | None = None
    if report_version is not None and version_text not in {"2", "3", "4"}:
        errors.append("audit_report_version must be integer 2, 3, or 4 when present")
    if is_v3:
        scan_schema = frontmatter.get("scan_schema_version")
        if str(scan_schema).strip() != "2":
            errors.append("scan_schema_version must be integer 2 for audit report v3/v4")
        raw_scan_profile = frontmatter.get("scan_profile")
        if not isinstance(raw_scan_profile, str) or raw_scan_profile not in SCAN_PROFILES:
            errors.append("scan_profile must be 'target' or 'framework' for audit report v3/v4")
        else:
            scan_profile = raw_scan_profile
        snapshot_id = frontmatter.get("scan_snapshot_id")
        if not isinstance(snapshot_id, str) or not SCAN_SNAPSHOT_ID.fullmatch(snapshot_id):
            errors.append("scan_snapshot_id must use sha256:<64 lowercase hex>")
        else:
            scan_snapshot_id = snapshot_id
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
        if first in {"入口", "entrypoint", "功能 id", "function id"}:
            continue
        required_columns = 10 if is_v2 else 9
        if len(cells) < (4 if is_v2 else 3):
            errors.append("each 入口覆蓋 row must include an entry, type, and status")
            continue
        entry_index = 1 if is_v2 else 0
        status_index = 3 if is_v2 else 2
        entry = cells[entry_index].strip().strip("`")
        status = _normalise_status(cells[status_index])
        if status not in COVERAGE_STATUSES:
            errors.append(f"入口覆蓋 row has invalid status: {cells[status_index]}")
            continue
        coverage_entries.append(entry)
        coverage_counts[status] += 1
        if len(cells) < required_columns:
            errors.append(
                "each 入口覆蓋 row must include transaction/configuration/logic/history statuses, trace, and reason"
            )
            continue
        required_fields = (
            ((0, "function"), (1, "entry"), (2, "type"), (8, "trace"), (9, "reason"))
            if is_v2
            else ((0, "entry"), (1, "type"), (7, "trace"), (8, "reason"))
        )
        for index, label in required_fields:
            if not cells[index].strip():
                errors.append(f"入口覆蓋 row is missing {label}")
        category_start, category_end = (4, 8) if is_v2 else (3, 7)
        for category_cell in cells[category_start:category_end]:
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
    if is_v2:
        required_sections = V3_REQUIRED_SECTIONS if is_v3 else V2_REQUIRED_SECTIONS
        for section in required_sections:
            if not re.search(rf"(?m)^##\s+{re.escape(section)}\s*$", managed):
                errors.append(f"missing required section: {section}")
        errors.extend(_validate_functional_v2(managed, findings))
    if is_v3:
        disposition_body = _section_body(managed, "檔案處置")
        disposition_rows, disposition_errors = _parse_file_disposition_rows(disposition_body)
        errors.extend(disposition_errors)
        if scan_profile is not None and scan_snapshot_id is not None:
            errors.extend(
                _scanner_bound_errors(
                    repo_root,
                    scan_profile,
                    scan_snapshot_id,
                    disposition_rows,
                )
            )
    if is_v4:
        errors.extend(_validate_v4_findings(managed, findings))
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
    if is_v4 and not re.search(
        r"Merge parent 核對|merge parent|no merge commit|沒有 merge",
        history,
        re.IGNORECASE,
    ):
        errors.append("v4 Git history section must record merge parent review or state that no merge commit was in scope")
    if is_v4:
        errors.extend(_validate_merge_parent_review(history))
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
        if re.match(r"^###\s+Merge parent 核對\s*$", line.strip(), re.IGNORECASE):
            in_commit_table = False
            continue
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
