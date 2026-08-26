"""Function-oriented NotebookLM Enterprise preflight and source-pack builder.

``--preflight`` performs a read-only inventory of the explicit filesystem root.
The apply mode packages curated BA Wiki documents into ``.notebooklm``. This
module never calls NotebookLM or modifies raw sources and Wiki pages.
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


EXPORT_SCHEMA_VERSION = 5
SUPPORTED_MANIFEST_SCHEMAS = {1, 2, 3, 4, EXPORT_SCHEMA_VERSION}
PREFLIGHT_SCHEMA_VERSION = 5
OUTPUT_TRANSACTION_VERSION = 1
OUTPUT_TRANSACTION_SUFFIX = ".notebooklm-transaction.json"
OUTPUT_TRANSACTION_LOCK_SUFFIX = ".notebooklm-transaction.lock"
PROFILE_NAME = "gemini-notebook-enterprise"
ENTERPRISE_MAX_SOURCES = 300
ENTERPRISE_MAX_BYTES = 500_000_000
ENTERPRISE_MAX_WORDS = 500_000
DEFAULT_MAX_SOURCES = ENTERPRISE_MAX_SOURCES
DEFAULT_MAX_BYTES = 450_000_000
DEFAULT_MAX_WORDS = 450_000
EXCLUDED_SUMMARY_ENTRY_LIMIT = 4_096

WIKI_LOG_PATH = "wiki/log.md"
REQUIRED_BA_DOCUMENTS = (
    "wiki/overview.md",
    "wiki/synthesis/functional-requirement-catalog.md",
    "wiki/synthesis/business-process-catalog.md",
    "wiki/synthesis/business-rule-catalog.md",
    "wiki/synthesis/business-glossary.md",
    "wiki/synthesis/business-knowledge-gaps.md",
)
COVERAGE_LEDGER_PATH = "wiki/synthesis/codebase-functional-coverage.md"
REQUIRED_WIKI_DOCUMENTS = (*REQUIRED_BA_DOCUMENTS, COVERAGE_LEDGER_PATH)
MANAGED_START = "<!-- codebase-wiki:managed:start -->"
MANAGED_END = "<!-- codebase-wiki:managed:end -->"
USER_NOTES_START = "<!-- codebase-wiki:user-notes:start -->"
USER_NOTES_END = "<!-- codebase-wiki:user-notes:end -->"
LOCAL_ONLY_START = "<!-- notebooklm:local-only:start -->"
LOCAL_ONLY_END = "<!-- notebooklm:local-only:end -->"
COVERAGE_DISPOSITIONS = {
    "functional-evidence",
    "supporting-technical",
    "no-observable-behavior",
    "analysis-gap",
}

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
AUDIENCE = "business-analyst"
CONTENT_MODE = "ba_only"
KNOWLEDGE_CONTRACT = "business-functional-requirements-v2"
RETRIEVAL_CONTRACT = "business-only-ba-v2"
QUERY_INDEX_SOURCE_ID = "query-index"
MAX_PRIMARY_SOURCE_GROUPS = 5
DLP_PROFILE = "notebooklm-enterprise-ba-mask-v1"
DLP_ANALYSIS_ENFORCEMENT = "mask_and_continue"
DLP_PAYLOAD_ENFORCEMENT = "mask_then_block_residual"
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
    content_mode: str
    analysis_include_tests: bool
    output_directory: str
    source_limit: int
    reserved_source_slots: int
    max_source_bytes: int
    max_source_words: int
    business_source_paths: tuple[str, ...]
    extra_paths: tuple[str, ...]
    exclude_paths: tuple[str, ...]
    dlp_profile: str
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
    content_mode = raw.get("content_mode", CONTENT_MODE)
    if content_mode != CONTENT_MODE:
        raise ExportError(f"content_mode must be {CONTENT_MODE!r}")
    analysis_include_tests = raw.get("analysis_include_tests", True)
    if not isinstance(analysis_include_tests, bool):
        raise ExportError("analysis_include_tests must be true or false")
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
    deprecated = [
        key
        for key in ("include_traceability", "include_evidence", "dlp_allowlist")
        if key in raw
    ]
    if deprecated:
        raise ExportError(
            "BA-only schema v5 no longer accepts "
            + ", ".join(deprecated)
            + "; remove these keys because raw evidence is never uploaded and DLP findings are masked"
        )

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
    business_source_paths = tuple(
        validate_relative_config_path(value, root, "business_source_paths")
        for value in _str_tuple_config(raw, "business_source_paths")
    )
    return Settings(
        profile=profile,
        scan_profile=scan_profile,
        content_mode=content_mode,
        analysis_include_tests=analysis_include_tests,
        output_directory=output_directory,
        source_limit=source_limit,
        reserved_source_slots=reserved,
        max_source_bytes=max_bytes,
        max_source_words=max_words,
        business_source_paths=business_source_paths,
        extra_paths=extra_paths,
        exclude_paths=exclude_paths,
        dlp_profile=dlp_profile,
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


def _iter_dlp_matches(text: str) -> Iterable[tuple[str, str, int, int]]:
    for match in DLP_PRIVATE_KEY_PATTERN.finditer(text):
        yield "GCP_CREDENTIALS", match.group(0), match.start(), match.end()

    for match in DLP_GCP_API_KEY_PATTERN.finditer(text):
        yield "GCP_API_KEY", match.group(0), match.start(), match.end()

    for match in DLP_PASSWORD_PATTERN.finditer(text):
        value = match.group("value")
        if _password_is_literal(value):
            yield "PASSWORD", value, match.start("value"), match.end("value")

    for match in DLP_FINANCIAL_ACCOUNT_PATTERN.finditer(text):
        value = match.group("value")
        if len(_normalized_digits(value)) >= 8:
            yield (
                "FINANCIAL_ACCOUNT_NUMBER",
                value,
                match.start("value"),
                match.end("value"),
            )

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
        yield "CREDIT_CARD_NUMBER", digits, match.start(), match.end()


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


def _dlp_findings(
    inputs: Iterable[InputFile],
) -> tuple[dict[str, InputFile], list[DlpFinding], dict[str, list[tuple[int, int, str]]]]:
    unique_inputs = {item.path: item for item in inputs}
    findings: list[DlpFinding] = []
    spans: dict[str, list[tuple[int, int, str]]] = {}
    seen: set[tuple[str, int, str, str]] = set()
    for item in sorted(unique_inputs.values(), key=lambda value: value.path):
        for rule, value, offset, end in _iter_dlp_matches(item.text):
            finding = _finding_from_match(item.path, item.text, rule, value, offset)
            key = (finding.path, finding.line, finding.rule, finding.fingerprint)
            if key in seen:
                continue
            seen.add(key)
            findings.append(finding)
            spans.setdefault(item.path, []).append((offset, end, rule))

    findings.sort(key=lambda item: (item.path, item.line, item.rule, item.fingerprint))
    return unique_inputs, findings, spans


def _dlp_report(
    inputs: Iterable[InputFile], *, phase: str, enforcement: str, blocked: bool
) -> dict[str, Any]:
    unique_inputs, findings, _ = _dlp_findings(inputs)
    findings_by_rule = dict(sorted(Counter(item.rule for item in findings).items()))
    status = "blocked" if findings and blocked else "passed"
    return {
        "profile": DLP_PROFILE,
        "phase": phase,
        "enforcement": enforcement,
        "status": status,
        "detectors": list(DLP_DETECTORS),
        "scanned_input_count": len(unique_inputs),
        "finding_count": len(findings),
        "findings_by_rule": findings_by_rule,
        "masked_count": 0,
        "findings": [item.as_dict() for item in findings],
    }


def mask_dlp_inputs(
    inputs: Iterable[InputFile], *, phase: str
) -> tuple[tuple[InputFile, ...], dict[str, Any]]:
    """Return deterministic masked copies without changing repository files."""

    unique_inputs, findings, spans = _dlp_findings(inputs)
    masked: list[InputFile] = []
    masked_count = 0
    for path in sorted(unique_inputs):
        item = unique_inputs[path]
        selected: list[tuple[int, int, str]] = []
        last_end = -1
        for start, end, rule in sorted(
            spans.get(path, []), key=lambda value: (value[0], -(value[1] - value[0]), value[2])
        ):
            if start < last_end:
                continue
            selected.append((start, end, rule))
            last_end = end
        text = item.text
        for start, end, rule in reversed(selected):
            text = text[:start] + f"[MASKED:{rule}]" + text[end:]
        masked_count += len(selected)
        masked.append(InputFile(path=item.path, text=text, digest=item.digest))

    findings_by_rule = dict(sorted(Counter(item.rule for item in findings).items()))
    report = {
        "profile": DLP_PROFILE,
        "phase": phase,
        "enforcement": (
            DLP_ANALYSIS_ENFORCEMENT
            if phase == "analysis"
            else DLP_PAYLOAD_ENFORCEMENT
        ),
        "status": "passed_with_masking" if findings else "passed",
        "detectors": list(DLP_DETECTORS),
        "scanned_input_count": len(unique_inputs),
        "finding_count": len(findings),
        "masked_count": masked_count,
        "findings_by_rule": findings_by_rule,
        "findings": [item.as_dict() for item in findings],
    }
    return tuple(masked), report


def scan_dlp_inputs(inputs: Iterable[InputFile], settings: Settings) -> dict[str, Any]:
    """Compatibility helper for a blocking residual-payload scan."""

    return _dlp_report(
        inputs,
        phase="payload_residual",
        enforcement=DLP_PAYLOAD_ENFORCEMENT,
        blocked=True,
    )


def dlp_warning(report: dict[str, Any]) -> str | None:
    if report["status"] == "blocked":
        return (
            f"DLP payload 檢核阻擋 export：仍有 {report['finding_count']} 個未遮罩 finding；"
            "報告不包含敏感原文"
        )
    if report["status"] == "passed_with_masking":
        return (
            f"DLP 已遮罩 {report['masked_count']} 個命中；原始值未進入 BA payload"
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


def _is_business_source_path(relative: str, settings: Settings) -> bool:
    return _has_prefix(relative, settings.business_source_paths)


def _exclusion_reason_for_relative(
    relative: str,
    settings: Settings,
    *,
    business_override: bool = False,
) -> str | None:
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
    if (
        _is_test_file(lower)
        and not settings.analysis_include_tests
        and not business_override
    ):
        return "scan_scope_tests"
    if _is_ci_or_iac(lower):
        return "scan_scope_ci_or_iac"
    if settings.scan_profile == "target" and _has_prefix(lower, DEFAULT_FRAMEWORK_PREFIXES):
        return "framework_adapter"
    if _is_dev_tool(lower) and not business_override and not (
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
    if _is_test_file(relative):
        return "behavioral_test"
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
    business_override: bool = False,
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
        reason = _exclusion_reason_for_relative(
            base_relative, settings, business_override=business_override
        )
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
                    reason = _exclusion_reason_for_relative(
                        relative, settings, business_override=business_override
                    )
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


def parse_coverage_ledger(
    pages: Iterable[InputFile], root: Path
) -> tuple[list[dict[str, Any]], list[str]]:
    page = next((item for item in pages if item.path == COVERAGE_LEDGER_PATH), None)
    if page is None:
        return [], [f"missing coverage ledger: {COVERAGE_LEDGER_PATH}"]
    rules: list[dict[str, Any]] = []
    issues: list[str] = []
    pattern = re.compile(
        r"(?m)^\|\s*`(?P<path>[^`]+)`\s*\|\s*"
        r"(?P<disposition>[a-z-]+)\s*\|\s*(?P<requirements>.*?)\s*\|\s*$"
    )
    for match in pattern.finditer(page.text):
        raw_path = match.group("path").strip().replace("\\", "/")
        is_prefix = raw_path.endswith("/")
        try:
            path = validate_relative_config_path(
                raw_path, root, "coverage ledger path"
            )
        except ExportError as exc:
            issues.append(str(exc))
            continue
        disposition = match.group("disposition")
        if disposition not in COVERAGE_DISPOSITIONS:
            issues.append(
                f"invalid coverage disposition for {raw_path}: {disposition}"
            )
            continue
        requirements = sorted(_wiki_link_targets(match.group("requirements")))
        if disposition in {"functional-evidence", "supporting-technical"} and not requirements:
            issues.append(
                f"coverage disposition {disposition} requires a requirement link: {raw_path}"
            )
        rules.append(
            {
                "path": path,
                "prefix": is_prefix,
                "disposition": disposition,
                "requirements": requirements,
            }
        )
    if not rules:
        issues.append("coverage ledger contains no disposition rows")
    return sorted(rules, key=lambda item: (-len(item["path"]), item["path"])), issues


def coverage_disposition(
    relative: str, rules: Sequence[dict[str, Any]]
) -> dict[str, Any] | None:
    for rule in rules:
        path = str(rule["path"])
        if relative == path or (rule["prefix"] and relative.startswith(path + "/")):
            return rule
    return None


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

    business_skipped: list[dict[str, str]] = []
    business_inputs: dict[str, InputFile] = {}
    for source in settings.business_source_paths:
        for item in expand_path(
            source,
            root,
            settings,
            business_skipped,
            business_override=True,
        ):
            business_inputs[item.path] = item
    by_path = {item["path"]: item for item in included}
    for item in business_inputs.values():
        by_path[item.path] = {
            "path": item.path,
            "category": "business_documentation",
            "byte_count": len(item.text.encode("utf-8")),
            "sha256": item.digest,
        }
    included = list(by_path.values())
    excluded.extend(business_skipped)

    included.sort(key=lambda item: item["path"])
    excluded.sort(key=lambda item: (item["path"], item["reason"]))
    excluded_roots.sort(key=lambda item: (item["path"], item["reason"]))
    page_list = list(pages)
    sources = declared_source_paths(page_list, root)
    ledger_rules, ledger_issues = parse_coverage_ledger(page_list, root)
    dispositions: list[dict[str, Any]] = []
    uncovered: list[str] = []
    for item in included:
        disposition = coverage_disposition(item["path"], ledger_rules)
        if disposition is None:
            uncovered.append(item["path"])
            continue
        dispositions.append(
            {
                "path": item["path"],
                "disposition": disposition["disposition"],
                "requirements": disposition["requirements"],
            }
        )
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
        "business_source_paths": list(settings.business_source_paths),
        "business_source_count": len(business_inputs),
        "excluded_by_reason": dict(sorted(Counter(item["reason"] for item in excluded).items())),
        "excluded_roots_by_reason": dict(
            sorted(Counter(item["reason"] for item in excluded_roots).items())
        ),
        "declared_source_paths": list(sources),
        "coverage_dispositions": dispositions,
        "coverage_disposition_counts": dict(
            sorted(Counter(item["disposition"] for item in dispositions).items())
        ),
        "coverage_ledger_issues": ledger_issues,
        "analysis_gap_paths": [
            item["path"]
            for item in dispositions
            if item["disposition"] == "analysis-gap"
        ],
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
        "business_source_paths": scan["business_source_paths"],
        "business_source_count": scan["business_source_count"],
        "excluded_by_reason": scan["excluded_by_reason"],
        "excluded_roots_by_reason": scan["excluded_roots_by_reason"],
        "excluded_roots": scan["excluded_roots"],
        "uncovered_paths": scan["uncovered_paths"],
        "coverage_disposition_counts": scan["coverage_disposition_counts"],
        "coverage_ledger_issues": scan["coverage_ledger_issues"],
        "analysis_gap_paths": scan["analysis_gap_paths"],
        "required_documents": scan["required_documents"],
    }


def collect_analysis_inputs(root: Path, scan: dict[str, Any]) -> tuple[InputFile, ...]:
    inputs: list[InputFile] = []
    for item in scan["included"]:
        path = root / Path(*PurePosixPath(item["path"]).parts)
        try:
            data = path.read_bytes()
            text = data.decode("utf-8")
        except (OSError, UnicodeDecodeError) as exc:
            raise ExportError(f"analysis input changed or became unreadable: {item['path']}") from exc
        digest = sha256_bytes(data)
        if digest != item["sha256"]:
            raise ExportError(f"analysis input changed during preflight: {item['path']}")
        inputs.append(InputFile(path=item["path"], text=text, digest=digest))
    return tuple(inputs)


def coverage_summary(scan: dict[str, Any]) -> dict[str, Any]:
    """Require every safe input to have a non-gap functional disposition."""
    uncovered = list(scan["uncovered_paths"])
    analysis_gaps = list(scan["analysis_gap_paths"])
    issues = list(scan["coverage_ledger_issues"])
    return {
        "status": "complete" if not uncovered and not analysis_gaps and not issues else "partial",
        "uncovered_count": len(uncovered),
        "uncovered_paths": uncovered,
        "analysis_gap_count": len(analysis_gaps),
        "analysis_gap_paths": analysis_gaps,
        "ledger_issues": issues,
        "disposition_counts": scan["coverage_disposition_counts"],
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
    business_override: bool = False,
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
    reason = _exclusion_reason_for_relative(
        displayed_relative, settings, business_override=business_override
    )
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
    *,
    business_override: bool = False,
) -> list[InputFile]:
    relative = validate_relative_config_path(value, root, "source path")
    path = root / Path(*PurePosixPath(relative).parts)
    if not path.exists():
        raise ExportError(f"referenced source does not exist: {relative}")
    files: list[InputFile] = []
    if path.is_file():
        paths: Iterable[tuple[Path, str]] = ((path, relative),)
    else:
        paths = _iter_project_files(
            root,
            settings,
            start=path,
            skipped=skipped,
            business_override=business_override,
        )
    for item, item_relative in paths:
        if item.is_file() or item.is_symlink():
            content = read_text_file(
                item,
                root,
                settings,
                skipped,
                relative=item_relative,
                business_override=business_override,
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
        "audience": AUDIENCE,
        "knowledge_contract": KNOWLEDGE_CONTRACT,
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


def notebooklm_role(page: InputFile) -> str | None:
    value = parse_frontmatter_text(page.text).get("notebooklm_role")
    return value if value in {"business", "traceability", "exclude"} else None


def pages_for_role(pages: Iterable[InputFile], role: str) -> list[InputFile]:
    return [page for page in pages if notebooklm_role(page) == role]


def _wiki_link_targets(text: str) -> set[str]:
    return {
        PurePosixPath(raw.split("|", 1)[0].split("#", 1)[0].strip()).stem
        for raw in re.findall(r"\[\[([^\]]+)\]\]", text)
        if raw.split("|", 1)[0].split("#", 1)[0].strip()
    }


def business_contract_coverage(pages: Sequence[InputFile]) -> dict[str, Any]:
    """Validate the structural BA knowledge contract without judging semantics."""

    by_path = {page.path: page for page in pages}
    processes = [
        page
        for page in pages
        if parse_frontmatter_text(page.text).get("type") == "business-process"
    ]
    rules = [
        page
        for page in pages
        if parse_frontmatter_text(page.text).get("type") == "business-rule"
    ]
    requirements = [
        page
        for page in pages
        if parse_frontmatter_text(page.text).get("type") == "business-requirement"
    ]
    issues: list[str] = []

    for path in REQUIRED_BA_DOCUMENTS:
        page = by_path.get(path)
        if page is not None and notebooklm_role(page) != "business":
            issues.append(f"required BA document lacks notebooklm_role business: {path}")
    ledger = by_path.get(COVERAGE_LEDGER_PATH)
    if ledger is not None and notebooklm_role(ledger) != "exclude":
        issues.append(f"coverage ledger must use notebooklm_role exclude: {COVERAGE_LEDGER_PATH}")

    process_ids = [
        str(parse_frontmatter_text(page.text).get("process_id", "")) for page in processes
    ]
    rule_ids = [
        str(parse_frontmatter_text(page.text).get("rule_id", "")) for page in rules
    ]
    requirement_ids = [
        str(parse_frontmatter_text(page.text).get("requirement_id", ""))
        for page in requirements
    ]
    for label, values in (
        ("process_id", process_ids),
        ("rule_id", rule_ids),
        ("requirement_id", requirement_ids),
    ):
        duplicates = sorted(value for value, count in Counter(values).items() if value and count > 1)
        if duplicates:
            issues.append(f"duplicate {label}: {', '.join(duplicates)}")

    active_processes = [
        page
        for page in processes
        if parse_frontmatter_text(page.text).get("status") == "active"
    ]
    active_rules = [
        page for page in rules if parse_frontmatter_text(page.text).get("status") == "active"
    ]
    active_requirements = [
        page
        for page in requirements
        if parse_frontmatter_text(page.text).get("status") == "active"
    ]
    if not active_processes:
        issues.append("no active business-process page")
    if not active_requirements:
        issues.append("no active business-requirement page")

    process_catalog = by_path.get("wiki/synthesis/business-process-catalog.md")
    process_catalog_links = _wiki_link_targets(process_catalog.text) if process_catalog else set()
    for page in active_processes:
        if Path(page.path).stem not in process_catalog_links:
            issues.append(f"business process missing from catalog: {page.path}")

    rule_catalog = by_path.get("wiki/synthesis/business-rule-catalog.md")
    rule_catalog_links = _wiki_link_targets(rule_catalog.text) if rule_catalog else set()
    process_stems = {Path(page.path).stem for page in processes}
    for page in active_rules:
        frontmatter = parse_frontmatter_text(page.text)
        if Path(page.path).stem not in rule_catalog_links:
            issues.append(f"business rule missing from catalog: {page.path}")
        for value in _frontmatter_strings(frontmatter.get("applies_to")):
            target = value[2:-2] if value.startswith("[[") and value.endswith("]]") else value
            if PurePosixPath(target).stem not in process_stems:
                issues.append(f"business rule has dangling applies_to: {page.path} -> {value}")

    requirement_catalog = by_path.get(
        "wiki/synthesis/functional-requirement-catalog.md"
    )
    requirement_catalog_links = (
        _wiki_link_targets(requirement_catalog.text) if requirement_catalog else set()
    )
    for page in active_requirements:
        frontmatter = parse_frontmatter_text(page.text)
        if Path(page.path).stem not in requirement_catalog_links:
            issues.append(f"functional requirement missing from catalog: {page.path}")
        for value in _frontmatter_strings(frontmatter.get("applies_to")):
            target = value[2:-2] if value.startswith("[[") and value.endswith("]]") else value
            if PurePosixPath(target).stem not in process_stems:
                issues.append(
                    f"functional requirement has dangling applies_to: {page.path} -> {value}"
                )
        if not re.search(r"(?mi)^##\s+驗收條件\s*$", page.text):
            issues.append(f"functional requirement lacks acceptance criteria heading: {page.path}")
        if not re.search(r"\bAC-[a-z0-9]+(?:-[a-z0-9]+)*\b", page.text, re.IGNORECASE):
            issues.append(f"functional requirement lacks stable acceptance criterion ID: {page.path}")

    business_pages = pages_for_role(pages, "business")
    term_count = len(
        {
            term
            for page in business_pages
            for term in _frontmatter_strings(
                parse_frontmatter_text(page.text).get("notebooklm_terms")
            )
        }
    )
    process_statuses = Counter(
        str(parse_frontmatter_text(page.text).get("coverage_status", "gap"))
        for page in processes
    )
    rule_evidence_states = Counter(
        str(parse_frontmatter_text(page.text).get("evidence_state", "gap"))
        for page in rules
    )
    requirement_evidence_states = Counter(
        str(parse_frontmatter_text(page.text).get("evidence_state", "gap"))
        for page in requirements
    )
    gaps_page = by_path.get("wiki/synthesis/business-knowledge-gaps.md")
    gap_ids = sorted(
        set(re.findall(r"\bgap-[a-z0-9]+(?:-[a-z0-9]+)*\b", gaps_page.text.lower()))
        if gaps_page
        else set()
    )
    if issues:
        status = "gap"
    elif (
        process_statuses.get("partial", 0)
        or process_statuses.get("gap", 0)
        or rule_evidence_states.get("inference", 0)
        or rule_evidence_states.get("gap", 0)
        or requirement_evidence_states.get("inference", 0)
        or requirement_evidence_states.get("gap", 0)
        or gap_ids
    ):
        status = "partial"
    else:
        status = "covered"

    return {
        "status": status,
        "required_documents": required_document_coverage(pages),
        "processes": {
            "total": len(processes),
            "active": len(active_processes),
            "by_coverage_status": dict(sorted(process_statuses.items())),
        },
        "rules": {
            "total": len(rules),
            "active": len(active_rules),
            "by_evidence_state": dict(sorted(rule_evidence_states.items())),
        },
        "requirements": {
            "total": len(requirements),
            "active": len(active_requirements),
            "by_evidence_state": dict(sorted(requirement_evidence_states.items())),
        },
        "notebooklm_term_count": term_count,
        "gap_count": len(gap_ids),
        "gap_ids": gap_ids,
        "structural_issues": sorted(set(issues)),
        "unclassified_pages": sorted(
            page.path for page in pages if notebooklm_role(page) is None
        ),
    }


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
                Path(page.path).stem,
                *_frontmatter_strings(frontmatter.get("title")),
                *_frontmatter_strings(frontmatter.get("summary")),
                *_frontmatter_strings(frontmatter.get("tags")),
                *_frontmatter_strings(frontmatter.get("notebooklm_terms")),
                *_frontmatter_strings(frontmatter.get("actors")),
                *_frontmatter_strings(frontmatter.get("process_id")),
                *_frontmatter_strings(frontmatter.get("rule_id")),
                *_frontmatter_strings(frontmatter.get("requirement_id")),
                *_frontmatter_strings(frontmatter.get("capability_id")),
                *_page_headings(page),
            ]
        )
        if notebooklm_role(page) != "business":
            values.append(page.path)
            values.extend(_frontmatter_strings(frontmatter.get("sources")))

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


def _without_frontmatter(text: str) -> str:
    match = re.match(r"\A---\s*\r?\n.*?\r?\n---\s*(?:\r?\n|\Z)", text, re.DOTALL)
    return text[match.end() :] if match else text


def _remove_marked_blocks(text: str, start: str, end: str) -> str:
    pattern = re.compile(
        re.escape(start) + r".*?" + re.escape(end),
        re.DOTALL,
    )
    return pattern.sub("", text)


def _business_wikilink(match: re.Match[str]) -> str:
    raw = match.group(1)
    target_and_heading, separator, alias = raw.partition("|")
    target, heading_separator, heading = target_and_heading.partition("#")
    stem = PurePosixPath(target.strip().replace("\\", "/")).stem
    normalized = stem + (f"#{heading}" if heading_separator and heading else "")
    return f"[[{normalized}{separator}{alias}]]"


def _redact_inline_path(match: re.Match[str]) -> str:
    value = match.group(1).strip()
    if (
        "/" in value
        or "\\" in value
        or value.startswith(".")
        or re.fullmatch(r"[A-Za-z]:.*", value)
    ):
        return "`[本機路徑已移除]`"
    return match.group(0)


def render_business_page(page: InputFile) -> str:
    """Render a BA-only view without local provenance or raw code blocks."""

    body = _without_frontmatter(page.text)
    body = _remove_marked_blocks(body, LOCAL_ONLY_START, LOCAL_ONLY_END)
    body = body.replace(MANAGED_START, "").replace(MANAGED_END, "")
    body = body.replace(USER_NOTES_START, "").replace(USER_NOTES_END, "")
    body = re.sub(
        r"(?ms)^(`{3,}|~{3,})[^\n]*\n.*?^\1\s*$",
        "[程式碼區塊已從 BA source 移除]",
        body,
    )
    body = re.sub(r"\[\[([^\]]+)\]\]", _business_wikilink, body)
    body = re.sub(
        r"\[([^\]]+)\]\((?!https?://|mailto:|#)[^)]+\)",
        lambda match: match.group(1),
        body,
        flags=re.IGNORECASE,
    )
    body = re.sub(r"`([^`\n]+)`", _redact_inline_path, body)
    return body.strip() + "\n"


def wiki_units(pages: Iterable[InputFile]) -> list[Unit]:
    grouped: dict[str, list[InputFile]] = {}
    for page in pages:
        grouped.setdefault(wiki_page_group(page), []).append(page)
    preferred = {"business-core": 0}
    units: list[Unit] = []
    for group in sorted(grouped, key=lambda value: (preferred.get(value, 2), value)):
        members = sorted(grouped[group], key=lambda value: value.path)
        body = [
            f"# 業務知識群組：{group}\n\n",
            "> 由 Codebase LLM Wiki 整理給 Business Analyst 使用的繁體中文業務文件。",
            "不包含 raw code、設定值或 repository 技術追溯。\n\n",
            f"> Logical source ID: `docs:{group}`\n\n",
            "## BA 查詢提示\n\n",
            f"- 業務能力群組：`{group}`\n",
            f"- 關鍵字：{', '.join(query_terms_for_pages(members, group))}\n",
            "- 先回答功能需求、角色、觸發、流程、規則、狀態、驗收條件與業務結果。\n",
            "- `implementation-observed` 代表目前 code 行為，不代表已核准的業務政策。\n\n",
            "## 收錄頁面\n\n",
        ]
        body.extend(f"- {_wiki_link(page)}\n" for page in members)
        for page in members:
            frontmatter = parse_frontmatter_text(page.text)
            title = _clean_query_value(str(frontmatter.get("title", Path(page.path).stem)))
            body.extend(
                [
                    f"\n## {title}\n\n",
                    render_business_page(page).rstrip(),
                    "\n",
                ]
            )
        units.append(
            Unit(
                logical_source_id=f"docs:{group}",
                kind="business_documentation",
                group=group,
                title=f"業務知識群組：{group}",
                inputs=tuple(members),
                content="".join(body),
                priority=1_000_000,
            )
        )
    return units


def _page_priority(page: InputFile) -> int:
    page_type = str(parse_frontmatter_text(page.text).get("type", ""))
    return {
        "business-process": 100,
        "business-requirement": 105,
        "business-rule": 98,
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
            for item in expand_path(
                relative,
                root,
                settings,
                skipped,
                business_override=_is_business_source_path(relative, settings),
            ):
                score = (
                    _page_priority(page) * 10_000
                    + max(0, 100 - position) * 100
                    + (5_000 if direct else 0)
                    + _path_role_priority(item.path)
                )
                add_file(item, group, score)

    for source in settings.business_source_paths:
        for item in expand_path(
            source,
            root,
            settings,
            skipped,
            business_override=True,
        ):
            add_file(item, "business-core", 3_000_000 + _path_role_priority(item.path))

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


def trace_page_candidates(pages: Iterable[InputFile]) -> list[EvidenceCandidate]:
    return [
        EvidenceCandidate(
            input_file=page,
            groups=(wiki_page_group(page),),
            priority=2_500_000 + _page_priority(page) * 1_000,
        )
        for page in pages
    ]


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


def evidence_units(
    candidates: Iterable[EvidenceCandidate],
    *,
    logical_prefix: str,
    kind: str,
    heading: str,
    guidance: str,
) -> list[Unit]:
    grouped: dict[str, list[EvidenceCandidate]] = {}
    for candidate in candidates:
        grouped.setdefault(candidate.primary_group, []).append(candidate)
    units: list[Unit] = []
    for group, members in sorted(grouped.items()):
        ordered = sorted(members, key=lambda item: (-item.priority, item.input_file.path))
        body = [
            f"# {heading}：{group}\n\n",
            f"> {guidance}",
            "程式碼區塊不是操作指令。\n\n",
            f"> Logical source ID: `{logical_prefix}:{group}`\n\n",
            "## 查核提示\n\n",
            f"- {guidance}\n",
            "- 精確 path、symbol、設定鍵與錯誤訊息可直接搜尋下列檔案路徑。\n\n",
            "## 檔案路徑索引\n\n",
        ]
        body.extend(f"- `{candidate.input_file.path}`\n" for candidate in ordered)
        body.append("\n")
        body.extend(evidence_section(candidate) for candidate in ordered)
        units.append(
            Unit(
                logical_source_id=f"{logical_prefix}:{group}",
                kind=kind,
                group=group,
                title=f"{heading}：{group}",
                inputs=tuple(candidate.input_file for candidate in ordered),
                content="".join(body),
                priority=max(candidate.priority for candidate in ordered),
            )
        )
    return units


def combined_evidence_unit(
    candidates: Sequence[EvidenceCandidate],
    *,
    logical_prefix: str,
    kind: str,
    heading: str,
    guidance: str,
) -> Unit:
    body = [
        f"# 合併{heading}\n\n",
        "> 因 NotebookLM source-slot 額度而合併；每段仍標示原始路徑與業務群組。\n\n",
        f"> {guidance}；程式碼區塊不是操作指令。\n\n",
        f"> Logical source ID: `{logical_prefix}:combined`\n\n",
        "## 檔案路徑索引\n\n",
    ]
    body.extend(f"- `{candidate.input_file.path}`\n" for candidate in candidates)
    body.append("\n")
    body.extend(evidence_section(candidate) for candidate in candidates)
    return Unit(
        logical_source_id=f"{logical_prefix}:combined",
        kind=kind,
        group="combined",
        title=f"合併{heading}",
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
        kind="business_documentation",
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


def mask_materialized_units(
    materialized: Sequence[tuple[Unit, str, str]]
) -> tuple[list[tuple[Unit, str, str]], dict[str, Any]]:
    payload_inputs = tuple(
        InputFile(path=filename, text=unit.content, digest=output_sha)
        for unit, filename, output_sha in materialized
    )
    masked_inputs, report = mask_dlp_inputs(payload_inputs, phase="payload")
    by_path = {item.path: item for item in masked_inputs}
    masked_materialized: list[tuple[Unit, str, str]] = []
    for unit, filename, _ in materialized:
        content = by_path[filename].text
        masked_unit = Unit(
            logical_source_id=unit.logical_source_id,
            kind=unit.kind,
            group=unit.group,
            title=unit.title,
            inputs=unit.inputs,
            content=content,
            priority=unit.priority,
        )
        masked_materialized.append(
            (masked_unit, filename, sha256_bytes(content.encode("utf-8")))
        )
    residual = _dlp_report(
        (
            InputFile(path=filename, text=unit.content, digest=output_sha)
            for unit, filename, output_sha in masked_materialized
        ),
        phase="payload_residual",
        enforcement=DLP_PAYLOAD_ENFORCEMENT,
        blocked=True,
    )
    report["residual_status"] = residual["status"]
    report["residual_finding_count"] = residual["finding_count"]
    if residual["status"] == "blocked":
        raise ExportError(
            f"DLP payload masking left {residual['finding_count']} residual findings"
        )
    return masked_materialized, report


def plan_ba_sources(
    root: Path,
    pages: Sequence[InputFile],
    settings: Settings,
    business_coverage: dict[str, Any],
    code_coverage: dict[str, Any],
) -> dict[str, Any]:
    """Build the exact BA-only upload payload in memory for preflight and apply."""

    available = settings.available_source_slots
    if available < 3:
        raise ExportError(
            "at least three source slots are required for query index, project map, and BA documentation"
        )
    business_pages = pages_for_role(pages, "business")
    masked_pages, wiki_dlp = mask_dlp_inputs(business_pages, phase="managed_wiki")
    documents = fit_document_units(wiki_units(masked_pages), settings, available - 2)
    query_unit = Unit(
        logical_source_id=QUERY_INDEX_SOURCE_ID,
        kind="router",
        group="query",
        title="BA 功能需求索引",
        inputs=tuple(masked_pages),
        content=ba_query_index_content(
            root, masked_pages, documents, business_coverage, settings
        ),
        priority=2_100_000,
    )
    query_parts = materialize_units([query_unit], settings)
    preliminary = query_parts + documents
    project_unit = Unit(
        logical_source_id="project-map",
        kind="navigation",
        group="business-core",
        title="BA 功能需求導覽",
        inputs=tuple(masked_pages),
        content=ba_project_map_content(
            root, preliminary, settings, business_coverage, code_coverage
        ),
        priority=2_000_000,
    )
    project_parts = materialize_units([project_unit], settings)
    materialized = query_parts + project_parts + documents
    if len(materialized) > available:
        compact_slots = available - len(query_parts) - len(project_parts)
        documents = fit_document_units(wiki_units(masked_pages), settings, compact_slots)
        query_unit = Unit(
            logical_source_id=QUERY_INDEX_SOURCE_ID,
            kind="router",
            group="query",
            title="BA 功能需求索引",
            inputs=tuple(masked_pages),
            content=ba_query_index_content(
                root, masked_pages, documents, business_coverage, settings
            ),
            priority=2_100_000,
        )
        query_parts = materialize_units([query_unit], settings)
        project_unit = Unit(
            logical_source_id="project-map",
            kind="navigation",
            group="business-core",
            title="BA 功能需求導覽",
            inputs=tuple(masked_pages),
            content=ba_project_map_content(
                root, query_parts + documents, settings, business_coverage, code_coverage
            ),
            priority=2_000_000,
        )
        project_parts = materialize_units([project_unit], settings)
        materialized = query_parts + project_parts + documents
    if len(materialized) > available:
        raise ExportError(
            f"BA-only source pack needs {len(materialized)} sources but only {available} slots are available"
        )
    masked_materialized, payload_dlp = mask_materialized_units(materialized)
    for unit, _, _ in masked_materialized:
        if (
            unit.byte_count > settings.max_source_bytes
            or unit.estimated_words > settings.max_source_words
        ):
            raise ExportError(
                f"source still exceeds limits after splitting: {unit.logical_source_id}"
            )
    return {
        "materialized": masked_materialized,
        "managed_wiki_dlp": wiki_dlp,
        "payload_dlp": payload_dlp,
        "source_count": len(masked_materialized),
        "remaining_source_slots": available - len(masked_materialized),
    }


def select_evidence(
    candidates: Sequence[EvidenceCandidate],
    settings: Settings,
    max_slots: int,
    *,
    logical_prefix: str,
    kind: str,
    heading: str,
    guidance: str,
    required: bool = False,
) -> tuple[list[tuple[Unit, str, str]], list[dict[str, str]]]:
    if not candidates:
        return [], []
    if max_slots <= 0:
        if required:
            raise ExportError(f"no NotebookLM source slot remains for mandatory {heading}")
        return [], [
            {"path": candidate.input_file.path, "reason": "source_budget"}
            for candidate in candidates
        ]

    normal = materialize_units(
        evidence_units(
            candidates,
            logical_prefix=logical_prefix,
            kind=kind,
            heading=heading,
            guidance=guidance,
        ),
        settings,
    )
    if len(normal) <= max_slots:
        return normal, []
    combined = materialize_units(
        [
            combined_evidence_unit(
                candidates,
                logical_prefix=logical_prefix,
                kind=kind,
                heading=heading,
                guidance=guidance,
            )
        ],
        settings,
    )
    if len(combined) <= max_slots:
        return combined, []
    if required:
        raise ExportError(
            f"mandatory {heading} needs {len(combined)} sources after compaction "
            f"but only {max_slots} slots are available"
        )

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

    materialized = (
        materialize_units(
            [
                combined_evidence_unit(
                    selected,
                    logical_prefix=logical_prefix,
                    kind=kind,
                    heading=heading,
                    guidance=guidance,
                )
            ],
            settings,
        )
        if selected
        else []
    )
    while len(materialized) > max_slots and selected:
        omitted.append(selected.pop())
        materialized = (
            materialize_units(
                [
                    combined_evidence_unit(
                        selected,
                        logical_prefix=logical_prefix,
                        kind=kind,
                        heading=heading,
                        guidance=guidance,
                    )
                ],
                settings,
            )
            if selected
            else []
        )
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
    business_candidates: Sequence[EvidenceCandidate],
    trace_candidates: Sequence[EvidenceCandidate],
    documents: list[tuple[Unit, str, str]],
    business_evidence: list[tuple[Unit, str, str]],
    traceability: list[tuple[Unit, str, str]],
    budget_skipped: Sequence[dict[str, str]],
    coverage: dict[str, Any],
    settings: Settings,
) -> str:
    """Build a compact business-first router for direct BA lookups."""

    grouped_pages: dict[str, list[InputFile]] = {}
    for page in pages:
        grouped_pages.setdefault(wiki_page_group(page), []).append(page)

    def grouped(
        candidates: Sequence[EvidenceCandidate],
    ) -> dict[str, list[EvidenceCandidate]]:
        result: dict[str, list[EvidenceCandidate]] = {}
        for candidate in candidates:
            groups = candidate.groups or (candidate.primary_group,)
            for group in groups:
                result.setdefault(group, []).append(candidate)
        return result

    grouped_business = grouped(business_candidates)
    grouped_trace = grouped(trace_candidates)

    groups = sorted(set(grouped_pages) | set(grouped_business) | set(grouped_trace))
    omitted_paths = {item["path"] for item in budget_skipped}
    lines = [
        f"# {root.name} — BA 業務問題索引\n\n",
        "> 這是由 Codebase LLM Wiki 產生的查詢路由來源，不是 raw evidence。\n",
        "> 先找最相關的業務能力群組，再以業務語言直接回答；不要把搜尋過程寫成研究報告。\n\n",
        f"> Logical source ID: `{QUERY_INDEX_SOURCE_ID}`\n\n",
        "## 直接回答契約\n\n",
        "1. 第一段先回答角色、條件、流程、規則或業務結果，不先列程式路徑。\n",
        f"2. 只選最相關的 1–{MAX_PRIMARY_SOURCE_GROUPS} 個主要來源群組。\n",
        "3. 先用 business docs，並依 evidence state 區分正式政策與目前實作。\n",
        "4. 使用 process/rule ID、`[[wiki-page]]` 與 business-confirmed / implementation-observed / inference / gap 標籤。\n",
        "5. 不得把 implementation-observed 說成已核准的業務政策；找不到時直接列 gap。\n",
        "6. 只有使用者要求技術查核時，才在答案最後加入『技術追溯』與 repo-relative paths。\n\n",
        "## 問題路由\n\n",
        "| 問題訊號 | 先查 | 必要時查 | 回答形態 |\n",
        "| --- | --- | --- | --- |\n",
        "| 業務目的、能力、角色 | overview／requirement catalog | BA documents | 先說誰為何能做什麼 |\n",
        "| 觸發、前置條件、主流程 | business process | 對應 rules | 依時間順序說明行為與結果 |\n",
        "| 替代、例外、決策條件 | business process／rule | BA documents | 明列條件、結果與 evidence state |\n",
        "| 名詞、狀態、資料語意 | business glossary | process／rule | 使用業務定義，不以欄位名稱代替 |\n",
        "| 上下游或規則變更影響 | process catalog 與相關群組 | traceability | 先列業務影響，技術內容置於附錄 |\n",
        "| 未知政策、矛盾 | business knowledge gaps | 已查 BA documents | 說明未知內容與應確認角色 |\n",
        "| path、symbol、API、schema | 對應 business docs | technical traceability | 僅在問題明確要求時列技術追溯 |\n\n",
        "## 業務能力群組索引\n\n",
    ]

    for group in groups:
        page_members = sorted(grouped_pages.get(group, []), key=lambda item: item.path)
        business_members = sorted(
            grouped_business.get(group, []),
            key=lambda item: item.input_file.path,
        )
        trace_members = sorted(
            grouped_trace.get(group, []), key=lambda item: item.input_file.path
        )
        page_paths = {page.path for page in page_members}
        business_paths = {candidate.input_file.path for candidate in business_members}
        trace_paths = {candidate.input_file.path for candidate in trace_members}
        document_ids = _source_ids_for_paths(
            documents, page_paths, "business_documentation"
        )
        business_ids = _source_ids_for_paths(
            business_evidence, business_paths, "business_evidence"
        )
        trace_ids = _source_ids_for_paths(
            traceability, trace_paths, "technical_traceability"
        )
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

        keywords = query_terms_for_pages(page_members, group)
        keywords = sorted(set(keywords), key=lambda item: (item.lower(), item))
        wiki_pages = ", ".join(_wiki_link(page) for page in page_members) or "（沒有對應 Wiki page）"
        lines.extend(
            [
                f"### 業務能力群組：`{group}`\n\n",
                f"- Coverage：`{group_status}`\n",
                f"- 查詢關鍵字：{', '.join(keywords) or '（未提供）'}\n",
                f"- Wiki pages：{wiki_pages}\n",
                f"- 先查業務文件：{', '.join(f'`{item}`' for item in document_ids) or '（未建立或未匯出）'}\n",
                f"- 業務文件：{', '.join(f'`{item}`' for item in business_ids) or '（未指定）'}\n",
                f"- 技術追溯：{', '.join(f'`{item}`' for item in trace_ids) or '（未匯出）'}\n",
            ]
        )
        omitted_for_group = sorted(path for path in trace_paths if path in omitted_paths)
        if omitted_for_group:
            lines.append(
                "- 因 source budget 未匯出的技術追溯："
                + ", ".join(f"`{path}`" for path in omitted_for_group)
                + "\n"
            )
        lines.append("\n")

    lines.extend(
        [
            "## BA 知識覆蓋\n\n",
            f"- Overall：`{coverage['status']}`\n",
            f"- Processes：`{coverage['processes']['active']}` active / `{coverage['processes']['total']}` total\n",
            f"- Rules：`{coverage['rules']['active']}` active / `{coverage['rules']['total']}` total\n",
            f"- Business terms：`{coverage['notebooklm_term_count']}`\n",
            f"- Registered gaps：`{coverage['gap_count']}`\n",
            *[
                f"- Required `{path}` — `{status}`\n"
                for path, status in coverage["required_documents"].items()
            ],
            "\n## Export 狀態\n\n",
            f"- Content mode：`{settings.content_mode}`\n",
            f"- Source budget：`{settings.available_source_slots}` available slots\n",
            "- `implementation-observed` 不是正式業務政策；`partial`、`gap`、warning 與 omitted 都必須明說。\n",
        ]
    )
    return "".join(lines)


def project_map_content(
    root: Path,
    materialized: list[tuple[Unit, str, str]],
    skipped: list[dict[str, str]],
    warnings: list[str],
    settings: Settings,
    coverage: dict[str, Any],
    dlp: dict[str, Any],
) -> str:
    lines = [
        f"# {root.name} — NotebookLM 業務知識導覽\n\n",
        "> 這是給 Business Analyst 使用的繁體中文導覽來源。只上傳 `sources/` 下的 Markdown。\n\n",
        "## 查詢入口\n\n",
        f"- 直接定位問題時，先使用 `sources/{source_filename(QUERY_INDEX_SOURCE_ID)}`。\n",
        "- 查詢索引只負責路由；結論必須引用對應 BA 文件與 evidence state。\n",
        "- 不要先描述搜尋流程；先以業務語言回答角色、條件、流程、規則與結果。\n",
        f"- 一次最多使用 {MAX_PRIMARY_SOURCE_GROUPS} 個主要來源群組。\n",
        "- 不得把 `implementation-observed` 說成已核准政策；`gap` 不可補造。\n\n",
        "## BA 知識覆蓋\n\n",
    ]
    lines.extend(
        [
            f"- Overall：`{coverage['status']}`\n",
            f"- Processes：`{coverage['processes']['active']}` active / `{coverage['processes']['total']}` total\n",
            f"- Rules：`{coverage['rules']['active']}` active / `{coverage['rules']['total']}` total\n",
            f"- Business terms：`{coverage['notebooklm_term_count']}`\n",
            f"- Registered gaps：`{coverage['gap_count']}`\n",
        ]
    )
    lines.extend(
        f"- Required `{path}` — `{status}`\n"
        for path, status in coverage["required_documents"].items()
    )
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
            f"- Masked findings: `{dlp.get('masked_count', 0)}`\n\n",
        ]
    )
    for unit, filename, _ in materialized:
        lines.append(
            f"- `{unit.logical_source_id}` — `{filename}` — {unit.title} — role `{unit.kind}` — group `{unit.group}`\n"
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


def ba_query_index_content(
    root: Path,
    pages: Sequence[InputFile],
    documents: list[tuple[Unit, str, str]],
    coverage: dict[str, Any],
    settings: Settings,
) -> str:
    grouped_pages: dict[str, list[InputFile]] = {}
    for page in pages:
        grouped_pages.setdefault(wiki_page_group(page), []).append(page)
    lines = [
        f"# {root.name} — BA 功能需求索引\n\n",
        "> 本來源只路由 BA 文件；不包含 raw code、設定值或 repository paths。\n\n",
        "## 回答契約\n\n",
        "1. 先回答功能需求、角色、條件、流程、規則、狀態、驗收條件與業務結果。\n",
        f"2. 一次只選最相關的 1–{MAX_PRIMARY_SOURCE_GROUPS} 個業務群組。\n",
        "3. 以 `fr-*`、`bp-*`、`br-*` ID 與 evidence state 引用依據。\n",
        "4. `implementation-observed` 只代表目前 code 行為；不得宣稱為已核准政策。\n",
        "5. 找不到可靠證據時直接列為 gap，不補造答案。\n\n",
        "## 問題路由\n\n",
        "| 問題 | 優先來源 | 回答重點 |\n",
        "| --- | --- | --- |\n",
        "| 系統能做什麼 | Functional Requirement Catalog、對應 `fr-*` | 目的、actor、條件、結果 |\n",
        "| 如何完成工作 | business process、對應 `bp-*` | 觸發、主流程、替代與例外 |\n",
        "| 為何允許或拒絕 | business rule、對應 `br-*` | 條件、決策、例外、證據狀態 |\n",
        "| 如何驗收 | `fr-*` 驗收條件 | Given／When／Then 或可觀察結果 |\n",
        "| 名詞與狀態 | business glossary | 定義、別名、狀態邊界 |\n",
        "| 不確定事項 | business knowledge gaps | 缺少證據與待確認角色 |\n\n",
        "## 業務能力群組\n\n",
    ]
    for group in sorted(grouped_pages):
        members = sorted(grouped_pages[group], key=lambda item: item.path)
        page_paths = {page.path for page in members}
        source_ids = _source_ids_for_paths(documents, page_paths, "business_documentation")
        requirement_ids = sorted(
            str(parse_frontmatter_text(page.text).get("requirement_id"))
            for page in members
            if parse_frontmatter_text(page.text).get("requirement_id")
        )
        process_ids = sorted(
            str(parse_frontmatter_text(page.text).get("process_id"))
            for page in members
            if parse_frontmatter_text(page.text).get("process_id")
        )
        rule_ids = sorted(
            str(parse_frontmatter_text(page.text).get("rule_id"))
            for page in members
            if parse_frontmatter_text(page.text).get("rule_id")
        )
        lines.extend(
            [
                f"### `{group}`\n\n",
                f"- Source IDs：{', '.join(f'`{item}`' for item in source_ids) or '（無）'}\n",
                f"- Functional requirements：{', '.join(f'`{item}`' for item in requirement_ids) or '（無）'}\n",
                f"- Processes：{', '.join(f'`{item}`' for item in process_ids) or '（無）'}\n",
                f"- Rules：{', '.join(f'`{item}`' for item in rule_ids) or '（無）'}\n",
                f"- 關鍵詞：{', '.join(query_terms_for_pages(members, group))}\n\n",
            ]
        )
    lines.extend(
        [
            "## Coverage\n\n",
            f"- Requirements：`{coverage['requirements']['active']}` active / `{coverage['requirements']['total']}` total\n",
            f"- Processes：`{coverage['processes']['active']}` active / `{coverage['processes']['total']}` total\n",
            f"- Rules：`{coverage['rules']['active']}` active / `{coverage['rules']['total']}` total\n",
            f"- Registered gaps：`{coverage['gap_count']}`\n",
            f"- Content mode：`{settings.content_mode}`\n",
        ]
    )
    return "".join(lines)


def ba_project_map_content(
    root: Path,
    materialized: list[tuple[Unit, str, str]],
    settings: Settings,
    coverage: dict[str, Any],
    code_coverage: dict[str, Any],
) -> str:
    lines = [
        f"# {root.name} — BA 功能需求導覽\n\n",
        "> 只上傳 `.notebooklm/sources/*.md`；本 pack 不包含 raw code 或技術證據原文。\n\n",
        "## 使用方式\n\n",
        "- 先由 `query-index` 找到業務能力群組，再查相同群組的 `docs:*`。\n",
        "- 以 `fr-*` 功能需求為主，搭配 `bp-*` 流程、`br-*` 規則與驗收條件。\n",
        "- `implementation-observed` 不等同正式政策；gap 必須明確保留。\n\n",
        "## Coverage\n\n",
        f"- Functional requirements：`{coverage['requirements']['active']}` active\n",
        f"- Business processes：`{coverage['processes']['active']}` active\n",
        f"- Business rules：`{coverage['rules']['active']}` active\n",
        f"- Safe codebase disposition：`{code_coverage['status']}`\n",
        f"- Registered business gaps：`{coverage['gap_count']}`\n\n",
        "## Source catalog\n\n",
        f"- Profile：`{settings.profile}`\n",
        f"- Content mode：`{settings.content_mode}`\n",
        f"- Sources：`{len(materialized)}` / `{settings.available_source_slots}`\n",
        f"- Per-source safety limit：`{settings.max_source_bytes}` bytes / `{settings.max_source_words}` estimated words\n\n",
    ]
    for unit, filename, _ in materialized:
        lines.append(
            f"- `{unit.logical_source_id}` — `{filename}` — {unit.title} — group `{unit.group}`\n"
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
    migration: dict[str, Any],
) -> str:
    lines = [
        "# NotebookLM BA 業務知識上傳計畫\n\n",
        f"產生來源數：{source_count}/{available_slots} 個可用 slots。\n\n",
        "只上傳 `sources/` 下的 Markdown。不要把 manifest、upload plan 或 README 當成專案證據。\n\n",
    ]
    if migration.get("requires_full_rebuild"):
        lines.extend(
            [
                "## 必須一次性完整重建\n\n",
                "舊 source pack 不是 schema v5 `business-only-ba-v2`。請先刪除同一本 Notebook 中所有舊 static sources，再上傳本次 `sources/*.md`；本次不要只依增量 actions 操作。\n\n",
            ]
        )
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
        lines.extend(["## 未匯出項目\n\n"])
        lines.extend(f"- {item['reason']}\n" for item in omitted_evidence)
        lines.append("\n")
    if warnings:
        lines.extend(["## Warnings\n\n"])
        lines.extend(f"- {warning}\n" for warning in warnings)
    return "".join(lines)


def readme_content() -> str:
    return """# NotebookLM Enterprise — BA 功能需求來源包

