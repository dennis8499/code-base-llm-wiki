from __future__ import annotations

import re
import unittest
from pathlib import Path


REPO_ROOT = Path(__file__).parents[2]
WORKFLOW_PATH = REPO_ROOT / ".github" / "workflows" / "release.yml"
FEATURE_PATH = REPO_ROOT / "tests" / "release" / "features" / "github-release.feature"


class GitHubReleaseWorkflowTests(unittest.TestCase):
    def test_release_workflow_is_tag_driven_and_publishes_exact_assets(self) -> None:
        workflow_root = REPO_ROOT / ".github" / "workflows"
        self.assertEqual(
            sorted(path.name for path in workflow_root.glob("*.y*ml")),
            ["release.yml"],
        )
        workflow = WORKFLOW_PATH.read_text(encoding="utf-8")
        for required in (
            "name: Release",
            "tags:",
            '- "v*.*.*"',
            "permissions:",
            "contents: write",
            "actions/checkout@v7",
            "actions/setup-python@v7",
            'python tools/release.py validate --tag "${GITHUB_REF_NAME}"',
            'python tools/release.py build --output dist --repository "${GITHUB_REPOSITORY}"',
            'GH_TOKEN: ${{ github.token }}',
            'gh release create "${GITHUB_REF_NAME}"',
            "--verify-tag",
            "--generate-notes",
            "dist/codebase-llm-wiki.zip",
            "dist/codebase-llm-wiki.tar.gz",
            "dist/update-manifest.json",
            "dist/SHA256SUMS",
        ):
            with self.subTest(required=required):
                self.assertIn(required, workflow)
        permission_names = {
            match.group(1)
            for match in re.finditer(
                r"(?m)^\s+([A-Za-z0-9_-]+):\s+(?:read|write|none)\s*$",
                workflow,
            )
        }
        self.assertEqual(permission_names, {"contents"})
        self.assertNotIn("dist/*", workflow)

    def test_release_feature_has_stable_scenarios(self) -> None:
        feature = FEATURE_PATH.read_text(encoding="utf-8")
        self.assertIn("Feature: GitHub release automation", feature)
        scenario_ids = re.findall(r"Scenario: \[(BDD-[A-Z0-9-]+)\]", feature)
        self.assertEqual(
            scenario_ids,
            [
                "BDD-RELEASE-001",
                "BDD-RELEASE-002",
                "BDD-RELEASE-003",
                "BDD-RELEASE-004",
            ],
        )
        self.assertIn("@manual", feature)

    def test_public_release_uses_the_selected_mit_license(self) -> None:
        license_text = (REPO_ROOT / "LICENSE").read_text(encoding="utf-8")
        for required in (
            "MIT License",
            "Copyright (c) 2026 dennis8499",
            'THE SOFTWARE IS PROVIDED "AS IS"',
        ):
            with self.subTest(required=required):
                self.assertIn(required, license_text)


if __name__ == "__main__":
    unittest.main()
