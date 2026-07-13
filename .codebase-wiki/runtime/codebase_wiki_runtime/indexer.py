from __future__ import annotations

import hashlib
import re
import subprocess
from pathlib import Path
from typing import Iterable

from .constants import DEFAULT_EXCLUDES, DEFAULT_MAX_FILE_BYTES, SUPPORTED_LANGUAGES
from .storage import IndexStore
from .structure import extract_source_documents
from .text import build_terms


HEADING_RE = re.compile(r"^(#{1,6})\s+(.+?)\s*$")


def repo_files(repo_root: Path) -> Iterable[Path]:
    try:
        result = subprocess.run(
            ["git", "-C", str(repo_root), "ls-files", "-co", "--exclude-standard", "-z"],
            check=True,
            capture_output=True,
        )
        for raw_path in result.stdout.split(b"\0"):
            if raw_path:
                path = repo_root / raw_path.decode("utf-8", errors="surrogateescape")
                if path.exists():
                    yield path
        return
    except (OSError, subprocess.CalledProcessError):
        pass

    for path in repo_root.rglob("*"):
        if not path.is_file() or any(part in DEFAULT_EXCLUDES for part in path.parts):
            continue
        yield path


def wiki_documents(repo_root: Path) -> list[dict[str, object]]:
    documents: list[dict[str, object]] = []
    for path in sorted((repo_root / "wiki").rglob("*.md")):
        relative = path.relative_to(repo_root).as_posix()
        lines = path.read_text(encoding="utf-8", errors="replace").splitlines()
        headings = [(index, match.group(2), len(match.group(1))) for index, line in enumerate(lines) if (match := HEADING_RE.match(line))]
        if not headings:
            headings = [(0, path.stem, 1)]
        for offset, (start, heading, level) in enumerate(headings):
            end = headings[offset + 1][0] if offset + 1 < len(headings) else len(lines)
            body = "\n".join(lines[start:end]).strip()
            stable = hashlib.sha256(f"{relative}:{start}:{heading}".encode("utf-8")).hexdigest()[:24]
            documents.append(
                {
                    "id": f"wiki:{stable}",
                    "kind": "wiki_section",
                    "path": relative,
                    "title": path.stem,
                    "heading": heading,
                    "body": body,
                    "terms": build_terms(path.stem, heading, body, relative),
                    "line_start": start + 1,
                    "line_end": end,
                    "tags": "wiki",
                }
            )
    return documents


def source_documents(repo_root: Path) -> tuple[list[dict[str, object]], list[dict[str, object]]]:
    documents: list[dict[str, object]] = []
    diagnostics: list[dict[str, object]] = []
    for path in repo_files(repo_root):
        relative = path.relative_to(repo_root).as_posix()
        if path.is_symlink():
            diagnostics.append({"code": "symlink_skipped", "path": relative})
            continue
        if path.stat().st_size > DEFAULT_MAX_FILE_BYTES:
            diagnostics.append({"code": "file_too_large", "path": relative})
            continue
        try:
            if b"\0" in path.read_bytes()[:4096]:
                diagnostics.append({"code": "binary_skipped", "path": relative})
                continue
        except OSError as exc:
            diagnostics.append({"code": "read_error", "path": relative, "detail": str(exc)})
            continue
        language = SUPPORTED_LANGUAGES.get(path.suffix.lower())
        if not language:
            continue
        extracted, errors = extract_source_documents(path, language)
        for item in extracted:
            item["path"] = relative
        documents.extend(extracted)
        diagnostics.extend({**item, "path": relative} for item in errors)
    return documents, diagnostics


def build_index(repo_root: Path, database: Path, scope: str = "all") -> dict[str, object]:
    documents: list[dict[str, object]] = []
    diagnostics: list[dict[str, object]] = []
    if scope in {"wiki", "all"}:
        documents.extend(wiki_documents(repo_root))
    if scope in {"source", "all"}:
        source_items, source_diagnostics = source_documents(repo_root)
        documents.extend(source_items)
        diagnostics.extend(source_diagnostics)
    store = IndexStore(database)
    count = store.replace_documents(documents)
    return {"documents": count, "diagnostics": diagnostics, "generation": store.generation()}
