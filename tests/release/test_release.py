from __future__ import annotations

import importlib.util
import json
import os
import shutil
from pathlib import Path
import subprocess
import sys
import tempfile
import unittest
import zipfile


REPO_ROOT = Path(__file__).parents[2]
RELEASE_PATH = REPO_ROOT / "tools" / "release.py"
TGREP_BINARY = REPO_ROOT / ".agents/skills/codebase-wiki/bin/windows-x64/tgrep.exe"
TGREP_SHA256 = "9b90e4446e2cbf05e1da086547501e35d7b32f0f6d5f687548cf270b07fbd9d7"


def add_bundled_tgrep(root: Path) -> None:
    binary = root / ".agents/skills/codebase-wiki/bin/windows-x64/tgrep.exe"
    binary.parent.mkdir(parents=True, exist_ok=True)
    shutil.copyfile(TGREP_BINARY, binary)
    (root / ".agents/skills/codebase-wiki/bin/tgrep-manifest.json").write_text(
        json.dumps(
            {
                "schema_version": 1,
                "tool": "tgrep",
                "version": "1.0.5",
                "platform": "windows-x86_64",
                "binary": "bin/windows-x64/tgrep.exe",
                "sha256": TGREP_SHA256,
                "upstream_release": "https://github.com/microsoft/tgrep/releases/tag/v1.0.5",
            },
            indent=2,
        )
        + "\n",
        encoding="utf-8",
    )


