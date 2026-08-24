from __future__ import annotations

import importlib.util
import io
import json
import os
from pathlib import Path
import subprocess
import sys
import tempfile
import unittest
from contextlib import redirect_stderr, redirect_stdout
from unittest import mock


REPO_ROOT = Path(__file__).parents[1]
SCRIPTS = REPO_ROOT / ".agents" / "skills" / "codebase-wiki" / "scripts"
sys.path.insert(0, str(SCRIPTS))

import frontmatter


def load_script(name: str, filename: str):
    path = SCRIPTS / filename
    spec = importlib.util.spec_from_file_location(name, path)
    assert spec and spec.loader
    module = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(module)
    return module


LINT = load_script("wiki_lint_under_test", "lint-wiki.py")
REBUILD = load_script("rebuild_index_under_test", "rebuild-index.py")
VALIDATE = load_script("validate_frontmatter_under_test", "validate-frontmatter.py")


def page(title: str, page_type: str, body: str = "") -> str:
    return (
        "---\n"
        f"title: {title}\n"
        f"type: {page_type}\n"
        "sources: []\n"
        "last_updated: 2026-07-29\n"
        f"tags: [{page_type}]\n"
        "status: active\n"
        "---\n\n"
        f"# {title}\n\n{body}\n"
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


class WikiLintTests(unittest.TestCase):
    def test_validate_frontmatter_cli_reports_success_failures_and_tree_errors(self) -> None:
        with tempfile.TemporaryDirectory() as directory:
            root = Path(directory)
            wiki = root / "wiki"
            wiki.mkdir()
            (wiki / "index.md").write_text(page("Index", "index"), encoding="utf-8")

            success_output = io.StringIO()
            with redirect_stdout(success_output):
                self.assertIsNone(VALIDATE.main([str(wiki)]))
            self.assertIn("OK: validated 1 wiki page(s)", success_output.getvalue())

            (wiki / "broken.md").write_text("not frontmatter\n", encoding="utf-8")
            failure_output = io.StringIO()
            with redirect_stdout(failure_output):
                with self.assertRaises(SystemExit) as failed:
                    VALIDATE.main([str(wiki)])
            self.assertEqual(failed.exception.code, 1)
            self.assertIn("FAILED: 1 issue(s)", failure_output.getvalue())

            missing_error = io.StringIO()
            with redirect_stderr(missing_error):
                with self.assertRaises(SystemExit) as missing:
                    VALIDATE.main([str(root / "missing")])
            self.assertEqual(missing.exception.code, 1)
            self.assertIn("wiki directory not found", missing_error.getvalue())

            tree_error = io.StringIO()
            with mock.patch.object(
                VALIDATE,
                "validate_regular_tree",
                side_effect=OSError("unsafe tree"),
            ), redirect_stderr(tree_error):
                with self.assertRaises(SystemExit) as unsafe:
                    VALIDATE.main([str(wiki)])
            self.assertEqual(unsafe.exception.code, 2)
            self.assertIn("unsafe tree", tree_error.getvalue())

    def test_validate_frontmatter_rejects_invalid_utf8_without_traceback(self) -> None:
        with tempfile.TemporaryDirectory() as directory:
            wiki = Path(directory) / "wiki"
            wiki.mkdir()
            (wiki / "index.md").write_bytes(b"\xff\xfe invalid utf-8")
            error = io.StringIO()

            with redirect_stderr(error):
                with self.assertRaises(SystemExit) as failed:
                    VALIDATE.main([str(wiki)])

            self.assertEqual(failed.exception.code, 2)
            self.assertIn("Error:", error.getvalue())
            self.assertNotIn("Traceback", error.getvalue())

    def test_rebuild_index_rejects_invalid_utf8_without_traceback(self) -> None:
        with tempfile.TemporaryDirectory() as directory:
            wiki = Path(directory) / "wiki"
            wiki.mkdir()
            (wiki / "index.md").write_bytes(b"\xff\xfe invalid utf-8")
            error = io.StringIO()

            with redirect_stderr(error):
                exit_code = REBUILD.main([str(wiki), "--check"])

            self.assertEqual(exit_code, 2)
            self.assertIn("Error:", error.getvalue())
            self.assertNotIn("Traceback", error.getvalue())

    def test_wiki_tools_reject_reparse_tree_before_reading_pages(self) -> None:
        with tempfile.TemporaryDirectory() as directory:
            wiki = Path(directory) / "wiki"
            wiki.mkdir()
            (wiki / "linked.md").write_text("outside\n", encoding="utf-8")

            with mock.patch.object(
                frontmatter,
                "is_reparse_point",
                side_effect=lambda path: path.name == "linked.md",
            ):
                with self.assertRaisesRegex(OSError, "symlink or reparse point"):
                    frontmatter.validate_regular_tree(wiki)
                with self.assertRaisesRegex(OSError, "symlink or reparse point"):
                    LINT.lint_wiki(wiki, Path(directory))

    def test_lint_cli_rejects_reparse_wiki_root_before_resolving(self) -> None:
        with tempfile.TemporaryDirectory() as directory:
            root = Path(directory)
            actual = root / "actual-wiki"
            actual.mkdir()
            linked = root / "wiki-link"
            try:
                create_directory_reparse_point(linked, actual)
            except (OSError, NotImplementedError) as exc:
                self.skipTest(f"directory reparse point unavailable: {exc}")

            result = subprocess.run(
                [
                    sys.executable,
                    str(SCRIPTS / "lint-wiki.py"),
                    str(linked),
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
            self.assertIn("symlink or reparse point", result.stdout)

    def test_notebooklm_group_requires_kebab_case(self) -> None:
        with tempfile.TemporaryDirectory() as directory:
            wiki = Path(directory) / "wiki"
            (wiki / "modules").mkdir(parents=True)
            valid = wiki / "modules/valid.md"
            invalid = wiki / "modules/invalid.md"
            valid.write_text(
                page("Valid", "module").replace(
                    "sources: []", "notebooklm_group: function-orders\nsources: []"
                ),
                encoding="utf-8",
            )
            invalid.write_text(
                page("Invalid", "module").replace(
                    "sources: []", "notebooklm_group: Function Orders\nsources: []"
                ),
                encoding="utf-8",
            )

            self.assertEqual(VALIDATE.validate_page(valid, wiki), [])
            self.assertIn(
                "notebooklm_group must be a non-empty kebab-case string",
                "\n".join(VALIDATE.validate_page(invalid, wiki)),
            )

    def test_cli_exit_code_contract(self) -> None:
        with tempfile.TemporaryDirectory() as directory:
            wiki = Path(directory)
            cases = (
                (0, {"critical": 0, "warning": 0}),
                (1, {"critical": 0, "warning": 1}),
                (2, {"critical": 1, "warning": 0}),
            )
            for expected, counts in cases:
                result = {
                    "ok": expected == 0,
                    "wiki_dir": wiki.as_posix(),
                    "summary": {"pages": 0, **counts, "types": {}, "statuses": {}},
                    "findings": [],
                    "agent_review_required": [],
                }
                with self.subTest(expected=expected), mock.patch.object(
                    LINT, "lint_wiki", return_value=result
                ), redirect_stdout(io.StringIO()):
                    self.assertEqual(
                        LINT.main([str(wiki), "--format", "json"]),
                        expected,
                    )
            with redirect_stdout(io.StringIO()), redirect_stderr(io.StringIO()):
                self.assertEqual(
                    LINT.main([str(wiki / "missing"), "--format", "json"]),
                    2,
                )

    def test_reports_broken_orphan_and_index_missing_as_json(self) -> None:
        with tempfile.TemporaryDirectory() as directory:
            root = Path(directory)
            wiki = root / "wiki"
            (wiki / "modules").mkdir(parents=True)
            (wiki / "index.md").write_text(page("Index", "index"), encoding="utf-8")
            (wiki / "log.md").write_text(page("Log", "log"), encoding="utf-8")
            (wiki / "modules/orders.md").write_text(
                page("Orders", "module", "[[missing-page]]"), encoding="utf-8"
            )

            result = LINT.lint_wiki(wiki, root)
            codes = {item["code"] for item in result["findings"]}

            self.assertIn("broken_wikilink", codes)
            self.assertIn("orphan", codes)
            self.assertIn("index_missing", codes)
            self.assertEqual(
                {item["status"] for item in result["agent_review_required"]},
                {"agent_review_required"},
            )
            self.assertEqual(result["deterministic_status"], "critical")
            self.assertEqual(result["semantic_status"], "review_required")
            self.assertEqual(result["overall_status"], "critical")

    def test_index_and_self_links_do_not_hide_orphans(self) -> None:
        with tempfile.TemporaryDirectory() as directory:
            root = Path(directory)
            wiki = root / "wiki"
            (wiki / "modules").mkdir(parents=True)
            (wiki / "guides").mkdir()
            (wiki / "index.md").write_text(
                page("Index", "index", "## Modules\n\n[[orders]]\n\n## Guides\n\n[[usage]]"),
                encoding="utf-8",
            )
            (wiki / "log.md").write_text(page("Log", "log"), encoding="utf-8")
            (wiki / "modules/orders.md").write_text(
                page("Orders", "module", "[[orders]]"), encoding="utf-8"
            )
            (wiki / "guides/usage.md").write_text(
                page("Usage", "guide", "See [[orders]]."), encoding="utf-8"
            )

            result = LINT.lint_wiki(wiki, root)
            orphan_pages = {
                item["page"] for item in result["findings"] if item["code"] == "orphan"
            }

            self.assertIn("guides/usage.md", orphan_pages)
            self.assertNotIn("modules/orders.md", orphan_pages)

    def test_invalid_source_has_stable_json_details(self) -> None:
        with tempfile.TemporaryDirectory() as directory:
            root = Path(directory)
            wiki = root / "wiki"
            wiki.mkdir()
            (wiki / "index.md").write_text(
                page("Index", "index", "[[unsafe]]"), encoding="utf-8"
            )
            (wiki / "log.md").write_text(page("Log", "log"), encoding="utf-8")
            unsafe = page("Unsafe", "module").replace(
                "sources: []", "sources:\n  - ../outside.py"
            )
            (wiki / "unsafe.md").write_text(unsafe, encoding="utf-8")

            first = LINT.lint_wiki(wiki, root)
            second = LINT.lint_wiki(wiki, root)
            self.assertEqual(
                json.dumps(first, ensure_ascii=False, sort_keys=True),
                json.dumps(second, ensure_ascii=False, sort_keys=True),
            )
            invalid = next(
                item for item in first["findings"] if item["code"] == "invalid_source"
            )
            self.assertEqual(invalid["severity"], "critical")
            self.assertEqual(invalid["details"]["sources"], ["../outside.py"])

    def test_windows_drive_source_is_rejected_by_frontmatter_and_lint(self) -> None:
        with tempfile.TemporaryDirectory() as directory:
            root = Path(directory)
            wiki = root / "wiki"
            wiki.mkdir()
            drive_page = wiki / "drive.md"
            drive_page.write_text(
                page("Drive", "module").replace(
                    "sources: []", "sources:\n  - C:/outside.py"
                ),
                encoding="utf-8",
            )

            self.assertTrue(
                any(
                    "source must stay inside" in error
                    for error in VALIDATE.validate_page(drive_page, wiki)
                )
            )
            result = LINT.lint_wiki(wiki, root)
            invalid = next(
                item for item in result["findings"] if item["code"] == "invalid_source"
            )
            self.assertEqual(invalid["details"]["sources"], ["C:/outside.py"])

    def test_stale_source_has_stable_json_details(self) -> None:
        with tempfile.TemporaryDirectory() as directory:
            root = Path(directory)
            wiki = root / "wiki"
            wiki.mkdir()
            source = root / "service.py"
            source.write_text("VERSION = 1\n", encoding="utf-8")
            (wiki / "index.md").write_text(
                page("Index", "index", "[[service]]"), encoding="utf-8"
            )
            (wiki / "log.md").write_text(page("Log", "log"), encoding="utf-8")
            service_page = page("Service", "module").replace(
                "sources: []", "sources:\n  - service.py"
            )
            (wiki / "service.md").write_text(service_page, encoding="utf-8")
            for command in (
                ["git", "init", "-q"],
                ["git", "config", "user.email", "tests@example.invalid"],
                ["git", "config", "user.name", "Wiki Tests"],
                ["git", "add", "."],
                ["git", "commit", "-q", "-m", "baseline"],
            ):
                subprocess.run(command, cwd=root, check=True, capture_output=True)
            source.write_text("VERSION = 2\n", encoding="utf-8")

            result = LINT.lint_wiki(wiki, root)
            stale = next(
                item for item in result["findings"] if item["code"] == "stale_source"
            )
            self.assertEqual(stale["severity"], "warning")
            self.assertEqual(stale["page"], "service.md")
            self.assertEqual(stale["details"]["sources"], ["service.py"])

    def test_rebuild_index_check_is_read_only(self) -> None:
        with tempfile.TemporaryDirectory() as directory:
            wiki = Path(directory) / "wiki"
            (wiki / "modules").mkdir(parents=True)
            (wiki / "modules/orders.md").write_text(
                page("Orders", "module"), encoding="utf-8"
            )
            index = wiki / "index.md"
            index.write_text(
                page("Index", "index", "## Modules\n\n[[orders]]"),
                encoding="utf-8",
            )
            before = index.read_bytes()

            output = io.StringIO()
            with redirect_stdout(output):
                exit_code = REBUILD.main([str(wiki), "--check"])

            self.assertEqual(exit_code, 0, output.getvalue())
            self.assertEqual(index.read_bytes(), before)

    def test_rebuild_index_preserves_content_outside_managed_region(self) -> None:
        with tempfile.TemporaryDirectory() as directory:
            wiki = Path(directory) / "wiki"
            (wiki / "modules").mkdir(parents=True)
            (wiki / "modules/orders.md").write_text(
                page("Orders", "module"), encoding="utf-8"
            )
            index = wiki / "index.md"
            index.write_text(
                page(
                    "Index",
                    "index",
                    "Manual introduction.\n\n"
                    f"{REBUILD.MANAGED_START}\n\n## Modules\n\n_old_\n\n"
                    f"{REBUILD.MANAGED_END}\n\n## Team notes\n\nKeep me.",
                ),
                encoding="utf-8",
            )

            rebuilt = REBUILD.rebuild_index(wiki)

            self.assertIn("Manual introduction.", rebuilt)
            self.assertIn("## Team notes\n\nKeep me.", rebuilt)
            self.assertIn("[[orders]]", rebuilt)
            self.assertNotIn("_old_", rebuilt)

    def test_rebuild_index_check_detects_wrong_type_section_without_writing(self) -> None:
        with tempfile.TemporaryDirectory() as directory:
            wiki = Path(directory) / "wiki"
            (wiki / "modules").mkdir(parents=True)
            (wiki / "modules/orders.md").write_text(
                page("Orders", "module"), encoding="utf-8"
            )
            index = wiki / "index.md"
            index.write_text(
                page("Index", "index", "## Guides\n\n[[orders]]"),
                encoding="utf-8",
            )
            before = index.read_bytes()

            output = io.StringIO()
            with redirect_stdout(output):
                exit_code = REBUILD.main([str(wiki), "--check"])

            self.assertEqual(exit_code, 1)
            self.assertIn("Wrong section for orders", output.getvalue())
            self.assertEqual(index.read_bytes(), before)

    def test_rebuild_index_rejects_reparse_tree_before_writing(self) -> None:
        with tempfile.TemporaryDirectory() as directory:
            wiki = Path(directory) / "wiki"
            wiki.mkdir()
            index = wiki / "index.md"
            index.write_text(page("Index", "index"), encoding="utf-8")
            before = index.read_bytes()
            with mock.patch.object(
                REBUILD,
                "_is_reparse_point",
                side_effect=lambda path: path == index,
            ):
                output = io.StringIO()
                with redirect_stderr(output):
                    exit_code = REBUILD.main([str(wiki)])

            self.assertEqual(exit_code, 2)
            self.assertIn("symlink or reparse point", output.getvalue())
            self.assertEqual(index.read_bytes(), before)

    def test_check_stale_cli_handles_invalid_sources(self) -> None:
        with tempfile.TemporaryDirectory() as directory:
            root = Path(directory)
            wiki = root / "wiki"
            wiki.mkdir()
            (wiki / "unsafe.md").write_text(
                "---\ntitle: Unsafe\ntype: module\nsources:\n"
                "  - ../outside.py\nlast_updated: 2026-07-29\n"
                "tags: [module]\nstatus: active\n---\n",
                encoding="utf-8",
            )

            result = subprocess.run(
                [sys.executable, str(SCRIPTS / "check-stale.py"), str(wiki), str(root)],
                capture_output=True,
                text=True,
                encoding="utf-8",
                errors="replace",
                check=False,
            )

            self.assertEqual(result.returncode, 1)
            self.assertIn("invalid:", result.stdout)
            self.assertNotIn("Traceback", result.stderr)


if __name__ == "__main__":
    unittest.main()
