from __future__ import annotations

import json
from pathlib import Path
import re
import subprocess
import sys


REPO_ROOT = Path(__file__).parents[2]
SCENARIO_TESTS = {
    "BDD-RELEASE-001": (
        "tests.release.test_release.ReleaseTests.test_version_is_stable_semver_and_tag_matches",
    ),
    "BDD-RELEASE-002": (
        "tests.release.test_release.ReleaseTests.test_build_creates_manifest_archives_and_checksums",
    ),
    "BDD-RELEASE-003": (
        "tests.installer.test_install_framework.FrameworkInstallerTests.test_copilot_surface_excludes_codex_files",
    ),
}
EXPECTED_SCENARIOS = (*SCENARIO_TESTS, "BDD-RELEASE-004")


def scenario_ids(feature_path: Path) -> list[str]:
    text = feature_path.read_text(encoding="utf-8")
    return re.findall(r"Scenario: \[(BDD-[A-Z0-9-]+)\]", text)


def run() -> int:
    if len(sys.argv) != 2:
        print("usage: scenario_runner.py FEATURE", file=sys.stderr)
        return 2

    feature_path = Path(sys.argv[1]).expanduser().resolve()
    try:
        identifiers = scenario_ids(feature_path)
    except (OSError, UnicodeError) as exc:
        print(json.dumps({"error": str(exc)}, ensure_ascii=False))
        return 1

    if identifiers != list(EXPECTED_SCENARIOS):
        print(
            json.dumps(
                {
                    "error": "feature scenario IDs do not match the approved release contract",
                    "expected": list(EXPECTED_SCENARIOS),
                    "actual": identifiers,
                },
                ensure_ascii=False,
            )
        )
        return 1

    evidence: list[dict[str, str]] = []
    failed = False
    for identifier in identifiers:
        if identifier == "BDD-RELEASE-004":
            evidence.append({"id": identifier, "status": "manual_pending"})
            continue
        result = subprocess.run(
            [sys.executable, "-m", "unittest", SCENARIO_TESTS[identifier][0]],
            cwd=REPO_ROOT,
            capture_output=True,
            text=True,
            encoding="utf-8",
            errors="replace",
            check=False,
        )
        status = "passed" if result.returncode == 0 else "failed"
        failed = failed or status == "failed"
        evidence.append({"id": identifier, "status": status})

    print(json.dumps({"scenarios": evidence}, ensure_ascii=False, sort_keys=True))
    return 1 if failed else 0


if __name__ == "__main__":
    raise SystemExit(run())
