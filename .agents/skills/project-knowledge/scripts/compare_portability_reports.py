#!/usr/bin/env python3
"""Compare independently produced Windows and Linux portability reports."""

from __future__ import annotations

import argparse
import json
import math
import re
import sys
from pathlib import Path
from typing import Any, Iterable

from knowledge_benchmark import (
    EXPECTED_FUNCTIONAL_SHA256,
    FILE_COUNT,
    MAX_SECONDS,
    OPERATION_ORDER,
    PAGE_COUNT,
    REPORT_SCHEMA,
    SAMPLE_COUNT,
    TIMING_CONTRACT,
    TIMING_CONTRACT_SHA256,
    evaluate_timing_evidence,
)
from knowledge_governance import canonical_sha256


REQUIRED_OSES = {"windows", "linux"}
SHA256_RE = re.compile(r"[0-9a-f]{64}")
GIT_SHA_RE = re.compile(r"(?:[0-9a-f]{40}|[0-9a-f]{64})")


def _is_non_negative_finite_number(value: object) -> bool:
    return (
        not isinstance(value, bool)
        and isinstance(value, (int, float))
        and math.isfinite(value)
        and value >= 0
    )


def _expected_result_sha256(
    operation_id: str,
    functional: dict[str, Any],
) -> str | None:
    queries = functional.get("queries")
    if not isinstance(queries, list) or len(queries) != 5:
        return None
    if operation_id.startswith("cold_query_"):
        index_text = operation_id.removeprefix("cold_query_")
    elif operation_id.startswith("warm_query_"):
        index_text = operation_id.removeprefix("warm_query_")
    elif operation_id == "index_candidate":
        return canonical_sha256(functional.get("index_candidate"))
    else:
        return None
    if not index_text.isdigit() or int(index_text) >= len(queries):
        return None
    return canonical_sha256(queries[int(index_text)])


