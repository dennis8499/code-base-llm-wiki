"""Function-oriented NotebookLM Enterprise preflight and source-pack builder.

``--preflight`` performs a read-only, Git-aware inventory. The default mode
packages curated Wiki documents and selected evidence into ``.notebooklm``.
This module never calls NotebookLM or modifies raw sources and Wiki pages.
"""

from __future__ import annotations

import argparse
from collections import Counter
from dataclasses import dataclass
from datetime import datetime, timezone
import fnmatch
import hashlib
import importlib.util
import json
import os
from pathlib import Path, PurePosixPath
import re
import shutil
import subprocess
import sys
import tempfile
import tomllib
from typing import Any, Iterable, Sequence

try:
    from frontmatter import configure_utf8_stdio, parse_frontmatter_text
except ModuleNotFoundError:  # pragma: no cover - useful when loaded by a caller
    sys.path.insert(0, str(Path(__file__).resolve().parent))
    from frontmatter import configure_utf8_stdio, parse_frontmatter_text


EXPORT_SCHEMA_VERSION = 2
SUPPORTED_MANIFEST_SCHEMAS = {1, EXPORT_SCHEMA_VERSION}
PREFLIGHT_SCHEMA_VERSION = 1
PROFILE_NAME = "gemini-notebook-enterprise"
ENTERPRISE_MAX_SOURCES = 300
ENTERPRISE_MAX_BYTES = 200_000_000
ENTERPRISE_MAX_WORDS = 500_000
DEFAULT_MAX_SOURCES = ENTERPRISE_MAX_SOURCES
DEFAULT_MAX_BYTES = 180_000_000
DEFAULT_MAX_WORDS = 450_000

WIKI_LOG_PATH = "wiki/log.md"
REQUIRED_WIKI_DOCUMENTS = (
    "wiki/overview.md",
    "wiki/synthesis/project-function-catalog.md",
    "wiki/architecture/system-architecture.md",
    "wiki/synthesis/system-analysis.md",
)

DEFAULT_GENERATED_PARTS = {
    ".git",
    ".notebooklm",
    ".venv",
    "__pycache__",
    "bin",
    "build",
    "cache",
    "coverage",
    "dist",
    "logs",
    "node_modules",
    "obj",
    "target",
    "vendor",
}
DEFAULT_DEPENDENCY_PARTS = {
    ".bundle",
    ".gradle",
    ".m2",
    ".nuget",
    ".pnpm-store",
    ".yarn",
}
DEFAULT_TEST_PARTS = {"__tests__", "spec", "specs", "test", "tests"}
DEFAULT_IAC_PARTS = {
    ".circleci",
    ".terraform",
    "helm",
    "infra",
    "infrastructure",
    "k8s",
    "terraform",
}
DEFAULT_FRAMEWORK_PREFIXES = (
    ".agents/skills/codebase-wiki",
    ".codex",
    ".github",
)
DEFAULT_CI_PREFIXES = (".github/workflows",)
DEFAULT_DEV_TOOL_PARTS = {"examples", "samples", "tools"}
DEFAULT_SENSITIVE_NAMES = {
    ".env",
    ".npmrc",
    "credentials.json",
    "service-account.json",
}
SENSITIVE_SUFFIXES = (".pem", ".p12", ".pfx", ".key")
SENSITIVE_NAME_PATTERNS = (
    "*.env",
    ".env.*",
    "*credential*",
    "*secret*",
    "id_rsa*",
)
TEST_CONFIG_NAMES = {
    ".coveragerc",
    "jest.config.js",
    "jest.config.ts",
    "playwright.config.js",
    "playwright.config.ts",
    "pytest.ini",
    "tox.ini",
}
CI_FILENAMES = {
    ".gitlab-ci.yml",
    "azure-pipelines.yml",
    "bitbucket-pipelines.yml",
    "jenkinsfile",
}
DEV_SCRIPT_STEMS = {
    "benchmark",
    "build",
    "coverage",
    "dev",
    "format",
    "generate",
    "lint",
    "release",
    "test",
}
DOCUMENTATION_EXTENSIONS = {".adoc", ".md", ".rst", ".txt"}
DATA_EXTENSIONS = {".gql", ".graphql", ".prisma", ".proto", ".sql"}
CONFIG_EXTENSIONS = {
    ".cfg",
    ".conf",
    ".csproj",
    ".gradle",
    ".ini",
    ".json",
    ".lock",
    ".props",
    ".properties",
    ".sln",
    ".toml",
    ".xml",
    ".yaml",
    ".yml",
}
CONFIG_NAMES = {
    ".gitattributes",
    ".gitignore",
    "dockerfile",
    "gemfile",
    "go.mod",
    "go.sum",
    "makefile",
    "package.json",
    "packages.lock.json",
    "pom.xml",
    "pyproject.toml",
    "requirements.txt",
}
DATA_PARTS = {"data", "database", "db", "migration", "migrations", "schema", "schemas"}
CJK_PATTERN = re.compile(r"[\u3400-\u4dbf\u4e00-\u9fff\uf900-\ufaff]")
GROUP_PATTERN = re.compile(r"^[a-z0-9]+(?:-[a-z0-9]+)*$")


class ExportError(ValueError):
    """Raised when a safe, complete documentation pack cannot be produced."""


@dataclass(frozen=True)
class Settings:
    profile: str
    scan_profile: str
    output_directory: str
    source_limit: int
    reserved_source_slots: int
    max_source_bytes: int
    max_source_words: int
    include_evidence: bool
    extra_paths: tuple[str, ...]
    exclude_paths: tuple[str, ...]
    config_path: Path | None

    @property
    def available_source_slots(self) -> int:
        return self.source_limit - self.reserved_source_slots


@dataclass(frozen=True)
class InputFile:
    path: str
    text: str
    digest: str


@dataclass(frozen=True)
class Unit:
    logical_source_id: str
    kind: str
    group: str
    title: str
    inputs: tuple[InputFile, ...]
    content: str
    priority: int = 0

    @property
    def byte_count(self) -> int:
        return len(self.content.encode("utf-8"))

    @property
    def estimated_words(self) -> int:
        return estimate_words(self.content)


@dataclass(frozen=True)
class EvidenceCandidate:
    input_file: InputFile
    groups: tuple[str, ...]
    priority: int

    @property
    def primary_group(self) -> str:
        functional = sorted(group for group in self.groups if group.startswith("function-"))
        if functional:
            return functional[0]
        return sorted(self.groups)[0] if self.groups else "shared"


def sha256_bytes(data: bytes) -> str:
    return hashlib.sha256(data).hexdigest()


def sha256_file(path: Path) -> str:
    digest = hashlib.sha256()
    with path.open("rb") as stream:
        for chunk in iter(lambda: stream.read(1024 * 1024), b""):
            digest.update(chunk)
    return digest.hexdigest()


def repo_relative(path: Path, root: Path) -> str:
    try:
        return path.resolve().relative_to(root.resolve()).as_posix()
    except ValueError as exc:
        raise ExportError(f"path escapes repository root: {path}") from exc


def validate_relative_config_path(value: str, root: Path, field: str) -> str:
    candidate = PurePosixPath(value.replace("\\", "/"))
    if candidate.is_absolute() or ".." in candidate.parts:
        raise ExportError(f"{field} must be a repo-relative path: {value!r}")
    path = root / Path(*candidate.parts)
    repo_relative(path, root)
    return candidate.as_posix().rstrip("/") or "."