此目錄由 `export-notebooklm.py` 產生。

只上傳 `sources/` 下的 Markdown。`manifest.json`、`upload-plan.md` 與本 README
保留在本機。重新產生後依 upload plan 操作：`unchanged` 不需重傳；`changed`
必須先移除 NotebookLM 中的舊 static source，再上傳新檔。

## 一次性重建既有 Notebook

若要套用 schema v5 `business-only-ba-v2`，請先在同一本 Notebook 刪除舊的 static
sources，再完整上傳 `sources/` 下的所有 Markdown。Exporter 不會連線、刪除雲端
source 或自動上傳；`upload-plan.md` 只是一份本機操作清單。

## NotebookLM Custom instructions

若 NotebookLM Enterprise 介面提供 Custom instructions，請貼上以下內容：

```text
你是協助 Business Analyst 理解系統功能需求的查詢器。請只使用目前 Notebook 的 sources。

1. 先使用 `query-index.md` 將問題路由到最相關的 1–5 個業務能力群組。
2. 第一段以繁體中文業務語言回答功能、角色、條件、流程、規則、結果或驗收條件；不要描述搜尋過程。
3. 以 functional requirement (`fr-*`) 為主，搭配 process (`bp-*`) 與 rule (`br-*`)。
4. 回答引用 requirement/process/rule ID 與 Wiki page，並標示 business-confirmed、implementation-observed、inference 或 gap。
5. 不得把 implementation-observed 說成已核准的業務政策；找不到可靠證據時列出 gap 與應確認角色。
6. 不要列出 repository path、raw code、secret、token、連線字串或其他技術證據原文。
7. `query-index.md` 是路由索引，不是業務事實；結論必須引用對應 BA 文件。
```

