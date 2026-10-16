#!/usr/bin/env python3
"""Refresh proven release metadata without claiming new source analysis.

Run after the release manager updates VERSION and the current README version.
The baseline must be HEAD and must already pass the complete Wiki preflight.
"""
from __future__ import annotations

import argparse
import datetime as dt
import importlib.util
import io
import json
from pathlib import Path, PurePosixPath
import re
import stat
import subprocess
import sys
import tarfile
import tempfile

ROOT = Path(__file__).resolve().parents[1]
SCRIPTS = ".agents/skills/codebase-wiki/scripts"


class PreparationError(ValueError):
    pass


def require(condition, message):
    if not condition:
        raise PreparationError(message)


def git(root, *arguments):
    return subprocess.check_output(["git", "-c", f"safe.directory={root.resolve()}", "-C", str(root), *arguments])


def read_file(root, relative):
    path = root / relative
    for parent in (path, *path.parents):
        if parent == root.parent:
            break
        if parent.exists():
            metadata = parent.lstat()
            require(not parent.is_symlink() and not (getattr(metadata, "st_file_attributes", 0)
                    & getattr(stat, "FILE_ATTRIBUTE_REPARSE_POINT", 0)), f"Unsafe release path: {relative}")
    require(path.is_file(), f"Missing release source: {relative}")
    return path.read_bytes()


def preflight(root):
    process = subprocess.run([sys.executable, "-X", "utf8", "-B", str(root / SCRIPTS / "export-notebooklm.py"),
                              "--root", str(root), "--preflight", "--format", "json"],
                             cwd=root, capture_output=True, text=True, encoding="utf-8")
    require(process.returncode == 0, "Wiki preflight failed: " + process.stderr[-2000:])
    return json.loads(process.stdout)


def replace_field(data, name, value):
    pattern = rb"(?m)^" + name.encode() + rb": [^\r\n]*"
    changed, count = re.subn(pattern, name.encode() + b": " + value.encode(), data, count=1)
    require(count == 1, f"Missing metadata field: {name}")
    return changed


def bumped_readme(original, previous, version):
    text = original.decode("utf-8").replace("\r\n", "\n")
    heading = re.search(r"^## ", text, re.MULTILINE)
    end = heading.start() if heading else len(text)
    introduction = re.sub(r"(?<![\d.])" + re.escape(previous) + r"(?![\d.])", version, text[:end])
    text = introduction + text[end:]
    sections = re.split(r"(?m)(?=^## )", text)
    for index, section in enumerate(sections):
        if re.match(r"^##\s+v?\d+\.\d+\.\d+\b", section):
            continue
        for tool in ("merge-reviewer", "release-reviewer", "gitlab-workspace", "gitlab-workspace-kit"):
            section = section.replace(f"{tool}-{previous}.zip", f"{tool}-{version}.zip")
            section = section.replace(f"{tool}-{previous}.vsix", f"{tool}-{version}.vsix")
        sections[index] = section.replace(f"scripts/package_release.py --tag v{previous}",
                                          f"scripts/package_release.py --tag v{version}")
    return "".join(sections).encode("utf-8")


def atomic_write(path, data):
    with tempfile.NamedTemporaryFile(dir=path.parent, prefix=".release-metadata-", delete=False) as stream:
        temporary = Path(stream.name)
        stream.write(data)
    try:
        temporary.replace(path)
    finally:
        temporary.unlink(missing_ok=True)