def _config_values(raw: dict[str, Any]) -> dict[str, Any]:
    nested = raw.get("notebooklm")
    if nested is None:
        return raw
    if not isinstance(nested, dict):
        raise ExportError("[notebooklm] must be a TOML table")
    return nested


def _int_config(values: dict[str, Any], key: str, default: int) -> int:
    value = values.get(key, default)
    if isinstance(value, bool) or not isinstance(value, int):
        raise ExportError(f"{key} must be an integer")
    if value < 0:
        raise ExportError(f"{key} must not be negative")
    return value


def _str_tuple_config(values: dict[str, Any], key: str) -> tuple[str, ...]:
    value = values.get(key, [])
    if not isinstance(value, list) or not all(isinstance(item, str) for item in value):
        raise ExportError(f"{key} must be an array of strings")
    return tuple(value)


def load_settings(root: Path, config_path: Path | None = None) -> Settings:
    selected_config = config_path or (root / "notebooklm.toml")
    raw: dict[str, Any] = {}
    if selected_config.exists():
        if not selected_config.is_file():
            raise ExportError(f"config path is not a file: {selected_config}")
        try:
            raw = _config_values(tomllib.loads(selected_config.read_text(encoding="utf-8")))
        except (OSError, tomllib.TOMLDecodeError) as exc:
            raise ExportError(f"unable to read config: {selected_config}: {exc}") from exc

    profile = raw.get("profile", PROFILE_NAME)
    if not isinstance(profile, str) or not profile.strip():
        raise ExportError("profile must be a non-empty string")
    scan_profile = raw.get("scan_profile", "target")
    if scan_profile not in {"target", "framework"}:
        raise ExportError("scan_profile must be 'target' or 'framework'")
    output_directory = raw.get("output_directory", ".notebooklm")
    if not isinstance(output_directory, str):
        raise ExportError("output_directory must be a string")
    output_directory = validate_relative_config_path(output_directory, root, "output_directory")

    source_limit = _int_config(raw, "source_limit", DEFAULT_MAX_SOURCES)
    reserved = _int_config(raw, "reserved_source_slots", 0)
    max_bytes = _int_config(raw, "max_source_bytes", DEFAULT_MAX_BYTES)
    max_words = _int_config(raw, "max_source_words", DEFAULT_MAX_WORDS)
    include_evidence = raw.get("include_evidence", True)
    if not isinstance(include_evidence, bool):
        raise ExportError("include_evidence must be true or false")

    if source_limit > ENTERPRISE_MAX_SOURCES:
        raise ExportError(
            f"source_limit {source_limit} exceeds Enterprise maximum {ENTERPRISE_MAX_SOURCES}"
        )
    if max_bytes > ENTERPRISE_MAX_BYTES:
        raise ExportError(
            f"max_source_bytes {max_bytes} exceeds Enterprise maximum {ENTERPRISE_MAX_BYTES}"
        )
    if max_words > ENTERPRISE_MAX_WORDS:
        raise ExportError(
            f"max_source_words {max_words} exceeds Enterprise maximum {ENTERPRISE_MAX_WORDS}"
        )
    if reserved > source_limit:
        raise ExportError("reserved_source_slots cannot exceed source_limit")
    if source_limit == 0 or max_bytes == 0 or max_words == 0:
        raise ExportError("source and size limits must be greater than zero")

    extra_paths = tuple(
        validate_relative_config_path(value, root, "extra_paths")
        for value in _str_tuple_config(raw, "extra_paths")
    )
    exclude_paths = tuple(
        validate_relative_config_path(value, root, "exclude_paths")
        for value in _str_tuple_config(raw, "exclude_paths")
    )
    return Settings(
        profile=profile,
        scan_profile=scan_profile,
        output_directory=output_directory,
        source_limit=source_limit,
        reserved_source_slots=reserved,
        max_source_bytes=max_bytes,
        max_source_words=max_words,
        include_evidence=include_evidence,
        extra_paths=extra_paths,
        exclude_paths=exclude_paths,
        config_path=selected_config if selected_config.is_file() else None,
    )


def estimate_words(text: str) -> int:
    """Conservatively estimate NotebookLM words for Latin and CJK text."""

    tokens = len(re.findall(r"\S+", text))
    cjk_characters = len(CJK_PATTERN.findall(text))
    return max(tokens, cjk_characters)


def is_sensitive(path: Path) -> bool:
    name = path.name.lower()
    if name in DEFAULT_SENSITIVE_NAMES or name.endswith(SENSITIVE_SUFFIXES):
        return True
    return any(fnmatch.fnmatch(name, pattern) for pattern in SENSITIVE_NAME_PATTERNS)


def _has_prefix(relative: str, prefixes: Iterable[str]) -> bool:
    return any(relative == value or relative.startswith(value + "/") for value in prefixes)


def _is_test_file(relative: str) -> bool:
    path = PurePosixPath(relative.lower())
    name = path.name
    if set(path.parts) & DEFAULT_TEST_PARTS or name in TEST_CONFIG_NAMES:
        return True
    stem = Path(name).stem
    return stem.startswith("test_") or stem.endswith("_test") or ".test." in name or ".spec." in name


def _is_ci_or_iac(relative: str) -> bool:
    path = PurePosixPath(relative.lower())
    if _has_prefix(path.as_posix(), DEFAULT_CI_PREFIXES):
        return True
    if path.name in CI_FILENAMES or set(path.parts) & DEFAULT_IAC_PARTS:
        return True
    return path.suffix in {".tf", ".tfvars"}


def _is_dev_tool(relative: str) -> bool:
    path = PurePosixPath(relative.lower())
    if set(path.parts) & DEFAULT_DEV_TOOL_PARTS:
        return True
    if "scripts" not in path.parts:
        return False
    stem = Path(path.name).stem.lower()
    return any(
        stem == value or stem.startswith(value + "-") or stem.startswith(value + "_")
        for value in DEV_SCRIPT_STEMS
    )


def exclusion_reason(path: Path, root: Path, settings: Settings) -> str | None:
    relative = repo_relative(path, root)
    lower = relative.lower()
    parts = set(PurePosixPath(lower).parts)
    output = settings.output_directory.lower()
    if lower == output or lower.startswith(output + "/"):
        return "export_output"
    if lower == "wiki" or lower.startswith("wiki/"):
        return "wiki_knowledge_layer"
    if parts & DEFAULT_GENERATED_PARTS or parts & DEFAULT_DEPENDENCY_PARTS:
        return "binary_or_generated"
    if _is_test_file(lower):
        return "scan_scope_tests"
    if _is_ci_or_iac(lower):
        return "scan_scope_ci_or_iac"
    if settings.scan_profile == "target" and _has_prefix(lower, DEFAULT_FRAMEWORK_PREFIXES):
        return "framework_adapter"
    if _is_dev_tool(lower) and not (
        settings.scan_profile == "framework"
        and _has_prefix(lower, (*DEFAULT_FRAMEWORK_PREFIXES, "tools"))
    ):
        return "scan_scope_dev_tooling"
    if _has_prefix(relative, settings.exclude_paths):
        return "configured_exclude"
    if is_sensitive(path):
        return "sensitive_filename"
    if path.name == ".gitkeep":
        return "binary_or_generated"
    return None


