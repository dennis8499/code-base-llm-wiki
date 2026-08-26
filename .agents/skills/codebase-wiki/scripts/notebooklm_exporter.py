"""Function-oriented NotebookLM Enterprise preflight and source-pack builder.

``--preflight`` performs a read-only inventory of the explicit filesystem root.
The default mode packages curated Wiki documents and selected evidence into
``.notebooklm``. This module never calls NotebookLM or modifies raw sources and
Wiki pages.
"""

from __future__ import annotations

import argparse
from collections import Counter
from dataclasses import dataclass, replace
from datetime import datetime, timezone
import fnmatch
import hashlib
import importlib.util
import json
import os
from pathlib import Path, PurePosixPath
import re
import shutil
import stat
import subprocess
import sys
import tempfile
import tomllib
from typing import Any, Iterable, Sequence

try:
    from frontmatter import (
        configure_utf8_stdio,
        parse_frontmatter_text,
        validate_regular_tree,
    )
except ModuleNotFoundError:  # pragma: no cover - useful when loaded by a caller
    sys.path.insert(0, str(Path(__file__).resolve().parent))
    from frontmatter import (
        configure_utf8_stdio,
        parse_frontmatter_text,
        validate_regular_tree,
    )


EXPORT_SCHEMA_VERSION = 3
SUPPORTED_MANIFEST_SCHEMAS = {1, 2, EXPORT_SCHEMA_VERSION}
PREFLIGHT_SCHEMA_VERSION = 3
OUTPUT_TRANSACTION_VERSION = 1
OUTPUT_TRANSACTION_SUFFIX = ".notebooklm-transaction.json"
OUTPUT_TRANSACTION_LOCK_SUFFIX = ".notebooklm-transaction.lock"
PROFILE_NAME = "gemini-notebook-enterprise"
ENTERPRISE_MAX_SOURCES = 300
ENTERPRISE_MAX_BYTES = 200_000_000
ENTERPRISE_MAX_WORDS = 500_000
DEFAULT_MAX_SOURCES = ENTERPRISE_MAX_SOURCES
DEFAULT_MAX_BYTES = 180_000_000
DEFAULT_MAX_WORDS = 450_000
EXCLUDED_SUMMARY_ENTRY_LIMIT = 4_096

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
    ".mypy_cache",
    ".ruff_cache",
    "bin",
    "build",
    "cache",
    "coverage",
    "dist",
    "logs",
    ".codex-hook-logs",
    ".github-hook-logs",
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
NON_CJK_TOKEN_PATTERN = re.compile(
    r"[^\s\u3400-\u4dbf\u4e00-\u9fff\uf900-\ufaff]+"
)
WORD_COUNT_MODEL = "han_characters_plus_non_han_tokens"
GROUP_PATTERN = re.compile(r"^[a-z0-9]+(?:-[a-z0-9]+)*$")
RETRIEVAL_CONTRACT = "wiki-first-direct-lookup-v1"
QUERY_INDEX_SOURCE_ID = "query-index"
MAX_PRIMARY_SOURCE_GROUPS = 5
DLP_PROFILE = "notebooklm-enterprise-basic"
DLP_ENFORCEMENT = "inspect_and_block"
DLP_DETECTORS = (
    "CREDIT_CARD_NUMBER",
    "FINANCIAL_ACCOUNT_NUMBER",
    "GCP_CREDENTIALS",
    "GCP_API_KEY",
    "PASSWORD",
)
DLP_RULE_METADATA = {
    "CREDIT_CARD_NUMBER": {"category": "financial", "severity": "high"},
    "FINANCIAL_ACCOUNT_NUMBER": {"category": "financial", "severity": "high"},
    "GCP_CREDENTIALS": {"category": "credential", "severity": "high"},
    "GCP_API_KEY": {"category": "credential", "severity": "high"},
    "PASSWORD": {"category": "credential", "severity": "high"},
}
DLP_FINGERPRINT_PATTERN = re.compile(r"^sha256:[0-9a-f]{64}$")
DLP_GCP_API_KEY_PATTERN = re.compile(
    r"(?<![A-Za-z0-9_-])AIza[0-9A-Za-z_-]{35}(?![A-Za-z0-9_-])"
)
DLP_PRIVATE_KEY_PATTERN = re.compile(
    r"-----BEGIN(?: [A-Z0-9]+)? PRIVATE KEY-----.*?"
    r"-----END(?: [A-Z0-9]+)? PRIVATE KEY-----",
    re.DOTALL,
)
DLP_PASSWORD_PATTERN = re.compile(
    r"""(?ix)
    (?P<key>\b(?:password|passwd|pwd)\b)\s*(?:[:=]|=>)\s*
    (?P<quote>['"]?)(?P<value>[^\s,;#}\]"']{3,})(?P=quote)
    """
)
DLP_FINANCIAL_ACCOUNT_PATTERN = re.compile(
    r"""(?ix)
    \b(?:account(?:[_ -]?number)?|bank(?:[_ -]?account)?|iban)\b
    \s*(?:[:=]\s*)?['"]?
    (?P<value>\d(?:[\d -]{6,18}\d))['"]?
    """
)
DLP_CREDIT_CARD_PATTERN = re.compile(r"(?<!\d)(?:\d[ -]?){11,18}\d(?!\d)")


class ExportError(ValueError):
    """Raised when a safe, complete documentation pack cannot be produced."""


@dataclass(frozen=True)
class DlpAllowlistEntry:
    path: str
    rule: str
    fingerprint: str

    def as_dict(self) -> dict[str, str]:
        return {
            "path": self.path,
            "rule": self.rule,
            "fingerprint": self.fingerprint,
        }


@dataclass(frozen=True)
class DlpFinding:
    path: str
    line: int
    rule: str
    category: str
    severity: str
    fingerprint: str

    def as_dict(self) -> dict[str, Any]:
        return {
            "path": self.path,
            "line": self.line,
            "rule": self.rule,
            "category": self.category,
            "severity": self.severity,
            "fingerprint": self.fingerprint,
        }


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
    dlp_profile: str
    dlp_allowlist: tuple[DlpAllowlistEntry, ...]
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
    if (
        candidate.is_absolute()
        or ".." in candidate.parts
        or re.fullmatch(r"[A-Za-z]:.*", candidate.as_posix())
    ):
        raise ExportError(f"{field} must be a repo-relative path: {value!r}")
    path = root / Path(*candidate.parts)
    repo_relative(path, root)
    return candidate.as_posix().rstrip("/") or "."


def _reject_symlink_components(root: Path, candidate: Path, field: str) -> None:
    """Reject a path that reaches its destination through a symlink."""

    lexical_root = Path(os.path.abspath(root))
    lexical_candidate = Path(os.path.abspath(candidate))

    # Windows can expose the same directory through an 8.3 short path or its
    # Unicode long-path spelling.  Scan the caller-provided spellings first so
    # symlink/reparse boundaries remain visible, then compare their resolved
    # identities so equivalent spellings are accepted.
    for path in (lexical_root, lexical_candidate):
        current = Path(path.anchor) if path.anchor else Path()
        for component in path.parts:
            if component == path.anchor:
                continue
            current /= component
            if _is_reparse_point(current):
                raise ExportError(
                    f"{field} must not contain symlink or reparse point: {candidate}"
                )

    try:
        lexical_candidate.resolve(strict=False).relative_to(
            lexical_root.resolve(strict=False)
        )
    except ValueError as exc:
        raise ExportError(f"{field} must stay inside the repository: {candidate}") from exc


def _is_reparse_point(path: Path) -> bool:
    """Detect symlinks and Windows junction/reparse points without following them."""

    if path.is_symlink():
        return True
    if os.name != "nt":
        return False
    try:
        attributes = os.stat(path, follow_symlinks=False).st_file_attributes
    except FileNotFoundError:
        return False
    except OSError as exc:
        raise ExportError(f"unable to inspect path boundary: {path}: {exc}") from exc
    return bool(attributes & getattr(stat, "FILE_ATTRIBUTE_REPARSE_POINT", 0x400))


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