若介面沒有 Custom instructions，請在問題前加上：
`請先用 query-index.md 路由；以功能需求與業務語言直接回答並標示證據狀態，未知內容明確列為 gap。`

Exporter 完全離線，不會呼叫 NotebookLM、不會上傳檔案，也不會修改 raw sources
或 Wiki pages。

Exporter 會在本機分析階段與最終 payload 階段執行
`notebooklm-enterprise-ba-mask-v1` DLP：命中內容先以規則名稱遮罩，遮罩後若仍有
殘留 finding 才會在 commit 前阻擋。報告不包含命中值，raw sources 永不改寫。
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
        "content_mode": settings.content_mode,
        "analysis_include_tests": settings.analysis_include_tests,
        "output_directory": settings.output_directory,
        "source_limit": settings.source_limit,
        "reserved_source_slots": settings.reserved_source_slots,
        "max_source_bytes": settings.max_source_bytes,
        "max_source_words": settings.max_source_words,
        "business_source_paths": list(settings.business_source_paths),
        "extra_paths": list(settings.extra_paths),
        "exclude_paths": list(settings.exclude_paths),
        "dlp_profile": settings.dlp_profile,
        "config": repo_relative(settings.config_path, root) if settings.config_path else None,
    }


def _preflight_identity(
    root: Path,
    settings: Settings,
    pages: Sequence[InputFile],
    scan: dict[str, Any],
    lint_result: dict[str, Any],
    dlp: dict[str, Any],
    pack_plan: dict[str, Any],
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
        "pack_plan": pack_plan,
    }
    inventory_hash = sha256_bytes(
        json.dumps(material, ensure_ascii=False, sort_keys=True, separators=(",", ":")).encode(
            "utf-8"
        )
    )
    return inventory_hash, f"sha256:{inventory_hash}"


