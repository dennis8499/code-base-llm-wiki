"""Read-only full-ingest inventory and completeness checks over the shared scanner."""
from __future__ import annotations

import hashlib
import json
from dataclasses import replace
from pathlib import Path, PurePosixPath
import subprocess
from offline_git import run_git

from frontmatter import is_reparse_point
from project_scanner import load_scan_settings, scan_project

SCHEMA = "codebase-ingest-coverage/v1"


def safe_path(root: Path, relative: str) -> Path:
    path = PurePosixPath(relative)
    if not relative or "\\" in relative or path.is_absolute() or any(p in (".", "..") or ":" in p for p in path.parts):
        raise ValueError(f"unsafe relative path: {relative}")
    candidate = root
    for part in path.parts:
        candidate = candidate / part
        if is_reparse_point(candidate):
            raise ValueError(f"link boundary: {relative}")
    candidate.resolve().relative_to(root.resolve())
    return candidate


def repository_names(root: Path, scope: str, selected: list[str] | None) -> list[str]:
    if scope == "repository":
        if selected:
            raise ValueError("--repo is only valid for Group scope")
        return ["."]
    if scope != "group":
        raise ValueError("scope must be repository or group")
    names = sorted(selected if selected is not None else [
        p.name for p in root.iterdir()
        if p.is_dir() and not is_reparse_point(p) and (p / ".git").exists()
    ])
    if not names or len(names) != len(set(n.casefold() for n in names)):
        raise ValueError("Group scope requires a non-empty, unique repository list")
    for name in names:
        if len(PurePosixPath(name).parts) != 1:
            raise ValueError("Group repositories must be direct children")
        repo = safe_path(root, name)
        if not repo.is_dir() or not (repo / ".git").exists() or is_reparse_point(repo / ".git"):
            raise ValueError(f"not a regular direct-child repository: {name}")
        result = run_git(repo, "rev-parse", "--show-toplevel", check=False)
        if result.returncode or Path(result.stdout.strip()).resolve() != repo.resolve():
            raise ValueError(f"not a valid repository root: {name}")
    return names


def inventory(root: Path, *, scope: str = "repository", selected: list[str] | None = None, profile: str = "target") -> dict:
    root = Path(root).absolute()
    if not root.is_dir() or is_reparse_point(root) or root.resolve() != root:
        raise ValueError("root must be a regular directory without link ancestors")
    repositories = repository_names(root, scope, selected)
    snapshots: dict[str, str] = {}
    files: list[dict] = []
    exclusions: list[dict] = []
    excluded_roots: list[dict] = []
    read_issues: list[dict] = []
    for name in repositories:
        repo = root if name == "." else root / name
        # NotebookLM's optional test filter must not silently narrow full Ingest.
        settings = replace(load_scan_settings(repo, profile), analysis_include_tests=True)
        scan = scan_project(repo, settings)
        snapshots[name] = scan["snapshot_id"]
        def prefixed(path: str) -> str:
            return path if name == "." else f"{name}/{path}"
        for item in scan["included"]:
            files.append({"path": prefixed(item["path"]), "sha256": item["sha256"], "category": item["category"],
                          "status": "blocked", "pages": [], "reason": "Not yet analyzed"})
        for item in scan["excluded"]:
            exclusions.append({"path": prefixed(item["path"]), "sha256": None, "status": "excluded", "reason": item["reason"]})
        for item in scan["excluded_roots"]:
            # Boundaries are recorded without opening secrets, dependencies or generated trees.
            excluded_roots.append({"path": prefixed(item["path"]), "status": "excluded", "reason": item["reason"]})
        for item in scan["read_issues"]:
            read_issues.append({**item, "path": prefixed(item["path"]), "status": "blocked"})
    contract = {"scope": scope, "selection": sorted(selected) if selected is not None else None,
                "scan_profile": profile, "analysis_include_tests": True,
                "repositories": repositories, "snapshots": snapshots}
    digest = hashlib.sha256(json.dumps(contract, sort_keys=True, ensure_ascii=False).encode("utf-8")).hexdigest()
    return {"schema": SCHEMA, **contract, "snapshot_id": f"sha256:{digest}", "files": files,
            "excluded": exclusions, "excluded_roots": excluded_roots, "read_issues": read_issues}


def validate(root: Path, ledger: dict, *, scope: str = "repository", selected: list[str] | None = None,
             profile: str = "target") -> dict:
    current = inventory(root, scope=scope, selected=selected, profile=profile)
    errors: list[str] = []
    if not isinstance(ledger, dict):
        return {"ok": False, "status": "partial", "errors": ["ledger must be an object"]}
    for key in ("schema", "scope", "selection", "scan_profile", "analysis_include_tests", "repositories", "snapshots", "snapshot_id"):
        if ledger.get(key) != current[key]:
            errors.append(f"snapshot or scope mismatch: {key}")
    for key in ("excluded", "excluded_roots", "read_issues"):
        actual_dispositions = ledger.get(key)
        expected_dispositions = current[key]
        if key != "read_issues" and isinstance(actual_dispositions, list):
            # Writing knowledge and delivery artifacts does not change raw-source scope.
            volatile = {"binary_or_generated", "export_output", "wiki_knowledge_layer"}
            actual_dispositions = [e for e in actual_dispositions if not isinstance(e, dict) or e.get("reason") not in volatile]
            expected_dispositions = [e for e in expected_dispositions if e.get("reason") not in volatile]
        if actual_dispositions != expected_dispositions:
            errors.append(f"scanner-owned dispositions changed: {key}")
    if current["read_issues"]:
        errors.append("source read issues remain blocked")
    entries = ledger.get("files")
    if not isinstance(entries, list) or any(not isinstance(e, dict) or not isinstance(e.get("path"), str) for e in entries):
        entries = []
        errors.append("files must be a list of file dispositions")
    actual = {e["path"]: e for e in entries}
    expected = {e["path"]: e for e in current["files"]}
    if len(actual) != len(entries):
        errors.append("duplicate file dispositions")
    for path in sorted(expected.keys() - actual.keys()):
        errors.append(f"missing disposition: {path}")
    for path in sorted(actual.keys() - expected.keys()):
        errors.append(f"unexpected disposition: {path}")
    for path in sorted(actual.keys() & expected.keys()):
        entry = actual[path]
        if any(entry.get(key) != expected[path][key] for key in ("sha256", "category")):
            errors.append(f"source changed: {path}")
        if entry.get("status") != "processed":
            errors.append(f"source remains blocked: {path}")
        pages = entry.get("pages")
        if not isinstance(pages, list) or any(not isinstance(p, str) for p in pages):
            errors.append(f"invalid page mapping: {path}")
            continue
        if not pages and (not isinstance(entry.get("reason"), str) or entry["reason"].strip() in ("", "Not yet analyzed")):
            errors.append(f"page mapping or no-page rationale required: {path}")
        for page in pages:
            try:
                target = safe_path(Path(root).absolute(), page)
                if not page.startswith("wiki/") or target.suffix != ".md" or not target.is_file():
                    raise ValueError("target must be an existing Wiki page")
            except (OSError, ValueError) as exc:
                errors.append(f"invalid page mapping for {path}: {page}: {exc}")
    return {"ok": not errors, "status": "complete" if not errors else "partial", "errors": errors,
            "snapshot_id": current["snapshot_id"], "file_count": len(expected),
            "verification": "Coverage and snapshot only; Agent evidence and Wiki quality checks are also required."}