def _dlp_allowlist_config(
    values: dict[str, Any], root: Path
) -> tuple[DlpAllowlistEntry, ...]:
    value = values.get("dlp_allowlist", [])
    if not isinstance(value, list):
        raise ExportError("dlp_allowlist must be an array of tables")
    entries: list[DlpAllowlistEntry] = []
    for index, item in enumerate(value):
        if not isinstance(item, dict):
            raise ExportError(f"dlp_allowlist[{index}] must be a table")
        path = item.get("path")
        rule = item.get("rule")
        fingerprint = item.get("fingerprint")
        if not isinstance(path, str) or not path.strip():
            raise ExportError(f"dlp_allowlist[{index}].path must be a non-empty string")
        if not isinstance(rule, str) or rule not in DLP_DETECTORS:
            raise ExportError(
                f"dlp_allowlist[{index}].rule must be one of {DLP_DETECTORS}"
            )
        if not isinstance(fingerprint, str) or not DLP_FINGERPRINT_PATTERN.fullmatch(
            fingerprint
        ):
            raise ExportError(
                f"dlp_allowlist[{index}].fingerprint must match sha256:<64 lowercase hex>"
            )
        relative = validate_relative_config_path(path, root, f"dlp_allowlist[{index}].path")
        if relative == ".":
            raise ExportError(f"dlp_allowlist[{index}].path must identify a file")
        entries.append(DlpAllowlistEntry(relative, rule, fingerprint))
    return tuple(sorted(entries, key=lambda item: (item.path, item.rule, item.fingerprint)))


def load_settings(root: Path, config_path: Path | None = None) -> Settings:
    if config_path is None:
        selected_config = root / "notebooklm.toml"
    elif config_path.is_absolute():
        _reject_symlink_components(root, config_path, "config path")
        try:
            relative = repo_relative(config_path, root)
        except ExportError as exc:
            raise ExportError(
                f"config path must stay inside the repository root: {config_path}"
            ) from exc
        selected_config = root / Path(*PurePosixPath(relative).parts)
    else:
        relative = validate_relative_config_path(config_path.as_posix(), root, "config path")
        selected_config = root / Path(*PurePosixPath(relative).parts)
    _reject_symlink_components(root, selected_config, "config path")
    raw: dict[str, Any] = {}
    if config_path is not None and not selected_config.exists():
        raise ExportError(f"config path does not exist: {selected_config}")
    if selected_config.exists():
        if not selected_config.is_file():
            raise ExportError(f"config path is not a file: {selected_config}")
        try:
            raw = _config_values(tomllib.loads(selected_config.read_text(encoding="utf-8")))
        except (OSError, UnicodeError, tomllib.TOMLDecodeError) as exc:
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
    if output_directory == ".":
        raise ExportError("output_directory must be a child directory of repository root")
    _reject_symlink_components(
        root,
        root / Path(*PurePosixPath(output_directory).parts),
        "output_directory",
    )

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

    dlp_profile = raw.get("dlp_profile", DLP_PROFILE)
    if dlp_profile != DLP_PROFILE:
        raise ExportError(f"dlp_profile must be {DLP_PROFILE!r}")

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
        dlp_profile=dlp_profile,
        dlp_allowlist=_dlp_allowlist_config(raw, root),
        config_path=selected_config if selected_config.is_file() else None,
    )


def estimate_words(text: str) -> int:
    """Estimate NotebookLM words without dropping mixed-language content.

    NotebookLM can count Han characters independently of whitespace-delimited
    Latin or code tokens.  Counting the larger of those two populations
    underestimates a source that contains both, so the safety estimate adds
    Han characters to maximal non-Han, non-whitespace token runs.  Han
    characters inside a mixed token are therefore counted once as Han and the
    surrounding identifier/text run is counted separately.
    """

    han_characters = len(CJK_PATTERN.findall(text))
    non_han_tokens = len(NON_CJK_TOKEN_PATTERN.findall(text))
    return han_characters + non_han_tokens


def _line_number(text: str, offset: int) -> int:
    return text.count("\n", 0, offset) + 1


def _normalized_digits(value: str) -> str:
    return re.sub(r"\D", "", value)


def _luhn_valid(value: str) -> bool:
    digits = _normalized_digits(value)
    if not 12 <= len(digits) <= 19:
        return False
    total = 0
    parity = len(digits) % 2
    for index, digit in enumerate(digits):
        number = int(digit)
        if index % 2 == parity:
            number *= 2
            if number > 9:
                number -= 9
        total += number
    return total % 10 == 0


def _password_is_literal(value: str) -> bool:
    normalized = value.strip().strip("'\"")
    lowered = normalized.lower()
    if not normalized:
        return False
    if lowered in {
        "changeme",
        "change-me",
        "change_me",
        "example",
        "replace-me",
        "replace_me",
        "sample",
        "todo",
        "tbd",
        "your-password",
        "your_password",
    }:
        return False
    return not normalized.startswith(("${", "{{", "$(", "<", "os.", "process.env", "getenv(", "env["))


def _line_text(text: str, offset: int) -> str:
    start = text.rfind("\n", 0, offset) + 1
    end = text.find("\n", offset)
    return text[start:] if end == -1 else text[start:end]


def _iter_dlp_matches(text: str) -> Iterable[tuple[str, str, int]]:
    for match in DLP_PRIVATE_KEY_PATTERN.finditer(text):
        yield "GCP_CREDENTIALS", match.group(0), match.start()

    for match in DLP_GCP_API_KEY_PATTERN.finditer(text):
        yield "GCP_API_KEY", match.group(0), match.start()

    for match in DLP_PASSWORD_PATTERN.finditer(text):
        value = match.group("value")
        if _password_is_literal(value):
            yield "PASSWORD", value, match.start("value")

    for match in DLP_FINANCIAL_ACCOUNT_PATTERN.finditer(text):
        value = match.group("value")
        if len(_normalized_digits(value)) >= 8:
            yield "FINANCIAL_ACCOUNT_NUMBER", value, match.start("value")

    for match in DLP_CREDIT_CARD_PATTERN.finditer(text):
        value = match.group(0)
        digits = _normalized_digits(value)
        if not _luhn_valid(value):
            continue
        if not any(separator in value for separator in (" ", "-")):
            context = _line_text(text, match.start()).lower()
            if not any(
                marker in context
                for marker in ("credit", "card", "visa", "mastercard", "amex", "cc_number")
            ):
                continue
        yield "CREDIT_CARD_NUMBER", digits, match.start()


def _dlp_fingerprint(rule: str, value: str) -> str:
    normalized = _normalized_digits(value) if rule in {
        "CREDIT_CARD_NUMBER",
        "FINANCIAL_ACCOUNT_NUMBER",
    } else value
    return f"sha256:{sha256_bytes(normalized.encode('utf-8'))}"


def _finding_from_match(path: str, text: str, rule: str, value: str, offset: int) -> DlpFinding:
    metadata = DLP_RULE_METADATA[rule]
    return DlpFinding(
        path=path,
        line=_line_number(text, offset),
        rule=rule,
        category=metadata["category"],
        severity=metadata["severity"],
        fingerprint=_dlp_fingerprint(rule, value),
    )


def scan_dlp_inputs(
    inputs: Iterable[InputFile], settings: Settings
) -> dict[str, Any]:
    unique_inputs = {item.path: item for item in inputs}
    allowlist = {
        (item.path, item.rule, item.fingerprint) for item in settings.dlp_allowlist
    }
    findings: list[DlpFinding] = []
    allowlisted_count = 0
    seen: set[tuple[str, int, str, str]] = set()
    for item in sorted(unique_inputs.values(), key=lambda value: value.path):
        for rule, value, offset in _iter_dlp_matches(item.text):
            finding = _finding_from_match(item.path, item.text, rule, value, offset)
            key = (finding.path, finding.line, finding.rule, finding.fingerprint)
            if key in seen:
                continue
            seen.add(key)
            allowlist_key = (finding.path, finding.rule, finding.fingerprint)
            if allowlist_key in allowlist:
                allowlisted_count += 1
            else:
                findings.append(finding)

    findings.sort(key=lambda item: (item.path, item.line, item.rule, item.fingerprint))
    findings_by_rule = dict(sorted(Counter(item.rule for item in findings).items()))
    if findings:
        status = "blocked"
    elif allowlisted_count:
        status = "passed_with_allowlist"
    else:
        status = "passed"
    return {
        "profile": settings.dlp_profile,
        "enforcement": DLP_ENFORCEMENT,
        "status": status,
        "detectors": list(DLP_DETECTORS),
        "scanned_input_count": len(unique_inputs),
        "finding_count": len(findings),
        "findings_by_rule": findings_by_rule,
        "allowlisted_count": allowlisted_count,
        "findings": [item.as_dict() for item in findings],
    }


