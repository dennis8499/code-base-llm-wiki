from __future__ import annotations

import importlib.util
import json
import os
from pathlib import Path
import subprocess
import sys
import tarfile
import tempfile
import unittest
import zipfile


REPO_ROOT = Path(__file__).parents[1]
RELEASE_PATH = REPO_ROOT / "tools" / "release.py"


def create_directory_reparse_point(link: Path, target: Path) -> None:
    try:
        os.symlink(target, link, target_is_directory=True)
        return
    except (OSError, NotImplementedError) as symlink_error:
        if os.name != "nt":
            raise symlink_error
    result = subprocess.run(
        ["cmd", "/c", "mklink", "/J", str(link), str(target)],
        check=False,
        capture_output=True,
        text=True,
        encoding="utf-8",
        errors="replace",
    )
    if result.returncode != 0:
        raise OSError(result.stderr or result.stdout or "unable to create directory junction")


def load_release():
    spec = importlib.util.spec_from_file_location("release_tool", RELEASE_PATH)
    if spec is None or spec.loader is None:
        raise RuntimeError(f"Unable to load release tool: {RELEASE_PATH}")
    module = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(module)
    return module


class ReleaseTests(unittest.TestCase):
    def test_release_cli_validate_and_build_contract(self) -> None:
        with tempfile.TemporaryDirectory() as directory:
            root = Path(directory) / "source"
            output = Path(directory) / "dist"
            (root / "docs/history").mkdir(parents=True)
            (root / "VERSION").write_text("0.2.0\n", encoding="utf-8")
            (root / "LICENSE").write_text("Test fixture license\n", encoding="utf-8")
            (root / "README.md").write_text("Fixture\n", encoding="utf-8")
            (root / "docs/history/llm-wiki.md").write_text(
                "https://gist.github.com/karpathy/442a6bf555914893e9891c11519de94f\n",
                encoding="utf-8",
            )
            cli_path = root / "tools/release.py"
            cli_path.parent.mkdir(parents=True)
            cli_path.write_text(RELEASE_PATH.read_text(encoding="utf-8"), encoding="utf-8")

            validated = subprocess.run(
                [
                    sys.executable,
                    str(cli_path),
                    "validate",
                    "--tag",
                    "v0.2.0",
                    "--format",
                    "json",
                ],
                cwd=root,
                capture_output=True,
                text=True,
                encoding="utf-8",
                check=False,
            )
            self.assertEqual(validated.returncode, 0, validated.stderr)
            self.assertEqual(json.loads(validated.stdout)["tag"], "v0.2.0")

            built = subprocess.run(
                [
                    sys.executable,
                    str(cli_path),
                    "build",
                    "--output",
                    str(output),
                    "--repository",
                    "owner/example",
                    "--format",
                    "json",
                ],
                cwd=root,
                capture_output=True,
                text=True,
                encoding="utf-8",
                check=False,
            )
            self.assertEqual(built.returncode, 0, built.stderr)
            payload = json.loads(built.stdout)
            self.assertEqual(payload["tag"], "v0.2.0")
            self.assertEqual(
                set(payload["files"]),
                {"codebase-llm-wiki.zip", "codebase-llm-wiki.tar.gz", "update-manifest.json", "SHA256SUMS"},
            )
            self.assertTrue((output / "SHA256SUMS").is_file())

            invalid_tag = subprocess.run(
                [
                    sys.executable,
                    str(cli_path),
                    "validate",
                    "--tag",
                    "v0.1.0",
                ],
                cwd=root,
                capture_output=True,
                text=True,
                encoding="utf-8",
                check=False,
            )
            self.assertEqual(invalid_tag.returncode, 2)
            self.assertIn("release validation failed", invalid_tag.stdout)

    def test_ci_covers_supported_linux_versions_and_windows_full_suite(self) -> None:
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
        self.assertRegex(
            workflow,
            r"os: windows-latest\s+python: \"3\.11\"\s+full: true",
        )
        self.assertIn("python -m compileall -q .agents/skills/codebase-wiki/scripts", workflow)

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
        self.assertEqual(release.repository_name(REPO_ROOT, "owner/example.git"), "owner/example")
        with self.assertRaises(release.ReleaseError):
            release.validate_tag("0.2.0", REPO_ROOT)
        with self.assertRaises(release.ReleaseError):
            release.validate_version("0.1.0-rc.1")
        for invalid in ("owner/name?query", "owner/../name", "owner/name/extra"):
            with self.subTest(invalid=invalid), self.assertRaises(release.ReleaseError):
                release.repository_name(REPO_ROOT, invalid)

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

    def test_release_cli_rejects_invalid_utf8_history_without_traceback(self) -> None:
        with tempfile.TemporaryDirectory() as directory:
            root = Path(directory) / "source"
            (root / "docs/history").mkdir(parents=True)
            (root / "VERSION").write_text("0.2.0\n", encoding="utf-8")
            (root / "LICENSE").write_text("Test fixture license\n", encoding="utf-8")
            (root / "docs/history/llm-wiki.md").write_bytes(b"\xff\xfe invalid utf-8")
            cli_path = root / "tools/release.py"
            cli_path.parent.mkdir(parents=True)
            cli_path.write_text(RELEASE_PATH.read_text(encoding="utf-8"), encoding="utf-8")

            result = subprocess.run(
                [sys.executable, str(cli_path), "validate", "--tag", "v0.2.0"],
                cwd=root,
                capture_output=True,
                text=True,
                encoding="utf-8",
                check=False,
            )

            self.assertEqual(result.returncode, 2)
            self.assertIn("release validation failed", result.stdout)
            self.assertNotIn("Traceback", result.stdout + result.stderr)

    def test_release_files_exclude_local_notebooklm_exports(self) -> None:
        release = load_release()
        with tempfile.TemporaryDirectory() as directory:
            root = Path(directory)
            (root / "VERSION").write_text("0.1.0\n", encoding="utf-8")
            (root / ".notebooklm/sources").mkdir(parents=True)
            (root / ".notebooklm/sources/private.md").write_text(
                "private\n", encoding="utf-8"
            )
            (root / ".codex-hook-logs").mkdir()
            (root / ".codex-hook-logs/audit.jsonl").write_text(
                "private audit\n", encoding="utf-8"
            )
            (root / ".github-hook-logs").mkdir()
            (root / ".github-hook-logs/audit.jsonl").write_text(
                "private audit\n", encoding="utf-8"
            )
            (root / "..notebooklm.notebooklm-transaction.json").write_text(
                "crash journal\n", encoding="utf-8"
            )
            (root / "..notebooklm.notebooklm-transaction.lock").write_bytes(b"\0")
            (root / ".target.codebase-wiki-install-transaction.json").write_text(
                "crash journal\n", encoding="utf-8"
            )
            (root / ".target.codebase-wiki-install-transaction.lock").write_bytes(b"\0")
            (root / ".target.codebase-wiki-install-transaction.json.tmp-crashed").write_text(
                "partial\n", encoding="utf-8"
            )
            for name in (
                "codebase-wiki-stage-crashed",
                "codebase-wiki-backup-crashed",
                "pack.staging-crashed",
                "pack.backup-crashed",
            ):
                (root / name).mkdir()
                (root / name / "private.md").write_text("private\n", encoding="utf-8")
            for name in (".mypy_cache", ".ruff_cache"):
                (root / name).mkdir()
                (root / name / "cache.json").write_text("generated\n", encoding="utf-8")
            (root / "README.md").write_text("readme\n", encoding="utf-8")
            files = release.release_files(root)
            self.assertEqual(
                [path.relative_to(root.resolve()).as_posix() for path in files],
                ["README.md", "VERSION"],
            )

    def test_release_builder_excludes_sensitive_paths_and_nested_output(self) -> None:
        release = load_release()
        with tempfile.TemporaryDirectory() as directory:
            root = Path(directory)
            output = root / "artifacts"
            (root / "docs/history").mkdir(parents=True)
            (root / "VERSION").write_text("0.2.0\n", encoding="utf-8")
            (root / "LICENSE").write_text("Test fixture license\n", encoding="utf-8")
            (root / "README.md").write_text("Fixture\n", encoding="utf-8")
            (root / "docs/history/llm-wiki.md").write_text(
                "https://gist.github.com/karpathy/442a6bf555914893e9891c11519de94f\n",
                encoding="utf-8",
            )
            (root / ".env").write_text("TOKEN=private\n", encoding="utf-8")
            (root / "secrets").mkdir()
            (root / "secrets/runtime.toml").write_text("token='private'\n", encoding="utf-8")
            (root / "private.pem").write_text("private key\n", encoding="utf-8")
            output.mkdir()
            (output / "old.txt").write_text("old artifact\n", encoding="utf-8")

            payload = release.build_release(output, root=root, repository="owner/example")
            names = zipfile.ZipFile(output / "codebase-llm-wiki.zip").namelist()

            self.assertTrue(payload["manifest"])
            self.assertFalse(any(name.endswith("/.env") for name in names))
            self.assertFalse(any("/secrets/" in name for name in names))
            self.assertFalse(any(name.endswith("/private.pem") for name in names))
            self.assertFalse(any("/artifacts/" in name for name in names))

            release.build_release(output, root=root, repository="owner/example")
            names_after_repeat = zipfile.ZipFile(
                output / "codebase-llm-wiki.zip"
            ).namelist()
            self.assertEqual(names, names_after_repeat)

    def test_release_builder_rejects_symlinked_output_without_overwriting_victim(self) -> None:
        release = load_release()
        with tempfile.TemporaryDirectory() as directory:
            root = Path(directory)
            output = root / "artifacts"
            victim = root / "victim.txt"
            (root / "docs/history").mkdir(parents=True)
            (root / "VERSION").write_text("0.2.0\n", encoding="utf-8")
            (root / "LICENSE").write_text("Test fixture license\n", encoding="utf-8")
            (root / "docs/history/llm-wiki.md").write_text(
                "https://gist.github.com/karpathy/442a6bf555914893e9891c11519de94f\n",
                encoding="utf-8",
            )
            output.mkdir()
            victim.write_text("must survive\n", encoding="utf-8")
            try:
                os.symlink(victim, output / "codebase-llm-wiki.zip")
            except (OSError, NotImplementedError) as exc:
                self.skipTest(f"symlink creation unavailable: {exc}")

            with self.assertRaisesRegex(release.ReleaseError, "symlink"):
                release.build_release(output, root=root, repository="owner/example")

            self.assertEqual(victim.read_text(encoding="utf-8"), "must survive\n")

    def test_release_files_reject_symlink_sources(self) -> None:
        release = load_release()
        with tempfile.TemporaryDirectory() as directory:
            root = Path(directory)
            outside = root / "outside.txt"
            outside.write_text("not a release source\n", encoding="utf-8")
            link = root / "README.md"
            try:
                os.symlink(outside, link)
            except (OSError, NotImplementedError) as exc:
                self.skipTest(f"symlink creation unavailable: {exc}")

            with self.assertRaisesRegex(release.ReleaseError, "symlink"):
                release.release_files(root)

    def test_release_files_reject_directory_reparse_sources(self) -> None:
        release = load_release()
        with tempfile.TemporaryDirectory() as directory:
            root = Path(directory)
            outside = root / "outside"
            outside.mkdir()
            (outside / "private.txt").write_text("not a release source\n", encoding="utf-8")
            try:
                create_directory_reparse_point(root / "linked", outside)
            except (OSError, NotImplementedError) as exc:
                self.skipTest(f"directory reparse point unavailable: {exc}")

            with self.assertRaisesRegex(release.ReleaseError, "reparse point"):
                release.release_files(root)


if __name__ == "__main__":
    unittest.main()
