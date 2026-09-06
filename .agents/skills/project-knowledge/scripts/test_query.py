#!/usr/bin/env python3
"""Focused inner tests for query and context contracts."""

from __future__ import annotations

import argparse
import contextlib
import hashlib
import io
import json
import os
import shutil
import subprocess
import sys
import unittest
from unittest import mock
from pathlib import Path


SCRIPT_DIR = Path(__file__).resolve().parent
if str(SCRIPT_DIR) not in sys.path:
    sys.path.insert(0, str(SCRIPT_DIR))

from knowledge_cli import main as knowledge_main
from test_behavior import (
    _build_golden_fixture,
    _build_query_performance_fixture,
    _build_retrieval_fixture,
    _evaluate_golden,
    _remove_fixture,
    _synthetic_portability_report,
    _tree_snapshot,
)


class QueryCliTests(unittest.TestCase):
    fixture_root: Path

    def setUp(self) -> None:
        self.repo = _build_retrieval_fixture(self.fixture_root)

    def tearDown(self) -> None:
        _remove_fixture(self.fixture_root)

    def _invoke(self, arguments: list[str]) -> tuple[int, str, str]:
        stdout = io.StringIO()
        stderr = io.StringIO()
        with contextlib.redirect_stdout(stdout), contextlib.redirect_stderr(stderr):
            exit_code = knowledge_main(arguments)
        return exit_code, stdout.getvalue(), stderr.getvalue()

    def test_query_returns_closed_context_without_writes(self) -> None:
        before = _tree_snapshot(self.repo)
        exit_code, stdout, stderr = self._invoke(
            [
                "query",
                "--repo",
                str(self.repo),
                "--stage",
                "ad-hoc",
                "--query",
                "capability token",
            ]
        )
        self.assertEqual(0, exit_code)
        self.assertEqual("", stderr)
        context = json.loads(stdout)
        self.assertEqual(
            {"schema", "stage", "query", "results", "diagnostics", "generated_at"},
            set(context),
        )
        self.assertEqual("knowledge-context/v1", context["schema"])
        self.assertLessEqual(len(context["results"]), 5)
        self.assertEqual(before, _tree_snapshot(self.repo))

    def test_invalid_query_returns_versioned_error(self) -> None:
        exit_code, stdout, stderr = self._invoke(
            [
                "query",
                "--repo",
                str(self.repo),
                "--stage",
                "ad-hoc",
                "--query",
                "   ",
            ]
        )
        self.assertEqual(2, exit_code)
        self.assertEqual("", stdout)
        error = json.loads(stderr)
        self.assertEqual(
            {"schema", "code", "message", "evidence_refs", "recoverable"},
            set(error),
        )
        self.assertEqual("knowledge-error/v1", error["schema"])
        self.assertEqual("INVALID_QUERY", error["code"])
        self.assertFalse(error["recoverable"])

    def test_ranking_uses_authority_and_stage_without_recency(self) -> None:
        exit_code, stdout, stderr = self._invoke(
            [
                "query",
                "--repo",
                str(self.repo),
                "--stage",
                "requirements",
                "--query",
                "capability token",
            ]
        )
        self.assertEqual(0, exit_code)
        self.assertEqual("", stderr)
        results = json.loads(stdout)["results"]
        self.assertGreaterEqual(len(results), 2)
        self.assertEqual("canonical", results[0]["authority"])
        self.assertEqual(1260, results[0]["score"])
        self.assertIn("stage:requirements", results[0]["match_reasons"])
        self.assertTrue(all(item["lifecycle"] == "current" for item in results))
        self.assertGreater(results[0]["score"], results[-1]["score"])

    def test_golden_evaluator_enforces_recall_and_citations(self) -> None:
        repo, cases = _build_golden_fixture(self.fixture_root)
        report = _evaluate_golden(repo, cases)
        self.assertEqual(20, report["queries"])
        self.assertGreaterEqual(report["top_five_hits"], 18)
        self.assertEqual(report["citation_count"], report["valid_citations"])
        self.assertEqual(0, report["ineligible_hits"])

    def test_current_claim_source_drift_is_excluded_without_aborting_query(self) -> None:
        source = self.repo / "src/stale-boundary.md"
        source.write_text("Changed current claim source.\n", encoding="utf-8", newline="\n")
        exit_code, stdout, stderr = self._invoke(
            [
                "query",
                "--repo",
                str(self.repo),
                "--stage",
                "requirements",
                "--query",
                "stale capability token",
            ]
        )
        self.assertEqual(0, exit_code, stderr)
        self.assertEqual("", stderr)
        self.assertNotIn(
            "docs/knowledge/incidents/stale-capability-token.md",
            {item["path"] for item in json.loads(stdout)["results"]},
        )

    def test_same_query_cache_is_read_only_and_invalidates_on_byte_drift(self) -> None:
        import knowledge_query

        arguments = [
            "query",
            "--repo",
            str(self.repo),
            "--stage",
            "requirements",
            "--query",
            "capability token",
        ]
        first = self._invoke(arguments)
        self.assertEqual(0, first[0], first[2])
        with mock.patch("knowledge_query._run", wraps=knowledge_query._run) as observed:
            second = self._invoke(arguments)
        self.assertEqual(0, second[0], second[2])
        self.assertEqual(json.loads(first[1])["results"], json.loads(second[1])["results"])
        self.assertFalse(
            any(call.args[0][0] == "rg" for call in observed.call_args_list),
            "same repository bytes and query should reuse the process-local match index",
        )

        source = self.repo / "src/security-boundary.md"
        source.write_text(
            "Capability tokens define the changed authorization boundary.\n",
            encoding="utf-8",
            newline="\n",
        )
        with mock.patch("knowledge_query._run", wraps=knowledge_query._run) as invalidated:
            third = self._invoke(arguments)
        self.assertEqual(0, third[0], third[2])
        self.assertTrue(
            any(call.args[0][0] == "rg" for call in invalidated.call_args_list),
            "tracked byte drift must invalidate cached matches",
        )

    def test_cache_hit_rejects_drift_after_fingerprint_before_source_read(self) -> None:
        import knowledge_query

        arguments = [
            "query",
            "--repo",
            str(self.repo),
            "--stage",
            "requirements",
            "--query",
            "capability token",
        ]
        warmed = self._invoke(arguments)
        self.assertEqual(0, warmed[0], warmed[2])

        source = self.repo / "src/security-boundary.md"
        original_capture = knowledge_query._capture_match_cache_snapshot
        drift_injected = False

        def snapshot_then_drift(
            repo: Path,
            cached: object,
        ) -> object:
            nonlocal drift_injected
            snapshot = original_capture(repo, cached)
            if not drift_injected:
                source.write_text(
                    "Unrelated prefix.\n"
                    "Capability tokens define the authorization boundary.\n",
                    encoding="utf-8",
                    newline="\n",
                )
                drift_injected = True
            return snapshot

        with mock.patch(
            "knowledge_query._capture_match_cache_snapshot",
            side_effect=snapshot_then_drift,
        ):
            exit_code, stdout, stderr = self._invoke(arguments)

        self.assertTrue(drift_injected)
        self.assertEqual(3, exit_code, stderr)
        self.assertEqual("", stdout)
        error = json.loads(stderr)
        self.assertEqual("SOURCE_DRIFT", error["code"])
        self.assertTrue(error["recoverable"])

    def test_cache_hit_rejects_sidecar_drift_before_return(self) -> None:
        import knowledge_query

        arguments = [
            "query",
            "--repo",
            str(self.repo),
            "--stage",
            "requirements",
            "--query",
            "capability token",
        ]
        warmed = self._invoke(arguments)
        self.assertEqual(0, warmed[0], warmed[2])
        self.assertTrue(
            any(item["authority"] == "canonical" for item in json.loads(warmed[1])["results"])
        )

        sidecar_path = (
            self.repo
            / "docs"
            / "knowledge"
            / "meta"
            / "pages"
            / "page-security-capability-token.json"
        )
        original_validator = knowledge_query._validate_result_snapshot
        drift_injected = False

        def drift_sidecar_then_validate(*args: object, **kwargs: object) -> None:
            nonlocal drift_injected
            sidecar = json.loads(sidecar_path.read_text(encoding="utf-8"))
            sidecar["lifecycle"] = "stale"
            sidecar["claims"][0]["lifecycle"] = "stale"
            sidecar_path.write_text(
                json.dumps(sidecar, ensure_ascii=False, sort_keys=True, indent=2) + "\n",
                encoding="utf-8",
                newline="\n",
            )
            drift_injected = True
            original_validator(*args, **kwargs)

        with mock.patch(
            "knowledge_query._validate_result_snapshot",
            side_effect=drift_sidecar_then_validate,
        ):
            exit_code, stdout, stderr = self._invoke(arguments)

        self.assertTrue(drift_injected)
        self.assertEqual(3, exit_code, stderr)
        self.assertEqual("", stdout)
        error = json.loads(stderr)
        self.assertEqual("SOURCE_DRIFT", error["code"])
        self.assertTrue(error["recoverable"])

    def test_redirected_parent_is_ineligible_for_query_reads(self) -> None:
        tracked_parent = self.repo / "src/redirected-parent"
        tracked_source = tracked_parent / "external.md"
        tracked_parent.mkdir(parents=True)
        tracked_source.write_text("Redirected evidence token.\n", encoding="utf-8", newline="\n")
        from test_behavior import _git

        _git(self.repo, "add", ".")
        external = self.fixture_root / "redirect-target"
        external.mkdir(parents=True)
        (external / "external.md").write_text(
            "Redirected evidence token.\n",
            encoding="utf-8",
            newline="\n",
        )
        shutil.rmtree(tracked_parent)
        try:
            os.symlink(external, tracked_parent, target_is_directory=True)
        except (OSError, NotImplementedError) as exc:
            if os.name != "nt":
                self.fail(f"REPARSE_CAPABILITY_REQUIRED: {exc}")
            powershell = shutil.which("pwsh") or shutil.which("powershell")
            if powershell is None:
                self.fail(f"REPARSE_CAPABILITY_REQUIRED: {exc}")
            completed = subprocess.run(
                [
                    powershell,
                    "-NoLogo",
                    "-NoProfile",
                    "-NonInteractive",
                    "-Command",
                    (
                        "$ErrorActionPreference='Stop'; "
                        "New-Item -ItemType Junction "
                        "-Path $env:KNOWLEDGE_TEST_LINK "
                        "-Target $env:KNOWLEDGE_TEST_TARGET "
                        "| Out-Null"
                    ),
                ],
                stdout=subprocess.PIPE,
                stderr=subprocess.PIPE,
                check=False,
                env={
                    **os.environ,
                    "KNOWLEDGE_TEST_LINK": str(tracked_parent),
                    "KNOWLEDGE_TEST_TARGET": str(external),
                },
                shell=False,
            )
            if completed.returncode != 0:
                detail = completed.stderr.decode("utf-8", errors="replace").strip()
                self.fail(f"REPARSE_CAPABILITY_REQUIRED: {detail or exc}")
        try:
            from knowledge_query import KnowledgeError, _eligible_paths, _read_eligible

            eligible = _eligible_paths(self.repo)
            self.assertNotIn("src/redirected-parent/external.md", eligible)
            with self.assertRaises(KnowledgeError) as raised:
                _read_eligible(self.repo, "src/redirected-parent/external.md", eligible)
            self.assertEqual("SOURCE_INELIGIBLE", raised.exception.code)
        finally:
            is_junction = getattr(tracked_parent, "is_junction", lambda: False)
            self.assertTrue(tracked_parent.is_symlink() or is_junction())
            self.assertEqual(external.resolve(strict=True), tracked_parent.resolve(strict=True))
            if tracked_parent.is_symlink():
                tracked_parent.unlink()
            else:
                os.rmdir(tracked_parent)
            self.assertFalse(tracked_parent.exists())
            self.assertTrue((external / "external.md").is_file())