def dlp_warning(report: dict[str, Any]) -> str | None:
    if report["status"] == "blocked":
        return (
            f"DLP 檢核阻擋 export：發現 {report['finding_count']} 個可能被 "
            "NotebookLM Enterprise 擋下的項目；報告不包含敏感原文"
        )
    if report["status"] == "passed_with_allowlist":
        return (
            f"DLP allowlist 已允許 {report['allowlisted_count']} 個精確命中；"
            "請在上傳前重新確認這些內容"
        )
    return None


def ensure_dlp_ready(report: dict[str, Any]) -> None:
    if report["status"] == "blocked":
        raise ExportError(
            f"DLP 檢核未通過：{report['finding_count']} 個 finding；"
            "請依 preflight 報告中的 path、line 與 rule 修正後重新執行 preflight"
        )


def is_sensitive(path: Path) -> bool:
    components = [part.lower() for part in path.parts]
    for component in components:
        if component in DEFAULT_SENSITIVE_NAMES or component.endswith(SENSITIVE_SUFFIXES):
            return True
        if any(fnmatch.fnmatch(component, pattern) for pattern in SENSITIVE_NAME_PATTERNS):
            return True
    return False


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


def _is_transaction_artifact(relative: str) -> bool:
    """Recognize crash-recovery siblings before they can become evidence."""

    markers = (
        ".codebase-wiki-install-transaction.",
        ".notebooklm-transaction.",
    )
    for component in PurePosixPath(relative.lower()).parts:
        if component.startswith(("codebase-wiki-stage-", "codebase-wiki-backup-")):
            return True
        if ".staging-" in component or ".backup-" in component:
            return True
        if any(marker in component for marker in markers):
            return True
    return False


def _exclusion_reason_for_relative(relative: str, settings: Settings) -> str | None:
    """Classify a lexical repo-relative path without resolving it."""

    path = PurePosixPath(relative)
    lower = relative.lower()
    lower_path = PurePosixPath(lower)
    parts = set(lower_path.parts)
    output = settings.output_directory.lower()
    if _is_transaction_artifact(relative):
        return "binary_or_generated"
    if path.name.lower().endswith(
        (OUTPUT_TRANSACTION_SUFFIX, OUTPUT_TRANSACTION_LOCK_SUFFIX)
    ):
        return "binary_or_generated"
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


def exclusion_reason(path: Path, root: Path, settings: Settings) -> str | None:
    """Classify a path after enforcing its repository boundary."""

    return _exclusion_reason_for_relative(repo_relative(path, root), settings)


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


def _lexical_relative(path: Path, root: Path) -> str:
    """Return a repo-relative path without resolving filesystem links."""

    try:
        return Path(os.path.relpath(os.fspath(path), os.fspath(root))).as_posix()
    except ValueError as exc:
        raise ExportError(f"path escapes repository root: {path}") from exc


def _path_requires_resolution(path: Path) -> bool:
    """Identify links/reparse points whose canonical target needs checking."""

    if path.is_symlink():
        return True
    return os.name == "nt" and _is_reparse_point(path)


def _link_exclusion_reason(
    path: Path, relative: str, root: Path, settings: Settings
) -> str:
    """Classify a link without ever traversing its target."""

    configured = _exclusion_reason_for_relative(relative, settings)
    if configured:
        return configured
    try:
        repo_relative(path, root)
    except ExportError:
        return "path_escape"
    return "binary_or_generated"


def _bounded_excluded_root_summary(
    path: Path, relative: str, reason: str, *, boundary_only: bool = False
) -> dict[str, Any]:
    """Summarize a pruned tree using bounded metadata-only inspection."""

    summary: dict[str, Any] = {
        "path": relative,
        "reason": reason,
        "kind": "directory",
        "pruned": True,
        "entry_limit": EXCLUDED_SUMMARY_ENTRY_LIMIT,
        "observed_entries": 0,
        "observed_files": 0,
        "observed_directories": 0,
        "observed_bytes": 0,
        "errors": 0,
        "truncated": False,
    }
    if boundary_only:
        return summary

    pending = [path]
    while pending and summary["observed_entries"] < EXCLUDED_SUMMARY_ENTRY_LIMIT:
        current = pending.pop()
        try:
            with os.scandir(current) as iterator:
                entries = sorted(iterator, key=lambda item: item.name)
        except OSError:
            summary["errors"] += 1
            continue
        for entry in entries:
            if summary["observed_entries"] >= EXCLUDED_SUMMARY_ENTRY_LIMIT:
                summary["truncated"] = True
                break
            summary["observed_entries"] += 1
            try:
                if entry.is_symlink():
                    continue
                if entry.is_dir(follow_symlinks=False):
                    summary["observed_directories"] += 1
                    entry_path = Path(entry.path)
                    if os.name == "nt" and _is_reparse_point(entry_path):
                        continue
                    pending.append(entry_path)
                elif entry.is_file(follow_symlinks=False):
                    summary["observed_files"] += 1
                    summary["observed_bytes"] += entry.stat(
                        follow_symlinks=False
                    ).st_size
            except OSError:
                summary["errors"] += 1

    if pending:
        summary["truncated"] = True
    return summary


def _append_excluded_root(
    excluded_roots: list[dict[str, Any]] | None,
    skipped: list[dict[str, str]] | None,
    path: Path,
    relative: str,
    reason: str,
    *,
    boundary_only: bool = False,
) -> None:
    if excluded_roots is not None:
        excluded_roots.append(
            _bounded_excluded_root_summary(
                path, relative, reason, boundary_only=boundary_only
            )
        )
    if skipped is not None:
        skipped.append({"path": relative, "reason": reason})


def _iter_project_files(
    root: Path,
    settings: Settings,
    *,
    start: Path | None = None,
    excluded_roots: list[dict[str, Any]] | None = None,
    skipped: list[dict[str, str]] | None = None,
) -> Iterable[tuple[Path, str]]:
    """Walk only eligible trees while retaining ignored/untracked source files."""

    base = start or root
    if base.is_file():
        yield base, _lexical_relative(base, root)
        return
    if not base.is_dir():
        return

    base_relative = _lexical_relative(base, root)
    if base_relative != ".":
        if _path_requires_resolution(base):
            reason = _link_exclusion_reason(base, base_relative, root, settings)
            _append_excluded_root(
                excluded_roots,
                skipped,
                base,
                base_relative,
                reason,
                boundary_only=True,
            )
            return
        reason = _exclusion_reason_for_relative(base_relative, settings)
        if reason:
            _append_excluded_root(
                excluded_roots, skipped, base, base_relative, reason
            )
            return

    pending = [base]
    while pending:
        current = pending.pop()
        try:
            with os.scandir(current) as iterator:
                entries = sorted(iterator, key=lambda item: item.name)
        except OSError:
            relative = _lexical_relative(current, root)
            _append_excluded_root(
                excluded_roots,
                skipped,
                current,
                relative,
                "unreadable",
                boundary_only=True,
            )
            continue

        directories: list[Path] = []
        try:
            for entry in entries:
                path = Path(entry.path)
                relative = _lexical_relative(path, root)
                try:
                    is_symlink = entry.is_symlink()
                    is_directory = entry.is_dir(follow_symlinks=False)
                    is_file = entry.is_file(follow_symlinks=False)
                except OSError:
                    _append_excluded_root(
                        excluded_roots,
                        skipped,
                        path,
                        relative,
                        "unreadable",
                        boundary_only=True,
                    )
                    continue

                is_reparse = is_symlink or (
                    os.name == "nt" and _is_reparse_point(path)
                )
                if is_reparse:
                    linked_directory = is_directory
                    if is_symlink and not linked_directory:
                        try:
                            linked_directory = entry.is_dir(follow_symlinks=True)
                        except OSError:
                            linked_directory = False
                    if linked_directory:
                        _append_excluded_root(
                            excluded_roots,
                            skipped,
                            path,
                            relative,
                            _link_exclusion_reason(path, relative, root, settings),
                            boundary_only=True,
                        )
                    else:
                        yield path, relative
                    continue

                if is_directory:
                    reason = _exclusion_reason_for_relative(relative, settings)
                    if reason:
                        _append_excluded_root(
                            excluded_roots, skipped, path, relative, reason
                        )
                    else:
                        directories.append(path)
                elif is_file:
                    yield path, relative
        finally:
            entries.clear()

        pending.extend(reversed(directories))


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
    excluded_roots: list[dict[str, Any]] = []
    for path, lexical_relative in _iter_project_files(
        root, settings, excluded_roots=excluded_roots
    ):
        try:
            relative = (
                repo_relative(path, root)
                if _path_requires_resolution(path)
                else lexical_relative
            )
        except ExportError:
            excluded.append({"path": lexical_relative, "reason": "path_escape"})
            continue
        reason = _exclusion_reason_for_relative(relative, settings)
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

    included.sort(key=lambda item: item["path"])
    excluded.sort(key=lambda item: (item["path"], item["reason"]))
    excluded_roots.sort(key=lambda item: (item["path"], item["reason"]))
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
        "excluded_roots": excluded_roots,
        "included_count": len(included),
        "excluded_count": len(excluded),
        "excluded_root_count": len(excluded_roots),
        "included_by_category": dict(sorted(Counter(item["category"] for item in included).items())),
        "excluded_by_reason": dict(sorted(Counter(item["reason"] for item in excluded).items())),
        "excluded_roots_by_reason": dict(
            sorted(Counter(item["reason"] for item in excluded_roots).items())
        ),
        "declared_source_paths": list(sources),
        "uncovered_paths": uncovered,
        "wiki_status_counts": dict(sorted(status_counts.items())),
        "required_documents": required_document_coverage(page_list),
    }