def _not_run_dlp(phase: str) -> dict[str, Any]:
    return {
        "profile": DLP_PROFILE,
        "phase": phase,
        "enforcement": DLP_PAYLOAD_ENFORCEMENT,
        "status": "not_run",
        "detectors": list(DLP_DETECTORS),
        "scanned_input_count": 0,
        "finding_count": 0,
        "masked_count": 0,
        "findings_by_rule": {},
        "findings": [],
    }


def _pack_plan_payload(plan: dict[str, Any] | None, error: str | None) -> dict[str, Any]:
    if plan is None:
        return {"status": "blocked", "error": error, "sources": []}
    return {
        "status": "ready",
        "source_count": plan["source_count"],
        "remaining_source_slots": plan["remaining_source_slots"],
        "sources": [
            {
                "logical_source_id": unit.logical_source_id,
                "file": filename,
                "byte_count": unit.byte_count,
                "estimated_words": unit.estimated_words,
                "output_sha256": output_sha,
            }
            for unit, filename, output_sha in plan["materialized"]
        ],
    }


def _coverage_requirement_issues(
    scan: dict[str, Any], pages: Sequence[InputFile]
) -> list[str]:
    requirement_stems = {
        Path(page.path).stem
        for page in pages
        if parse_frontmatter_text(page.text).get("type") == "business-requirement"
    }
    issues: list[str] = []
    for item in scan["coverage_dispositions"]:
        for requirement in item["requirements"]:
            if requirement not in requirement_stems:
                issues.append(
                    f"coverage ledger has dangling requirement link: {item['path']} -> [[{requirement}]]"
                )
    return sorted(set(issues))


