#!/usr/bin/env python3
"""Aggregate deterministic Wiki checks without changing repository state."""

from __future__ import annotations

import argparse
from collections import Counter
import importlib.util
import json
from pathlib import Path
import re
import sys
from typing import Any

from frontmatter import configure_utf8_stdio, parse_frontmatter_text, validate_regular_tree


WIKILINK_PATTERN = re.compile(r"\[\[([^\]]+)\]\]")
SKIP_ORPHAN = {"index.md", "log.md", "overview.md"}


def load_script(name: str, filename: str):
    path = Path(__file__).with_name(filename)
    spec = importlib.util.spec_from_file_location(name, path)
    if spec is None or spec.loader is None:
        raise RuntimeError(f"Unable to load {path}")
    module = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(module)
    return module


def normalized_target(raw: str) -> str:
    return raw.split("|", 1)[0].split("#", 1)[0].strip().replace("\\", "/")


def wikilinks(text: str) -> list[str]:
    visible = re.sub(r"```.*?```", "", text, flags=re.DOTALL)
    visible = re.sub(r"`[^`\n]*`", "", visible)
    return WIKILINK_PATTERN.findall(visible)


def finding(
    severity: str,
    code: str,
    message: str,
    page: str | None = None,
    details: dict[str, Any] | None = None,
) -> dict[str, Any]:
    result: dict[str, Any] = {
        "severity": severity,
        "code": code,
        "message": message,
    }
    if page:
        result["page"] = page
    if details:
        result["details"] = details
    return result


def lint_wiki(wiki_dir: Path, repo_root: Path) -> dict[str, Any]:
    validate_regular_tree(wiki_dir)
    pages = sorted(wiki_dir.rglob("*.md"))
    findings: list[dict[str, Any]] = []
    validate = load_script("validate_frontmatter_for_lint", "validate-frontmatter.py")
    stale = load_script("check_stale_for_lint", "check-stale.py")
    log_validator = load_script("validate_log_for_lint", "validate-log.py")

    for path in pages:
        relative = path.relative_to(wiki_dir).as_posix()
        for error in validate.validate_page(path, wiki_dir):
            findings.append(finding("critical", "frontmatter", error, relative))

    stale_results = stale.check_stale(wiki_dir, repo_root)
    for item in stale_results["critical"]:
        page = str(item["page"])
        if "invalid_sources" in item:
            values = item["invalid_sources"]
            sources = values if isinstance(values, list) else [values]
            findings.append(
                finding(
                    "critical",
                    "invalid_source",
                    "frontmatter.sources contains an invalid path or value",
                    page,
                    {"sources": sources},
                )
            )
        if "all_missing" in item:
            findings.append(
                finding(
                    "critical",
                    "missing_source",
                    "All listed source paths are missing",
                    page,
                    {"sources": item["all_missing"]},
                )
            )
    for item in stale_results["warning"]:
        page = str(item["page"])
        if item.get("missing"):
            findings.append(
                finding(
                    "warning",
                    "missing_source",
                    "One or more source paths are missing",
                    page,
                    {"sources": item["missing"]},
                )
            )
        if item.get("stale") or item.get("digest_mismatch"):
            details: dict[str, Any] = {"sources": item.get("stale", [])}
            if item.get("digest_mismatch"):
                details["source_digest"] = item["digest_mismatch"]
            findings.append(
                finding(
                    "warning",
                    "stale_source",
                    "One or more source paths changed after the Wiki page or source digest",
                    page,
                    details,
                )
            )

    log_result = log_validator.validate_log(wiki_dir / "log.md", repo_root)
    for message in log_result["errors"]:
        findings.append(finding("critical", "log_integrity", message, "log.md"))
    for message in log_result["warnings"]:
        findings.append(finding("info", "log_legacy", message, "log.md"))

    stems: dict[str, list[Path]] = {}
    for path in pages:
        stems.setdefault(path.stem, []).append(path)
    for stem, matches in stems.items():
        if len(matches) > 1:
            findings.append(
                finding(
                    "critical",
                    "ambiguous_wikilink",
                    f"Multiple pages share wikilink target {stem!r}",
                )
            )

    inbound: Counter[str] = Counter()
    index_targets: set[str] = set()
    for path in pages:
        text = path.read_text(encoding="utf-8")
        for raw in wikilinks(text):
            target = normalized_target(raw)
            if not target:
                continue
            stem = Path(target).stem
            if stem not in stems:
                findings.append(
                    finding(
                        "critical",
                        "broken_wikilink",
                        f"Missing target [[{target}]]",
                        path.relative_to(wiki_dir).as_posix(),
                    )
                )
                continue
            if path.name not in {"index.md", "log.md"} and path.stem != stem:
                inbound[stem] += 1
            if path.name == "index.md":
                index_targets.add(stem)

    for path in pages:
        if path.name in SKIP_ORPHAN:
            continue
        if inbound[path.stem] == 0:
            findings.append(
                finding(
                    "warning",
                    "orphan",
                    "Page has no inbound wikilink",
                    path.relative_to(wiki_dir).as_posix(),
                )
            )
        if path.stem not in index_targets:
            findings.append(
                finding(
                    "critical",
                    "index_missing",
                    "Page is not linked from wiki/index.md",
                    path.relative_to(wiki_dir).as_posix(),
                )
            )

    type_counts: Counter[str] = Counter()
    status_counts: Counter[str] = Counter()
    for path in pages:
        fm = parse_frontmatter_text(path.read_text(encoding="utf-8"))
        type_counts[str(fm.get("type", "unknown"))] += 1
        status_counts[str(fm.get("status", "unknown"))] += 1
        sources = fm.get("sources", [])
        if fm.get("status") == "active" and isinstance(sources, list) and sources:
            missing_metadata = [
                key for key in ("summary", "source_digest") if not fm.get(key)
            ]
            if missing_metadata:
                findings.append(
                    finding(
                        "info",
                        "evidence_metadata",
                        "Active evidence page is missing recommended provenance metadata",
                        path.relative_to(wiki_dir).as_posix(),
                        {"missing": missing_metadata},
                    )
                )
            if len(sources) > 5:
                findings.append(
                    finding(
                        "info",
                        "broad_source_scope",
                        "Page lists more than five core sources; consider splitting its evidence scope",
                        path.relative_to(wiki_dir).as_posix(),
                        {"source_count": len(sources)},
                    )
                )

    review_required = [
        {
            "check": "missing_module_coverage",
            "status": "agent_review_required",
            "reason": "Importance and module boundaries require source interpretation.",
        },
        {
            "check": "semantic_contradictions",
            "status": "agent_review_required",
            "reason": "Cross-page factual equivalence requires semantic review.",
        },
    ]
    severities = Counter(item["severity"] for item in findings)
    deterministic_status = (
        "critical"
        if severities["critical"]
        else "warning"
        if severities["warning"]
        else "pass"
    )
    semantic_status = "review_required" if review_required else "complete"
    overall_status = (
        deterministic_status
        if deterministic_status != "pass"
        else semantic_status
        if semantic_status != "complete"
        else "pass"
    )
    return {
        # Deprecated compatibility field: this covers deterministic Critical and
        # Warning findings only. Consumers should use the explicit status fields.
        "ok": deterministic_status == "pass",
        "deterministic_status": deterministic_status,
        "semantic_status": semantic_status,
        "overall_status": overall_status,
        "wiki_dir": wiki_dir.as_posix(),
        "summary": {
            "pages": len(pages),
            "critical": severities["critical"],
            "warning": severities["warning"],
            "info": severities["info"],
            "types": dict(sorted(type_counts.items())),
            "statuses": dict(sorted(status_counts.items())),
        },
        "findings": findings,
        "agent_review_required": review_required,
    }


