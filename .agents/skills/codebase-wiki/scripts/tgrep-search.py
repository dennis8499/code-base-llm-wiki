#!/usr/bin/env python3
"""Run the bundled tgrep binary as a bounded, read-only source search."""

from __future__ import annotations

import argparse
from dataclasses import dataclass
import hashlib
import json
import os
from pathlib import Path
import platform
import re
import stat
import subprocess
import sys
from typing import Sequence


SKILL_ROOT = Path(__file__).resolve().parents[1]
MANIFEST_PATH = SKILL_ROOT / "bin" / "tgrep-manifest.json"
SUPPORTED_SYSTEM = "Windows"
SUPPORTED_MACHINES = frozenset({"amd64", "x86_64", "x64"})
TGREP_EXIT_CODES = frozenset({0, 1, 2})
UNAVAILABLE_EXIT_CODE = 3
MAX_CHECK_SECONDS = 10
SHA256_PATTERN = re.compile(r"^[0-9a-f]{64}$")
EXPECTED_VERSION = "1.0.5"
EXPECTED_PLATFORM = "windows-x86_64"
EXPECTED_BINARY = "bin/windows-x64/tgrep.exe"


class TgrepError(RuntimeError):
    """A controlled wrapper or tgrep invocation failure."""

    exit_code = 2


class TgrepUnavailable(TgrepError):
    """The bundled tool cannot be used on this host or installation."""

    exit_code = UNAVAILABLE_EXIT_CODE


@dataclass(frozen=True)
class Bundle:
    """Validated metadata and path for the bundled tgrep executable."""

    version: str
    binary: Path
    sha256: str
    upstream_release: str


def _is_supported_host() -> bool:
    return sys.platform == "win32" and platform.machine().lower() in SUPPORTED_MACHINES


def _is_reparse_point(path: Path) -> bool:
    """Detect symlinks and Windows reparse points without following them."""

    if path.is_symlink():
        return True
    if os.name != "nt":
        return False
    try:
        attributes = os.stat(path, follow_symlinks=False).st_file_attributes
    except FileNotFoundError:
        return False
    except OSError as exc:
        raise TgrepError(f"unable to inspect search path: {path}: {exc}") from exc
    return bool(attributes & getattr(stat, "FILE_ATTRIBUTE_REPARSE_POINT", 0x400))


def _within(child: Path, parent: Path) -> bool:
    try:
        child.relative_to(parent)
    except ValueError:
        return False
    return True


def _read_manifest() -> dict[str, object]:
    try:
        payload = json.loads(MANIFEST_PATH.read_text(encoding="utf-8"))
    except (OSError, UnicodeError, json.JSONDecodeError) as exc:
        raise TgrepUnavailable(f"unable to read tgrep manifest: {MANIFEST_PATH}: {exc}") from exc
    if not isinstance(payload, dict):
        raise TgrepUnavailable("tgrep manifest must contain a JSON object")
    return payload


def _sha256(path: Path) -> str:
    digest = hashlib.sha256()
    try:
        with path.open("rb") as stream:
            for chunk in iter(lambda: stream.read(1024 * 1024), b""):
                digest.update(chunk)
    except OSError as exc:
        raise TgrepUnavailable(f"unable to read bundled tgrep binary: {path}: {exc}") from exc
    return digest.hexdigest()