class PerformanceTests(unittest.TestCase):
    fixture_root: Path

    def setUp(self) -> None:
        self.repo = _build_query_performance_fixture(self.fixture_root)

    def tearDown(self) -> None:
        _remove_fixture(self.fixture_root)

    def _invoke(self, arguments: list[str]) -> tuple[int, str, str]:
        stdout = io.StringIO()
        stderr = io.StringIO()
        with contextlib.redirect_stdout(stdout), contextlib.redirect_stderr(stderr):
            exit_code = knowledge_main(arguments)
        return exit_code, stdout.getvalue(), stderr.getvalue()

    def test_timing_decision_uses_the_closed_three_sample_contract(self) -> None:
        import knowledge_benchmark

        self.assertTrue(
            hasattr(knowledge_benchmark, "classify_operation"),
            "the approved public timing-decision seam is missing",
        )
        classify = knowledge_benchmark.classify_operation
        cases = (
            ([0.1, 0.2, 2.0], 0, "within-threshold"),
            ([0.1, 2.001, 0.2], 1, "isolated-outlier"),
            ([2.001, 0.2, 2.1], 2, "mixed-inconclusive"),
            ([2.001, 2.1, 2.2], 3, "sustained-violation"),
        )
        for samples, breach_count, classification in cases:
            with self.subTest(classification=classification):
                decisions = [classify(samples) for _ in range(10)]
                self.assertEqual([decisions[0]] * 10, decisions)
                self.assertEqual(samples, decisions[0]["samples_seconds"])
                self.assertEqual(sorted(samples)[1], decisions[0]["median_seconds"])
                self.assertEqual(breach_count, decisions[0]["breach_count"])
                self.assertEqual(classification, decisions[0]["classification"])

        for invalid in (
            [0.1, 0.2],
            [0.1, 0.2, True],
            [0.1, 0.2, float("nan")],
            [0.1, 0.2, float("inf")],
            [0.1, 0.2, -0.1],
        ):
            with self.subTest(invalid=invalid), self.assertRaises(ValueError):
                classify(invalid)

    def test_benchmark_cli_preserves_output_and_safe_environment_errors(self) -> None:
        import knowledge_benchmark

        report = {
            "schema": "knowledge-portability-report/v3",
            "measurement_mode": "observed",
            "outcome": "passed",
            "verdict": "pass",
            "cleanup": "removed",
        }
        output = self.fixture_root / "saved-report.json"
        expected = json.dumps(report, ensure_ascii=False, sort_keys=True) + "\n"
        stdout = io.StringIO()
        stderr = io.StringIO()
        with (
            mock.patch(
                "knowledge_benchmark.run_benchmark",
                return_value=report,
            ) as benchmark,
            contextlib.redirect_stdout(stdout),
            contextlib.redirect_stderr(stderr),
        ):
            exit_code = knowledge_benchmark.main(["--output", str(output)])
        self.assertEqual(0, exit_code)
        self.assertEqual(expected, stdout.getvalue())
        self.assertEqual("", stderr.getvalue())
        self.assertEqual(expected.encode("utf-8"), output.read_bytes())
        benchmark.assert_called_once_with(
            Path(".knowledge-test-tmp"),
            reuse_fixture=False,
            keep_fixture=False,
        )

        with (
            self.assertRaises(SystemExit) as unsupported,
            contextlib.redirect_stderr(io.StringIO()),
        ):
            knowledge_benchmark.main(["--controlled-operation-samples", "{}"])
        self.assertEqual(2, unsupported.exception.code)

        stdout = io.StringIO()
        stderr = io.StringIO()
        with (
            mock.patch("knowledge_benchmark.run_benchmark", return_value=report),
            contextlib.redirect_stdout(stdout),
            contextlib.redirect_stderr(stderr),
        ):
            exit_code = knowledge_benchmark.main(["--output", str(output)])
        self.assertEqual(4, exit_code)
        self.assertEqual("", stdout.getvalue())
        error = json.loads(stderr.getvalue())
        self.assertEqual("knowledge-portability-error/v2", error["schema"])
        self.assertEqual("environment-error", error["verdict"])
        self.assertEqual("report-output", error["category"])
        self.assertNotIn(str(output), stderr.getvalue())
        self.assertEqual(expected.encode("utf-8"), output.read_bytes())

        failures = (
            (FileNotFoundError("token=secret-value"), "dependency"),
            (subprocess.TimeoutExpired(["secret-command"], 30), "timeout"),
            (ValueError("C:/private/fixture"), "fixture"),
            (RuntimeError("password=secret-value"), "process"),
            (
                knowledge_benchmark.BenchmarkEnvironmentError(
                    "cleanup",
                    "BENCHMARK_CLEANUP_FAILED",
                    "Remove the bounded temporary fixture before retrying.",
                    cleanup="failed",
                ),
                "cleanup",
            ),
        )
        for failure, category in failures:
            with self.subTest(category=category):
                stdout = io.StringIO()
                stderr = io.StringIO()
                with (
                    mock.patch("knowledge_benchmark.run_benchmark", side_effect=failure),
                    contextlib.redirect_stdout(stdout),
                    contextlib.redirect_stderr(stderr),
                ):
                    exit_code = knowledge_benchmark.main([])
                self.assertEqual(4, exit_code)
                self.assertEqual("", stdout.getvalue())
                error = json.loads(stderr.getvalue())
                self.assertEqual(category, error["category"])
                self.assertEqual("failed", error["outcome"])
                self.assertNotIn("secret-value", stderr.getvalue())
                self.assertNotIn("private", stderr.getvalue())

        failed_report = dict(report, outcome="failed", verdict="inconclusive")
        stdout = io.StringIO()
        stderr = io.StringIO()
        with (
            mock.patch("knowledge_benchmark.run_benchmark", return_value=failed_report),
            contextlib.redirect_stdout(stdout),
            contextlib.redirect_stderr(stderr),
        ):
            exit_code = knowledge_benchmark.main([])
        self.assertEqual(1, exit_code)
        self.assertEqual("", stderr.getvalue())
        self.assertEqual(failed_report, json.loads(stdout.getvalue()))

    def test_benchmark_functional_drift_precedes_timing_and_cleanup_failure(self) -> None:
        import knowledge_benchmark

        real_normalize = knowledge_benchmark._normalized_query_result
        normalization_count = 0

        def drifting_normalize(query: str, report: dict[str, object]) -> dict[str, object]:
            nonlocal normalization_count
            normalization_count += 1
            value = real_normalize(query, report)
            if normalization_count == 2:
                value = dict(value)
                value["query"] = f"{query}-drift"
            return value

        _remove_fixture(self.fixture_root)
        with (
            mock.patch.object(knowledge_benchmark, "FILE_COUNT", 250),
            mock.patch.object(knowledge_benchmark, "PAGE_COUNT", 20),
            mock.patch.object(
                knowledge_benchmark,
                "EXPECTED_FUNCTIONAL_SHA256",
                "6310a73a73d1beb175615d927b429bce350694a95a131a1c68356a69d9f6ba32",
            ),
            mock.patch(
                "knowledge_benchmark._normalized_query_result",
                side_effect=drifting_normalize,
            ),
        ):
            report = knowledge_benchmark.run_benchmark(
                self.fixture_root,
                file_count=250,
                page_count=20,
            )
        self.assertEqual("failed", report["outcome"])
        self.assertEqual("functional-failure", report["verdict"])
        self.assertEqual(
            report["functional_sha256"], report["expected_functional_sha256"]
        )
        self.assertEqual("removed", report["cleanup"])
        self.assertFalse(self.fixture_root.exists())

        with (
            mock.patch(
                "knowledge_benchmark._producer_identity",
                return_value={
                    "version": "test",
                    "git_head_sha": "0" * 40,
                    "worktree_clean": False,
                    "script_sha256": "0" * 64,
                },
            ),
            mock.patch(
                "knowledge_benchmark._build_fixture",
                side_effect=RuntimeError("initial product failure"),
            ),
            mock.patch(
                "knowledge_benchmark._safe_remove_fixture",
                side_effect=RuntimeError("cleanup failure"),
            ),
            self.assertRaises(knowledge_benchmark.BenchmarkEnvironmentError) as raised,
        ):
            knowledge_benchmark.run_benchmark(
                self.fixture_root,
                file_count=50,
                page_count=5,
            )
        self.assertEqual("cleanup", raised.exception.category)
        self.assertEqual("failed", raised.exception.cleanup)

    def test_controlled_samples_are_validated_before_fixture_mutation(self) -> None:
        import knowledge_benchmark

        valid = {
            operation_id: [0.1, 0.2, 0.3]
            for operation_id in knowledge_benchmark.OPERATION_ORDER
        }
        invalid_cases: dict[str, object] = {
            "not-a-mapping": [],
            "missing-operation": dict(list(valid.items())[:-1]),
            "extra-operation": {**valid, "unexpected": [0.1, 0.2, 0.3]},
            "wrong-order": dict(reversed(list(valid.items()))),
            "wrong-sample-container": {
                **valid,
                knowledge_benchmark.OPERATION_ORDER[0]: (0.1, 0.2, 0.3),
            },
            "wrong-sample-count": {
                **valid,
                knowledge_benchmark.OPERATION_ORDER[0]: [0.1, 0.2],
            },
            "boolean-sample": {
                **valid,
                knowledge_benchmark.OPERATION_ORDER[0]: [0.1, 0.2, True],
            },
            "non-finite-sample": {
                **valid,
                knowledge_benchmark.OPERATION_ORDER[0]: [0.1, 0.2, float("nan")],
            },
            "negative-sample": {
                **valid,
                knowledge_benchmark.OPERATION_ORDER[0]: [0.1, 0.2, -0.1],
            },
        }
        before = _tree_snapshot(self.fixture_root)
        for label, controlled_samples in invalid_cases.items():
            with (
                self.subTest(label=label),
                mock.patch("knowledge_benchmark._producer_identity") as producer,
                mock.patch("knowledge_benchmark._build_fixture") as build_fixture,
                mock.patch("knowledge_benchmark._safe_remove_fixture") as cleanup,
                self.assertRaises(ValueError),
            ):
                knowledge_benchmark.run_benchmark(
                    self.fixture_root,
                    file_count=250,
                    page_count=20,
                    controlled_operation_samples=controlled_samples,
                )
            producer.assert_not_called()
            build_fixture.assert_not_called()
            cleanup.assert_not_called()
            self.assertEqual(before, _tree_snapshot(self.fixture_root))

    def test_controlled_samples_do_not_replace_functional_operations(self) -> None:
        import knowledge_benchmark

        controlled_samples = {
            operation_id: [0.1, 0.2, 0.3]
            for operation_id in knowledge_benchmark.OPERATION_ORDER
        }
        _remove_fixture(self.fixture_root)
        with (
            mock.patch.object(knowledge_benchmark, "FILE_COUNT", 250),
            mock.patch.object(knowledge_benchmark, "PAGE_COUNT", 20),
            mock.patch.object(
                knowledge_benchmark,
                "EXPECTED_FUNCTIONAL_SHA256",
                "6310a73a73d1beb175615d927b429bce350694a95a131a1c68356a69d9f6ba32",
            ),
            mock.patch.object(
                knowledge_benchmark,
                "_cold_query",
                wraps=knowledge_benchmark._cold_query,
            ) as cold_queries,
            mock.patch.object(
                knowledge_benchmark,
                "query_repository",
                wraps=knowledge_benchmark.query_repository,
            ) as warm_queries,
            mock.patch.object(
                knowledge_benchmark,
                "build_stage_candidate_draft",
                wraps=knowledge_benchmark.build_stage_candidate_draft,
            ) as index_candidates,
        ):
            report = knowledge_benchmark.run_benchmark(
                self.fixture_root,
                file_count=250,
                page_count=20,
                controlled_operation_samples=controlled_samples,
            )

        self.assertEqual("knowledge-portability-report/v3", report["schema"])
        self.assertEqual("controlled", report["measurement_mode"])
        self.assertEqual(16, cold_queries.call_count)
        self.assertEqual(20, warm_queries.call_count)
        self.assertEqual(4, index_candidates.call_count)
        self.assertEqual(
            controlled_samples,
            {
                operation["operation_id"]: operation["samples_seconds"]
                for operation in report["timing"]["operations"]
            },
        )
        self.assertFalse(self.fixture_root.exists())

    def test_query_reuses_one_snapshot_and_one_fixed_pattern_search(self) -> None:
        import knowledge_query

        calls: list[tuple[list[str], bytes | None]] = []
        real_run = knowledge_query._run
        real_validate = knowledge_query.QuerySearchSession.validate

        def recording_validate(session: object) -> None:
            real_validate(session)

        def recording_run(command: list[str], **kwargs: object) -> object:
            input_bytes = kwargs.get("input_bytes")
            calls.append(
                (
                    list(command),
                    input_bytes if isinstance(input_bytes, bytes) else None,
                )
            )
            return real_run(command, **kwargs)

        knowledge_query._MATCH_CACHE.clear()
        with (
            mock.patch(
                "knowledge_query._match_cache_fingerprint",
                wraps=knowledge_query._match_cache_fingerprint,
            ) as fingerprints,
            mock.patch.object(
                knowledge_query.QuerySearchSession,
                "validate",
                autospec=True,
                side_effect=recording_validate,
            ) as validations,
            mock.patch("knowledge_query._run", side_effect=recording_run),
        ):
            exit_code, stdout, stderr = self._invoke(
                [
                    "query",
                    "--repo",
                    str(self.repo),
                    "--stage",
                    "implementation",
                    "--query",
                    "violet cedar ember quartz",
                ]
            )

        self.assertEqual(0, exit_code, stderr)
        self.assertEqual("", stderr)
        context = json.loads(stdout)
        self.assertEqual(
            [
                ("canonical", "docs/knowledge/topics/session.md", 5),
                ("raw", "evidence/source-000.md", 1),
                ("raw", "evidence/source-001.md", 1),
                ("raw", "evidence/source-002.md", 1),
                ("raw", "evidence/source-003.md", 1),
            ],
            [
                (item["authority"], item["path"], item["start_line"])
                for item in context["results"]
            ],
        )
        self.assertEqual(1, fingerprints.call_count, "one complete pre capture")
        self.assertEqual(1, validations.call_count, "one independent post validate")
        fixed_calls = [
            (command, input_bytes)
            for command, input_bytes in calls
            if command[0] == "rg" and "--fixed-strings" in command
        ]
        self.assertEqual(1, len(fixed_calls), calls)
        fixed_command, fixed_input = fixed_calls[0]
        self.assertIn("--file", fixed_command)
        self.assertIn("--max-count", fixed_command)
        self.assertIsNotNone(fixed_input)
        patterns = fixed_input.decode("utf-8").splitlines()
        self.assertEqual(66, len(patterns))
        self.assertEqual("docs/knowledge/topics/session.md", patterns[0])
        self.assertEqual("evidence/source-064.md", patterns[-1])
        self.assertLessEqual(len(calls), 10, calls)

    def test_warm_query_reuses_staged_snapshot_when_repository_is_stable(self) -> None:
        import knowledge_query

        arguments = [
            "query",
            "--repo",
            str(self.repo),
            "--stage",
            "implementation",
            "--query",
            "violet cedar ember quartz",
        ]
        knowledge_query._MATCH_CACHE.clear()
        warmed = self._invoke(arguments)
        self.assertEqual(0, warmed[0], warmed[2])

        with (
            mock.patch(
                "knowledge_query._match_cache_fingerprint",
                wraps=knowledge_query._match_cache_fingerprint,
            ) as full_fingerprints,
            mock.patch(
                "knowledge_query._match_cache_dirty_fingerprint",
                wraps=knowledge_query._match_cache_dirty_fingerprint,
            ) as dirty_fingerprints,
            mock.patch(
                "knowledge_query._match_cache_index_snapshot",
                wraps=knowledge_query._match_cache_index_snapshot,
            ) as index_snapshots,
            mock.patch("knowledge_query._run", wraps=knowledge_query._run) as runner,
        ):
            repeated = self._invoke(arguments)

        self.assertEqual(0, repeated[0], repeated[2])
        self.assertEqual(
            json.loads(warmed[1])["results"],
            json.loads(repeated[1])["results"],
        )
        self.assertEqual(0, full_fingerprints.call_count)
        self.assertEqual(0, index_snapshots.call_count)
        self.assertEqual(2, dirty_fingerprints.call_count)
        git_calls = [
            call.args[0]
            for call in runner.call_args_list
            if call.args and call.args[0] and call.args[0][0] == "git"
        ]
        self.assertFalse(
            any("--stage" in command for command in git_calls),
            git_calls,
        )

    def test_pathological_fixed_patterns_preserve_regex_fallback_output(self) -> None:
        import knowledge_query

        first = knowledge_query.Match("docs/knowledge/meta/pages/first.json", 1, "first")
        second = knowledge_query.Match("docs/knowledge/meta/pages/second.json", 2, "second")
        patterns = [f"safe-value-{index:03d}" for index in range(64)]
        patterns.append("pathological\nvalue")
        with (
            mock.patch(
                "knowledge_query._rg_matches",
                side_effect=([first], [second]),
            ) as fallback,
            mock.patch("knowledge_query._run") as direct_runner,
        ):
            matches = knowledge_query._rg_fixed_matches(
                self.repo,
                patterns,
                roots=("docs/knowledge/meta/pages",),
                session=mock.sentinel.query_session,
            )

        self.assertEqual([first, second], matches)
        self.assertEqual(2, fallback.call_count)
        self.assertTrue(
            all(call.kwargs["session"] is mock.sentinel.query_session for call in fallback.call_args_list)
        )
        self.assertTrue(
            all(call.kwargs["roots"] == ("docs/knowledge/meta/pages",) for call in fallback.call_args_list)
        )
        direct_runner.assert_not_called()

    def test_large_index_search_overlays_dirty_and_untracked_worktree_bytes(self) -> None:
        import knowledge_query

        dirty_path = self.repo / "evidence" / "source-000.md"
        dirty_path.write_text(
            "saffron tide worktree replacement.\n",
            encoding="utf-8",
            newline="\n",
        )
        untracked_path = self.repo / "evidence" / "untracked.md"
        untracked_path.write_text(
            "saffron tide untracked addition.\n",
            encoding="utf-8",
            newline="\n",
        )
        commands: list[list[str]] = []
        real_run = knowledge_query._run

        def recording_run(command: list[str], **kwargs: object) -> object:
            commands.append(list(command))
            return real_run(command, **kwargs)

        knowledge_query._MATCH_CACHE.clear()
        with (
            mock.patch.object(knowledge_query, "INDEX_SEARCH_MIN_TRACKED_PATHS", 1),
            mock.patch("knowledge_query._run", side_effect=recording_run),
        ):
            replacement = knowledge_query.query_repository(
                str(self.repo),
                stage="implementation",
                query="saffron tide",
            )
            original = knowledge_query.query_repository(
                str(self.repo),
                stage="implementation",
                query="violet cedar ember quartz",
            )

        replacement_paths = {
            item["path"]
            for item in replacement["results"]
            if item["authority"] == "raw"
        }
        self.assertEqual(
            {"evidence/source-000.md", "evidence/untracked.md"},
            replacement_paths,
        )
        self.assertNotIn(
            "evidence/source-000.md",
            {item["path"] for item in original["results"]},
        )
        self.assertTrue(
            any(
                command[0] == "git"
                and "grep" in command
                and "--cached" in command
                for command in commands
            ),
            commands,
        )
        self.assertFalse(
            any(command[0] == "rg" and command[-1] == "." for command in commands),
            commands,
        )
        overlay_roots = {
            value
            for command in commands
            if command[0] == "rg"
            for value in command
            if value in {"evidence/source-000.md", "evidence/untracked.md"}
        }
        self.assertEqual(
            {"evidence/source-000.md", "evidence/untracked.md"},
            overlay_roots,
        )

    def test_large_index_search_falls_back_for_semantic_attributes(self) -> None:
        import knowledge_query

        (self.repo / ".gitattributes").write_text(
            "*.md filter=semantic-transform\n",
            encoding="utf-8",
            newline="\n",
        )
        subprocess.run(
            ["git", "add", "--", ".gitattributes"],
            cwd=self.repo,
            stdout=subprocess.PIPE,
            stderr=subprocess.PIPE,
            check=True,
            shell=False,
        )
        commands: list[list[str]] = []
        real_run = knowledge_query._run

        def recording_run(command: list[str], **kwargs: object) -> object:
            commands.append(list(command))
            return real_run(command, **kwargs)

        knowledge_query._MATCH_CACHE.clear()
        with (
            mock.patch.object(knowledge_query, "INDEX_SEARCH_MIN_TRACKED_PATHS", 1),
            mock.patch("knowledge_query._run", side_effect=recording_run),
        ):
            report = knowledge_query.query_repository(
                str(self.repo),
                stage="implementation",
                query="violet cedar ember quartz",
            )

        self.assertTrue(report["results"])
        self.assertTrue(
            any(command[0] == "rg" and command[-1] == "." for command in commands),
            commands,
        )
        self.assertFalse(
            any(
                command[0] == "git"
                and "grep" in command
                and "--cached" in command
                for command in commands
            ),
            commands,
        )
        self.assertFalse(
            any(
                ".gitattributes" in command or "**/.gitattributes" in command
                for command in commands
            ),
            "tracked attribute paths must be reused from the staged snapshot",
        )

    def test_fingerprint_splits_staged_dirty_and_untracked_inventory(self) -> None:
        import knowledge_query

        (self.repo / ".gitattributes").write_text(
            "*.md text\n",
            encoding="utf-8",
            newline="\n",
        )
        subprocess.run(
            ["git", "add", "--", ".gitattributes"],
            cwd=self.repo,
            stdout=subprocess.PIPE,
            stderr=subprocess.PIPE,
            check=True,
            shell=False,
        )
        dirty_path = self.repo / "evidence" / "source-064.md"
        dirty_path.write_text(
            "violet cedar ember quartz changed source 064.\n",
            encoding="utf-8",
            newline="\n",
        )
        untracked_path = self.repo / "untracked-evidence.md"
        untracked_path.write_text(
            "violet cedar ember quartz untracked.\n",
            encoding="utf-8",
            newline="\n",
        )

        staged = subprocess.run(
            [
                "git",
                "-c",
                "core.quotepath=false",
                "ls-files",
                "--stage",
                "-v",
                "-z",
                "--",
            ],
            cwd=self.repo,
            stdout=subprocess.PIPE,
            stderr=subprocess.PIPE,
            check=True,
            shell=False,
        ).stdout
        tracked_dirty = subprocess.run(
            [
                "git",
                "-c",
                "core.quotepath=false",
                "diff-files",
                "--name-only",
                "-z",
                "--",
            ],
            cwd=self.repo,
            stdout=subprocess.PIPE,
            stderr=subprocess.PIPE,
            check=True,
            shell=False,
        ).stdout
        untracked = subprocess.run(
            [
                "git",
                "-c",
                "core.quotepath=false",
                "ls-files",
                "--others",
                "--exclude-standard",
                "-z",
                "--",
            ],
            cwd=self.repo,
            stdout=subprocess.PIPE,
            stderr=subprocess.PIPE,
            check=True,
            shell=False,
        ).stdout
        dirty_records = sorted(
            {
                value
                for stream in (tracked_dirty, untracked)
                for value in stream.split(b"\0")
                if value
            }
        )
        dirty = b"\0".join(dirty_records) + (b"\0" if dirty_records else b"")
        digest = hashlib.sha256()
        for label, value in ((b"staged", staged), (b"dirty", dirty)):
            digest.update(label)
            digest.update(len(value).to_bytes(8, "big"))
            digest.update(value)
        for raw_path in sorted({value for value in dirty.split(b"\0") if value}):
            relative = knowledge_query.normalized_path(raw_path.decode("utf-8"))
            lexical = self.repo / Path(*relative.split("/"))
            digest.update(len(raw_path).to_bytes(8, "big"))
            digest.update(raw_path)
            if lexical.exists():
                digest.update(hashlib.sha256(lexical.read_bytes()).digest())
            else:
                digest.update(b"missing")
        expected = digest.hexdigest()

        with mock.patch("knowledge_query._run", wraps=knowledge_query._run) as runner:
            actual = knowledge_query._match_cache_fingerprint(self.repo)

        self.assertEqual(expected, actual)
        self.assertIsNotNone(actual)
        self.assertEqual((".gitattributes",), actual.attribute_paths)
        git_commands = [
            call.args[0]
            for call in runner.call_args_list
            if call.args and call.args[0] and call.args[0][0] == "git"
        ]
        self.assertEqual(
            [
                [
                    "git",
                    "-c",
                    "core.quotepath=false",
                    "ls-files",
                    "--stage",
                    "-v",
                    "-z",
                    "--",
                ],
                [
                    "git",
                    "-c",
                    "core.quotepath=false",
                    "diff-files",
                    "--name-only",
                    "-z",
                    "--",
                ],
                [
                    "git",
                    "-c",
                    "core.quotepath=false",
                    "ls-files",
                    "--others",
                    "--exclude-standard",
                    "-z",
                    "--",
                ],
            ],
            git_commands,
        )

    def test_dirty_fingerprint_splits_tracked_and_untracked_inventory(self) -> None:
        import knowledge_query

        dirty_path = self.repo / "evidence" / "source-064.md"
        dirty_path.write_text(
            "violet cedar ember quartz changed source 064.\n",
            encoding="utf-8",
            newline="\n",
        )
        untracked_path = self.repo / "untracked-evidence.md"
        untracked_path.write_text(
            "violet cedar ember quartz untracked.\n",
            encoding="utf-8",
            newline="\n",
        )
        tracked_dirty = subprocess.run(
            [
                "git",
                "-c",
                "core.quotepath=false",
                "diff-files",
                "--name-only",
                "-z",
                "--",
            ],
            cwd=self.repo,
            stdout=subprocess.PIPE,
            stderr=subprocess.PIPE,
            check=True,
            shell=False,
        ).stdout
        untracked = subprocess.run(
            [
                "git",
                "-c",
                "core.quotepath=false",
                "ls-files",
                "--others",
                "--exclude-standard",
                "-z",
                "--",
            ],
            cwd=self.repo,
            stdout=subprocess.PIPE,
            stderr=subprocess.PIPE,
            check=True,
            shell=False,
        ).stdout
        dirty_records = sorted(
            {
                value
                for stream in (tracked_dirty, untracked)
                for value in stream.split(b"\0")
                if value
            }
        )
        dirty = b"\0".join(dirty_records) + (b"\0" if dirty_records else b"")
        expected = knowledge_query._dirty_fingerprint(self.repo, dirty)

        with mock.patch("knowledge_query._run", wraps=knowledge_query._run) as runner:
            actual = knowledge_query._match_cache_dirty_fingerprint(self.repo)

        self.assertEqual(expected, actual)
        git_commands = [
            call.args[0]
            for call in runner.call_args_list
            if call.args and call.args[0] and call.args[0][0] == "git"
        ]
        self.assertEqual(
            [
                [
                    "git",
                    "-c",
                    "core.quotepath=false",
                    "diff-files",
                    "--name-only",
                    "-z",
                    "--",
                ],
                [
                    "git",
                    "-c",
                    "core.quotepath=false",
                    "ls-files",
                    "--others",
                    "--exclude-standard",
                    "-z",
                    "--",
                ],
            ],
            git_commands,
        )

    def test_index_snapshot_resolves_normal_git_directory_without_git_process(self) -> None:
        import knowledge_query

        with mock.patch(
            "knowledge_query._run",
            side_effect=AssertionError("normal repository index lookup must be direct"),
        ) as runner:
            snapshot = knowledge_query._match_cache_index_snapshot(self.repo)

        self.assertIsNotNone(snapshot)
        index_path, index_fingerprint = snapshot
        self.assertEqual(self.repo / ".git" / "index", index_path)
        self.assertEqual(
            knowledge_query._match_cache_index_fingerprint(index_path),
            index_fingerprint,
        )
        runner.assert_not_called()

    def test_benchmark_preserves_warm_samples_and_adds_fresh_cold_samples(self) -> None:
        import knowledge_benchmark

        _remove_fixture(self.fixture_root)
        with (
            mock.patch.object(knowledge_benchmark, "FILE_COUNT", 250),
            mock.patch.object(knowledge_benchmark, "PAGE_COUNT", 20),
            mock.patch.object(
                knowledge_benchmark,
                "EXPECTED_FUNCTIONAL_SHA256",
                "6310a73a73d1beb175615d927b429bce350694a95a131a1c68356a69d9f6ba32",
            ),
            mock.patch.object(
                knowledge_benchmark,
                "_cold_query",
                wraps=knowledge_benchmark._cold_query,
            ) as cold_queries,
        ):
            report = knowledge_benchmark.run_benchmark(
                self.fixture_root,
                file_count=250,
                page_count=20,
            )

        durations = report["durations_seconds"]
        self.assertEqual("knowledge-portability-report/v3", report["schema"])
        self.assertEqual("observed", report["measurement_mode"])
        self.assertEqual("pass", report["verdict"])
        self.assertEqual("removed", report["cleanup"])
        self.assertEqual(5, len(durations["queries"]))
        self.assertEqual(5, len(durations["cold_queries"]))
        self.assertEqual(16, cold_queries.call_count)
        for sample_call in cold_queries.call_args_list[1:4]:
            self.assertEqual(cold_queries.call_args_list[0].kwargs, sample_call.kwargs)
        timing = report["timing"]
        self.assertEqual(11, len(timing["operations"]))
        self.assertEqual(3, timing["contract"]["sample_count"])
        for operation in timing["operations"]:
            self.assertEqual(3, len(operation["samples_seconds"]))
            self.assertEqual(3, len(operation["result_sha256s"]))
            self.assertEqual(
                [operation["result_sha256s"][0]] * 3,
                operation["result_sha256s"],
            )
        self.assertEqual(
            durations["cold_queries"],
            [item["samples_seconds"][0] for item in timing["operations"][:5]],
        )
        self.assertEqual(
            durations["queries"],
            [item["samples_seconds"][0] for item in timing["operations"][5:10]],
        )
        self.assertGreaterEqual(durations["fixture_setup"], 0.0)
        self.assertEqual(report["warm_queries_sha256"], report["cold_queries_sha256"])
        self.assertFalse(self.fixture_root.exists())

    def test_fixture_build_creates_each_planned_directory_once(self) -> None:
        import knowledge_benchmark

        _remove_fixture(self.fixture_root)
        mkdir_calls: list[Path] = []
        git_calls: list[tuple[list[str], bytes | None]] = []
        real_mkdir = Path.mkdir
        real_run = knowledge_benchmark.subprocess.run

        def recording_mkdir(path: Path, *args: object, **kwargs: object) -> None:
            mkdir_calls.append(path.resolve(strict=False))
            real_mkdir(path, *args, **kwargs)

        def recording_run(command: list[str], **kwargs: object) -> object:
            input_bytes = kwargs.get("input")
            git_calls.append(
                (
                    list(command),
                    input_bytes if isinstance(input_bytes, bytes) else None,
                )
            )
            return real_run(command, **kwargs)

        with (
            mock.patch.object(Path, "mkdir", new=recording_mkdir),
            mock.patch("knowledge_benchmark.subprocess.run", side_effect=recording_run),
        ):
            repo = knowledge_benchmark._build_fixture(
                self.fixture_root,
                file_count=50,
                page_count=5,
                reuse_fixture=False,
            )

        expected = {
            self.fixture_root.resolve(strict=False),
            repo.resolve(strict=False),
            *knowledge_benchmark._fixture_parent_directories(
                repo,
                source_count=38,
            ),
        }
        relevant_calls = [path for path in mkdir_calls if path in expected]
        self.assertEqual(expected, set(relevant_calls))
        self.assertEqual(len(expected), len(relevant_calls), relevant_calls)
        self.assertFalse(
            any(call[0][:2] == ["git", "add"] for call in git_calls),
            git_calls,
        )
        import_calls = [
            call for call in git_calls if call[0][:2] == ["git", "fast-import"]
        ]
        self.assertEqual(1, len(import_calls), git_calls)
        import_command, import_input = import_calls[0]
        self.assertEqual(
            ["git", "fast-import", "--quiet"],
            import_command,
        )
        self.assertIsNotNone(import_input)
        import_paths = [
            line.removeprefix(b"M 100644 inline ").decode("utf-8")
            for line in import_input.splitlines()
            if line.startswith(b"M 100644 inline ")
        ]
        self.assertEqual(
            1,
            sum(call[0][:2] == ["git", "read-tree"] for call in git_calls),
            git_calls,
        )
        self.assertEqual(
            1,
            sum(call[0][:2] == ["git", "checkout-index"] for call in git_calls),
            git_calls,
        )
        refresh_calls = [
            index
            for index, call in enumerate(git_calls)
            if call[0][:2] == ["git", "update-index"]
            and "--refresh" in call[0]
        ]
        checkout_calls = [
            index
            for index, call in enumerate(git_calls)
            if call[0][:2] == ["git", "checkout-index"]
        ]
        self.assertEqual(1, len(refresh_calls), git_calls)
        self.assertLess(checkout_calls[0], refresh_calls[0], git_calls)
        tracked = real_run(
            ["git", "ls-files", "-z"],
            cwd=repo,
            stdout=subprocess.PIPE,
            stderr=subprocess.PIPE,
            check=True,
            shell=False,
        ).stdout
        tracked_paths = [item.decode("utf-8") for item in tracked.split(b"\0") if item]
        self.assertEqual(50, len(import_paths))
        self.assertEqual(set(tracked_paths), set(import_paths))
        self.assertEqual(len(import_paths), len(set(import_paths)))

    def test_benchmark_cleanup_covers_fixture_build_failure(self) -> None:
        import knowledge_benchmark

        _remove_fixture(self.fixture_root)
        with (
            mock.patch(
                "knowledge_benchmark._write",
                side_effect=RuntimeError("injected fixture write failure"),
            ),
            self.assertRaisesRegex(RuntimeError, "injected fixture write failure"),
        ):
            knowledge_benchmark.run_benchmark(
                self.fixture_root,
                file_count=50,
                page_count=5,
            )
        self.assertFalse(self.fixture_root.exists())

    def test_portability_comparator_replays_v3_observed_evidence_and_rejects_drift(self) -> None:
        import compare_portability_reports

        reports = [
            _synthetic_portability_report(os_name)
            for os_name in ("windows", "linux")
        ]
        functional_digest = reports[0]["functional_sha256"]
        original = compare_portability_reports.EXPECTED_FUNCTIONAL_SHA256
        compare_portability_reports.EXPECTED_FUNCTIONAL_SHA256 = functional_digest
        try:
            valid = compare_portability_reports.compare_reports(reports)
            mutations = []

            v2 = json.loads(json.dumps(reports))
            v2[0]["schema"] = "knowledge-portability-report/v2"
            mutations.append(v2)

            missing_mode = json.loads(json.dumps(reports))
            del missing_mode[0]["measurement_mode"]
            mutations.append(missing_mode)

            unknown_mode = json.loads(json.dumps(reports))
            unknown_mode[0]["measurement_mode"] = "simulated"
            mutations.append(unknown_mode)

            controlled = json.loads(json.dumps(reports))
            controlled[0]["measurement_mode"] = "controlled"
            mutations.append(controlled)

            missing_sample = json.loads(json.dumps(reports))
            missing_sample[0]["timing"]["operations"][0]["samples_seconds"].pop()
            mutations.append(missing_sample)

            asserted_drift = json.loads(json.dumps(reports))
            asserted_drift[0]["timing"]["operations"][0]["median_seconds"] = 1.5
            mutations.append(asserted_drift)

            hash_drift = json.loads(json.dumps(reports))
            hash_drift[0]["timing"]["operations"][0]["result_sha256s"][0] = "0" * 64
            mutations.append(hash_drift)

            projection_drift = json.loads(json.dumps(reports))
            projection_drift[0]["durations_seconds"]["cold_queries"][0] = 1.5
            mutations.append(projection_drift)

            dirty = json.loads(json.dumps(reports))
            dirty[0]["producer"]["worktree_clean"] = False
            mutations.append(dirty)

            identity_drift = json.loads(json.dumps(reports))
            identity_drift[0]["producer"]["script_sha256"] = "3" * 64
            mutations.append(identity_drift)

            invalid_number = json.loads(json.dumps(reports))
            invalid_number[0]["timing"]["operations"][0]["samples_seconds"][0] = float("nan")
            mutations.append(invalid_number)

            rejected = [
                compare_portability_reports.compare_reports(value)
                for value in mutations
            ]
        finally:
            compare_portability_reports.EXPECTED_FUNCTIONAL_SHA256 = original

        self.assertEqual("passed", valid["outcome"])
        self.assertEqual("knowledge-portability-comparison/v2", valid["schema"])
        self.assertEqual([], valid["diagnostics"])
        self.assertEqual(["linux", "windows"], valid["oses"])
        self.assertTrue(all(value["outcome"] == "failed" for value in rejected), rejected)
        expected_mode_diagnostics = (
            "incompatible report schema",
            "measurement mode is missing",
            "measurement mode is unsupported",
            "controlled report is not admissible",
        )
        for result, expected_diagnostic in zip(
            rejected[:4],
            expected_mode_diagnostics,
            strict=True,
        ):
            self.assertTrue(
                any(expected_diagnostic in item for item in result["diagnostics"]),
                result,
            )
        self.assertTrue(
            any(
                "top-level verdict differs" in diagnostic
                for diagnostic in rejected[6]["diagnostics"]
            ),
            rejected[6],
        )

    def test_portability_comparator_cli_only_reads_named_v3_observed_reports(self) -> None:
        import compare_portability_reports

        report_root = self.fixture_root / "portability-reports"
        report_root.mkdir()
        reports = [
            _synthetic_portability_report(os_name)
            for os_name in ("windows", "linux")
        ]
        for report in reports:
            path = report_root / f"knowledge-portability-report-{report['host']['os']}.json"
            path.write_text(
                json.dumps(report, ensure_ascii=False, sort_keys=True) + "\n",
                encoding="utf-8",
                newline="\n",
            )
        (report_root / "knowledge-portability-comparison.json").write_text(
            "not json\n",
            encoding="utf-8",
            newline="\n",
        )

        stdout = io.StringIO()
        original = compare_portability_reports.EXPECTED_FUNCTIONAL_SHA256
        compare_portability_reports.EXPECTED_FUNCTIONAL_SHA256 = reports[0][
            "functional_sha256"
        ]
        try:
            with contextlib.redirect_stdout(stdout):
                exit_code = compare_portability_reports.main(
                    ["--root", str(report_root)]
                )
        finally:
            compare_portability_reports.EXPECTED_FUNCTIONAL_SHA256 = original

        self.assertEqual(0, exit_code)
        comparison = json.loads(stdout.getvalue())
        self.assertEqual("knowledge-portability-comparison/v2", comparison["schema"])
        self.assertEqual("passed", comparison["outcome"])


def main(argv: list[str] | None = None) -> int:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("test_cases", nargs="*")
    parser.add_argument("--fixture-root", type=Path, default=Path(".knowledge-test-tmp"))
    args = parser.parse_args(argv)
    QueryCliTests.fixture_root = args.fixture_root.resolve()
    PerformanceTests.fixture_root = args.fixture_root.resolve()
    test_cases = {
        "QueryCliTests": QueryCliTests,
        "PerformanceTests": PerformanceTests,
    }
    selected = args.test_cases or list(test_cases)
    unknown = sorted(set(selected) - set(test_cases))
    if unknown:
        parser.error(f"unknown test case: {', '.join(unknown)}")
    suite = unittest.TestSuite(
        unittest.defaultTestLoader.loadTestsFromTestCase(test_cases[name])
        for name in selected
    )
    result = unittest.TextTestRunner(verbosity=2).run(suite)
    _remove_fixture(QueryCliTests.fixture_root)
    return 0 if result.wasSuccessful() and not result.skipped else 1


if __name__ == "__main__":
    raise SystemExit(main())