def classify_project_file(relative: str) -> str:
    path = PurePosixPath(relative.lower())
    if path.suffix in DOCUMENTATION_EXTENSIONS or path.name.startswith(
        ("readme", "changelog", "license", "contributing")
    ):
        return "documentation"
    if path.suffix in DATA_EXTENSIONS or set(path.parts) & DATA_PARTS:
        return "data_schema"
    if path.suffix in CONFIG_EXTENSIONS or path.name in CONFIG_NAMES:
        return "runtime_config"
    return "runtime_source"


def repository_files(root: Path) -> list[Path]:
    try:
        result = subprocess.run(
            ["git", "-C", str(root), "ls-files", "--cached", "--others", "--exclude-standard", "-z"],
            check=True,
            capture_output=True,
        )
        values = [value for value in result.stdout.split(b"\0") if value]
        paths = [root / value.decode("utf-8", errors="surrogateescape") for value in values]
        return sorted((path for path in paths if path.is_file()), key=lambda item: item.as_posix())
    except (OSError, subprocess.CalledProcessError):
        return sorted((path for path in root.rglob("*") if path.is_file()), key=lambda item: item.as_posix())


def declared_source_paths(pages: Iterable[InputFile], root: Path) -> tuple[str, ...]:
    values: set[str] = set()
    for page in pages:
        sources = parse_frontmatter_text(page.text).get("sources", [])
        if sources in (None, []):
            continue
        if not isinstance(sources, list) or not all(isinstance(item, str) for item in sources):
            raise ExportError(f"invalid sources list in Wiki page: {page.path}")
        for source in sources:
            values.add(validate_relative_config_path(source, root, "frontmatter.sources"))
    return tuple(sorted(values))


def _covered_by(relative: str, source: str, root: Path) -> bool:
    source_path = root / Path(*PurePosixPath(source).parts)
    if source_path.is_dir():
        return relative == source or relative.startswith(source + "/")
    return relative == source


def required_document_coverage(pages: Iterable[InputFile]) -> dict[str, str]:
    by_path = {page.path: page for page in pages}
    result: dict[str, str] = {}
    for path in REQUIRED_WIKI_DOCUMENTS:
        page = by_path.get(path)
        if page is None:
            result[path] = "missing"
            continue
        status = str(parse_frontmatter_text(page.text).get("status", "missing"))
        result[path] = status if status in {"active", "stale", "placeholder"} else "invalid"
    return result


def scan_project(root: Path, settings: Settings, pages: Iterable[InputFile]) -> dict[str, Any]:
    included: list[dict[str, Any]] = []
    excluded: list[dict[str, str]] = []
    for path in repository_files(root):
        try:
            relative = repo_relative(path, root)
        except ExportError:
            excluded.append({"path": str(path), "reason": "path_escape"})
            continue
        reason = exclusion_reason(path, root, settings)
        if reason:
            excluded.append({"path": relative, "reason": reason})
            continue
        try:
            data = path.read_bytes()
        except OSError:
            excluded.append({"path": relative, "reason": "unreadable"})
            continue
        if b"\x00" in data:
            excluded.append({"path": relative, "reason": "binary_or_unsupported_encoding"})
            continue
        try:
            data.decode("utf-8")
        except UnicodeDecodeError:
            excluded.append({"path": relative, "reason": "binary_or_unsupported_encoding"})
            continue
        included.append(
            {
                "path": relative,
                "category": classify_project_file(relative),
                "byte_count": len(data),
                "sha256": sha256_bytes(data),
            }
        )

    page_list = list(pages)
    sources = declared_source_paths(page_list, root)
    uncovered = [
        item["path"]
        for item in included
        if not any(_covered_by(item["path"], source, root) for source in sources)
    ]
    status_counts = Counter(
        str(parse_frontmatter_text(page.text).get("status", "missing")) for page in page_list
    )
    return {
        "included": included,
        "excluded": excluded,
        "included_count": len(included),
        "excluded_count": len(excluded),
        "included_by_category": dict(sorted(Counter(item["category"] for item in included).items())),
        "excluded_by_reason": dict(sorted(Counter(item["reason"] for item in excluded).items())),
        "declared_source_paths": list(sources),
        "uncovered_paths": uncovered,
        "wiki_status_counts": dict(sorted(status_counts.items())),
        "required_documents": required_document_coverage(page_list),
    }


def scan_summary(scan: dict[str, Any]) -> dict[str, Any]:
    return {
        "included_count": scan["included_count"],
        "excluded_count": scan["excluded_count"],
        "included_by_category": scan["included_by_category"],
        "excluded_by_reason": scan["excluded_by_reason"],
        "uncovered_paths": scan["uncovered_paths"],
        "required_documents": scan["required_documents"],
    }


def read_text_file(
    path: Path,
    root: Path,
    settings: Settings,
    skipped: list[dict[str, str]],
) -> InputFile | None:
    relative = repo_relative(path, root)
    reason = exclusion_reason(path, root, settings)
    if reason:
        skipped.append({"path": relative, "reason": reason})
        return None
    if not path.is_file():
        skipped.append({"path": relative, "reason": "not_a_file"})
        return None
    try:
        data = path.read_bytes()
        if b"\x00" in data:
            skipped.append({"path": relative, "reason": "binary_or_unsupported_encoding"})
            return None
        text = data.decode("utf-8")
    except (OSError, UnicodeDecodeError):
        skipped.append({"path": relative, "reason": "binary_or_unsupported_encoding"})
        return None
    return InputFile(path=relative, text=text, digest=sha256_bytes(data))


def expand_path(
    value: str,
    root: Path,
    settings: Settings,
    skipped: list[dict[str, str]],
) -> list[InputFile]:
    relative = validate_relative_config_path(value, root, "source path")
    path = root / Path(*PurePosixPath(relative).parts)
    if not path.exists():
        raise ExportError(f"referenced source does not exist: {relative}")
    paths = [path] if path.is_file() else sorted(path.rglob("*"))
    files: list[InputFile] = []
    for item in paths:
        if item.is_file():
            content = read_text_file(item, root, settings, skipped)
            if content is not None:
                files.append(content)
    return files


def collect_wiki_pages(root: Path) -> tuple[list[InputFile], list[dict[str, str]], list[str]]:
    wiki = root / "wiki"
    if not wiki.is_dir():
        raise ExportError(f"Wiki directory not found: {wiki}")
    pages: list[InputFile] = []
    skipped: list[dict[str, str]] = []
    warnings: list[str] = []
    for path in sorted(wiki.rglob("*.md")):
        relative = repo_relative(path, root)
        if relative == WIKI_LOG_PATH:
            skipped.append({"path": relative, "reason": "wiki_log_disabled"})
            continue
        try:
            data = path.read_bytes()
            text = data.decode("utf-8")
        except (OSError, UnicodeDecodeError) as exc:
            raise ExportError(f"unable to read Wiki page: {path}: {exc}") from exc
        frontmatter = parse_frontmatter_text(text)
        status = str(frontmatter.get("status", ""))
        if status in {"stale", "placeholder"}:
            warnings.append(f"{relative} 的 Wiki status 為 {status}")
        pages.append(InputFile(relative, text, sha256_bytes(data)))
    if not pages:
        raise ExportError("Wiki contains no Markdown pages to export")
    return pages, skipped, warnings


