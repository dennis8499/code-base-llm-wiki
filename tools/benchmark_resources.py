#!/usr/bin/env python3
"""Compare local HEAD with current scanner/log implementations; no network."""
from __future__ import annotations

import argparse
import importlib.util
import io
import json
from pathlib import Path
import platform
import statistics
import sys
import tempfile
import time
from types import ModuleType, SimpleNamespace

ROOT = Path(__file__).resolve().parents[1]
SCRIPTS = ROOT / ".agents/skills/codebase-wiki/scripts"
sys.path.insert(0, str(SCRIPTS))
from offline_git import run_git
import project_scanner


def baseline(filename):
    relative = (SCRIPTS / filename).relative_to(ROOT).as_posix()
    source = run_git(ROOT, "show", "HEAD:" + relative).stdout
    name = "baseline_" + filename.replace("-", "_").replace(".", "_")
    module = ModuleType(name); module.__file__ = str(SCRIPTS / filename)
    sys.modules[name] = module
    exec(compile(source, module.__file__, "exec"), module.__dict__)
    return module


def current(filename):
    spec = importlib.util.spec_from_file_location("benchmark_current_log", SCRIPTS / filename)
    module = importlib.util.module_from_spec(spec); spec.loader.exec_module(module)
    return module


def measured(function, repeats):
    times = []
    for _ in range(repeats):
        start = time.perf_counter(); result = function(); times.append(time.perf_counter() - start)
    return result, round(statistics.median(times), 6)


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--output", type=Path)
    parser.add_argument("--sizes", type=int, nargs="+", default=[2000, 4000, 8000])
    parser.add_argument("--repeats", type=int, default=3)
    args = parser.parse_args()
    if args.repeats <= 0 or any(size <= 0 for size in args.sizes):
        parser.error("sizes and repeats must be positive")
    old_scan, old_log = baseline("project_scanner.py"), baseline("validate-log.py")
    new_log = current("validate-log.py")
    report = {"schema": "codebase-wiki-resource-benchmark/v1", "python": platform.python_version(),
              "platform": platform.system(), "baseline": run_git(ROOT, "rev-parse", "HEAD").stdout.strip(),
              "repeats": args.repeats, "scanner_fixture": "in-memory file doubles; excludes physical filesystem I/O",
              "log_fixture": "physical temporary Wiki pages and log", "scanner": []}
    class File:
        def read_bytes(self): return b"VALUE = 1\n"
        def open(self, *args, **kwargs): return io.BytesIO(self.read_bytes())
    with tempfile.TemporaryDirectory() as directory:
        root = Path(directory).resolve()
        settings = SimpleNamespace(scan_profile="framework", output_directory=".notebooklm", analysis_include_tests=True,
                                   business_source_paths=(), exclude_paths=())
        original = project_scanner._iter_project_files
        try:
            for count in args.sizes:
                iterator = lambda *a, count=count, **k: ((File(), f"src/f{i:06d}.py") for i in range(count))
                old_scan._iter_project_files = iterator; project_scanner._iter_project_files = iterator
                before, old_time = measured(lambda: old_scan.scan_project(root, settings), args.repeats)
                after, new_time = measured(lambda: project_scanner.scan_project(root, settings), args.repeats)
                if before["snapshot_id"] != after["snapshot_id"]:
                    raise RuntimeError("scanner snapshot changed for identical complete evidence")
                report["scanner"].append({"files": count, "baseline_seconds": old_time, "current_seconds": new_time,
                                           "speedup": round(old_time / new_time, 3), "same_snapshot": True})
        finally:
            project_scanner._iter_project_files = original
        wiki = root / "wiki"; wiki.mkdir()
        for number in range(200):
            (wiki / f"page-{number:03}.md").write_bytes(b"# Page\n")
        log = wiki / "log.md"
        log.write_bytes(b"---\nlast_updated: 2026-10-20\n---\n<!-- codebase-wiki:log-contract-v1 -->\n" +
                        b"\n## [2026-10-20] update | change\n- Affected pages: [[page-199]]\n" * 1000)
        before, old_time = measured(lambda: old_log.validate_log(log, root, use_git=False), args.repeats)
        after, new_time = measured(lambda: new_log.validate_log(log, root, use_git=False), args.repeats)
        if before != after:
            raise RuntimeError("log validation changed for identical valid history")
        report["log"] = {"pages": 201, "entries": 1000, "baseline_seconds": old_time, "current_seconds": new_time,
                         "speedup": round(old_time / new_time, 3), "same_result": True}
    encoded = json.dumps(report, ensure_ascii=False, sort_keys=True, indent=2) + "\n"
    if args.output:
        args.output.parent.mkdir(parents=True, exist_ok=True); args.output.write_text(encoded, encoding="utf-8", newline="")
    print(encoded, end="")


if __name__ == "__main__":
    main()