def _validate_report(
    report: dict[str, Any],
    os_name: str,
) -> tuple[list[str], dict[str, Any]]:
    diagnostics: list[str] = []
    facts: dict[str, Any] = {
        "functional": None,
        "functional_sha256": None,
        "producer": None,
        "max_observed_seconds": 0.0,
    }

    if report.get("schema") != REPORT_SCHEMA:
        diagnostics.append(f"{os_name}: incompatible report schema")
    measurement_mode = report.get("measurement_mode")
    if measurement_mode is None:
        diagnostics.append(f"{os_name}: measurement mode is missing")
    elif measurement_mode == "controlled":
        diagnostics.append(
            f"{os_name}: controlled report is not admissible for portability comparison"
        )
    elif measurement_mode != "observed":
        diagnostics.append(f"{os_name}: measurement mode is unsupported")
    if report.get("file_count") != FILE_COUNT or report.get("page_count") != PAGE_COUNT:
        diagnostics.append(f"{os_name}: fixture scale drifted")
    if (
        report.get("tracked_fixture") is not True
        or report.get("total_fixture_files") != FILE_COUNT
        or report.get("source_file_count") != FILE_COUNT - (PAGE_COUNT * 2) - 2
    ):
        diagnostics.append(f"{os_name}: fixture is not the reviewed tracked-file shape")
    if report.get("max_operation_seconds") != MAX_SECONDS:
        diagnostics.append(f"{os_name}: operation threshold drifted")
    if report.get("cleanup") != "removed":
        diagnostics.append(f"{os_name}: benchmark fixture cleanup is not complete")

    producer = report.get("producer")
    producer_valid = (
        isinstance(producer, dict)
        and set(producer)
        == {"version", "git_head_sha", "worktree_clean", "script_sha256"}
        and isinstance(producer.get("version"), str)
        and bool(producer.get("version"))
        and isinstance(producer.get("git_head_sha"), str)
        and GIT_SHA_RE.fullmatch(producer["git_head_sha"]) is not None
        and producer.get("worktree_clean") is True
        and isinstance(producer.get("script_sha256"), str)
        and SHA256_RE.fullmatch(producer["script_sha256"]) is not None
    )
    if not producer_valid:
        diagnostics.append(f"{os_name}: producer identity is invalid or not strict-clean")
    else:
        facts["producer"] = producer

    functional = report.get("functional")
    functional_sha256 = report.get("functional_sha256")
    functional_valid = (
        isinstance(functional, dict)
        and isinstance(functional.get("queries"), list)
        and len(functional["queries"]) == 5
        and canonical_sha256(functional) == functional_sha256
        and functional_sha256 == EXPECTED_FUNCTIONAL_SHA256
        and report.get("expected_functional_sha256") == EXPECTED_FUNCTIONAL_SHA256
    )
    if not functional_valid:
        diagnostics.append(f"{os_name}: functional payload or reviewed oracle is invalid")
    else:
        facts["functional"] = functional
        facts["functional_sha256"] = functional_sha256

    functional_queries = functional.get("queries") if isinstance(functional, dict) else None
    query_sha256 = (
        canonical_sha256(functional_queries)
        if isinstance(functional_queries, list)
        else None
    )
    query_hash_contract_valid = (
        isinstance(query_sha256, str)
        and report.get("warm_queries_sha256") == query_sha256
        and report.get("cold_queries_sha256") == query_sha256
    )
    if not query_hash_contract_valid:
        diagnostics.append(f"{os_name}: cold/warm query hash contract is invalid")

    timing = report.get("timing")
    operations = timing.get("operations") if isinstance(timing, dict) else None
    operation_samples: dict[str, list[float]] = {}
    operation_hashes: dict[str, list[str]] = {}
    result_hash_contract_valid = True
    timing_shape_valid = (
        isinstance(timing, dict)
        and timing.get("schema") == "knowledge-timing-decision/v1"
        and timing.get("contract") == TIMING_CONTRACT
        and timing.get("contract_sha256") == TIMING_CONTRACT_SHA256
        and canonical_sha256(timing.get("contract")) == TIMING_CONTRACT_SHA256
        and isinstance(operations, list)
        and [
            operation.get("operation_id") if isinstance(operation, dict) else None
            for operation in operations
        ]
        == list(OPERATION_ORDER)
    )
    if not timing_shape_valid:
        diagnostics.append(f"{os_name}: timing contract or operation order is invalid")
    else:
        assert isinstance(operations, list)
        for operation in operations:
            assert isinstance(operation, dict)
            operation_id = operation["operation_id"]
            samples = operation.get("samples_seconds")
            hashes = operation.get("result_sha256s")
            samples_valid = (
                isinstance(samples, list)
                and len(samples) == SAMPLE_COUNT
                and all(_is_non_negative_finite_number(value) for value in samples)
            )
            hashes_valid = (
                isinstance(hashes, list)
                and len(hashes) == SAMPLE_COUNT
                and all(
                    isinstance(value, str) and SHA256_RE.fullmatch(value) is not None
                    for value in hashes
                )
                and len(set(hashes)) == 1
            )
            expected_hash = (
                _expected_result_sha256(operation_id, functional)
                if isinstance(functional, dict)
                else None
            )
            if not samples_valid:
                diagnostics.append(f"{os_name}: {operation_id} samples are invalid")
            else:
                operation_samples[operation_id] = [float(value) for value in samples]
            if not hashes_valid:
                result_hash_contract_valid = False
                diagnostics.append(f"{os_name}: {operation_id} result hashes are invalid")
            else:
                operation_hashes[operation_id] = list(hashes)
                if expected_hash is None or hashes[0] != expected_hash:
                    result_hash_contract_valid = False
                    diagnostics.append(f"{os_name}: {operation_id} result hashes are invalid")
    if not timing_shape_valid:
        result_hash_contract_valid = False

    recomputed: dict[str, Any] | None = None
    if list(operation_samples) == list(OPERATION_ORDER):
        try:
            recomputed = evaluate_timing_evidence(operation_samples)
        except ValueError:
            diagnostics.append(f"{os_name}: timing evidence cannot be replayed")
        else:
            for operation in recomputed["operations"]:
                operation["result_sha256s"] = operation_hashes.get(
                    operation["operation_id"],
                    [],
                )
            facts["max_observed_seconds"] = max(
                value for samples in operation_samples.values() for value in samples
            )
            if timing != recomputed:
                diagnostics.append(f"{os_name}: asserted timing decision differs from raw evidence")

    durations = report.get("durations_seconds")
    projection_valid = isinstance(durations, dict)
    if projection_valid:
        warm = durations.get("queries")
        cold = durations.get("cold_queries")
        fixture_setup = durations.get("fixture_setup")
        projection_valid = (
            isinstance(warm, list)
            and len(warm) == 5
            and isinstance(cold, list)
            and len(cold) == 5
            and all(_is_non_negative_finite_number(value) for value in [*warm, *cold])
            and _is_non_negative_finite_number(durations.get("index_candidate"))
            and _is_non_negative_finite_number(fixture_setup)
            and list(cold)
            == [operation_samples.get(f"cold_query_{index}", [None])[0] for index in range(5)]
            and list(warm)
            == [operation_samples.get(f"warm_query_{index}", [None])[0] for index in range(5)]
            and durations.get("index_candidate")
            == operation_samples.get("index_candidate", [None])[0]
        )
    if not projection_valid:
        diagnostics.append(f"{os_name}: legacy duration projection is invalid")

    functional_evidence_valid = (
        functional_valid
        and query_hash_contract_valid
        and result_hash_contract_valid
        and list(operation_hashes) == list(OPERATION_ORDER)
    )
    if functional_evidence_valid and recomputed is not None:
        expected_verdict = {
            "sustained-violation": "performance-failure",
            "inconclusive": "inconclusive",
        }.get(recomputed["status"], "pass")
    else:
        expected_verdict = "functional-failure"
    expected_outcome = "passed" if expected_verdict == "pass" else "failed"
    if report.get("verdict") != expected_verdict or report.get("outcome") != expected_outcome:
        diagnostics.append(f"{os_name}: top-level verdict differs from replayed evidence")
    if expected_verdict != "pass":
        diagnostics.append(f"{os_name}: benchmark verdict is not pass")

    return diagnostics, facts