def validate_bundle(check_version: bool = False) -> Bundle:
    """Validate host, manifest, containment, and the bundled binary digest."""

    if not _is_supported_host():
        raise TgrepUnavailable("bundled tgrep is available only on Windows x64")

    payload = _read_manifest()
    if payload.get("schema_version") != 1 or payload.get("tool") != "tgrep":
        raise TgrepUnavailable("unsupported tgrep manifest")

    version = payload.get("version")
    platform_name = payload.get("platform")
    binary_value = payload.get("binary")
    expected_digest = payload.get("sha256")
    upstream_release = payload.get("upstream_release")
    if not all(isinstance(value, str) and value for value in (
        version,
        platform_name,
        binary_value,
        expected_digest,
        upstream_release,
    )):
        raise TgrepUnavailable("tgrep manifest is missing required string fields")
    if (
        version != EXPECTED_VERSION
        or platform_name != EXPECTED_PLATFORM
        or binary_value != EXPECTED_BINARY
        or not SHA256_PATTERN.fullmatch(expected_digest.lower())
    ):
        raise TgrepUnavailable("tgrep manifest has invalid pinned metadata or SHA-256")

    relative_binary = Path(binary_value)
    if relative_binary.is_absolute() or ".." in relative_binary.parts:
        raise TgrepUnavailable("tgrep manifest binary path escapes the Skill")
    skill_root = SKILL_ROOT.resolve(strict=True)
    binary = (SKILL_ROOT / relative_binary).resolve(strict=False)
    if not _within(binary, skill_root):
        raise TgrepUnavailable("tgrep manifest binary path escapes the Skill")
    if not binary.is_file() or _is_reparse_point(SKILL_ROOT / relative_binary):
        raise TgrepUnavailable(f"bundled tgrep binary is unavailable: {binary}")

    actual_digest = _sha256(binary)
    if actual_digest != expected_digest.lower():
        raise TgrepUnavailable(
            f"bundled tgrep SHA-256 mismatch: expected {expected_digest}, got {actual_digest}"
        )

    bundle = Bundle(
        version=version,
        binary=binary,
        sha256=actual_digest,
        upstream_release=upstream_release,
    )
    if check_version:
        try:
            result = subprocess.run(
                [str(bundle.binary), "--version"],
                cwd=str(SKILL_ROOT),
                capture_output=True,
                check=False,
                shell=False,
                timeout=MAX_CHECK_SECONDS,
            )
        except (OSError, subprocess.TimeoutExpired) as exc:
            raise TgrepUnavailable(f"unable to execute bundled tgrep self-check: {exc}") from exc
        output = (result.stdout + result.stderr).decode("utf-8", errors="replace").strip()
        if result.returncode != 0 or output != f"tgrep {bundle.version}":
            raise TgrepUnavailable(
                f"bundled tgrep version mismatch: expected tgrep {bundle.version}, got {output!r}"
            )
    return bundle


def resolve_search_path(root_value: Path, path_value: Path) -> tuple[Path, Path, str]:
    """Resolve a search path and prove it remains inside the requested root."""

    root_candidate = root_value.expanduser()
    if not root_candidate.exists() or not root_candidate.is_dir():
        raise TgrepError(f"search root must be an existing directory: {root_candidate}")
    if _is_reparse_point(root_candidate):
        raise TgrepError(
            f"search root must not be a symlink or reparse point: {root_candidate}"
        )
    try:
        root = root_candidate.resolve(strict=True)
    except OSError as exc:
        raise TgrepError(f"unable to resolve search root: {root_candidate}: {exc}") from exc

    candidate = path_value.expanduser()
    if not candidate.is_absolute():
        candidate = root / candidate
    if not candidate.exists():
        raise TgrepError(f"search path does not exist: {path_value}")
    try:
        resolved = candidate.resolve(strict=True)
    except OSError as exc:
        raise TgrepError(f"unable to resolve search path: {path_value}: {exc}") from exc
    if not _within(resolved, root):
        raise TgrepError(f"search path escapes repo root: {path_value}")
    if not resolved.is_file() and not resolved.is_dir():
        raise TgrepError(f"search path is not a file or directory: {path_value}")

    relative = os.path.relpath(str(resolved), str(root))
    relative = relative.replace(os.sep, "/") or "."
    return root, resolved, relative


def build_command(args: argparse.Namespace, bundle: Bundle, root: Path, relative_path: str) -> list[str]:
    """Build the allowlisted tgrep argv with the pattern after ``--``."""

    command = [str(bundle.binary)]
    if args.no_index:
        command.append("--no-index")
    for glob in args.glob:
        command.extend(("--glob", glob))
    for file_type in args.type:
        command.extend(("--type", file_type))

    if args.list_files:
        command.extend(("--files", relative_path))
        return command

    if args.fixed:
        command.append("--fixed-strings")
    if args.ignore_case:
        command.append("--ignore-case")
    if args.files_only:
        command.append("--files-with-matches")
    if args.count:
        command.append("--count")
    if args.context is not None:
        command.extend(("--context", str(args.context)))
    if args.json:
        command.append("--json")
    command.extend(("--", args.pattern, relative_path))
    return command