def slugify(value: str) -> str:
    slug = re.sub(r"[^a-z0-9]+", "-", value.lower()).strip("-")
    return slug or "project"


def wiki_page_group(page: InputFile) -> str:
    frontmatter = parse_frontmatter_text(page.text)
    explicit = frontmatter.get("notebooklm_group")
    if explicit not in (None, ""):
        if not isinstance(explicit, str) or not GROUP_PATTERN.fullmatch(explicit):
            raise ExportError(
                f"invalid notebooklm_group in {page.path}; expected a kebab-case string"
            )
        return explicit

    page_type = str(frontmatter.get("type", ""))
    tags = frontmatter.get("tags", [])
    stem = slugify(Path(page.path).stem)
    if page_type in {"index", "overview"}:
        return "project"
    if page_type == "architecture" or page_type in {"dependency", "pattern"}:
        return "architecture"
    if page_type == "synthesis" and isinstance(tags, list) and "system-analysis" in tags:
        return "system-analysis"
    if page.path == "wiki/synthesis/project-function-catalog.md":
        return "project"
    if page_type == "module":
        return f"function-{stem}"
    if page_type == "entity":
        parent = frontmatter.get("parent_module")
        return f"function-{slugify(parent if isinstance(parent, str) else stem)}"
    if page_type == "guide":
        return "project-guides"
    return "project-analysis"


def wiki_units(pages: Iterable[InputFile]) -> list[Unit]:
    grouped: dict[str, list[InputFile]] = {}
    for page in pages:
        grouped.setdefault(wiki_page_group(page), []).append(page)
    preferred = {"project": 0, "architecture": 1, "system-analysis": 3}
    units: list[Unit] = []
    for group in sorted(grouped, key=lambda value: (preferred.get(value, 2), value)):
        members = sorted(grouped[group], key=lambda value: value.path)
        body = [
            f"# 專案文件群組：{group}\n\n",
            "> 由 Codebase LLM Wiki 整理的繁體中文專案文件。",
            "原始識別字、API 名稱與路徑保持不變。\n\n",
            f"> Logical source ID: `docs:{group}`\n\n",
            "## 收錄頁面\n\n",
        ]
        body.extend(f"- `{page.path}`\n" for page in members)
        for page in members:
            body.extend(
                [
                    f"\n## Wiki 頁面：`{page.path}`\n\n",
                    page.text.rstrip(),
                    "\n",
                ]
            )
        units.append(
            Unit(
                logical_source_id=f"docs:{group}",
                kind="documentation",
                group=group,
                title=f"專案文件群組：{group}",
                inputs=tuple(members),
                content="".join(body),
                priority=1_000_000,
            )
        )
    return units


def _page_priority(page: InputFile) -> int:
    page_type = str(parse_frontmatter_text(page.text).get("type", ""))
    return {
        "overview": 95,
        "architecture": 90,
        "synthesis": 85,
        "module": 75,
        "entity": 70,
        "dependency": 55,
        "guide": 45,
        "pattern": 40,
        "index": 20,
    }.get(page_type, 30)


def _path_role_priority(relative: str) -> int:
    path = PurePosixPath(relative.lower())
    name = path.name
    if any(value in name for value in ("main", "program", "server", "route", "controller", "api")):
        return 80
    if path.suffix in DATA_EXTENSIONS or set(path.parts) & DATA_PARTS:
        return 70
    if path.suffix in CONFIG_EXTENSIONS or name in CONFIG_NAMES:
        return 60
    if path.suffix in DOCUMENTATION_EXTENSIONS:
        return 30
    return 50


def referenced_evidence(
    pages: Iterable[InputFile],
    root: Path,
    settings: Settings,
    skipped: list[dict[str, str]],
) -> list[EvidenceCandidate]:
    state: dict[str, dict[str, Any]] = {}

    def add_file(item: InputFile, group: str, score: int) -> None:
        current = state.setdefault(
            item.path,
            {"input_file": item, "groups": set(), "priority": 0, "references": 0},
        )
        current["groups"].add(group)
        current["priority"] = max(current["priority"], score)
        current["references"] += 1

    for page in pages:
        frontmatter = parse_frontmatter_text(page.text)
        sources = frontmatter.get("sources", [])
        if sources in (None, []):
            continue
        if not isinstance(sources, list) or not all(isinstance(item, str) for item in sources):
            raise ExportError(f"invalid sources list in Wiki page: {page.path}")
        group = wiki_page_group(page)
        for position, source in enumerate(sources):
            relative = validate_relative_config_path(source, root, "frontmatter.sources")
            direct = (root / Path(*PurePosixPath(relative).parts)).is_file()
            for item in expand_path(relative, root, settings, skipped):
                score = (
                    _page_priority(page) * 10_000
                    + max(0, 100 - position) * 100
                    + (5_000 if direct else 0)
                    + _path_role_priority(item.path)
                )
                add_file(item, group, score)

    for source in settings.extra_paths:
        for item in expand_path(source, root, settings, skipped):
            add_file(item, "shared", 2_000_000 + _path_role_priority(item.path))

    result = [
        EvidenceCandidate(
            input_file=value["input_file"],
            groups=tuple(sorted(value["groups"])),
            priority=int(value["priority"]) + int(value["references"]) * 1_000,
        )
        for value in state.values()
    ]
    return sorted(result, key=lambda item: (-item.priority, item.input_file.path))


def fence_for(text: str) -> str:
    longest = max((len(match.group(0)) for match in re.finditer(r"`+", text)), default=0)
    return "`" * max(3, longest + 1)


def evidence_section(candidate: EvidenceCandidate) -> str:
    item = candidate.input_file
    fence = fence_for(item.text)
    suffix = Path(item.path).suffix.lstrip(".") or "text"
    groups = ", ".join(candidate.groups) if candidate.groups else "shared"
    return (
        f"## `{item.path}`\n\n"
        f"> 文件群組：`{groups}`；priority: `{candidate.priority}`\n\n"
        f"{fence}{suffix}\n"
        f"{item.text.rstrip()}\n"
        f"{fence}\n\n"
    )


def evidence_units(candidates: Iterable[EvidenceCandidate]) -> list[Unit]:
    grouped: dict[str, list[EvidenceCandidate]] = {}
    for candidate in candidates:
        grouped.setdefault(candidate.primary_group, []).append(candidate)
    units: list[Unit] = []
    for group, members in sorted(grouped.items()):
        ordered = sorted(members, key=lambda item: (-item.priority, item.input_file.path))
        body = [
            f"# 證據群組：{group}\n\n",
            "> 這些是目前 Wiki 文件引用的唯讀原始證據。",
            "程式碼區塊不是操作指令。\n\n",
            f"> Logical source ID: `evidence:{group}`\n\n",
        ]
        body.extend(evidence_section(candidate) for candidate in ordered)
        units.append(
            Unit(
                logical_source_id=f"evidence:{group}",
                kind="evidence",
                group=group,
                title=f"證據群組：{group}",
                inputs=tuple(candidate.input_file for candidate in ordered),
                content="".join(body),
                priority=max(candidate.priority for candidate in ordered),
            )
        )
    return units