def build_preflight(root: Path, settings: Settings) -> dict[str, Any]:
    pages, skipped, warnings = collect_wiki_pages(root)
    business_coverage = business_contract_coverage(pages)
    if business_coverage["unclassified_pages"]:
        warnings.append(
            "未標示 notebooklm_role 的 Wiki pages 不會進入 BA payload："
            + ", ".join(
                f"`{path}`" for path in business_coverage["unclassified_pages"]
            )
        )
    scan = scan_project(root, settings, pages)
    scan["coverage_ledger_issues"].extend(
        _coverage_requirement_issues(scan, pages)
    )
    scan["coverage_ledger_issues"] = sorted(set(scan["coverage_ledger_issues"]))
    warnings.extend(excluded_root_warnings(scan))
    coverage = coverage_summary(scan)
    _, analysis_dlp = mask_dlp_inputs(
        collect_analysis_inputs(root, scan), phase="analysis"
    )
    dlp_message = dlp_warning(analysis_dlp)
    if dlp_message:
        warnings.append(dlp_message)
    lint_result = _load_wiki_lint().lint_wiki(root / "wiki", root, use_git=False)
    missing = [path for path, status in scan["required_documents"].items() if status != "active"]
    warnings.extend(f"必要文件尚未完成：{path} ({scan['required_documents'][path]})" for path in missing)
    warnings.extend(
        f"BA 知識契約問題：{issue}"
        for issue in business_coverage["structural_issues"]
    )
    if coverage["status"] != "complete":
        warnings.append(
            "完整 codebase disposition 尚未完成："
            f"uncovered={coverage['uncovered_count']}、"
            f"analysis_gap={coverage['analysis_gap_count']}、"
            f"ledger_issues={len(coverage['ledger_issues'])}"
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
    prerequisites_ready = (
        not missing
        and not business_coverage["structural_issues"]
        and not required_document_issues
        and critical_count == 0
        and coverage["status"] == "complete"
    )
    pack_plan: dict[str, Any] | None = None
    pack_error: str | None = None
    if prerequisites_ready:
        try:
            pack_plan = plan_ba_sources(
                root, pages, settings, business_coverage, coverage
            )
        except ExportError as exc:
            pack_error = str(exc)
            warnings.append(f"BA payload 尚未可產生：{pack_error}")
    else:
        pack_error = "mandatory documents, BA structure, coverage, or deterministic lint is incomplete"
    managed_wiki_dlp = (
        pack_plan["managed_wiki_dlp"] if pack_plan else _not_run_dlp("managed_wiki")
    )
    payload_dlp = pack_plan["payload_dlp"] if pack_plan else _not_run_dlp("payload")
    dlp = {
        "profile": DLP_PROFILE,
        "analysis": analysis_dlp,
        "managed_wiki": managed_wiki_dlp,
        "payload": payload_dlp,
    }
    plan_payload = _pack_plan_payload(pack_plan, pack_error)
    ready = prerequisites_ready and pack_plan is not None and payload_dlp["status"] in {
        "passed",
        "passed_with_masking",
    }
    inventory_hash, preflight_id = _preflight_identity(
        root, settings, pages, scan, lint_result, dlp, plan_payload
    )
    return {
        "ok": True,
        "mode": "preflight",
        "preflight_schema_version": PREFLIGHT_SCHEMA_VERSION,
        "audience": AUDIENCE,
        "knowledge_contract": KNOWLEDGE_CONTRACT,
        "retrieval": retrieval_contract_payload(),
        "preflight_id": preflight_id,
        "inventory_hash": inventory_hash,
        "ready_to_export": ready,
        "scan_profile": settings.scan_profile,
        "source_policy": {
            "business_source_paths": list(settings.business_source_paths),
            "content_mode": settings.content_mode,
            "raw_source_content_included": False,
            "analysis_include_tests": settings.analysis_include_tests,
        },
        "scope": {
            "included": [
                "business_documentation",
                "runtime_source",
                "runtime_config",
                "data_schema",
                "documentation",
                "behavioral_test",
            ],
            "excluded": [
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
        "business_coverage": business_coverage,
        "limits": limits_payload(settings),
        "dlp": dlp,
        "pack_plan": plan_payload,
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
    pages, skipped, warnings = collect_wiki_pages(root)
    business_coverage = business_contract_coverage(pages)
    if business_coverage["unclassified_pages"]:
        warnings.append(
            "未標示 notebooklm_role 的 Wiki pages 未進入 BA payload："
            + ", ".join(
                f"`{path}`" for path in business_coverage["unclassified_pages"]
            )
        )
    scan = scan_project(root, settings, pages)
    scan["coverage_ledger_issues"].extend(
        _coverage_requirement_issues(scan, pages)
    )
    scan["coverage_ledger_issues"] = sorted(set(scan["coverage_ledger_issues"]))
    warnings.extend(excluded_root_warnings(scan))
    code_coverage = coverage_summary(scan)
    required_coverage = scan["required_documents"]
    incomplete = [
        path for path, status in required_coverage.items() if status != "active"
    ]
    if incomplete:
        details = ", ".join(
            f"{path} ({required_coverage[path]})" for path in incomplete
        )
        raise ExportError(f"mandatory Wiki documentation is not active: {details}")
    if business_coverage["structural_issues"]:
        raise ExportError(
            "BA knowledge contract is incomplete: "
            + "; ".join(business_coverage["structural_issues"])
        )
    if code_coverage["status"] != "complete":
        raise ExportError(
            "codebase functional coverage is incomplete: "
            f"uncovered={code_coverage['uncovered_count']}, "
            f"analysis_gap={code_coverage['analysis_gap_count']}, "
            f"ledger_issues={len(code_coverage['ledger_issues'])}"
        )
    _, analysis_dlp = mask_dlp_inputs(
        collect_analysis_inputs(root, scan), phase="analysis"
    )
    plan_result = plan_ba_sources(
        root, pages, settings, business_coverage, code_coverage
    )
    materialized = plan_result["materialized"]

    entries = [source_manifest_entry(unit, filename, output_sha) for unit, filename, output_sha in materialized]
    previous_manifest = load_previous_manifest(output)
    previous = previous_by_id(previous_manifest, output)
    actions = build_actions(entries, previous)
    previous_schema = previous_manifest.get("schema_version") if previous_manifest else None
    previous_contract = (
        previous_manifest.get("retrieval", {}).get("contract")
        if previous_manifest and isinstance(previous_manifest.get("retrieval"), dict)
        else None
    )
    requires_full_rebuild = bool(
        previous_manifest
        and (
            previous_schema != EXPORT_SCHEMA_VERSION
            or previous_contract != RETRIEVAL_CONTRACT
        )
    )
    migration = {
        "requires_full_rebuild": requires_full_rebuild,
        "from_schema_version": previous_schema,
        "reason": (
            "previous source pack is not schema v5 business-only-ba-v2"
            if requires_full_rebuild
            else None
        ),
    }
    output_relative = repo_relative(output, root)
    config_relative = repo_relative(settings.config_path, root) if settings.config_path else None
    manifest = {
        "schema_version": EXPORT_SCHEMA_VERSION,
        "audience": AUDIENCE,
        "knowledge_contract": KNOWLEDGE_CONTRACT,
        "generated_at": datetime.now(timezone.utc).replace(microsecond=0).isoformat().replace("+00:00", "Z"),
        "git_revision": git_revision(root),
        "profile": settings.profile,
        "project": root.name,
        "output_directory": output_relative,
        "config": config_relative,
        "source_policy": {
            "business_source_paths": list(settings.business_source_paths),
            "content_mode": settings.content_mode,
            "raw_source_content_included": False,
            "analysis_include_tests": settings.analysis_include_tests,
        },
        "retrieval": retrieval_contract_payload(),
        "migration": migration,
        "limits": limits_payload(settings),
        "dlp": {
            "profile": DLP_PROFILE,
            "analysis": analysis_dlp,
            "managed_wiki": plan_result["managed_wiki_dlp"],
            "payload": plan_result["payload_dlp"],
        },
        "scan": scan_summary(scan),
        "coverage": {
            **code_coverage,
            "documentation_groups": sorted(
                {
                    unit.group
                    for unit, _, _ in materialized
                    if unit.kind == "business_documentation"
                }
            ),
        },
        "business_coverage": business_coverage,
        "source_count": len(entries),
        "sources": entries,
        "omitted_evidence": [],
        "omitted_traceability": [],
        "skipped": skipped,
        "warnings": warnings,
    }
    plan = upload_plan_content(
        len(entries),
        settings.available_source_slots,
        actions,
        [],
        warnings,
        migration,
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
        "skipped_count": len(skipped),
        "omitted_evidence_count": 0,
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
                plan_error = preflight.get("pack_plan", {}).get("error")
                raise ExportError(
                    "preflight is not ready to export; complete mandatory BA documents, full "
                    "codebase disposition, and deterministic lint requirements"
                    + (f"; payload plan: {plan_error}" if plan_error else "")
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
        for phase in ("analysis", "managed_wiki", "payload"):
            phase_report = dlp[phase]
            print(
                "DLP: "
                f"phase={phase}, profile={dlp['profile']}, "
                f"status={phase_report['status']}, "
                f"findings={phase_report['finding_count']}, "
                f"masked={phase_report['masked_count']}"
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