def scan_summary(scan: dict[str, Any]) -> dict[str, Any]:
    return {
        "included_count": scan["included_count"],
        "excluded_count": scan["excluded_count"],
        "excluded_root_count": scan["excluded_root_count"],
        "included_by_category": scan["included_by_category"],
        "excluded_by_reason": scan["excluded_by_reason"],
        "excluded_roots_by_reason": scan["excluded_roots_by_reason"],
        "excluded_roots": scan["excluded_roots"],
        "uncovered_paths": scan["uncovered_paths"],
        "required_documents": scan["required_documents"],
    }


def coverage_summary(scan: dict[str, Any]) -> dict[str, Any]:
    """Distinguish export readiness from complete Wiki source coverage."""
    uncovered = list(scan["uncovered_paths"])
    return {
        "status": "complete" if not uncovered else "partial",
        "uncovered_count": len(uncovered),
        "uncovered_paths": uncovered,
    }


def excluded_root_warnings(scan: dict[str, Any]) -> list[str]:
    """Describe bounded or partially unreadable excluded-tree summaries."""

    warnings: list[str] = []
    truncated = [
        item["path"] for item in scan["excluded_roots"] if item.get("truncated")
    ]
    if truncated:
        warnings.append(
            "排除目錄摘要採 bounded metadata scan，以下路徑超過統計上限："
            + ", ".join(f"`{path}`" for path in truncated)
        )
    unreadable = [
        item["path"] for item in scan["excluded_roots"] if item.get("errors")
    ]
    if unreadable:
        warnings.append(
            "部分排除目錄只能取得不完整 metadata："
            + ", ".join(f"`{path}`" for path in unreadable)
        )
    return warnings


def read_text_file(
    path: Path,
    root: Path,
    settings: Settings,
    skipped: list[dict[str, str]],
    *,
    relative: str | None = None,
) -> InputFile | None:
    displayed_relative = relative
    try:
        if displayed_relative is None or _path_requires_resolution(path):
            displayed_relative = repo_relative(path, root)
    except ExportError:
        skipped.append(
            {
                "path": displayed_relative or _lexical_relative(path, root),
                "reason": "path_escape",
            }
        )
        return None
    assert displayed_relative is not None
    reason = _exclusion_reason_for_relative(displayed_relative, settings)
    if reason:
        skipped.append({"path": displayed_relative, "reason": reason})
        return None
    if not path.is_file():
        skipped.append({"path": displayed_relative, "reason": "not_a_file"})
        return None
    try:
        data = path.read_bytes()
        if b"\x00" in data:
            skipped.append(
                {"path": displayed_relative, "reason": "binary_or_unsupported_encoding"}
            )
            return None
        text = data.decode("utf-8")
    except (OSError, UnicodeDecodeError):
        skipped.append(
            {"path": displayed_relative, "reason": "binary_or_unsupported_encoding"}
        )
        return None
    return InputFile(path=displayed_relative, text=text, digest=sha256_bytes(data))


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
    files: list[InputFile] = []
    if path.is_file():
        paths: Iterable[tuple[Path, str]] = ((path, relative),)
    else:
        paths = _iter_project_files(root, settings, start=path, skipped=skipped)
    for item, item_relative in paths:
        if item.is_file() or item.is_symlink():
            content = read_text_file(
                item, root, settings, skipped, relative=item_relative
            )
            if content is not None:
                files.append(content)
    return files


def collect_wiki_pages(root: Path) -> tuple[list[InputFile], list[dict[str, str]], list[str]]:
    if _is_reparse_point(root):
        raise ExportError(f"root must not be a symlink or reparse point: {root}")
    if not root.is_dir():
        raise ExportError(f"root is not a directory: {root}")
    wiki = root / "wiki"
    if not wiki.is_dir():
        raise ExportError(f"Wiki directory not found: {wiki}")
    try:
        validate_regular_tree(wiki)
    except (OSError, UnicodeError) as exc:
        raise ExportError(f"Wiki directory is unsafe to read: {wiki}: {exc}") from exc
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


def retrieval_contract_payload() -> dict[str, Any]:
    """Describe the source-side query contract exposed by the exporter."""

    return {
        "contract": RETRIEVAL_CONTRACT,
        "router_source": QUERY_INDEX_SOURCE_ID,
        "navigation_source": "project-map",
        "max_primary_source_groups": MAX_PRIMARY_SOURCE_GROUPS,
        "instructions_location": "README.md",
    }


def _clean_query_value(value: str) -> str:
    return " ".join(value.replace("`", "'").split())


def _frontmatter_strings(value: Any) -> list[str]:
    if isinstance(value, str):
        return [_clean_query_value(value)] if value.strip() else []
    if isinstance(value, list):
        return [
            _clean_query_value(item)
            for item in value
            if isinstance(item, str) and item.strip()
        ]
    return []


def _page_headings(page: InputFile) -> list[str]:
    return [
        _clean_query_value(match.group(1))
        for match in re.finditer(r"(?m)^#{1,3}\s+(.+?)\s*$", page.text)
        if match.group(1).strip()
    ]


def _wiki_link(page: InputFile) -> str:
    return f"[[{Path(page.path).stem}]]"


def query_terms_for_pages(pages: Iterable[InputFile], group: str) -> list[str]:
    """Collect explicit human-facing terms for deterministic source routing."""

    values: list[str] = [group]
    for page in pages:
        frontmatter = parse_frontmatter_text(page.text)
        values.extend(
            [
                page.path,
                Path(page.path).stem,
                *_frontmatter_strings(frontmatter.get("title")),
                *_frontmatter_strings(frontmatter.get("summary")),
                *_frontmatter_strings(frontmatter.get("tags")),
                *_page_headings(page),
            ]
        )
        for source in _frontmatter_strings(frontmatter.get("sources")):
            values.append(source)

    terms: set[str] = set()
    for value in values:
        clean = _clean_query_value(value)
        if not clean:
            continue
        terms.add(clean)
        terms.update(
            token
            for token in re.findall(r"[A-Za-z0-9][A-Za-z0-9_.:/-]*", clean)
            if len(token) > 1
        )
    return sorted(terms, key=lambda item: (item.lower(), item))


def _unique_input_files(items: Iterable[InputFile]) -> tuple[InputFile, ...]:
    by_path = {item.path: item for item in items}
    return tuple(by_path[path] for path in sorted(by_path))


