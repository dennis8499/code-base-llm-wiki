from __future__ import annotations

import importlib.util
import json
from pathlib import Path
import tarfile
import tempfile
import unittest
import zipfile


REPO_ROOT = Path(__file__).parents[1]
RELEASE_PATH = REPO_ROOT / "tools" / "release.py"


def load_release():
    spec = importlib.util.spec_from_file_location("release_tool", RELEASE_PATH)
    if spec is None or spec.loader is None:
        raise RuntimeError(f"Unable to load release tool: {RELEASE_PATH}")
    module = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(module)
    return module


class ReleaseTests(unittest.TestCase):
    def test_ci_covers_supported_linux_versions_and_windows_smoke(self) -> None:
        workflow = (REPO_ROOT / ".github" / "workflows" / "ci.yml").read_text(
            encoding="utf-8"
        )
        for required in (
            "ubuntu-latest",
            'python: "3.11"',
            'python: "3.14"',
            "windows-latest",
            "python -m unittest discover -s tests -v",
            "parity-check.py",
            "validate-frontmatter.py wiki",
            "check-stale.py wiki .",
            "validate-log.py wiki/log.md --repo-root .",
            "rebuild-index.py wiki --check",
            "lint-wiki.py wiki --repo-root .",
        ):
            with self.subTest(required=required):
                self.assertIn(required, workflow)

    def test_release_workflow_validates_and_publishes_tagged_assets(self) -> None:
        workflow = (REPO_ROOT / ".github" / "workflows" / "release.yml").read_text(
            encoding="utf-8"
        )
        for required in (
            'tags:\n      - "v*.*.*"',
            "contents: write",
            "actions/checkout@v4",
            "actions/setup-python@v5",
            "tools/release.py validate",
            "tools/release.py build",
            "gh release create",
            "--verify-tag",
        ):
            with self.subTest(required=required):
                self.assertIn(required, workflow)

    def test_version_is_stable_semver_and_tag_matches(self) -> None:
        release = load_release()
        self.assertEqual(release.read_version(REPO_ROOT), "0.2.0")
        self.assertEqual(release.validate_tag("v0.2.0", REPO_ROOT), "0.2.0")
        with self.assertRaises(release.ReleaseError):
            release.validate_tag("0.2.0", REPO_ROOT)
        with self.assertRaises(release.ReleaseError):
            release.validate_version("0.1.0-rc.1")

    def test_build_creates_manifest_archives_and_checksums(self) -> None:
        release = load_release()
        with tempfile.TemporaryDirectory() as directory:
            temporary = Path(directory)
            source_root = temporary / "source"
            output = temporary / "output"
            (source_root / "tools").mkdir(parents=True)
            (source_root / "docs/history").mkdir(parents=True)
            (source_root / "VERSION").write_text("0.2.0\n", encoding="utf-8")
            (source_root / "LICENSE").write_text("Test fixture license\n", encoding="utf-8")
            (source_root / "README.md").write_text("Fixture\n", encoding="utf-8")
            (source_root / "tools/release.py").write_text("# fixture\n", encoding="utf-8")
            (source_root / "docs/history/llm-wiki.md").write_text(
                "https://gist.github.com/karpathy/442a6bf555914893e9891c11519de94f\n",
                encoding="utf-8",
            )
            payload = release.build_release(
                output,
                root=source_root,
                repository="owner/example",
            )

            self.assertEqual(payload["version"], "0.2.0")
            self.assertEqual(payload["tag"], "v0.2.0")
            manifest = json.loads((output / "update-manifest.json").read_text(encoding="utf-8"))
            self.assertEqual(
                set(manifest),
                {
                    "schema_version",
                    "product",
                    "version",
                    "tag",
                    "channel",
                    "installer_contract_version",
                    "release_url",
                    "assets",
                },
            )
            self.assertEqual(manifest["schema_version"], 1)
            self.assertEqual(manifest["installer_contract_version"], 3)
            self.assertEqual(manifest["release_url"], "https://github.com/owner/example/releases/tag/v0.2.0")
            self.assertEqual(
                [asset["name"] for asset in manifest["assets"]],
                ["codebase-llm-wiki.zip", "codebase-llm-wiki.tar.gz"],
            )

            checksum_lines = (output / "SHA256SUMS").read_text(encoding="utf-8").splitlines()
            self.assertEqual(len(checksum_lines), 3)
            for asset in manifest["assets"]:
                asset_path = output / asset["name"]
                self.assertTrue(asset_path.is_file())
                self.assertEqual(asset["sha256"], release.sha256(asset_path))
                self.assertIn(asset["sha256"], checksum_lines[0] + checksum_lines[1])
                self.assertIn(
                    "https://github.com/owner/example/releases/download/v0.2.0/",
                    asset["download_url"],
                )

            zip_names = zipfile.ZipFile(output / "codebase-llm-wiki.zip").namelist()
            tar_names = tarfile.open(output / "codebase-llm-wiki.tar.gz", "r:gz").getnames()
            for names in (zip_names, tar_names):
                self.assertTrue(any(name.endswith("/VERSION") for name in names))
                self.assertTrue(any(name.endswith("/tools/release.py") for name in names))
                self.assertFalse(any("/.git/" in name for name in names))
                self.assertFalse(any("/__pycache__/" in name for name in names))
                self.assertFalse(any("/logs/" in name for name in names))

    def test_public_release_is_blocked_until_owner_selects_a_license(self) -> None:
        release = load_release()
        with self.assertRaisesRegex(release.ReleaseError, "explicit LICENSE"):
            release.validate_release_readiness(REPO_ROOT)

    def test_release_files_exclude_local_notebooklm_exports(self) -> None:
        release = load_release()
        with tempfile.TemporaryDirectory() as directory:
            root = Path(directory)
            (root / "VERSION").write_text("0.1.0\n", encoding="utf-8")
            (root / ".notebooklm/sources").mkdir(parents=True)
            (root / ".notebooklm/sources/private.md").write_text(
                "private\n", encoding="utf-8"
            )
            (root / "README.md").write_text("readme\n", encoding="utf-8")
            files = release.release_files(root)
            self.assertEqual(
                [path.relative_to(root).as_posix() for path in files],
                ["README.md", "VERSION"],
            )


if __name__ == "__main__":
    unittest.main()
