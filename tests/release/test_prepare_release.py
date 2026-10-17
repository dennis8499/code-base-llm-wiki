"""Metadata preparation reuses complete analysis and rejects unrelated edits."""
import importlib.util
from pathlib import Path
import shutil
import subprocess
import tempfile
import unittest

ROOT = Path(__file__).resolve().parents[2]
spec = importlib.util.spec_from_file_location("wiki_prepare_under_test", ROOT / "tools/prepare_release.py")
release = importlib.util.module_from_spec(spec)
spec.loader.exec_module(release)


def git(root, *arguments):
    return subprocess.check_output(["git", "-c", f"safe.directory={root.resolve()}",
        "-c", "core.hooksPath=/dev/null", "-C", str(root), *arguments], stderr=subprocess.DEVNULL).decode().strip()


class ReadmeMetadataTests(unittest.TestCase):
    def test_active_install_and_use_sections_advance_but_version_history_is_preserved(self):
        original = ("# Product 1.2.3\n\n## Install\nDownload merge-reviewer-1.2.3.zip\n"
                    "## v1.2.3 - history\nDownload merge-reviewer-1.2.3.zip\n"
                    "python scripts/package_release.py --tag v1.2.3\n"
                    "## Use\nInstall dist/gitlab-workspace-1.2.3.vsix\n"
                    "python scripts/package_release.py --tag v1.2.3\n")
        result = release.bumped_readme(original.encode(), "1.2.3", "1.2.4").decode()
        self.assertTrue(result.startswith("# Product 1.2.4"))
        self.assertIn("## Install\nDownload merge-reviewer-1.2.4.zip", result)
        self.assertIn("## Use\nInstall dist/gitlab-workspace-1.2.4.vsix", result)
        self.assertIn("## v1.2.3 - history\nDownload merge-reviewer-1.2.3.zip\n"
                      "python scripts/package_release.py --tag v1.2.3", result)
        self.assertEqual(result.count("--tag v1.2.4"), 1)


class MetadataPreparationTests(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        cls.storage = tempfile.TemporaryDirectory(prefix="wiki-prepare-test-")
        cls.addClassCleanup(cls.storage.cleanup)
        cls.seed = Path(cls.storage.name) / "seed"
        cls.seed.mkdir()
        names = release.git(ROOT, "ls-files", "--cached", "--others", "--exclude-standard", "-z").split(b"\0")
        for name in names:
            if name and (ROOT / name.decode()).is_file():
                relative = name.decode()
                destination = cls.seed / relative
                destination.parent.mkdir(parents=True, exist_ok=True)
                shutil.copyfile(ROOT / relative, destination)
        git(cls.seed, "init", "-b", "main")
        git(cls.seed, "config", "user.name", "Release test")
        git(cls.seed, "config", "user.email", "release-test@example.invalid")
        git(cls.seed, "add", "--all")
        git(cls.seed, "commit", "-m", "analyzed release candidate fixture")
        cls.baseline = git(cls.seed, "rev-parse", "HEAD")
        cls.previous = (cls.seed / "VERSION").read_text(encoding="utf-8").strip()
        major, minor, patch = map(int, cls.previous.split("."))
        cls.version = f"{major}.{minor}.{patch + 1}"

    def setUp(self):
        temporary = tempfile.TemporaryDirectory(prefix="wiki-prepare-case-")
        self.addCleanup(temporary.cleanup)
        self.root = Path(temporary.name) / "wiki"
        subprocess.run(["git", "-c", f"safe.directory={self.seed.resolve()}", "clone", "--local",
                        str(self.seed), str(self.root)], check=True, stdout=subprocess.DEVNULL, stderr=subprocess.DEVNULL)
        self.bump()

    def bump(self):
        (self.root / "VERSION").write_bytes((self.version + "\n").encode())
        readme = self.root / "README.md"
        readme.write_bytes(release.bumped_readme(readme.read_bytes(), self.previous, self.version))

    def wiki_bytes(self):
        return {path.relative_to(self.root).as_posix(): path.read_bytes() for path in (self.root / "wiki").rglob("*.md")}

    def test_next_version_is_ready_without_reanalysis_and_retry_is_byte_identical(self):
        before = self.wiki_bytes()
        result = release.prepare(self.root, self.baseline, self.version)
        self.assertTrue(result["ready_to_export"] and result["analysis_reused"])
        self.assertTrue(result["updated_paths"])
        after = self.wiki_bytes()
        self.assertTrue(release.preflight(self.root)["ready_to_export"])
        ledger = "wiki/synthesis/codebase-functional-coverage.md"
        self.assertEqual(sum(line.startswith(b"| `") for line in before[ledger].splitlines()),
                         sum(line.startswith(b"| `") for line in after[ledger].splitlines()))
        repeat = release.prepare(self.root, self.baseline, self.version)
        self.assertTrue(repeat["idempotent"])
        self.assertEqual(after, self.wiki_bytes())

    def test_unanalyzed_source_or_arbitrary_readme_edit_is_rejected_before_writes(self):
        before = self.wiki_bytes()
        source = self.root / "tools/release.py"
        original = source.read_bytes()
        source.write_bytes(original + b"\n# unreviewed behavior\n")
        with self.assertRaisesRegex(release.PreparationError, "Unanalyzed source"):
            release.prepare(self.root, self.baseline, self.version)
        self.assertEqual(before, self.wiki_bytes())
        source.write_bytes(original)
        readme = self.root / "README.md"
        readme.write_bytes(readme.read_bytes() + b"\nUnreviewed product claim\n")
        with self.assertRaisesRegex(release.PreparationError, "Unexpected release metadata"):
            release.prepare(self.root, self.baseline, self.version)
        self.assertEqual(before, self.wiki_bytes())

    def test_existing_wiki_notes_and_new_source_files_are_preserved_and_block_preparation(self):
        overview = self.root / "wiki/overview.md"
        original = overview.read_bytes()
        overview.write_bytes(original + b"\nUser-authored note\n")
        before = self.wiki_bytes()
        with self.assertRaisesRegex(release.PreparationError, "Unexpected Wiki change"):
            release.prepare(self.root, self.baseline, self.version)
        self.assertEqual(before, self.wiki_bytes())
        overview.write_bytes(original)
        (self.root / "unreviewed.py").write_bytes(b"pass\n")
        with self.assertRaisesRegex(release.PreparationError, "cannot add or remove"):
            release.prepare(self.root, self.baseline, self.version)

    def test_incomplete_baseline_analysis_cannot_be_refreshed_into_readiness(self):
        git(self.root, "config", "user.name", "Release test")
        git(self.root, "config", "user.email", "release-test@example.invalid")
        git(self.root, "reset", "--hard", self.baseline)
        ledger = self.root / "wiki/synthesis/codebase-functional-coverage.md"
        ledger.write_bytes(ledger.read_bytes().replace(b"Analyzed discovery ID:", b"Unreviewed discovery ID:", 1))
        git(self.root, "add", "wiki/synthesis/codebase-functional-coverage.md")
        git(self.root, "commit", "-m", "incomplete analysis fixture")
        baseline = git(self.root, "rev-parse", "HEAD")
        self.bump()
        before = self.wiki_bytes()
        with self.assertRaisesRegex(release.PreparationError, "Baseline Wiki analysis must already be ready"):
            release.prepare(self.root, baseline, self.version)
        self.assertEqual(before, self.wiki_bytes())


if __name__ == "__main__":
    unittest.main()