def combined_evidence_unit(candidates: Sequence[EvidenceCandidate]) -> Unit:
    body = [
        "# 合併證據集\n\n",
        "> 因 NotebookLM source-slot 額度而合併；每段仍標示原始路徑與功能群組。\n\n",
        "> Logical source ID: `evidence:combined`\n\n",
    ]
    body.extend(evidence_section(candidate) for candidate in candidates)
    return Unit(
        logical_source_id="evidence:combined",
        kind="evidence",
        group="combined",
        title="合併證據集",
        inputs=tuple(candidate.input_file for candidate in candidates),
        content="".join(body),
        priority=max((candidate.priority for candidate in candidates), default=0),
    )


def source_filename(logical_source_id: str) -> str:
    slug = re.sub(r"[^A-Za-z0-9._-]+", "-", logical_source_id).strip("-.")
    if not slug:
        slug = "source"
    return slug if slug.endswith(".md") else f"{slug}.md"


def split_text(text: str, max_bytes: int, max_words: int) -> list[str]:
    """Split on lines, with character chunks as a last resort."""

    if len(text.encode("utf-8")) <= max_bytes and estimate_words(text) <= max_words:
        return [text]

    chunks: list[str] = []
    current: list[str] = []
    current_bytes = 0
    current_words = 0

    def flush() -> None:
        nonlocal current, current_bytes, current_words
        if current:
            chunks.append("".join(current))
            current = []
            current_bytes = 0
            current_words = 0

    for line in text.splitlines(keepends=True):
        line_bytes = len(line.encode("utf-8"))
        line_words = estimate_words(line)
        if line_bytes > max_bytes or line_words > max_words:
            flush()
            remaining = line
            while remaining:
                low, high, best = 1, len(remaining), 1
                while low <= high:
                    middle = (low + high) // 2
                    candidate = remaining[:middle]
                    if len(candidate.encode("utf-8")) <= max_bytes and estimate_words(candidate) <= max_words:
                        best = middle
                        low = middle + 1
                    else:
                        high = middle - 1
                piece = remaining[:best]
                chunks.append(piece)
                remaining = remaining[best:]
            continue
        if current and (
            current_bytes + line_bytes > max_bytes
            or current_words + line_words > max_words
        ):
            flush()
        current.append(line)
        current_bytes += line_bytes
        current_words += line_words
    flush()
    if not chunks:
        raise ExportError("unable to split an oversized source")
    return chunks


def materialize_units(units: Iterable[Unit], settings: Settings) -> list[tuple[Unit, str, str]]:
    materialized: list[tuple[Unit, str, str]] = []
    for unit in units:
        chunks = split_text(unit.content, settings.max_source_bytes, settings.max_source_words)
        base_filename = source_filename(unit.logical_source_id)
        base_path = Path("sources") / base_filename
        for index, chunk in enumerate(chunks, start=1):
            if len(chunks) == 1:
                logical_id = unit.logical_source_id
                filename = base_path
            else:
                logical_id = f"{unit.logical_source_id}#part-{index:03d}"
                filename = base_path.with_name(
                    f"{base_path.stem}.part-{index:03d}{base_path.suffix}"
                )
            part = Unit(
                logical_source_id=logical_id,
                kind=unit.kind,
                group=unit.group,
                title=unit.title,
                inputs=unit.inputs,
                content=chunk,
                priority=unit.priority,
            )
            output_sha = sha256_bytes(chunk.encode("utf-8"))
            materialized.append((part, filename.as_posix(), output_sha))
    return materialized


def compact_document_unit(units: Sequence[Unit]) -> Unit:
    body = [
        "# 完整專案文件\n\n",
        "> 因 NotebookLM source-slot 額度而合併；功能群組與原始 Wiki 路徑仍保留在各節。\n\n",
        "> Logical source ID: `docs:combined`\n\n",
    ]
    for unit in units:
        body.extend([f"## 文件群組：{unit.group}\n\n", unit.content.rstrip(), "\n\n"])
    by_path = {item.path: item for unit in units for item in unit.inputs}
    return Unit(
        logical_source_id="docs:combined",
        kind="documentation",
        group="combined",
        title="完整專案文件",
        inputs=tuple(by_path[key] for key in sorted(by_path)),
        content="".join(body),
        priority=1_000_000,
    )


def fit_document_units(
    units: Sequence[Unit], settings: Settings, max_slots: int
) -> list[tuple[Unit, str, str]]:
    if max_slots <= 0:
        raise ExportError("no NotebookLM source slot remains for mandatory documentation")
    normal = materialize_units(units, settings)
    if len(normal) <= max_slots:
        return normal
    compacted = materialize_units([compact_document_unit(units)], settings)
    if len(compacted) <= max_slots:
        return compacted
    raise ExportError(
        f"mandatory documentation needs {len(compacted)} sources after compaction "
        f"but only {max_slots} slots are available"
    )


def select_evidence(
    candidates: Sequence[EvidenceCandidate],
    settings: Settings,
    max_slots: int,
) -> tuple[list[tuple[Unit, str, str]], list[dict[str, str]]]:
    if not candidates:
        return [], []
    if max_slots <= 0:
        return [], [
            {"path": candidate.input_file.path, "reason": "source_budget"}
            for candidate in candidates
        ]

    normal = materialize_units(evidence_units(candidates), settings)
    if len(normal) <= max_slots:
        return normal, []
    combined = materialize_units([combined_evidence_unit(candidates)], settings)
    if len(combined) <= max_slots:
        return combined, []

    max_bytes = max_slots * settings.max_source_bytes
    max_words = max_slots * settings.max_source_words
    selected: list[EvidenceCandidate] = []
    omitted: list[EvidenceCandidate] = []
    used_bytes = len("# 合併證據集\n".encode("utf-8"))
    used_words = estimate_words("# 合併證據集\n")
    for candidate in candidates:
        section = evidence_section(candidate)
        section_bytes = len(section.encode("utf-8"))
        section_words = estimate_words(section)
        if used_bytes + section_bytes <= max_bytes and used_words + section_words <= max_words:
            selected.append(candidate)
            used_bytes += section_bytes
            used_words += section_words
        else:
            omitted.append(candidate)

    materialized = materialize_units([combined_evidence_unit(selected)], settings) if selected else []
    while len(materialized) > max_slots and selected:
        omitted.append(selected.pop())
        materialized = materialize_units([combined_evidence_unit(selected)], settings) if selected else []
    skipped = [
        {"path": candidate.input_file.path, "reason": "source_budget"}
        for candidate in sorted(omitted, key=lambda item: item.input_file.path)
    ]
    return materialized, skipped


def git_revision(root: Path) -> str | None:
    try:
        result = subprocess.run(
            ["git", "-C", str(root), "rev-parse", "HEAD"],
            check=True,
            capture_output=True,
            text=True,
            encoding="utf-8",
        )
    except (OSError, subprocess.CalledProcessError):
        return None
    value = result.stdout.strip()
    return value or None


