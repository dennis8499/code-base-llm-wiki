from __future__ import annotations

import argparse
import io
import json
import os
from pathlib import Path
import shutil
import subprocess
import sys
import tempfile
import unittest


ROOT = Path(__file__).resolve().parents[1]
TESTS = Path(__file__).resolve().parent
TEST_TEMP_ROOT = ROOT / ".notebooklm-tests-tmp"


def _prepare_temp_root() -> Path:
    try:
        TEST_TEMP_ROOT.mkdir(parents=True, exist_ok=True)
        return TEST_TEMP_ROOT
    except OSError:
        # Managed sandboxes can expose a readable worktree outside their writable
        # root. Keep the runner usable there while retaining the repo-local path
        # for ordinary development and CI execution.
        return Path(tempfile.mkdtemp(prefix="notebooklm-tests-"))


def _suite(module_name: str, prefix: str, selected_id: str | None) -> unittest.TestSuite:
    if str(TESTS) not in sys.path:
        sys.path.insert(0, str(TESTS))
    module = __import__(module_name)
    loaded = unittest.defaultTestLoader.loadTestsFromModule(module)
    selected = unittest.TestSuite()
    expected = selected_id.lower().replace("-", "_") if selected_id else None
    for case in _iter_cases(loaded):
        method = case._testMethodName
        if method.startswith(prefix) and (expected is None or expected in method):
            selected.addTest(case)
    return selected


def _iter_cases(suite: unittest.TestSuite):
    for item in suite:
        if isinstance(item, unittest.TestSuite):
            yield from _iter_cases(item)
        else:
            yield item


def _ids(suite: unittest.TestSuite, marker: str) -> list[str]:
    found: list[str] = []
    for case in _iter_cases(suite):
        method = case._testMethodName.upper().replace("_", "-")
        start = method.find(marker)
        if start >= 0:
            found.append(method[start : start + len(marker) + 3])
    return sorted(set(found))


def _run_suite(
    suite: unittest.TestSuite,
    expected: str | None = None,
    marker: str | None = None,
) -> int:
    discovered = suite.countTestCases()
    ids = [expected] if expected else (_ids(suite, marker) if marker else [])
    stream = io.StringIO()
    result = unittest.TextTestRunner(stream=stream, verbosity=2).run(suite)
    executed = result.testsRun
    payload = {
        "discovered": discovered,
        "selected": executed,
        "executed": executed,
        "passed": executed - len(result.failures) - len(result.errors) - len(result.skipped),
        "failed": len(result.failures),
        "errors": len(result.errors),
        "skipped": len(result.skipped),
        "ids": ids,
        "output": stream.getvalue(),
    }
    print(json.dumps(payload, ensure_ascii=False, sort_keys=True))
    return 0 if executed and result.wasSuccessful() and not result.skipped else 1


def _subprocess_suite(patterns: list[str], *, cwd: Path = ROOT) -> int:
    unittest_arguments = (
        ["discover", "-v", *patterns[1:]]
        if patterns and patterns[0] == "discover"
        else ["-v", *patterns]
    )
    command = [
        sys.executable,
        "-X",
        "utf8",
        "-B",
        "-m",
        "unittest",
        *unittest_arguments,
    ]
    env = os.environ.copy()
    env.update(
        {
            "TMP": str(TEST_TEMP_ROOT),
            "TEMP": str(TEST_TEMP_ROOT),
            "PYTHONUTF8": "1",
            "PYTHONIOENCODING": "utf-8",
        }
    )
    result = subprocess.run(
        command,
        cwd=cwd,
        capture_output=True,
        text=True,
        encoding="utf-8",
        env=env,
    )
    skipped_tests = [
        line.strip()
        for line in result.stderr.splitlines()
        if " ... skipped " in line
    ]
    print(
        json.dumps(
            {
                "command": command,
                "exit_code": result.returncode,
                "stdout": result.stdout,
                "stderr": result.stderr,
                "skipped_count": len(skipped_tests),
                "skipped_tests": skipped_tests,
            },
            ensure_ascii=False,
            sort_keys=True,
        )
    )
    return result.returncode