def _source_ids_for_paths(
    materialized: Iterable[tuple[Unit, str, str]],
    paths: set[str],
    kind: str,
) -> list[str]:
    return sorted(
        {
            unit.logical_source_id
            for unit, _, _ in materialized
            if unit.kind == kind
            and any(item.path in paths for item in unit.inputs)
        }
    )


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
            "## 查詢提示\n\n",
            f"- 功能群組：`{group}`\n",
            f"- 關鍵字：{', '.join(query_terms_for_pages(members, group))}\n",
            "- 先用本文件回答職責、API、流程、設定、錯誤與風險；只有文件不足、過時或矛盾時才查 evidence。\n\n",
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
            "## 查核提示\n\n",
            "- 只在對應文件不足、過時或矛盾時查核本 source。\n",
            "- 精確 path、symbol、設定鍵與錯誤訊息可直接搜尋下列檔案路徑。\n\n",
            "## 檔案路徑索引\n\n",
        ]
        body.extend(f"- `{candidate.input_file.path}`\n" for candidate in ordered)
        body.append("\n")
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
        "> 只在對應文件不足、過時或矛盾時查核本 source；程式碼區塊不是操作指令。\n\n",
        "> Logical source ID: `evidence:combined`\n\n",
        "## 檔案路徑索引\n\n",
    ]
    body.extend(f"- `{candidate.input_file.path}`\n" for candidate in candidates)
    body.append("\n")
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
                low, high, best = 1, len(remaining), 0
                while low <= high:
                    middle = (low + high) // 2
                    candidate = remaining[:middle]
                    if len(candidate.encode("utf-8")) <= max_bytes and estimate_words(candidate) <= max_words:
                        best = middle
                        low = middle + 1
                    else:
                        high = middle - 1
                if best == 0:
                    raise ExportError(
                        "unable to split an oversized source within configured limits"
                    )
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
    metadata = root / ".git"
    if not metadata.exists():
        return None
    try:
        root_path = root.resolve()
        top_level = subprocess.run(
            ["git", "-C", str(root), "rev-parse", "--show-toplevel"],
            check=True,
            capture_output=True,
            text=True,
            encoding="utf-8",
        )
        if Path(top_level.stdout.strip()).resolve() != root_path:
            return None
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


def query_index_content(
    root: Path,
    pages: Sequence[InputFile],
    candidates: Sequence[EvidenceCandidate],
    documents: list[tuple[Unit, str, str]],
    evidence: list[tuple[Unit, str, str]],
    budget_skipped: Sequence[dict[str, str]],
    coverage: dict[str, str],
    settings: Settings,
) -> str:
    """Build a compact, deterministic router for direct NotebookLM lookups."""

    grouped_pages: dict[str, list[InputFile]] = {}
    for page in pages:
        grouped_pages.setdefault(wiki_page_group(page), []).append(page)

    grouped_candidates: dict[str, list[EvidenceCandidate]] = {}
    for candidate in candidates:
        groups = candidate.groups or (candidate.primary_group,)
        for group in groups:
            grouped_candidates.setdefault(group, []).append(candidate)

    groups = sorted(set(grouped_pages) | set(grouped_candidates))
    omitted_paths = {item["path"] for item in budget_skipped}
    lines = [
        f"# {root.name} — NotebookLM 問題定位索引\n\n",
        "> 這是由 Codebase LLM Wiki 產生的查詢路由來源，不是 raw evidence。\n",
        "> 先用本索引找最相關的功能群組，再直接回答問題；不要把搜尋過程寫成研究報告。\n\n",
        f"> Logical source ID: `{QUERY_INDEX_SOURCE_ID}`\n\n",
        "## 直接回答契約\n\n",
        "1. 第一段先回答結論、位置或目前行為。\n",
        f"2. 只選最相關的 1–{MAX_PRIMARY_SOURCE_GROUPS} 個主要來源群組。\n",
        "3. 先使用文件 source；只有文件不足、過時或矛盾時才查 evidence source。\n",
        "4. 引用 `[[wiki-page]]` 與反引號 repo-relative source paths。\n",
        "5. 明確標示事實、推論、矛盾與 coverage gap；找不到時不要補造答案。\n",
        "6. 除非問題要求調查、比較或除錯步驟，不要先拆解問題或敘述搜尋流程。\n\n",
        "## 問題路由\n\n",
        "| 問題訊號 | 先查 | 必要時查 | 回答形態 |\n",
        "| --- | --- | --- | --- |\n",
        "| 精確 path、symbol、error、stack trace | 對應功能的文件 source | 對應 evidence source | 直接給位置、行為與 source path |\n",
        "| 職責、API、流程、入口 | 對應功能的文件 source | evidence source | 先給結論，再列關鍵流程 |\n",
        "| 設定、schema、資料邊界 | 對應功能／架構文件 | config、schema 或 migration evidence | 列設定／資料來源與限制 |\n",
        "| 原因、影響、風險、矛盾 | system-analysis／功能文件 | raw evidence | 分開事實、推論與 gap |\n",
        "| 跨功能比較 | project／architecture 與最多 5 個功能群組 | 各群組 evidence | 只比較問題指定的維度 |\n\n",
        "## 功能群組索引\n\n",
    ]

    for group in groups:
        page_members = sorted(grouped_pages.get(group, []), key=lambda item: item.path)
        candidate_members = sorted(
            grouped_candidates.get(group, []),
            key=lambda item: item.input_file.path,
        )
        page_paths = {page.path for page in page_members}
        candidate_paths = {candidate.input_file.path for candidate in candidate_members}
        document_ids = _source_ids_for_paths(documents, page_paths, "documentation")
        evidence_ids = _source_ids_for_paths(evidence, candidate_paths, "evidence")
        page_statuses = {
            str(parse_frontmatter_text(page.text).get("status", ""))
            for page in page_members
        }
        if not document_ids:
            group_status = "gap"
        elif page_statuses & {"stale", "placeholder"}:
            group_status = "partial"
        else:
            group_status = "covered"

        source_paths = set(candidate_paths)
        for page in page_members:
            source_paths.update(_frontmatter_strings(parse_frontmatter_text(page.text).get("sources")))
        keywords = query_terms_for_pages(page_members, group)
        for path in sorted(candidate_paths):
            keywords.extend(
                token
                for token in re.findall(r"[A-Za-z0-9][A-Za-z0-9_.:/-]*", path)
                if len(token) > 1
            )
        keywords = sorted(set(keywords), key=lambda item: (item.lower(), item))
        wiki_pages = ", ".join(_wiki_link(page) for page in page_members) or "（沒有對應 Wiki page）"
        lines.extend(
            [
                f"### 功能群組：`{group}`\n\n",
                f"- Coverage：`{group_status}`\n",
                f"- 查詢關鍵字：{', '.join(keywords) or '（未提供）'}\n",
                f"- Wiki pages：{wiki_pages}\n",
                f"- 先查文件：{', '.join(f'`{item}`' for item in document_ids) or '（未建立或未匯出）'}\n",
                f"- 必要時查 evidence：{', '.join(f'`{item}`' for item in evidence_ids) or '（目前沒有可用 evidence source）'}\n",
                f"- 相關 source paths：{', '.join(f'`{item}`' for item in sorted(source_paths)) or '（未列出）'}\n",
            ]
        )
        omitted_for_group = sorted(path for path in candidate_paths if path in omitted_paths)
        if omitted_for_group:
            lines.append(
                "- 因 source budget 未匯出的 evidence："
                + ", ".join(f"`{path}`" for path in omitted_for_group)
                + "\n"
            )
        lines.append("\n")

    lines.extend(
        [
            "## 必要文件覆蓋\n\n",
            *[f"- `{path}` — `{status}`\n" for path, status in coverage.items()],
            "\n## Export 狀態\n\n",
            f"- Evidence export：`{'enabled' if settings.include_evidence else 'disabled'}`\n",
            f"- Source budget：`{settings.available_source_slots}` available slots\n",
            "- `partial`、`gap`、warning、skipped 與 omitted 項目都不是已驗證事實。\n",
        ]
    )
    return "".join(lines)