def project_map_content(
    root: Path,
    materialized: list[tuple[Unit, str, str]],
    skipped: list[dict[str, str]],
    warnings: list[str],
    settings: Settings,
    coverage: dict[str, str],
) -> str:
    lines = [
        f"# {root.name} — NotebookLM 專案導覽\n\n",
        "> 這是產生的繁體中文導覽來源。只上傳 `sources/` 下的 Markdown。\n\n",
        "## 建議閱讀順序\n\n",
        "1. 先讀 `docs:*` 文件，了解功能、架構與系統分析。\n",
        "2. 再以 `evidence:*` 查核原始程式、設定、資料結構與既有文件。\n",
        "3. `partial`、`gap`、warning 或 skipped 項目都不是已驗證事實。\n\n",
        "## 文件覆蓋\n\n",
    ]
    lines.extend(f"- `{path}` — `{status}`\n" for path, status in coverage.items())
    lines.extend(
        [
            "\n## Source catalog\n\n",
            f"- Profile: `{settings.profile}`\n",
            f"- Sources: `{len(materialized)}` / `{settings.available_source_slots}` available slots\n",
            f"- 每 source safety limit: `{settings.max_source_bytes}` bytes / `{settings.max_source_words}` estimated words\n\n",
        ]
    )
    for unit, filename, _ in materialized:
        lines.append(
            f"- `{unit.logical_source_id}` — `{filename}` — {unit.title} — group `{unit.group}`\n"
        )
    if warnings:
        lines.extend(["\n## Warnings\n\n"])
        lines.extend(f"- {warning}\n" for warning in warnings)
    if skipped:
        lines.extend(["\n## Skipped inputs\n\n"])
        lines.extend(f"- `{item['path']}` — {item['reason']}\n" for item in skipped)
    lines.extend(
        [
            "\n## 增量更新規則\n\n",
            "依 `upload-plan.md` 新增、替換或刪除 static sources；`unchanged` 不需重傳。\n",
        ]
    )
    return "".join(lines)


def source_manifest_entry(unit: Unit, filename: str, output_sha: str) -> dict[str, Any]:
    return {
        "byte_count": unit.byte_count,
        "estimated_words": unit.estimated_words,
        "file": filename,
        "group": unit.group,
        "inputs": [{"path": item.path, "sha256": item.digest} for item in unit.inputs],
        "kind": unit.kind,
        "logical_source_id": unit.logical_source_id,
        "output_sha256": output_sha,
        "priority": unit.priority,
    }


def load_previous_manifest(output: Path) -> dict[str, Any] | None:
    path = output / "manifest.json"
    if not path.exists():
        return None
    try:
        value = json.loads(path.read_text(encoding="utf-8"))
    except (OSError, json.JSONDecodeError) as exc:
        raise ExportError(f"unable to read previous manifest: {path}: {exc}") from exc
    schema = value.get("schema_version") if isinstance(value, dict) else None
    if not isinstance(value, dict) or schema not in SUPPORTED_MANIFEST_SCHEMAS:
        raise ExportError(
            f"unsupported manifest schema in {path}; expected one of "
            f"{sorted(SUPPORTED_MANIFEST_SCHEMAS)}"
        )
    if not isinstance(value.get("sources", []), list):
        raise ExportError(f"previous manifest sources must be an array: {path}")
    return value


def previous_by_id(previous: dict[str, Any] | None, output: Path) -> dict[str, dict[str, Any]]:
    if not previous:
        return {}
    result: dict[str, dict[str, Any]] = {}
    for item in previous.get("sources", []):
        if not isinstance(item, dict) or not isinstance(item.get("logical_source_id"), str):
            continue
        entry = dict(item)
        if not entry.get("output_sha256") and isinstance(entry.get("file"), str):
            old_path = output / entry["file"]
            if old_path.is_file():
                entry["output_sha256"] = sha256_file(old_path)
        result[entry["logical_source_id"]] = entry
    return result


def build_actions(
    current: list[dict[str, Any]], previous: dict[str, dict[str, Any]]
) -> dict[str, list[dict[str, Any]]]:
    actions = {key: [] for key in ("added", "changed", "deleted", "unchanged")}
    current_ids = set()
    for item in current:
        source_id = item["logical_source_id"]
        current_ids.add(source_id)
        old = previous.get(source_id)
        if old is None:
            actions["added"].append({"logical_source_id": source_id, "file": item["file"]})
        elif old.get("output_sha256") == item.get("output_sha256") and old.get("file") == item.get("file"):
            actions["unchanged"].append({"logical_source_id": source_id, "file": item["file"]})
        else:
            actions["changed"].append(
                {
                    "logical_source_id": source_id,
                    "previous_file": old.get("file"),
                    "file": item["file"],
                }
            )
    for source_id, old in previous.items():
        if source_id not in current_ids:
            actions["deleted"].append(
                {"logical_source_id": source_id, "file": old.get("file")}
            )
    for values in actions.values():
        values.sort(key=lambda item: str(item.get("logical_source_id", "")))
    return actions


def upload_plan_content(
    source_count: int,
    available_slots: int,
    actions: dict[str, list[dict[str, Any]]],
    omitted_evidence: list[dict[str, str]],
    warnings: list[str],
) -> str:
    lines = [
        "# NotebookLM 增量上傳計畫\n\n",
        f"產生來源數：{source_count}/{available_slots} 個可用 slots。\n\n",
        "只上傳 `sources/` 下的 Markdown。不要把 manifest、upload plan 或 README 當成專案證據。\n\n",
    ]
    labels = (
        ("added", "## 新增\n\n"),
        ("changed", "## 替換（先移除舊 source）\n\n"),
        ("deleted", "## 刪除\n\n"),
        ("unchanged", "## 不需動作\n\n"),
    )
    for key, heading in labels:
        lines.append(heading)
        values = actions[key]
        if not values:
            lines.append("_無。_\n\n")
            continue
        for item in values:
            if key == "changed":
                lines.append(
                    f"- `{item['logical_source_id']}` — 移除 `{item.get('previous_file')}`，再上傳 `{item['file']}`\n"
                )
            else:
                lines.append(f"- `{item['logical_source_id']}` — `{item.get('file')}`\n")
        lines.append("\n")
    if omitted_evidence:
        lines.extend(["## 因額度未匯出的證據\n\n"])
        lines.extend(f"- `{item['path']}` — {item['reason']}\n" for item in omitted_evidence)
        lines.append("\n")
    if warnings:
        lines.extend(["## Warnings\n\n"])
        lines.extend(f"- {warning}\n" for warning in warnings)
    return "".join(lines)


def readme_content() -> str:
    return """# NotebookLM Enterprise 本機來源包

此目錄由 `export-notebooklm.py` 產生。

只上傳 `sources/` 下的 Markdown。`manifest.json`、`upload-plan.md` 與本 README
保留在本機。重新產生後依 upload plan 操作：`unchanged` 不需重傳；`changed`
必須先移除 NotebookLM 中的舊 static source，再上傳新檔。

Exporter 完全離線，不會呼叫 NotebookLM、不會上傳檔案，也不會修改 raw sources
或 Wiki pages。
"""


def _json_bytes(value: Any) -> bytes:
    return (json.dumps(value, ensure_ascii=False, indent=2, sort_keys=True) + "\n").encode(
        "utf-8"
    )