def compare_reports(reports: Iterable[dict[str, Any]]) -> dict[str, Any]:
    values = list(reports)
    diagnostics: list[str] = []
    by_os: dict[str, dict[str, Any]] = {}
    facts_by_os: dict[str, dict[str, Any]] = {}

    if len(values) != len(REQUIRED_OSES):
        diagnostics.append("comparison requires exactly two reports")
    for report in values:
        host = report.get("host") if isinstance(report, dict) else None
        os_name = host.get("os") if isinstance(host, dict) else None
        if os_name not in REQUIRED_OSES:
            diagnostics.append("report has an unsupported or missing host OS")
            continue
        if os_name in by_os:
            diagnostics.append(f"duplicate report for {os_name}")
            continue
        by_os[os_name] = report
        report_diagnostics, facts = _validate_report(report, os_name)
        diagnostics.extend(report_diagnostics)
        facts_by_os[os_name] = facts

    missing = REQUIRED_OSES - set(by_os)
    if missing:
        diagnostics.append(f"missing OS reports: {','.join(sorted(missing))}")

    if set(facts_by_os) == REQUIRED_OSES:
        windows = facts_by_os["windows"]
        linux = facts_by_os["linux"]
        if windows["producer"] != linux["producer"]:
            diagnostics.append("producer identities differ across operating systems")
        if (
            windows["functional_sha256"] != linux["functional_sha256"]
            or windows["functional"] != linux["functional"]
        ):
            diagnostics.append("functional results differ across operating systems")

    functional_hashes = {
        facts["functional_sha256"]
        for facts in facts_by_os.values()
        if isinstance(facts.get("functional_sha256"), str)
    }
    maximum = max(
        (float(facts["max_observed_seconds"]) for facts in facts_by_os.values()),
        default=0.0,
    )
    return {
        "schema": "knowledge-portability-comparison/v2",
        "outcome": "passed" if not diagnostics else "failed",
        "oses": sorted(by_os),
        "functional_sha256": next(iter(functional_hashes), None),
        "max_observed_seconds": maximum,
        "diagnostics": diagnostics,
    }


def main(argv: list[str] | None = None) -> int:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--root", type=Path, required=True)
    args = parser.parse_args(argv)
    paths = sorted(args.root.rglob("knowledge-portability-report-*.json"))
    reports: list[dict[str, Any]] = []
    try:
        for path in paths:
            value = json.loads(path.read_text(encoding="utf-8"))
            if not isinstance(value, dict):
                raise ValueError("report is not an object")
            reports.append(value)
        comparison = compare_reports(reports)
    except (OSError, UnicodeError, json.JSONDecodeError, ValueError):
        comparison = {
            "schema": "knowledge-portability-comparison/v2",
            "outcome": "failed",
            "oses": [],
            "functional_sha256": None,
            "max_observed_seconds": 0.0,
            "diagnostics": ["REPORT_READ_FAILED"],
        }
    print(json.dumps(comparison, ensure_ascii=False, sort_keys=True))
    return 0 if comparison["outcome"] == "passed" else 1


if __name__ == "__main__":
    raise SystemExit(main())