def build_parser() -> argparse.ArgumentParser:
    parser = argparse.ArgumentParser()
    parser.add_argument("wiki_dir", nargs="?", type=Path, default=Path("wiki"))
    parser.add_argument("--repo-root", type=Path, default=Path("."))
    parser.add_argument("--format", choices=("text", "json"), default="text")
    return parser


def main(argv: list[str] | None = None) -> int:
    configure_utf8_stdio()
    args = build_parser().parse_args(argv)
    requested_wiki_dir = args.wiki_dir
    if not requested_wiki_dir.is_dir():
        print(f"Wiki directory not found: {requested_wiki_dir}", file=sys.stderr)
        return 2
    try:
        # Validate the caller-provided lexical root before canonicalization;
        # resolving first would let a symlink/reparse Wiki tree bypass the
        # regular-tree boundary enforced by lint_wiki().
        validate_regular_tree(requested_wiki_dir)
        wiki_dir = requested_wiki_dir.resolve()
        repo_root = args.repo_root.resolve()
        result = lint_wiki(wiki_dir, repo_root)
    except (OSError, RuntimeError, ValueError) as exc:
        print(json.dumps({"ok": False, "error": str(exc)}, ensure_ascii=False))
        return 2
    if args.format == "json":
        print(json.dumps(result, ensure_ascii=False, indent=2))
    else:
        summary = result["summary"]
        print(
            "Wiki lint: "
            f"{summary['critical']} critical, {summary['warning']} warning, "
            f"{summary.get('info', 0)} info, {summary['pages']} pages; "
            f"semantic={result['semantic_status']}"
        )
        for item in result["findings"]:
            page = f" [{item['page']}]" if "page" in item else ""
            print(f"- {item['severity'].upper()} {item['code']}{page}: {item['message']}")
        for item in result["agent_review_required"]:
            print(f"- REVIEW {item['check']}: {item['reason']}")
    if result["summary"]["critical"]:
        return 2
    if result["summary"]["warning"]:
        return 1
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