def commit_output(
    output: Path,
    files: dict[str, bytes],
    previous: dict[str, Any] | None,
) -> None:
    if output.exists() and not output.is_dir():
        raise ExportError(f"output path is not a directory: {output}")
    parent = output.parent
    parent.mkdir(parents=True, exist_ok=True)
    stage: Path | None = Path(tempfile.mkdtemp(prefix=f"{output.name}.staging-", dir=parent))
    backup: Path | None = None
    try:
        if output.is_dir():
            assert stage is not None
            shutil.copytree(output, stage, dirs_exist_ok=True)
        old_sources = {
            item.get("file")
            for item in (previous or {}).get("sources", [])
            if isinstance(item, dict) and isinstance(item.get("file"), str)
        }
        for old_file in old_sources:
            assert stage is not None
            old_path = stage / old_file
            if old_path.is_file():
                old_path.unlink()
        for relative, data in files.items():
            assert stage is not None
            destination = stage / relative
            destination.parent.mkdir(parents=True, exist_ok=True)
            destination.write_bytes(data)
        if output.exists():
            backup = Path(tempfile.mkdtemp(prefix=f"{output.name}.backup-", dir=parent))
            backup.rmdir()
            os.replace(output, backup)
        assert stage is not None
        os.replace(stage, output)
        stage = None
        if backup is not None and backup.exists():
            shutil.rmtree(backup)
            backup = None
    except OSError as exc:
        if not output.exists() and backup is not None and backup.exists():
            os.replace(backup, output)
            backup = None
        raise ExportError(f"unable to commit NotebookLM output: {exc}") from exc
    finally:
        if stage is not None and stage.exists():
            shutil.rmtree(stage, ignore_errors=True)
        if backup is not None and backup.exists():
            shutil.rmtree(backup, ignore_errors=True)


def limits_payload(settings: Settings) -> dict[str, int]:
    return {
        "enterprise_max_bytes": ENTERPRISE_MAX_BYTES,
        "enterprise_max_sources": ENTERPRISE_MAX_SOURCES,
        "enterprise_max_words": ENTERPRISE_MAX_WORDS,
        "max_bytes": settings.max_source_bytes,
        "max_sources": settings.source_limit,
        "max_words": settings.max_source_words,
        "reserved_source_slots": settings.reserved_source_slots,
        "available_sources": settings.available_source_slots,
    }


def _load_wiki_lint():
    path = Path(__file__).with_name("lint-wiki.py")
    spec = importlib.util.spec_from_file_location("codebase_wiki_notebooklm_lint", path)
    if spec is None or spec.loader is None:
        raise ExportError(f"unable to load Wiki lint implementation: {path}")
    module = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(module)
    return module


def _settings_fingerprint(settings: Settings, root: Path) -> dict[str, Any]:
    return {
        "profile": settings.profile,
        "scan_profile": settings.scan_profile,
        "output_directory": settings.output_directory,
        "source_limit": settings.source_limit,
        "reserved_source_slots": settings.reserved_source_slots,
        "max_source_bytes": settings.max_source_bytes,
        "max_source_words": settings.max_source_words,
        "include_evidence": settings.include_evidence,
        "extra_paths": list(settings.extra_paths),
        "exclude_paths": list(settings.exclude_paths),
        "config": repo_relative(settings.config_path, root) if settings.config_path else None,
    }


def _preflight_identity(
    root: Path,
    settings: Settings,
    pages: Sequence[InputFile],
    scan: dict[str, Any],
    lint_result: dict[str, Any],
) -> tuple[str, str]:
    material = {
        "schema_version": PREFLIGHT_SCHEMA_VERSION,
        "settings": _settings_fingerprint(settings, root),
        "wiki": [{"path": page.path, "sha256": page.digest} for page in pages],
        "inventory": [
            {"path": item["path"], "sha256": item["sha256"]}
            for item in scan["included"]
        ],
        "required_documents": scan["required_documents"],
        "deterministic_findings": lint_result.get("findings", []),
    }
    inventory_hash = sha256_bytes(
        json.dumps(material, ensure_ascii=False, sort_keys=True, separators=(",", ":")).encode(
            "utf-8"
        )
    )
    return inventory_hash, f"sha256:{inventory_hash}"


def build_preflight(root: Path, settings: Settings) -> dict[str, Any]:
    pages, skipped, warnings = collect_wiki_pages(root)
    scan = scan_project(root, settings, pages)
    lint_result = _load_wiki_lint().lint_wiki(root / "wiki", root)
    missing = [path for path, status in scan["required_documents"].items() if status != "active"]
    warnings.extend(f"必要文件尚未完成：{path} ({scan['required_documents'][path]})" for path in missing)
    required_relatives = {
        PurePosixPath(path).relative_to("wiki").as_posix() for path in REQUIRED_WIKI_DOCUMENTS
    }
    required_document_issues = [
        item
        for item in lint_result.get("findings", [])
        if item.get("page") in required_relatives
        and item.get("code")
        in {"frontmatter", "invalid_source", "missing_source", "stale_source"}
    ]
    critical_count = int(lint_result.get("summary", {}).get("critical", 0))
    ready = not missing and not required_document_issues and critical_count == 0
    inventory_hash, preflight_id = _preflight_identity(
        root, settings, pages, scan, lint_result
    )
    return {
        "ok": True,
        "mode": "preflight",
        "preflight_schema_version": PREFLIGHT_SCHEMA_VERSION,
        "preflight_id": preflight_id,
        "inventory_hash": inventory_hash,
        "ready_to_export": ready,
        "scan_profile": settings.scan_profile,
        "scope": {
            "included": ["runtime_source", "runtime_config", "data_schema", "documentation"],
            "excluded": [
                "tests",
                "ci_cd",
                "iac",
                "build_dev_tooling",
                "dependencies",
                "generated",
                "binary",
                "credentials",
            ]
            + (["framework_adapters"] if settings.scan_profile == "target" else []),
        },
        "inventory": scan,
        "limits": limits_payload(settings),
        "wiki_pages": len(pages),
        "lint": {
            "deterministic_status": lint_result.get("deterministic_status"),
            "semantic_status": lint_result.get("semantic_status"),
            "overall_status": lint_result.get("overall_status"),
            "summary": lint_result.get("summary", {}),
            "findings": lint_result.get("findings", []),
        },
        "required_document_issues": required_document_issues,
        "skipped": skipped,
        "warnings": warnings,
    }