def add_release_package_surfaces(root: Path) -> None:
    """Create the minimal two-surface source expected by the release builder."""

    skill = root / ".agents/skills/codebase-wiki"
    (skill / "assets/wiki-starter").mkdir(parents=True, exist_ok=True)
    (skill / "scripts").mkdir(parents=True, exist_ok=True)
    (skill / "SKILL.md").write_text("shared skill\n", encoding="utf-8")
    shutil.copyfile(
        REPO_ROOT / ".agents/skills/codebase-wiki/scripts/install-framework.py",
        skill / "scripts/install-framework.py",
    )
    shutil.copyfile(
        REPO_ROOT / ".agents/skills/codebase-wiki/assets/target-agents-block.md",
        skill / "assets/target-agents-block.md",
    )
    (skill / "assets/wiki-starter/overview.md").write_text("starter\n", encoding="utf-8")
    (root / "AGENTS.md").write_text("framework rules\n", encoding="utf-8")
    (root / "Codex.md").write_text("codex adapter\n", encoding="utf-8")
    (root / ".codex").mkdir(exist_ok=True)
    (root / ".codex/config.toml").write_text("[wiki_guard]\nmode = 'framework'\n", encoding="utf-8")
    (root / ".github/prompts").mkdir(parents=True, exist_ok=True)
    (root / ".github/instructions").mkdir(parents=True, exist_ok=True)
    (root / ".github/hooks").mkdir(parents=True, exist_ok=True)
    (root / ".github/copilot-instructions.md").write_text("copilot adapter\n", encoding="utf-8")
    (root / ".github/prompts/query-wiki.prompt.md").write_text("query\n", encoding="utf-8")
    (root / ".github/instructions/wiki-pages.instructions.md").write_text("pages\n", encoding="utf-8")
    (root / ".github/hooks/config.toml").write_text("[wiki_guard]\nmode = 'framework'\n", encoding="utf-8")


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
            add_bundled_tgrep(root)
            add_release_package_surfaces(root)
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
            self.assertEqual(payload["bundled_tools"][0]["tool"], "tgrep")
            self.assertEqual(payload["bundled_tools"][0]["sha256"], TGREP_SHA256)
            self.assertEqual(
                set(payload["files"]),
                {
                    "codebase-llm-wiki-codex.zip",
                    "codebase-llm-wiki-copilot.zip",
                    "update-manifest.json",
                    "SHA256SUMS",
                },
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

    def test_release_guide_names_the_exact_release_assets(self) -> None:
        guide = (REPO_ROOT / "docs" / "operations" / "releases" / "README.md").read_text(
            encoding="utf-8"
        )
        for required in (
            "python tools/release.py validate --tag",
            "python tools/release.py build --output dist",
            "gh release create",
            "dist/codebase-llm-wiki-codex.zip",
            "dist/codebase-llm-wiki-copilot.zip",
            "dist/update-manifest.json",
            "dist/SHA256SUMS",
            "bundled_tools",
            ".tgrep/",
            "--verify-tag",
            "--generate-notes",
        ):
            with self.subTest(required=required):
                self.assertIn(required, guide)

    def test_version_is_stable_semver_and_tag_matches(self) -> None:
        release = load_release()
        self.assertEqual(release.read_version(REPO_ROOT), "0.2.1")
        self.assertEqual(release.validate_tag("v0.2.1", REPO_ROOT), "0.2.1")
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
            add_bundled_tgrep(source_root)
            add_release_package_surfaces(source_root)
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
                    "bundled_tools",
                },
            )
            self.assertEqual(manifest["schema_version"], 2)
            self.assertEqual(manifest["installer_contract_version"], 6)
            self.assertEqual(manifest["release_url"], "https://github.com/owner/example/releases/tag/v0.2.0")
            self.assertEqual(
                manifest["bundled_tools"],
                [
                    {
                        "tool": "tgrep",
                        "version": "1.0.5",
                        "platform": "windows-x86_64",
                        "path": ".agents/skills/codebase-wiki/bin/windows-x64/tgrep.exe",
                        "sha256": TGREP_SHA256,
                        "source_url": "https://github.com/microsoft/tgrep/releases/tag/v1.0.5",
                    }
                ],
            )
            self.assertEqual(
                [(asset["surface"], asset["name"]) for asset in manifest["assets"]],
                [
                    ("codex", "codebase-llm-wiki-codex.zip"),
                    ("copilot", "codebase-llm-wiki-copilot.zip"),
                ],
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

            zip_names_by_surface = {
                surface: zipfile.ZipFile(output / f"codebase-llm-wiki-{surface}.zip").namelist()
                for surface in ("codex", "copilot")
            }
            for surface, names in zip_names_by_surface.items():
                self.assertTrue(any(name.endswith(f"codebase-llm-wiki-{surface}-0.2.0/README.md") for name in names))
                self.assertTrue(any(name.endswith("/AGENTS.md") for name in names))
                self.assertTrue(any(name.endswith("/VERSION") for name in names))
                self.assertFalse(any("/docs/" in name for name in names))
                self.assertFalse(any("/tests/" in name for name in names))
                self.assertFalse(any("/wiki/" in name for name in names))
                self.assertFalse(any("/.git/" in name for name in names))
                self.assertFalse(any("/__pycache__/" in name for name in names))
                self.assertFalse(any("/logs/" in name for name in names))
                if surface == "codex":
                    self.assertTrue(any(name.endswith("/Codex.md") for name in names))
                    self.assertTrue(any("/.codex/" in name for name in names))
                    self.assertFalse(any("/.github/" in name for name in names))
                else:
                    self.assertTrue(any(name.endswith("/.github/copilot-instructions.md") for name in names))
                    self.assertTrue(any("/.github/prompts/" in name for name in names))
                    self.assertFalse(any("/.codex/" in name for name in names))
                self.assertTrue(
                    any(
                        name.endswith(
                            "/.agents/skills/codebase-wiki/bin/windows-x64/tgrep.exe"
                        )
                        for name in names
                    )
                )

    def test_public_release_readiness_passes_with_the_selected_license(self) -> None:
        release = load_release()
        release.validate_release_readiness(REPO_ROOT)

    def test_surface_archives_install_and_reject_the_wrong_surface_before_writes(self) -> None:
        release = load_release()
        with tempfile.TemporaryDirectory() as directory:
            root = Path(directory) / "source"
            output = Path(directory) / "dist"
            (root / "docs/history").mkdir(parents=True)
            (root / "VERSION").write_text("0.2.0\n", encoding="utf-8")
            (root / "LICENSE").write_text("Test fixture license\n", encoding="utf-8")
            (root / "docs/history/llm-wiki.md").write_text(
                "https://gist.github.com/karpathy/442a6bf555914893e9891c11519de94f\n",
                encoding="utf-8",
            )
            add_bundled_tgrep(root)
            add_release_package_surfaces(root)
            release.build_release(output, root=root, repository="owner/example")

            with tempfile.TemporaryDirectory() as extracted_directory:
                extracted = Path(extracted_directory)
                with zipfile.ZipFile(output / "codebase-llm-wiki-codex.zip") as archive:
                    archive.extractall(extracted)
                package_root = extracted / "codebase-llm-wiki-codex-0.2.0"
                installer = package_root / ".agents/skills/codebase-wiki/scripts/install-framework.py"
                target = Path(directory) / "target"
                target.mkdir()

                preview = subprocess.run(
                    [
                        sys.executable,
                        str(installer),
                        "install",
                        "--target",
                        str(target),
                        "--surface",
                        "codex",
                        "--format",
                        "json",
                    ],
                    capture_output=True,
                    text=True,
                    encoding="utf-8",
                    check=False,
                )
                self.assertEqual(preview.returncode, 0, preview.stdout + preview.stderr)
                self.assertEqual(list(target.iterdir()), [])

                applied = subprocess.run(
                    [
                        sys.executable,
                        str(installer),
                        "install",
                        "--target",
                        str(target),
                        "--surface",
                        "codex",
                        "--apply",
                        "--format",
                        "json",
                    ],
                    capture_output=True,
                    text=True,
                    encoding="utf-8",
                    check=False,
                )
                self.assertEqual(applied.returncode, 0, applied.stdout + applied.stderr)
                local_note = target / "wiki/local-note.md"
                local_note.write_text("keep me\n", encoding="utf-8")
                upgraded = subprocess.run(
                    [
                        sys.executable,
                        str(installer),
                        "upgrade",
                        "--target",
                        str(target),
                        "--surface",
                        "codex",
                        "--apply",
                        "--format",
                        "json",
                    ],
                    capture_output=True,
                    text=True,
                    encoding="utf-8",
                    check=False,
                )
                self.assertEqual(upgraded.returncode, 0, upgraded.stdout + upgraded.stderr)
                self.assertEqual(local_note.read_text(encoding="utf-8"), "keep me\n")

                wrong_surface_target = Path(directory) / "wrong-surface-target"
                wrong_surface_target.mkdir()
                wrong = subprocess.run(
                    [
                        sys.executable,
                        str(installer),
                        "install",
                        "--target",
                        str(wrong_surface_target),
                        "--surface",
                        "copilot",
                        "--apply",
                        "--format",
                        "json",
                    ],
                    capture_output=True,
                    text=True,
                    encoding="utf-8",
                    check=False,
                )
                self.assertEqual(wrong.returncode, 2)
                self.assertEqual(list(wrong_surface_target.iterdir()), [])

                copilot_extracted = Path(extracted_directory) / "copilot"
                copilot_extracted.mkdir()
                with zipfile.ZipFile(output / "codebase-llm-wiki-copilot.zip") as archive:
                    archive.extractall(copilot_extracted)
                copilot_root = copilot_extracted / "codebase-llm-wiki-copilot-0.2.0"
                copilot_installer = copilot_root / ".agents/skills/codebase-wiki/scripts/install-framework.py"
                copilot_target = Path(directory) / "copilot-target"
                copilot_target.mkdir()
                for action, apply_flag in (("install", False), ("install", True), ("upgrade", True)):
                    arguments = [
                        sys.executable,
                        str(copilot_installer),
                        action,
                        "--target",
                        str(copilot_target),
                        "--surface",
                        "copilot",
                    ]
                    if apply_flag:
                        arguments.append("--apply")
                    arguments.append("--format")
                    arguments.append("json")
                    result = subprocess.run(
                        arguments,
                        capture_output=True,
                        text=True,
                        encoding="utf-8",
                        check=False,
                    )
                    self.assertEqual(result.returncode, 0, result.stdout + result.stderr)
                self.assertTrue((copilot_target / ".github/copilot-instructions.md").exists())

    def test_release_rejects_bundled_tgrep_metadata_or_hash_drift(self) -> None:
        release = load_release()
        with tempfile.TemporaryDirectory() as directory:
            root = Path(directory)
            add_bundled_tgrep(root)
            manifest_path = root / ".agents/skills/codebase-wiki/bin/tgrep-manifest.json"
            metadata = json.loads(manifest_path.read_text(encoding="utf-8"))

            metadata["version"] = "1.0.4"
            manifest_path.write_text(json.dumps(metadata), encoding="utf-8")
            with self.assertRaisesRegex(release.ReleaseError, "manifest mismatch for version"):
                release.bundled_tool_metadata(root)

            metadata["version"] = "1.0.5"
            manifest_path.write_text(json.dumps(metadata), encoding="utf-8")
            binary = root / ".agents/skills/codebase-wiki/bin/windows-x64/tgrep.exe"
            binary.write_bytes(binary.read_bytes() + b"drift")
            with self.assertRaisesRegex(release.ReleaseError, "SHA-256 mismatch"):
                release.bundled_tool_metadata(root)

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
            (root / ".tgrep/index/state.bin").parent.mkdir(parents=True)
            (root / ".tgrep/index/state.bin").write_bytes(b"generated index\n")
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
            add_bundled_tgrep(root)
            add_release_package_surfaces(root)
            (root / ".env").write_text("TOKEN=private\n", encoding="utf-8")
            (root / "secrets").mkdir()
            (root / "secrets/runtime.toml").write_text("token='private'\n", encoding="utf-8")
            (root / "private.pem").write_text("private key\n", encoding="utf-8")
            output.mkdir()
            (output / "old.txt").write_text("old artifact\n", encoding="utf-8")

            payload = release.build_release(output, root=root, repository="owner/example")
            self.assertTrue(payload["manifest"])
            names_by_surface = {
                surface: zipfile.ZipFile(output / f"codebase-llm-wiki-{surface}.zip").namelist()
                for surface in ("codex", "copilot")
            }
            for names in names_by_surface.values():
                self.assertFalse(any(name.endswith("/.env") for name in names))
                self.assertFalse(any("/secrets/" in name for name in names))
                self.assertFalse(any(name.endswith("/private.pem") for name in names))
                self.assertFalse(any("/artifacts/" in name for name in names))
                self.assertTrue(
                    any(
                        name.endswith(
                            "/.agents/skills/codebase-wiki/bin/windows-x64/tgrep.exe"
                        )
                        for name in names
                    )
                )

            release.build_release(output, root=root, repository="owner/example")
            for surface, names in names_by_surface.items():
                names_after_repeat = zipfile.ZipFile(
                    output / f"codebase-llm-wiki-{surface}.zip"
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
                os.symlink(victim, output / "codebase-llm-wiki-codex.zip")
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