def project_map_content(
    root: Path,
    materialized: list[tuple[Unit, str, str]],
    skipped: list[dict[str, str]],
    warnings: list[str],
    settings: Settings,
    coverage: dict[str, str],
    dlp: dict[str, Any],
) -> str:
    lines = [
        f"# {root.name} — NotebookLM 專案導覽\n\n",
        "> 這是產生的繁體中文導覽來源。只上傳 `sources/` 下的 Markdown。\n\n",
        "## 查詢入口\n\n",
        f"- 直接定位問題時，先使用 `sources/{source_filename(QUERY_INDEX_SOURCE_ID)}`。\n",
        "- 查詢索引只負責路由；實際答案優先引用對應文件，再以 evidence 查核。\n",
        "- 不要先描述搜尋流程；先回答結論，再補充必要證據。\n",
        f"- 一次最多使用 {MAX_PRIMARY_SOURCE_GROUPS} 個主要來源群組。\n",
        "- `partial`、`gap`、warning 或 skipped 項目都不是已驗證事實。\n\n",
        "## 文件覆蓋\n\n",
    ]
    lines.extend(f"- `{path}` — `{status}`\n" for path, status in coverage.items())
    lines.extend(
        [
            "\n## Source catalog\n\n",
            f"- Profile: `{settings.profile}`\n",
            f"- Sources: `{len(materialized)}` / `{settings.available_source_slots}` available slots\n",
            f"- 每 source safety limit: `{settings.max_source_bytes}` bytes / "
            f"`{settings.max_source_words}` estimated words "
            f"(model: `{WORD_COUNT_MODEL}`)\n\n",
        ]
    )
    lines.extend(
        [
            "## DLP preflight\n\n",
            f"- Profile: `{dlp['profile']}`\n",
            f"- Enforcement: `{dlp['enforcement']}`\n",
            f"- Status: `{dlp['status']}`\n",
            f"- Findings: `{dlp['finding_count']}`\n",
            f"- Allowlisted findings: `{dlp['allowlisted_count']}`\n\n",
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
    _validate_output_tree(output)
    path = output / "manifest.json"
    if not path.exists():
        return None
    try:
        value = json.loads(path.read_text(encoding="utf-8"))
    except (OSError, UnicodeError, json.JSONDecodeError) as exc:
        raise ExportError(f"unable to read previous manifest: {path}: {exc}") from exc
    schema = value.get("schema_version") if isinstance(value, dict) else None
    if not isinstance(value, dict) or schema not in SUPPORTED_MANIFEST_SCHEMAS:
        raise ExportError(
            f"unsupported manifest schema in {path}; expected one of "
            f"{sorted(SUPPORTED_MANIFEST_SCHEMAS)}"
        )
    if not isinstance(value.get("sources", []), list):
        raise ExportError(f"previous manifest sources must be an array: {path}")
    for item in value["sources"]:
        if isinstance(item, dict) and "file" in item:
            _validate_pack_file_path(item["file"], output)
    return value


def _validate_pack_file_path(value: Any, output: Path) -> str:
    """Validate a pack file path before it can be read, written, or deleted."""

    if not isinstance(value, str) or not value.strip() or "\x00" in value:
        raise ExportError(
            "pack file must be a non-empty relative path"
        )
    normalized = value.replace("\\", "/")
    candidate = PurePosixPath(normalized)
    if (
        candidate.is_absolute()
        or candidate == PurePosixPath(".")
        or ".." in candidate.parts
        or re.fullmatch(r"[A-Za-z]:.*", normalized)
    ):
        raise ExportError(
            "pack file must stay inside the output directory: "
            f"{value!r}"
        )
    output_root = output.resolve(strict=False)
    candidate_path = (output / Path(*candidate.parts)).resolve(strict=False)
    try:
        candidate_path.relative_to(output_root)
    except ValueError as exc:
        raise ExportError(
            "pack file must stay inside the output directory: "
            f"{value!r}"
        ) from exc
    return candidate.as_posix()


def _validate_output_tree(output: Path) -> None:
    """Reject output trees containing symlinks before copying or replacing them."""

    if _is_reparse_point(output):
        raise ExportError(f"output path is not a regular directory: {output}")
    if not output.exists():
        return
    if not output.is_dir():
        raise ExportError(f"output path is not a regular directory: {output}")
    for path in output.rglob("*"):
        if _is_reparse_point(path):
            raise ExportError(f"output directory must not contain symlink or reparse point: {path}")


def _output_transaction_path(output: Path) -> Path:
    absolute = output.absolute()
    return absolute.parent / f".{absolute.name}{OUTPUT_TRANSACTION_SUFFIX}"


def _output_transaction_lock_path(output: Path) -> Path:
    absolute = output.absolute()
    return absolute.parent / f".{absolute.name}{OUTPUT_TRANSACTION_LOCK_SUFFIX}"


class _OutputTransactionLock:
    """Hold an OS-level lock for one NotebookLM output transaction."""

    def __init__(self, path: Path) -> None:
        self.path = path
        self._fd: int | None = None

    def __enter__(self) -> "_OutputTransactionLock":
        if _is_reparse_point(self.path):
            raise ExportError(
                f"NotebookLM transaction lock is a symlink or reparse point: {self.path}"
            )
        fd = os.open(self.path, os.O_CREAT | os.O_RDWR, 0o600)
        self._fd = fd
        try:
            if os.name == "nt":
                import msvcrt

                if os.fstat(fd).st_size == 0:
                    os.write(fd, b"\0")
                os.lseek(fd, 0, os.SEEK_SET)
                msvcrt.locking(fd, msvcrt.LK_NBLCK, 1)
            else:
                import fcntl

                fcntl.flock(fd, fcntl.LOCK_EX | fcntl.LOCK_NB)  # type: ignore[attr-defined]
        except BaseException:
            os.close(fd)
            self._fd = None
            raise
        return self

    def __exit__(self, exc_type: object, exc_value: object, traceback: object) -> None:
        fd = self._fd
        self._fd = None
        if fd is None:
            return
        try:
            if os.name == "nt":
                import msvcrt

                os.lseek(fd, 0, os.SEEK_SET)
                msvcrt.locking(fd, msvcrt.LK_UNLCK, 1)
            else:
                import fcntl

                fcntl.flock(fd, fcntl.LOCK_UN)  # type: ignore[attr-defined]
        except OSError:
            # Closing the descriptor still releases the process-owned lock.
            pass
        finally:
            os.close(fd)


def _write_output_transaction(path: Path, payload: dict[str, Any]) -> None:
    fd, temporary_name = tempfile.mkstemp(
        prefix=f"{path.name}.tmp-", dir=path.parent
    )
    temporary = Path(temporary_name)
    try:
        with os.fdopen(fd, "w", encoding="utf-8", newline="\n") as stream:
            json.dump(payload, stream, ensure_ascii=True, sort_keys=True)
            stream.write("\n")
            stream.flush()
            os.fsync(stream.fileno())
        os.replace(temporary, path)
    finally:
        if temporary.exists():
            temporary.unlink()


def _output_transaction_sibling(
    parent: Path, value: object, prefix: str, label: str
) -> Path:
    if not isinstance(value, str) or Path(value).name != value or not value.startswith(prefix):
        raise ExportError(f"invalid NotebookLM transaction {label}")
    candidate = parent / value
    if candidate.parent != parent:
        raise ExportError(f"NotebookLM transaction {label} escapes its parent")
    return candidate


def _remove_output_tree(path: Path, label: str) -> None:
    if _is_reparse_point(path):
        raise ExportError(f"NotebookLM transaction {label} is a symlink or reparse point")
    if not path.exists():
        return
    if not path.is_dir():
        raise ExportError(f"NotebookLM transaction {label} is not a directory")
    _validate_output_tree(path)
    shutil.rmtree(path)


def _remove_output_transaction_tree(path: Path, label: str) -> None:
    if _is_reparse_point(path):
        raise ExportError(f"NotebookLM transaction {label} is a symlink or reparse point")
    if not path.exists():
        return
    if not path.is_dir():
        raise ExportError(f"NotebookLM transaction {label} is not a directory")
    shutil.rmtree(path)


def _recover_pending_output_unlocked(output: Path) -> bool:
    """Recover or finish an output transaction left by a killed process."""

    journal = _output_transaction_path(output)
    if _is_reparse_point(journal):
        raise ExportError(f"NotebookLM transaction journal is a symlink or reparse point: {journal}")
    if not journal.exists():
        return False
    if _is_reparse_point(output):
        raise ExportError(f"output path is a symlink or reparse point: {output}")
    try:
        payload = json.loads(journal.read_text(encoding="utf-8"))
    except (OSError, UnicodeError, json.JSONDecodeError) as exc:
        raise ExportError(f"unable to read NotebookLM transaction journal: {journal}") from exc
    if not isinstance(payload, dict) or payload.get("version") != OUTPUT_TRANSACTION_VERSION:
        raise ExportError(f"unsupported NotebookLM transaction journal: {journal}")
    absolute = output.absolute()
    if payload.get("output_name") != absolute.name:
        raise ExportError(f"NotebookLM transaction output mismatch: {journal}")
    parent = absolute.parent
    stage = _output_transaction_sibling(
        parent, payload.get("stage"), f"{absolute.name}.staging-", "stage"
    )
    backup = _output_transaction_sibling(
        parent, payload.get("backup"), f"{absolute.name}.backup-", "backup"
    )
    phase = payload.get("phase")
    if phase not in {"active", "committed"}:
        raise ExportError(f"unsupported NotebookLM transaction phase: {phase!r}")
    had_output = payload.get("had_output")
    if not isinstance(had_output, bool):
        raise ExportError(f"invalid NotebookLM transaction output state: {journal}")

    if phase == "active":
        if had_output and backup.exists():
            _validate_output_tree(backup)
            _remove_output_tree(output, "output")
            os.replace(backup, output)
        elif not had_output:
            _remove_output_tree(output, "output")
    elif not output.exists():
        raise ExportError(
            f"committed NotebookLM transaction has no output directory: {journal}"
        )
    else:
        _validate_output_tree(output)

    _remove_output_transaction_tree(stage, "stage")
    _remove_output_transaction_tree(backup, "backup")
    journal.unlink()
    return True


def _recover_pending_output(output: Path) -> bool:
    output.absolute().parent.mkdir(parents=True, exist_ok=True)
    try:
        with _OutputTransactionLock(_output_transaction_lock_path(output)):
            return _recover_pending_output_unlocked(output)
    except OSError as exc:
        raise ExportError(f"unable to acquire NotebookLM transaction lock: {output}") from exc


def previous_by_id(previous: dict[str, Any] | None, output: Path) -> dict[str, dict[str, Any]]:
    if not previous:
        return {}
    result: dict[str, dict[str, Any]] = {}
    for item in previous.get("sources", []):
        if not isinstance(item, dict) or not isinstance(item.get("logical_source_id"), str):
            continue
        entry = dict(item)
        if "file" in entry:
            entry["file"] = _validate_pack_file_path(entry["file"], output)
        if not entry.get("output_sha256") and isinstance(entry.get("file"), str):
            old_path = output / entry["file"]
            if old_path.is_file():
                entry["output_sha256"] = sha256_file(old_path)
        result[entry["logical_source_id"]] = entry
    return result


def build_actions(
    current: list[dict[str, Any]], previous: dict[str, dict[str, Any]]
) -> dict[str, list[dict[str, Any]]]:
    actions: dict[str, list[dict[str, Any]]] = {
        key: [] for key in ("added", "changed", "deleted", "unchanged")
    }
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

## 一次性重建既有 Notebook

若要套用新的 Wiki-first 直接定位行為，請先在同一本 Notebook 刪除舊的 static
sources，再完整上傳 `sources/` 下的所有 Markdown。Exporter 不會連線、刪除雲端
source 或自動上傳；`upload-plan.md` 只是一份本機操作清單。

## NotebookLM Custom instructions

若 NotebookLM Enterprise 介面提供 Custom instructions，請貼上以下內容：

```text
你是 Codebase LLM Wiki 的直接查詢器。請只使用目前 Notebook 的 sources。

1. 先使用 `query-index.md` 將問題路由到最相關的 1–5 個主要來源群組。
2. 第一段直接回答結論、位置或目前行為，不要描述搜尋過程，也不要先寫研究計畫。
3. 優先使用對應的 docs source；只有文件不足、過時或矛盾時才查 evidence source。
4. 回答必須引用 Wiki page（例如 [[overview]]）與 repo-relative source path（例如 `src/service.py`）。
5. 明確區分已證實事實、推論、矛盾與 coverage gap；找不到資料時直接說未找到，不要補造答案。
6. 除非問題明確要求調查、比較或除錯步驟，否則不要把問題逐步拆成研究流程。
7. `query-index.md` 是路由索引，不是實際行為證據；實際結論請引用對應 docs/evidence source。
```

若介面沒有 Custom instructions，請在問題前加上：
`請直接回答結論；先使用 query-index.md 路由到最多 5 個來源，引用 Wiki page 與 source path，不要描述搜尋流程。`

Exporter 完全離線，不會呼叫 NotebookLM、不會上傳檔案，也不會修改 raw sources
或 Wiki pages。

Exporter 也會在本機執行 `notebooklm-enterprise-basic` DLP preflight；未 allowlist
的 finding 會在 commit 前阻擋並保留既有 pack，報告不包含命中值。
"""


def _json_bytes(value: Any) -> bytes:
    return (json.dumps(value, ensure_ascii=False, indent=2, sort_keys=True) + "\n").encode(
        "utf-8"
    )


def _commit_output_unlocked(
    output: Path,
    files: dict[str, bytes],
    previous: dict[str, Any] | None,
) -> None:
    _recover_pending_output_unlocked(output)
    _validate_output_tree(output)
    safe_files: dict[str, bytes] = {}
    for relative, data in files.items():
        safe_relative = _validate_pack_file_path(relative, output)
        if safe_relative in safe_files:
            raise ExportError(f"duplicate output file path after normalization: {relative!r}")
        safe_files[safe_relative] = data
    parent = output.parent
    parent.mkdir(parents=True, exist_ok=True)
    stage: Path | None = Path(tempfile.mkdtemp(prefix=f"{output.name}.staging-", dir=parent))
    backup = Path(tempfile.mkdtemp(prefix=f"{output.name}.backup-", dir=parent))
    backup.rmdir()
    journal = _output_transaction_path(output)
    journal_created = False
    had_output = output.exists()
    assert stage is not None
    stage_name = stage.name
    backup_name = backup.name
    try:
        if output.is_dir():
            assert stage is not None
            shutil.copytree(output, stage, dirs_exist_ok=True)
        old_sources = {
            _validate_pack_file_path(item["file"], output)
            for item in (previous or {}).get("sources", [])
            if isinstance(item, dict) and "file" in item
        }
        for old_file in old_sources:
            assert stage is not None
            old_path = stage / old_file
            if old_path.is_file():
                old_path.unlink()
        for relative, data in safe_files.items():
            assert stage is not None
            destination = stage / relative
            destination.parent.mkdir(parents=True, exist_ok=True)
            destination.write_bytes(data)
        _write_output_transaction(
            journal,
            {
                "version": OUTPUT_TRANSACTION_VERSION,
                "output_name": output.absolute().name,
                "phase": "active",
                "stage": stage_name,
                "backup": backup_name,
                "had_output": had_output,
            },
        )
        journal_created = True
        if had_output:
            assert backup is not None
            os.replace(output, backup)
        assert stage is not None
        os.replace(stage, output)
        stage = None
        _write_output_transaction(
            journal,
            {
                "version": OUTPUT_TRANSACTION_VERSION,
                "output_name": output.absolute().name,
                "phase": "committed",
                "stage": stage_name,
                "backup": backup_name,
                "had_output": had_output,
            },
        )
        _recover_pending_output_unlocked(output)
        journal_created = False
    except OSError as exc:
        if journal_created:
            _recover_pending_output_unlocked(output)
            journal_created = False
        raise ExportError(f"unable to commit NotebookLM output: {exc}") from exc
    finally:
        if not journal_created and stage is not None and stage.exists():
            shutil.rmtree(stage, ignore_errors=True)
        if not journal_created and backup is not None and backup.exists():
            shutil.rmtree(backup, ignore_errors=True)


def commit_output(
    output: Path,
    files: dict[str, bytes],
    previous: dict[str, Any] | None,
) -> None:
    output.absolute().parent.mkdir(parents=True, exist_ok=True)
    try:
        with _OutputTransactionLock(_output_transaction_lock_path(output)):
            _commit_output_unlocked(output, files, previous)
    except OSError as exc:
        raise ExportError(f"unable to acquire NotebookLM transaction lock: {output}") from exc


def limits_payload(settings: Settings) -> dict[str, Any]:
    return {
        "enterprise_max_bytes": ENTERPRISE_MAX_BYTES,
        "enterprise_max_sources": ENTERPRISE_MAX_SOURCES,
        "enterprise_max_words": ENTERPRISE_MAX_WORDS,
        "max_bytes": settings.max_source_bytes,
        "max_sources": settings.source_limit,
        "max_words": settings.max_source_words,
        "word_count_model": WORD_COUNT_MODEL,
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
        "dlp_profile": settings.dlp_profile,
        "dlp_allowlist": [item.as_dict() for item in settings.dlp_allowlist],
        "config": repo_relative(settings.config_path, root) if settings.config_path else None,
    }


def _preflight_identity(
    root: Path,
    settings: Settings,
    pages: Sequence[InputFile],
    scan: dict[str, Any],
    lint_result: dict[str, Any],
    dlp: dict[str, Any],
) -> tuple[str, str]:
    material = {
        "schema_version": PREFLIGHT_SCHEMA_VERSION,
        "retrieval": retrieval_contract_payload(),
        "settings": _settings_fingerprint(settings, root),
        "wiki": [{"path": page.path, "sha256": page.digest} for page in pages],
        "inventory": [
            {"path": item["path"], "sha256": item["sha256"]}
            for item in scan["included"]
        ],
        "required_documents": scan["required_documents"],
        "deterministic_findings": lint_result.get("findings", []),
        "dlp": dlp,
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
    warnings.extend(excluded_root_warnings(scan))
    coverage = coverage_summary(scan)
    candidates = referenced_evidence(pages, root, settings, skipped) if settings.include_evidence else []
    dlp_inputs = [*pages, *(candidate.input_file for candidate in candidates)]
    dlp = scan_dlp_inputs(dlp_inputs, settings)
    dlp_message = dlp_warning(dlp)
    if dlp_message:
        warnings.append(dlp_message)
    lint_result = _load_wiki_lint().lint_wiki(root / "wiki", root, use_git=False)
    missing = [path for path, status in scan["required_documents"].items() if status != "active"]
    warnings.extend(f"必要文件尚未完成：{path} ({scan['required_documents'][path]})" for path in missing)
    if coverage["status"] == "partial":
        warnings.append(
            "安全掃描仍有 "
            f"{coverage['uncovered_count']} 個路徑未被 Wiki sources 覆蓋；"
            "ready_to_export 僅代表必要文件與 deterministic gate 通過"
        )
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
    ready = (
        not missing
        and not required_document_issues
        and critical_count == 0
        and dlp["status"] != "blocked"
    )
    inventory_hash, preflight_id = _preflight_identity(
        root, settings, pages, scan, lint_result, dlp
    )
    return {
        "ok": True,
        "mode": "preflight",
        "preflight_schema_version": PREFLIGHT_SCHEMA_VERSION,
        "retrieval": retrieval_contract_payload(),
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
        "coverage": coverage,
        "limits": limits_payload(settings),
        "dlp": dlp,
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
    _recover_pending_output(output)
    pages, initial_skipped, warnings = collect_wiki_pages(root)
    scan = scan_project(root, settings, pages)
    warnings.extend(excluded_root_warnings(scan))
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
    dlp = scan_dlp_inputs(
        [*pages, *(candidate.input_file for candidate in candidates)], settings
    )
    dlp_message = dlp_warning(dlp)
    if dlp_message:
        warnings.append(dlp_message)
    ensure_dlp_ready(dlp)
    available = settings.available_source_slots
    if available < 3:
        raise ExportError(
            "at least three source slots are required for query index, project map, "
            "and documentation"
        )

    documents = fit_document_units(wiki_units(pages), settings, available - 2)
    query_inputs = _unique_input_files(
        [*pages, *(candidate.input_file for candidate in candidates)]
    )
    preliminary_query = Unit(
        logical_source_id=QUERY_INDEX_SOURCE_ID,
        kind="query_index",
        group="query",
        title="問題定位索引",
        inputs=query_inputs,
        content=query_index_content(
            root,
            pages,
            candidates,
            documents,
            [],
            [],
            coverage,
            settings,
        ),
        priority=2_100_000,
    )
    preliminary_query_parts = materialize_units([preliminary_query], settings)
    preliminary_map = Unit(
        logical_source_id="project-map",
        kind="project",
        group="project",
        title="專案導覽",
        inputs=tuple(pages),
        content=project_map_content(
            root,
            preliminary_query_parts + documents,
            skipped,
            warnings,
            settings,
            coverage,
            dlp,
        ),
        priority=2_000_000,
    )
    preliminary_map_parts = materialize_units([preliminary_map], settings)
    evidence_slots = max(
        0,
        available
        - len(documents)
        - len(preliminary_query_parts)
        - len(preliminary_map_parts),
    )

    evidence: list[tuple[Unit, str, str]] = []
    budget_skipped: list[dict[str, str]] = []
    project_parts: list[tuple[Unit, str, str]] = []
    query_parts: list[tuple[Unit, str, str]] = []
    for _ in range(8):
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
        query_unit = Unit(
            logical_source_id=QUERY_INDEX_SOURCE_ID,
            kind="query_index",
            group="query",
            title="問題定位索引",
            inputs=query_inputs,
            content=query_index_content(
                root,
                pages,
                candidates,
                documents,
                evidence,
                budget_skipped,
                coverage,
                settings,
            ),
            priority=2_100_000,
        )
        query_parts = materialize_units([query_unit], settings)
        project_unit = Unit(
            logical_source_id="project-map",
            kind="project",
            group="project",
            title="專案導覽",
            inputs=tuple(project_inputs),
            content=project_map_content(
                root,
                query_parts + documents + evidence,
                all_skipped,
                current_warnings,
                settings,
                coverage,
                dlp,
            ),
            priority=2_000_000,
        )
        project_parts = materialize_units([project_unit], settings)
        total = len(query_parts) + len(project_parts) + len(documents) + len(evidence)
        if total <= available:
            warnings = current_warnings
            break
        evidence_slots = max(0, evidence_slots - (total - available))
    else:
        raise ExportError("unable to fit project map and mandatory documentation within source limit")

    materialized = query_parts + project_parts + documents + evidence
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
        "retrieval": retrieval_contract_payload(),
        "limits": limits_payload(settings),
        "dlp": dlp,
        "scan": scan_summary(scan),
        "coverage": {
            **coverage_summary(scan),
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


def apply_output_override(root: Path, settings: Settings, output: Path | None) -> Settings:
    """Bind a CLI output override into the preflight configuration identity."""

    if output is None:
        return settings
    if output.is_absolute():
        candidate = output
    else:
        output_directory = validate_relative_config_path(output.as_posix(), root, "output")
        candidate = root / Path(*PurePosixPath(output_directory).parts)
    _reject_symlink_components(root, candidate, "output")
    output_directory = repo_relative(candidate, root)
    if output_directory == ".":
        raise ExportError("output must be a child directory of repository root")
    return replace(settings, output_directory=output_directory)


def main(argv: Sequence[str] | None = None) -> int:
    configure_utf8_stdio()
    args = build_parser().parse_args(argv)
    try:
        # Keep the caller-provided root lexical long enough to reject a root
        # symlink/reparse point before resolve() can hide that boundary.
        if _is_reparse_point(args.root):
            raise ExportError(f"root must not be a symlink or reparse point: {args.root}")
        root = args.root.resolve()
        if not root.is_dir():
            raise ExportError(f"root is not a directory: {root}")
        config_path = None
        if args.config:
            config_path = args.config if args.config.is_absolute() else root / args.config
        settings = load_settings(root, config_path)
        settings = apply_output_override(root, settings, args.output)
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
                    "deterministic Critical or DLP findings"
                )
            output = root / Path(*PurePosixPath(settings.output_directory).parts)
            _reject_symlink_components(root, output, "output")
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
            f"excluded_files={inventory['excluded_count']}, "
            f"excluded_roots={inventory['excluded_root_count']}, "
            f"uncovered={len(inventory['uncovered_paths'])}, "
            f"ready={str(result['ready_to_export']).lower()}"
        )
        print(f"Preflight ID: {result['preflight_id']}")
        dlp = result["dlp"]
        print(
            "DLP: "
            f"profile={dlp['profile']}, "
            f"status={dlp['status']}, "
            f"findings={dlp['finding_count']}, "
            f"allowlisted={dlp['allowlisted_count']}"
        )
        for finding in dlp["findings"]:
            print(
                "DLP finding: "
                f"{finding['path']}:{finding['line']} — "
                f"{finding['rule']} ({finding['severity']})"
            )
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