def build_pack(root: Path, output: Path, settings: Settings) -> dict[str, Any]:
    pages, initial_skipped, warnings = collect_wiki_pages(root)
    scan = scan_project(root, settings, pages)
    coverage = scan["required_documents"]
    incomplete = [path for path, status in coverage.items() if status != "active"]
    if incomplete:
        details = ", ".join(f"{path} ({coverage[path]})" for path in incomplete)
        raise ExportError(f"mandatory Wiki documentation is not active: {details}")
    for path, status in coverage.items():
        if status != "active":
            warnings.append(f"必要文件尚未完成：{path} ({status})")
    if scan["uncovered_paths"]:
        warnings.append(f"安全掃描仍有 {len(scan['uncovered_paths'])} 個路徑未被 Wiki sources 覆蓋")

    skipped = list(initial_skipped)
    candidates = referenced_evidence(pages, root, settings, skipped) if settings.include_evidence else []
    available = settings.available_source_slots
    if available < 2:
        raise ExportError("at least two source slots are required for project map and documentation")

    documents = fit_document_units(wiki_units(pages), settings, available - 1)
    preliminary_map = Unit(
        logical_source_id="project-map",
        kind="project",
        group="project",
        title="專案導覽",
        inputs=tuple(pages),
        content=project_map_content(root, documents, skipped, warnings, settings, coverage),
        priority=2_000_000,
    )
    preliminary_map_parts = materialize_units([preliminary_map], settings)
    evidence_slots = max(0, available - len(documents) - len(preliminary_map_parts))

    evidence: list[tuple[Unit, str, str]] = []
    budget_skipped: list[dict[str, str]] = []
    project_parts: list[tuple[Unit, str, str]] = []
    for _ in range(4):
        evidence, budget_skipped = select_evidence(candidates, settings, evidence_slots)
        all_skipped = skipped + budget_skipped
        current_warnings = list(warnings)
        if budget_skipped:
            current_warnings.append(
                f"因 source budget 未匯出 {len(budget_skipped)} 個 evidence files"
            )
        omitted_paths = {item["path"] for item in budget_skipped}
        project_inputs = pages + [
            candidate.input_file
            for candidate in candidates
            if candidate.input_file.path not in omitted_paths
        ]
        project_unit = Unit(
            logical_source_id="project-map",
            kind="project",
            group="project",
            title="專案導覽",
            inputs=tuple(project_inputs),
            content=project_map_content(
                root,
                documents + evidence,
                all_skipped,
                current_warnings,
                settings,
                coverage,
            ),
            priority=2_000_000,
        )
        project_parts = materialize_units([project_unit], settings)
        total = len(project_parts) + len(documents) + len(evidence)
        if total <= available:
            warnings = current_warnings
            break
        evidence_slots = max(0, evidence_slots - (total - available))
    else:
        raise ExportError("unable to fit project map and mandatory documentation within source limit")

    materialized = project_parts + documents + evidence
    if len(materialized) > available:
        raise ExportError(
            f"source pack needs {len(materialized)} sources but only {available} slots are available"
        )
    for unit, _, _ in materialized:
        if unit.byte_count > settings.max_source_bytes or unit.estimated_words > settings.max_source_words:
            raise ExportError(f"source still exceeds limits after splitting: {unit.logical_source_id}")

    entries = [source_manifest_entry(unit, filename, output_sha) for unit, filename, output_sha in materialized]
    previous_manifest = load_previous_manifest(output)
    previous = previous_by_id(previous_manifest, output)
    actions = build_actions(entries, previous)
    output_relative = repo_relative(output, root)
    config_relative = repo_relative(settings.config_path, root) if settings.config_path else None
    all_skipped = skipped + budget_skipped
    manifest = {
        "schema_version": EXPORT_SCHEMA_VERSION,
        "generated_at": datetime.now(timezone.utc).replace(microsecond=0).isoformat().replace("+00:00", "Z"),
        "git_revision": git_revision(root),
        "profile": settings.profile,
        "project": root.name,
        "output_directory": output_relative,
        "config": config_relative,
        "limits": limits_payload(settings),
        "scan": scan_summary(scan),
        "coverage": {
            "required_documents": coverage,
            "documentation_groups": sorted({unit.group for unit, _, _ in documents}),
        },
        "source_count": len(entries),
        "sources": entries,
        "omitted_evidence": budget_skipped,
        "skipped": all_skipped,
        "warnings": warnings,
    }
    plan = upload_plan_content(
        len(entries), settings.available_source_slots, actions, budget_skipped, warnings
    )
    files: dict[str, bytes] = {
        "manifest.json": _json_bytes(manifest),
        "upload-plan.md": plan.encode("utf-8"),
        "README.md": readme_content().encode("utf-8"),
    }
    files.update({filename: unit.content.encode("utf-8") for unit, filename, _ in materialized})
    return {
        "manifest": manifest,
        "actions": actions,
        "files": files,
        "output": output_relative,
        "source_count": len(entries),
        "warnings": warnings,
        "skipped_count": len(all_skipped),
        "omitted_evidence_count": len(budget_skipped),
    }


def build_parser() -> argparse.ArgumentParser:
    parser = argparse.ArgumentParser(prog="export-notebooklm.py")
    parser.add_argument("--root", type=Path, default=Path("."))
    parser.add_argument("--output", type=Path)
    parser.add_argument("--config", type=Path)
    action = parser.add_mutually_exclusive_group()
    action.add_argument("--preflight", action="store_true")
    action.add_argument("--apply", action="store_true")
    parser.add_argument("--preflight-id")
    parser.add_argument("--format", choices=("json", "text"), default="text")
    return parser


def main(argv: Sequence[str] | None = None) -> int:
    configure_utf8_stdio()
    args = build_parser().parse_args(argv)
    root = args.root.resolve()
    if not root.is_dir():
        print(json.dumps({"ok": False, "error": f"root is not a directory: {root}"}, ensure_ascii=False))
        return 2
    try:
        config_path = None
        if args.config:
            config_path = args.config if args.config.is_absolute() else root / args.config
            config_path = config_path.resolve()
        settings = load_settings(root, config_path)
        if args.preflight:
            if args.preflight_id:
                raise ExportError("--preflight-id is valid only with --apply")
            result = build_preflight(root, settings)
        else:
            if not args.apply:
                raise ExportError(
                    "direct export is disabled; run --preflight, then use "
                    "--apply --preflight-id <id>"
                )
            if not args.preflight_id:
                raise ExportError("--apply requires --preflight-id from the latest preflight")
            preflight = build_preflight(root, settings)
            if args.preflight_id != preflight["preflight_id"]:
                raise ExportError(
                    "preflight_id no longer matches the current Wiki, inventory, or configuration; "
                    "run --preflight again"
                )
            if not preflight["ready_to_export"]:
                raise ExportError(
                    "preflight is not ready to export; complete mandatory documents and resolve "
                    "deterministic Critical findings"
                )
            output = (root / args.output) if args.output else (root / settings.output_directory)
            output = output.resolve()
            output_relative = repo_relative(output, root)
            if output == root or output_relative == ".":
                raise ExportError("output must be a child directory of repository root")
            result = build_pack(root, output, settings)
            commit_output(output, result.pop("files"), load_previous_manifest(output))
            result["ok"] = True
            result["mode"] = "apply"
            result["preflight_id"] = preflight["preflight_id"]
    except (ExportError, OSError) as exc:
        result = {"ok": False, "error": str(exc)}
        if args.format == "json":
            print(json.dumps(result, ensure_ascii=False, indent=2))
        else:
            print(f"NotebookLM export failed: {exc}")
        return 2

    if args.format == "json":
        print(json.dumps(result, ensure_ascii=False, indent=2, sort_keys=True))
    elif args.preflight:
        inventory = result["inventory"]
        print(
            "NotebookLM preflight: "
            f"included={inventory['included_count']}, "
            f"excluded={inventory['excluded_count']}, "
            f"uncovered={len(inventory['uncovered_paths'])}, "
            f"ready={str(result['ready_to_export']).lower()}"
        )
        print(f"Preflight ID: {result['preflight_id']}")
        for warning in result["warnings"]:
            print(f"Warning: {warning}")
    else:
        actions = result["actions"]
        print(
            "NotebookLM export: "
            f"{result['source_count']} sources; "
            + ", ".join(f"{key}={len(actions[key])}" for key in actions)
        )
        print(f"Output: {result['output']}")
        for warning in result["warnings"]:
            print(f"Warning: {warning}")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