def prepare(root, baseline, version):
    root = root.resolve()
    require(bool(re.fullmatch(r"[0-9a-f]{40}", baseline)), "Baseline must be an exact 40-character commit SHA")
    require(git(root, "rev-parse", "HEAD").decode().strip() == baseline, "Baseline must equal current HEAD")
    require(bool(re.fullmatch(r"(?:0|[1-9]\d*)\.(?:0|[1-9]\d*)\.(?:0|[1-9]\d*)", version)), "Version must be stable X.Y.Z")
    with tempfile.TemporaryDirectory(prefix="wiki-release-baseline-") as temporary:
        archived = Path(temporary)
        originals = {}
        with tarfile.open(fileobj=io.BytesIO(git(root, "archive", "--format=tar", baseline)), mode="r:") as archive:
            for member in archive:
                relative = PurePosixPath(member.name)
                require(not relative.is_absolute() and ".." not in relative.parts and "\\" not in member.name
                        and all(":" not in part for part in relative.parts), "Unsafe baseline archive path")
                require(member.isdir() or member.isfile(), "Baseline source must contain only regular files/directories")
                if member.isfile():
                    require(member.name not in originals, "Duplicate baseline archive path")
                    data = archive.extractfile(member).read()
                    originals[member.name] = data
                    path = archived.joinpath(*relative.parts)
                    path.parent.mkdir(parents=True, exist_ok=True)
                    path.write_bytes(data)
        previous = originals["VERSION"].decode().strip()
        require(tuple(map(int, version.split("."))) > tuple(map(int, previous.split("."))), "Target version must advance the baseline")
        expected_metadata = {"VERSION": (version + "\n").encode(),
                             "README.md": bumped_readme(originals["README.md"], previous, version)}
        paths = {value.decode("utf-8") for value in git(root, "ls-files", "--cached", "--others", "--exclude-standard", "-z").split(b"\0") if value}
        require(paths == set(originals), "Release preparation cannot add or remove source files")
        current = {path: read_file(root, path) for path in paths}
        for path, data in current.items():
            if path in expected_metadata:
                require(data == expected_metadata[path], f"Unexpected release metadata change: {path}")
            elif not path.startswith("wiki/"):
                require(data == originals[path], f"Unanalyzed source change: {path}")
        prior = preflight(archived)
        require(prior["ready_to_export"], "Baseline Wiki analysis must already be ready; complete framework maintenance first")
        now = preflight(root)
        old_inventory = {item["path"]: item for item in prior["inventory"]["included"]}
        inventory = {item["path"]: item for item in now["inventory"]["included"]}
        require(set(inventory) == set(old_inventory), "Release metadata changed the analyzed source inventory")
        for path, row in inventory.items():
            require(row["category"] == old_inventory[path]["category"], f"Source classification changed: {path}")
            require(path in expected_metadata or row["sha256"] == old_inventory[path]["sha256"], f"Unanalyzed source digest: {path}")
        sys.path.insert(0, str(root / SCRIPTS))
        spec = importlib.util.spec_from_file_location("release_metadata_stale", root / SCRIPTS / "check-stale.py")
        stale = importlib.util.module_from_spec(spec)
        spec.loader.exec_module(stale)
        log = "wiki/log.md"
        original_log = originals[log]
        date = max(dt.date.fromisoformat(git(root, "show", "-s", "--format=%cs", baseline).decode().strip()),
                   dt.date.fromisoformat(str(stale.parse_frontmatter(archived / log)["last_updated"]))).isoformat()
        expected = {}
        ledger = "wiki/synthesis/codebase-functional-coverage.md"
        def update_hash(match):
            path = match[2].decode()
            require(path in inventory, f"Baseline ledger has an unknown path: {path}")
            return match[1] + b"sha256:" + inventory[path]["sha256"].encode() + match[3]
        expected[ledger] = re.sub(rb"(?m)^(\| `([^`]+)` \| `)sha256:[0-9a-f]{64}(` \|)",
                                 update_hash, originals[ledger])
        expected[ledger] = re.sub(rb"(?m)^Analyzed discovery ID: [^\r\n]*",
            b"Analyzed discovery ID: `" + now["discovery_id"].encode() + b"`", expected[ledger])
        expected[ledger] = replace_field(expected[ledger], "last_updated", date)
        cache = stale.SourceCache(root, True)
        for path, data in originals.items():
            if not path.startswith("wiki/") or not path.endswith(".md") or path in (log, ledger):
                continue
            fields = stale.parse_frontmatter(archived / path)
            if fields.get("sources") and fields.get("source_digest"):
                fingerprint = stale.compute_source_digest(root, fields["sources"], cache=cache)
                if fingerprint != fields["source_digest"]:
                    expected[path] = replace_field(replace_field(data, "source_digest", '"' + fingerprint + '"'), "last_updated", date)
        links = sorted({Path(path).stem for path in expected})
        expected[log] = replace_field(original_log, "last_updated", date) + (
            f"\n\n## [{date}] update | Prepare release v{version} metadata\n\n"
            f"- Reuse the complete analysis at `{baseline}`; update only VERSION/README fingerprints and the existing coverage identity. No source reanalysis or new dispositions.\n"
            "- Affected pages: " + ", ".join("[[" + name + "]]" for name in links) + "\n").encode()
        for path, data in current.items():
            if path.startswith("wiki/"):
                require(data == originals[path] or (path in expected and data == expected[path]),
                        f"Unexpected Wiki change; preserve and review it before release: {path}")
        changes = {path: data for path, data in expected.items() if current[path] != data}
        try:
            for path, data in changes.items():
                atomic_write(root / path, data)
            final = preflight(root)
            require(final["ready_to_export"], "Prepared metadata did not pass Wiki readiness")
        except BaseException:
            for path in changes:
                atomic_write(root / path, current[path])
            raise
    return {"ok": True, "baseline": baseline, "version": version, "ready_to_export": True,
            "analysis_reused": True, "updated_paths": sorted(changes), "idempotent": not changes,
            "discovery_id": final["discovery_id"], "metadata_date": date}


def main(argv=None):
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--baseline", required=True)
    parser.add_argument("--version", required=True)
    parser.add_argument("--format", choices=("json", "text"), default="text")
    args = parser.parse_args(argv)
    try:
        report = prepare(ROOT, args.baseline, args.version)
    except (OSError, ValueError, KeyError, subprocess.SubprocessError) as error:
        report = {"ok": False, "error": str(error)}
    print(json.dumps(report, ensure_ascii=False, indent=2) if args.format == "json" else
          ("Release metadata ready" if report["ok"] else report["error"]))
    return 0 if report["ok"] else 2


if __name__ == "__main__":
    raise SystemExit(main())