def main(argv: list[str] | None = None) -> int:
    parser = argparse.ArgumentParser()
    group = parser.add_mutually_exclusive_group(required=True)
    group.add_argument("--list", action="store_true")
    group.add_argument("--scenario")
    group.add_argument("--all", action="store_true")
    group.add_argument("--inner")
    group.add_argument("--related", action="store_true")
    group.add_argument("--build", action="store_true")
    group.add_argument("--unit-all", action="store_true")
    group.add_argument("--governance", action="store_true")
    args = parser.parse_args(argv)

    if args.list:
        suite = _suite("test_notebooklm_acceptance", "test_bdd_", None)
        ids = _ids(suite, "BDD-")
        print(json.dumps({"discovered": len(ids), "selected": 0, "executed": 0, "passed": 0, "failed": 0, "errors": 0, "skipped": 0, "ids": ids}, sort_keys=True))
        return 0
    if args.scenario:
        return _run_suite(_suite("test_notebooklm_acceptance", "test_bdd_", args.scenario), args.scenario)
    if args.all:
        return _run_suite(
            _suite("test_notebooklm_acceptance", "test_bdd_", None),
            marker="BDD-",
        )
    if args.inner:
        return _run_suite(_suite("test_notebooklm_contract", "test_test_", args.inner), args.inner)
    if args.related:
        return _subprocess_suite(
            [
                "test_export_notebooklm",
                "test_wiki_lint",
                "test_install_framework",
                "test_notebooklm_acceptance",
                "test_notebooklm_contract",
            ],
            cwd=TESTS,
        )
    if args.unit_all:
        return _subprocess_suite(["discover", "-s", "tests"])
    if args.build:
        failures: list[str] = []
        python_files = sorted(
            path
            for path in ROOT.rglob("*.py")
            if ".git" not in path.parts and ".notebooklm-tests-tmp" not in path.parts
        )
        for path in python_files:
            try:
                compile(path.read_text(encoding="utf-8"), str(path), "exec")
            except Exception as exc:
                failures.append(f"{path.relative_to(ROOT).as_posix()}: {exc}")
        schemas = sorted(ROOT.rglob("*.schema.json"))
        for path in schemas:
            try:
                json.loads(path.read_text(encoding="utf-8"))
            except Exception as exc:
                failures.append(f"{path.relative_to(ROOT).as_posix()}: {exc}")
        print(json.dumps({"python_files_checked": len(python_files), "json_schema_files_checked": len(schemas), "failures": failures}, ensure_ascii=False, sort_keys=True))
        return 1 if failures else 0
    if args.governance:
        commands = [
            [sys.executable, "-X", "utf8", "-B", ".agents/skills/codebase-wiki/scripts/parity-check.py"],
            [sys.executable, "-X", "utf8", "-B", ".agents/skills/codebase-wiki/scripts/validate-frontmatter.py", "wiki"],
            [sys.executable, "-X", "utf8", "-B", ".agents/skills/codebase-wiki/scripts/check-stale.py", "wiki", "."],
            [sys.executable, "-X", "utf8", "-B", ".agents/skills/codebase-wiki/scripts/validate-log.py", "wiki/log.md", "--repo-root", "."],
            [sys.executable, "-X", "utf8", "-B", ".agents/skills/codebase-wiki/scripts/rebuild-index.py", "wiki", "--check"],
            [sys.executable, "-X", "utf8", "-B", ".agents/skills/codebase-wiki/scripts/lint-wiki.py", "wiki", "--repo-root", "."],
        ]
        reports = []
        for command in commands:
            result = subprocess.run(command, cwd=ROOT, capture_output=True, text=True, encoding="utf-8")
            reports.append({"command": command, "exit_code": result.returncode, "stdout": result.stdout, "stderr": result.stderr})
        print(json.dumps(reports, ensure_ascii=False, sort_keys=True))
        return 0 if all(item["exit_code"] == 0 for item in reports) else 1
    return 2


if __name__ == "__main__":
    TEST_TEMP_ROOT = _prepare_temp_root()
    tempfile.tempdir = str(TEST_TEMP_ROOT)
    try:
        raise SystemExit(main())
    finally:
        tempfile.tempdir = None
        shutil.rmtree(TEST_TEMP_ROOT, ignore_errors=True)
