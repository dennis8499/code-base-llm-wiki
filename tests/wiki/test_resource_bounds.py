from __future__ import annotations

import importlib.util
import io
import os
from pathlib import Path
import subprocess
import stat
import sys
import tempfile
from types import SimpleNamespace
import unittest
from unittest import mock

SCRIPTS = Path(__file__).parents[2] / ".agents/skills/codebase-wiki/scripts"
sys.path.insert(0, str(SCRIPTS))
from bounded_process import ProcessLimitError, run_bounded
from offline_git import run_git
import project_scanner as scanner


class ResourceBoundsTests(unittest.TestCase):
    def test_output_and_deadline_fail_as_incomplete_not_partial_success(self):
        with self.assertRaisesRegex(ProcessLimitError, "output exceeded"):
            run_bounded([sys.executable, "-c", "import sys;sys.stdout.buffer.write(b'x'*2000000)"], max_output_bytes=1024)
        with self.assertRaisesRegex(ProcessLimitError, "seconds"):
            run_bounded([sys.executable, "-c", "import time;time.sleep(10)"], timeout=0.1)
        result = run_bounded([sys.executable, "-c", "import sys;print('ok');sys.stderr.write('note')"], text=True)
        self.assertEqual((result.returncode, result.stdout.strip(), result.stderr), (0, "ok", "note"))

    def test_offline_environment_overrides_inherited_network_and_prompt_settings(self):
        with mock.patch.dict(os.environ, GIT_NO_LAZY_FETCH="0", GIT_TERMINAL_PROMPT="1"), \
             mock.patch("offline_git.run_bounded", return_value=subprocess.CompletedProcess([], 0, "", "")) as run:
            run_git(Path("."), "show", "HEAD:source.py")
        env = run.call_args.kwargs["env"]
        self.assertEqual((env["GIT_NO_LAZY_FETCH"], env["GIT_OPTIONAL_LOCKS"], env["GIT_TERMINAL_PROMPT"]), ("1", "0", "0"))
        self.assertEqual(env["GIT_ALLOW_PROTOCOL"], "")
        with self.assertRaises(ValueError):
            run_git(Path("."), "fetch", "origin")

    def test_missing_promisor_object_never_launches_fetch(self):
        with tempfile.TemporaryDirectory() as directory:
            root = Path(directory).resolve()
            repo, remote = root / "repo", root / "remote.git"
            def git(*args):
                return subprocess.run(["git", *map(str, args)], check=True, capture_output=True).stdout.decode().strip()
            git("init", "-q", repo)
            (repo / "source.py").write_text("value = 1\n", encoding="utf-8")
            git("-C", repo, "add", ".")
            git("-C", repo, "-c", "user.name=Wiki", "-c", "user.email=wiki@example.invalid", "commit", "-qm", "source")
            blob = git("-C", repo, "rev-parse", "HEAD:source.py")
            git("clone", "--bare", repo, remote)
            git("-C", repo, "remote", "add", "promisor", remote.as_uri())
            git("-C", repo, "config", "remote.promisor.promisor", "true")
            git("-C", repo, "config", "remote.promisor.partialclonefilter", "blob:none")
            object_path = repo / ".git/objects" / blob[:2] / blob[2:]
            object_path.chmod(stat.S_IREAD | stat.S_IWRITE)
            object_path.unlink()
            trace = root / "trace.jsonl"
            with mock.patch.dict(os.environ, GIT_TRACE2_EVENT=str(trace), GIT_NO_LAZY_FETCH="0"):
                result = run_git(repo, "show", "HEAD:source.py", check=False)
            self.assertNotEqual(result.returncode, 0)
            events = trace.read_text(encoding="utf-8")
            self.assertNotIn('"fetch"', events)
            self.assertNotIn("upload-pack", events)

    def test_excluded_flat_directory_enumeration_is_actually_bounded(self):
        class Entry:
            name = "file"
            path = "file"
            def is_symlink(self): return False
            def is_dir(self, **kwargs): return False
            def is_file(self, **kwargs): return True
            def stat(self, **kwargs): return SimpleNamespace(st_size=1)
        class Entries:
            consumed = 0
            def __enter__(self): return self
            def __exit__(self, *args): pass
            def __iter__(self):
                for _ in range(12000):
                    self.consumed += 1
                    yield Entry()
        entries = Entries()
        with mock.patch.object(scanner.os, "scandir", return_value=entries):
            result = scanner._bounded_excluded_root_summary(Path("node_modules"), "node_modules", "binary_or_generated")
        self.assertEqual(entries.consumed, 4097)
        self.assertEqual(result["observed_entries"], 4096)
        self.assertTrue(result["truncated"])

    def test_source_budgets_retain_explicit_blockers_and_stream_exact_utf8(self):
        with tempfile.TemporaryDirectory() as directory:
            root = Path(directory).resolve()
            (root / "source.py").write_bytes("字 = 1\n".encode("utf-8"))
            settings = scanner.parse_scan_settings(root, {"scan_max_file_bytes": 16, "scan_max_total_bytes": 16})
            texts = {}
            scan = scanner.scan_project(root, settings, source_texts=texts)
            self.assertEqual(texts["source.py"], "字 = 1\n")
            import hashlib
            self.assertEqual(scan["included"][0]["sha256"], hashlib.sha256("字 = 1\n".encode()).hexdigest())
            (root / "large.py").write_text("x" * 100, encoding="utf-8")
            scan = scanner.scan_project(root, settings)
            self.assertTrue(any(issue["path"] == "large.py" and "scan_max_file_bytes" in issue["detail"] for issue in scan["read_issues"]))
            self.assertNotIn("large.py", {item["path"] for item in scan["included"]})
            (root / "other.py").write_bytes(b"123456789")
            scan = scanner.scan_project(root, settings)
            self.assertTrue(any("scan_max_total_bytes" in issue["detail"] for issue in scan["read_issues"]))

    def test_utf8_character_split_between_stream_chunks_is_preserved(self):
        import hashlib
        with tempfile.TemporaryDirectory() as directory:
            path = Path(directory) / "source.py"
            for offset in (8192 - 1, 8192 + 16384 - 1, 1024 * 1024 - 8192 - 1):
                with self.subTest(offset=offset):
                    content = b"a" * offset + "\u5b57".encode("utf-8") + b"\n"
                    path.write_bytes(content)
                    text, digest, size = scanner.read_source(path, 2 * 1024 * 1024)
                    self.assertEqual(text.encode("utf-8"), content)
                    self.assertEqual((digest, size), (hashlib.sha256(content).hexdigest(), len(content)))

    def test_tiny_source_does_not_allocate_megabyte_reads_including_eof(self):
        class Stream(io.BytesIO):
            requests = []
            def read(self, size=-1):
                self.requests.append(size)
                return super().read(size)
        stream = Stream(b"VALUE = 1\n")
        with mock.patch.object(Path, "open", return_value=stream) as opened:
            text, _, size = scanner.read_source(Path("source.py"), 64 * 1024 * 1024)
        self.assertEqual((text, size), ("VALUE = 1\n", 10))
        self.assertEqual(opened.call_count, 1)
        self.assertEqual(len(stream.requests), 2)
        self.assertLessEqual(max(stream.requests), 8192)

    def test_short_reads_do_not_hide_later_bytes_or_file_budget_overflow(self):
        class Stream(io.BytesIO):
            def read(self, size=-1):
                return super().read(min(size, 3))
        with mock.patch.object(Path, "open", return_value=Stream(b"0123456789")):
            self.assertEqual(scanner.read_source(Path("source.py"), 10)[0], "0123456789")
        with mock.patch.object(Path, "open", return_value=Stream(b"01234567890")):
            with self.assertRaisesRegex(OSError, "scan_max_file_bytes"):
                scanner.read_source(Path("source.py"), 10)

    def test_large_source_tail_uses_small_eof_probe_without_reopening(self):
        class Stream(io.BytesIO):
            requests = []
            def read(self, size=-1):
                self.requests.append(size)
                return super().read(size)
        content = b"x" * (2 * 1024 * 1024 + 3)
        stream = Stream(content)
        with mock.patch.object(Path, "open", return_value=stream) as opened:
            text, _, size = scanner.read_source(Path("source.py"), 4 * 1024 * 1024)
        self.assertEqual((text.encode(), size), (content, len(content)))
        self.assertEqual(opened.call_count, 1)
        self.assertEqual(stream.requests[-1], 8192)

    def test_scan_charges_failed_reads_and_never_opens_files_after_total_limit(self):
        with tempfile.TemporaryDirectory() as directory:
            root = Path(directory).resolve()
            for name, content in {
                "a-invalid.py": b"\xff" + b"a" * 20000,
                "b-binary.py": b"\x00" + b"b" * 20000,
                "c-oversized.py": b"c" * 20000,
                "d-total.py": b"d" * 20000,
                "e-unopened.py": b"VALUE = 1\n",
            }.items():
                (root / name).write_bytes(content)
            settings = scanner.parse_scan_settings(root, {"scan_max_file_bytes": 12288, "scan_max_total_bytes": 32768})
            original = Path.open
            opened, actual_bytes, buffering = [], {}, []
            class Observed:
                def __init__(self, stream, name): self.stream, self.name = stream, name
                def __enter__(self): return self
                def __exit__(self, *args): return self.stream.__exit__(*args)
                def fileno(self): return self.stream.fileno()
                def tell(self): return self.stream.tell()
                def read(self, size=-1):
                    data = self.stream.read(size)
                    actual_bytes[self.name] = actual_bytes.get(self.name, 0) + len(data)
                    return data
            def observe(path, *args, **kwargs):
                stream = original(path, *args, **kwargs)
                if path.suffix == ".py":
                    opened.append(path.name); buffering.append(kwargs.get("buffering"))
                    return Observed(stream, path.name)
                return stream
            with mock.patch.object(Path, "open", observe):
                scan = scanner.scan_project(root, settings)
            self.assertEqual(sum(actual_bytes.values()), 32768)
            self.assertEqual(actual_bytes["a-invalid.py"], 8192)
            self.assertEqual(actual_bytes["b-binary.py"], 8192)
            self.assertEqual(actual_bytes["c-oversized.py"], 12289)
            self.assertNotIn("e-unopened.py", opened)
            self.assertEqual(set(buffering), {0})
            issues = {issue["path"]: issue["detail"] for issue in scan["read_issues"]}
            self.assertIn("scan_max_file_bytes", issues["c-oversized.py"])
            self.assertIn("scan_max_total_bytes", issues["d-total.py"])
            self.assertIn("scan_max_total_bytes", issues["e-unopened.py"])
            self.assertEqual({row["path"] for row in scan["excluded"]}, {p.name for p in root.iterdir()})

    def test_exact_total_boundary_accepts_complete_regular_file_without_overread(self):
        with tempfile.TemporaryDirectory() as directory:
            root = Path(directory).resolve()
            (root / "a.py").write_bytes(b"0123456789")
            (root / "b.py").write_bytes(b"must not open")
            budget = scanner.SourceReadBudget(10)
            self.assertEqual(scanner.read_source(root / "a.py", 10, budget=budget)[0], "0123456789")
            self.assertEqual(budget.consumed, 10)
            with mock.patch.object(Path, "open") as opened:
                with self.assertRaisesRegex(OSError, "scan_max_total_bytes"):
                    scanner.read_source(root / "b.py", 100, budget=budget)
            opened.assert_not_called()

    def test_total_boundary_detects_new_bytes_without_reading_past_the_budget(self):
        with tempfile.TemporaryDirectory() as directory:
            path = Path(directory) / "source.py"
            path.write_bytes(b"0123456789")
            original = scanner.os.fstat
            def grow_before_terminal_stat(fd):
                with path.open("ab") as writer:
                    writer.write(b"new bytes")
                return original(fd)
            budget = scanner.SourceReadBudget(10)
            with mock.patch.object(scanner.os, "fstat", side_effect=grow_before_terminal_stat):
                with self.assertRaisesRegex(OSError, "scan_max_total_bytes"):
                    scanner.read_source(path, 100, budget=budget)
            self.assertEqual(budget.consumed, 10)

    def test_coincident_file_and_total_boundary_reports_known_file_overflow(self):
        with tempfile.TemporaryDirectory() as directory:
            path = Path(directory) / "source.py"
            path.write_bytes(b"01234567890")
            budget = scanner.SourceReadBudget(10)
            with self.assertRaisesRegex(OSError, "scan_max_file_bytes"):
                scanner.read_source(path, 10, budget=budget)
            self.assertEqual(budget.consumed, 10)

    def test_unprovable_eof_at_total_boundary_stays_incomplete(self):
        budget = scanner.SourceReadBudget(10)
        with mock.patch.object(Path, "open", return_value=io.BytesIO(b"0123456789")):
            with self.assertRaisesRegex(OSError, "scan_max_total_bytes"):
                scanner.read_source(Path("source.py"), 100, budget=budget)
        self.assertEqual(budget.consumed, 10)

    def test_io_error_keeps_previously_read_bytes_charged(self):
        class FailedStream(io.BytesIO):
            def read(self, size=-1):
                if self.tell():
                    raise OSError("interrupted source read")
                return super().read(min(size, 5))
        budget = scanner.SourceReadBudget(10)
        with mock.patch.object(Path, "open", return_value=FailedStream(b"abcdefghij")):
            with self.assertRaisesRegex(OSError, "interrupted source read"):
                scanner.read_source(Path("source.py"), 100, budget=budget)
        self.assertEqual((budget.consumed, budget.remaining), (5, 5))

    def test_log_links_enumerate_page_stems_once_even_with_long_history(self):
        spec = importlib.util.spec_from_file_location("resource_log", SCRIPTS / "validate-log.py")
        module = importlib.util.module_from_spec(spec); spec.loader.exec_module(module)
        with tempfile.TemporaryDirectory() as directory:
            root = Path(directory).resolve(); (root / "wiki").mkdir()
            (root / "wiki/page.md").write_text("# Page\n", encoding="utf-8")
            log = root / "wiki/log.md"
            log.write_text("---\nlast_updated: 2026-10-20\n---\n<!-- codebase-wiki:log-contract-v1 -->\n" +
                           "\n## [2026-10-20] update | change\n- Affected pages: [[page]]\n" * 2000, encoding="utf-8")
            original = Path.rglob; calls = []
            def rglob(path, pattern, *args, **kwargs):
                calls.append(pattern)
                return original(path, pattern, *args, **kwargs)
            with mock.patch.object(Path, "rglob", rglob):
                result = module.validate_log(log, root, use_git=False)
            self.assertTrue(result["ok"], result)
            self.assertEqual(calls.count("*.md"), 1)


if __name__ == "__main__":
    unittest.main()