def _emit(data: bytes, stream: object) -> None:
    buffer = getattr(stream, "buffer", None)
    if buffer is not None:
        buffer.write(data)
        buffer.flush()
        return
    text_stream = stream
    text_stream.write(data.decode("utf-8", errors="replace"))  # type: ignore[attr-defined]
    text_stream.flush()  # type: ignore[attr-defined]


def run_search(command: Sequence[str], root: Path) -> int:
    """Run without a shell and preserve tgrep's documented exit codes."""

    try:
        result = subprocess.run(
            list(command),
            cwd=str(root),
            capture_output=True,
            check=False,
            shell=False,
        )
    except OSError as exc:
        raise TgrepUnavailable(f"unable to execute bundled tgrep: {exc}") from exc
    _emit(result.stdout, sys.stdout)
    _emit(result.stderr, sys.stderr)
    return result.returncode if result.returncode in TGREP_EXIT_CODES else TgrepError.exit_code


def build_parser() -> argparse.ArgumentParser:
    parser = argparse.ArgumentParser(
        prog="tgrep-search.py",
        description="Bounded, read-only access to the bundled tgrep source searcher.",
    )
    parser.add_argument("--root", type=Path, help="repository root; required for searches")
    parser.add_argument("--path", type=Path, default=Path("."), help="file or directory under --root")
    modes = parser.add_mutually_exclusive_group()
    modes.add_argument("--pattern", help="regex or literal pattern to search")
    modes.add_argument("--files", dest="list_files", action="store_true", help="list searchable files")
    parser.add_argument("--fixed", action="store_true", help="treat --pattern as a literal string")
    parser.add_argument("--ignore-case", action="store_true")
    parser.add_argument("--files-only", action="store_true", help="print only files with matches")
    parser.add_argument("--count", action="store_true", help="print match counts per file")
    parser.add_argument("--context", type=int, metavar="N", help="print N lines of context")
    parser.add_argument("--glob", action="append", default=[], help="allowlisted tgrep glob filter")
    parser.add_argument("--type", action="append", default=[], help="allowlisted tgrep file type filter")
    parser.add_argument("--no-index", action="store_true", help="read the current filesystem instead of an index")
    parser.add_argument("--json", action="store_true", help="request tgrep JSON output")
    parser.add_argument("--check", action="store_true", help="verify the bundled binary and version")
    return parser


def _validate_arguments(parser: argparse.ArgumentParser, args: argparse.Namespace) -> None:
    if args.check:
        if args.root is not None or args.pattern is not None or args.list_files:
            parser.error("--check cannot be combined with a search")
        return
    if args.root is None:
        parser.error("--root is required for searches")
    if args.pattern is None and not args.list_files:
        parser.error("one of --pattern or --files is required")
    if args.context is not None and args.context < 0:
        parser.error("--context must be zero or greater")
    if args.list_files and any((args.fixed, args.ignore_case, args.files_only, args.count, args.context, args.json)):
        parser.error("file listing cannot use pattern-only flags")


def main(argv: Sequence[str] | None = None) -> int:
    parser = build_parser()
    args = parser.parse_args(argv)
    _validate_arguments(parser, args)
    try:
        if args.check:
            bundle = validate_bundle(check_version=True)
            print(f"tgrep {bundle.version} verified ({bundle.sha256})")
            return 0
        root, _, relative_path = resolve_search_path(args.root, args.path)
        bundle = validate_bundle()
        return run_search(build_command(args, bundle, root, relative_path), root)
    except TgrepError as exc:
        print(f"tgrep unavailable: {exc}" if isinstance(exc, TgrepUnavailable) else f"tgrep search error: {exc}", file=sys.stderr)
        return exc.exit_code


if __name__ == "__main__":
    raise SystemExit(main())
