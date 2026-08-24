from __future__ import annotations

import importlib.util
import os
from pathlib import Path
import subprocess
import sys
import tempfile
import unittest
from unittest import mock


REPO_ROOT = Path(__file__).parents[1]
SCRIPTS = REPO_ROOT / ".agents/skills/codebase-wiki/scripts"
sys.path.insert(0, str(SCRIPTS))


def load_validator():
    spec = importlib.util.spec_from_file_location(
        "validate_log_under_test", SCRIPTS / "validate-log.py"
    )
    assert spec and spec.loader
    module = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(module)
    return module


def log_text(entry: str, last_updated: str = "2026-08-21") -> str:
    return (
        "---\n"
        "title: Wiki Activity Log\n"
        "type: log\n"
        "sources: []\n"
        f"last_updated: {last_updated}\n"
        "tags: [log]\n"
        "status: active\n"
        "---\n\n"
        "# Activity Log\n\n"
        "<!-- codebase-wiki:log-contract-v1 -->\n\n"
        f"{entry}"
    )


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


class LogIntegrityTests(unittest.TestCase):
    def test_log_validator_rejects_unsafe_tree_before_reading(self) -> None:
        validator = load_validator()
        with tempfile.TemporaryDirectory() as directory:
            root = Path(directory)
            wiki = root / "wiki"
            wiki.mkdir()
            log = wiki / "log.md"
            log.write_text(log_text(""), encoding="utf-8")
            with mock.patch.object(
                validator,
                "validate_regular_tree",
                side_effect=OSError("symlink or reparse point"),
            ):
                result = validator.validate_log(log, root)

            self.assertFalse(result["ok"])
            self.assertIn("unsafe Wiki log path", result["errors"][0])

    def test_log_cli_rejects_reparse_parent_before_resolving(self) -> None:
        load_validator()
        with tempfile.TemporaryDirectory() as directory:
            root = Path(directory)
            actual = root / "actual-wiki"
            actual.mkdir()
            (actual / "log.md").write_text(log_text(""), encoding="utf-8")
            linked = root / "wiki-link"
            try:
                create_directory_reparse_point(linked, actual)
            except (OSError, NotImplementedError) as exc:
                self.skipTest(f"directory reparse point unavailable: {exc}")

            result = subprocess.run(
                [
                    sys.executable,
                    str(SCRIPTS / "validate-log.py"),
                    str(linked / "log.md"),
                    "--repo-root",
                    str(root),
                    "--format",
                    "json",
                ],
                check=False,
                capture_output=True,
                text=True,
                encoding="utf-8",
                errors="replace",
            )
            self.assertEqual(result.returncode, 2)
            self.assertIn("unsafe Wiki log path", result.stdout)

    def test_strict_entry_requires_resolvable_affected_pages(self) -> None:
        validator = load_validator()
        with tempfile.TemporaryDirectory() as directory:
            root = Path(directory)
            (root / "wiki").mkdir()
            (root / "wiki/index.md").write_text("# Index\n", encoding="utf-8")
            log = root / "wiki/log.md"
            log.write_text(
                log_text(
                    "## [2026-08-21] update | Contract\n\n"
                    "- Affected pages: [[index]]\n"
                ),
                encoding="utf-8",
            )

            result = validator.validate_log(log, root)

            self.assertTrue(result["ok"])
            self.assertEqual(result["entries"], 1)

            log.write_text(
                log_text("## [2026-08-21] update | Contract\n\n- No pages\n"),
                encoding="utf-8",
            )
            self.assertFalse(validator.validate_log(log, root)["ok"])

    def test_log_dates_and_frontmatter_are_monotonic(self) -> None:
        validator = load_validator()
        with tempfile.TemporaryDirectory() as directory:
            root = Path(directory)
            (root / "wiki").mkdir()
            (root / "wiki/index.md").write_text("# Index\n", encoding="utf-8")
            log = root / "wiki/log.md"
            log.write_text(
                log_text(
                    "## [2026-08-21] update | Newer\n\n"
                    "- Affected pages: [[index]]\n\n"
                    "## [2026-08-20] update | Older\n\n"
                    "- Affected pages: [[index]]\n",
                    last_updated="2026-08-20",
                ),
                encoding="utf-8",
            )

            result = validator.validate_log(log, root)

            self.assertFalse(result["ok"])
            self.assertTrue(any("nondecreasing" in item for item in result["errors"]))
            self.assertTrue(any("last_updated" in item for item in result["errors"]))

    def test_git_baseline_body_is_append_only(self) -> None:
        validator = load_validator()
        with tempfile.TemporaryDirectory() as directory:
            root = Path(directory)
            (root / "wiki").mkdir()
            (root / "wiki/index.md").write_text("# Index\n", encoding="utf-8")
            log = root / "wiki/log.md"
            original = log_text(
                "## [2026-08-20] update | Original\n\n"
                "- Affected pages: [[index]]\n",
                last_updated="2026-08-20",
            )
            log.write_text(original, encoding="utf-8")
            for command in (
                ["git", "init", "-q"],
                ["git", "config", "user.email", "tests@example.invalid"],
                ["git", "config", "user.name", "Wiki Tests"],
                ["git", "add", "."],
                ["git", "commit", "-q", "-m", "baseline"],
            ):
                subprocess.run(command, cwd=root, check=True, capture_output=True)
            log.write_text(original.replace("Original", "Rewritten"), encoding="utf-8")

            result = validator.validate_log(log, root)

            self.assertFalse(result["ok"])
            self.assertTrue(any("append-only" in item for item in result["errors"]))


if __name__ == "__main__":
    unittest.main()
