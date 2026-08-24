#!/usr/bin/env python3
"""Build and validate Codebase LLM Wiki release assets.

The release tool uses only the Python standard library so that the GitHub
release workflow has no project-specific dependency installation step.
"""

from __future__ import annotations

import argparse
import fnmatch
import hashlib
import io
import json
import os
from pathlib import Path
import re
import subprocess
import stat
import sys
import tarfile
import zipfile
import gzip
from typing import Iterable, Sequence


PRODUCT_ID = "codebase-llm-wiki"
INSTALLER_CONTRACT_VERSION = 3
VERSION_FILE = "VERSION"
VERSION_PATTERN = re.compile(r"^(0|[1-9][0-9]*)\.(0|[1-9][0-9]*)\.(0|[1-9][0-9]*)$")
ARCHIVE_NAMES = ("codebase-llm-wiki.zip", "codebase-llm-wiki.tar.gz")
MANIFEST_NAME = "update-manifest.json"
CHECKSUMS_NAME = "SHA256SUMS"
EXCLUDED_PARTS = {
    ".git",
    ".venv",
    "__pycache__",
    ".mypy_cache",
    ".ruff_cache",
    "cache",
    ".codex-hook-logs",
    ".github-hook-logs",
    "dist",
    "logs",
    ".notebooklm",
}
EXCLUDED_PARTS_LOWER = {value.lower() for value in EXCLUDED_PARTS}
GENERATED_SUFFIXES = (
    ".notebooklm-transaction.json",
    ".notebooklm-transaction.lock",
)
GENERATED_TRANSACTION_MARKERS = (
    ".codebase-wiki-install-transaction.",
    ".notebooklm-transaction.",
)
SENSITIVE_NAMES = {
    ".env",
    ".npmrc",
    "credentials.json",
    "service-account.json",
}
SENSITIVE_SUFFIXES = (".pem", ".p12", ".pfx", ".key")
SENSITIVE_PATTERNS = ("*.env", ".env.*", "*credential*", "*secret*", "id_rsa*")
REPO_ROOT = Path(__file__).resolve().parents[1]


def configure_utf8_stdio() -> None:
    for stream in (sys.stdout, sys.stderr):
        if hasattr(stream, "reconfigure"):
            stream.reconfigure(encoding="utf-8", errors="replace")


class ReleaseError(ValueError):
    """Raised when release metadata cannot be produced safely."""


def validate_version(version: str) -> str:
    """Validate and return a stable X.Y.Z semantic version."""

    if not VERSION_PATTERN.fullmatch(version):
        raise ReleaseError(f"VERSION must use stable SemVer X.Y.Z, got {version!r}")
    return version


def read_version(root: Path = REPO_ROOT) -> str:
    path = root / VERSION_FILE
    if not path.is_file():
        raise ReleaseError(f"missing {VERSION_FILE}: {path}")
    lines = path.read_text(encoding="utf-8").splitlines()
    if len(lines) != 1 or lines[0] != lines[0].strip():
        raise ReleaseError(f"{VERSION_FILE} must contain exactly one version line")
    return validate_version(lines[0])


def expected_tag(version: str) -> str:
    return f"v{validate_version(version)}"


def validate_tag(tag: str, root: Path = REPO_ROOT) -> str:
    version = read_version(root)
    expected = expected_tag(version)
    if tag != expected:
        raise ReleaseError(f"tag {tag!r} does not match {VERSION_FILE} ({expected})")
    return version


def validate_release_readiness(root: Path = REPO_ROOT) -> None:
    """Require an owner-selected license before public release artifacts exist."""

    licenses = [root / name for name in ("LICENSE", "LICENSE.md", "LICENSE.txt")]
    if not any(path.is_file() and path.stat().st_size > 0 for path in licenses):
        raise ReleaseError(
            "public release is blocked until the project owner adds an explicit LICENSE"
        )
    history = root / "docs/history/llm-wiki.md"
    if history.is_file():
        text = history.read_text(encoding="utf-8")
        if "gist.github.com/karpathy/442a6bf555914893e9891c11519de94f" not in text:
            raise ReleaseError("upstream LLM Wiki attribution link is missing")


def _repository_from_git(root: Path) -> str:
    try:
        remote = subprocess.run(
            ["git", "config", "--get", "remote.origin.url"],
            cwd=root,
            check=True,
            capture_output=True,
            text=True,
        ).stdout.strip()
    except (OSError, subprocess.CalledProcessError) as exc:
        raise ReleaseError("repository is required when origin cannot be read") from exc

    if remote.startswith("git@github.com:"):
        remote = remote.removeprefix("git@github.com:")
    elif remote.startswith("https://github.com/"):
        remote = remote.removeprefix("https://github.com/")
    elif remote.startswith("http://github.com/"):
        remote = remote.removeprefix("http://github.com/")
    else:
        raise ReleaseError(f"unsupported GitHub origin URL: {remote!r}")
    return _normalize_repository(remote)


def _normalize_repository(repository: str) -> str:
    normalized = repository.strip().strip("/").removesuffix(".git")
    parts = normalized.split("/")
    component_pattern = re.compile(r"^[A-Za-z0-9][A-Za-z0-9_.-]*$")
    if (
        len(parts) != 2
        or any(part in {".", ".."} or not component_pattern.fullmatch(part) for part in parts)
    ):
        raise ReleaseError(f"repository must be OWNER/NAME, got {repository!r}")
    return normalized


def repository_name(root: Path = REPO_ROOT, repository: str | None = None) -> str:
    value = repository or os.environ.get("GITHUB_REPOSITORY")
    return _normalize_repository(value) if value else _repository_from_git(root)


def _is_sensitive_path(relative_parts: Sequence[str]) -> bool:
    for part in relative_parts:
        component = part.lower()
        if component in SENSITIVE_NAMES or component.endswith(SENSITIVE_SUFFIXES):
            return True
        if any(fnmatch.fnmatch(component, pattern) for pattern in SENSITIVE_PATTERNS):
            return True
    return False


def _is_generated_transaction_path(relative_parts: Sequence[str]) -> bool:
    for part in relative_parts:
        component = part.lower()
        if component.startswith(("codebase-wiki-stage-", "codebase-wiki-backup-")):
            return True
        if ".staging-" in component or ".backup-" in component:
            return True
        if any(marker in component for marker in GENERATED_TRANSACTION_MARKERS):
            return True
    return False


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
        raise ReleaseError(f"unable to inspect release path boundary: {path}: {exc}") from exc
    return bool(attributes & getattr(stat, "FILE_ATTRIBUTE_REPARSE_POINT", 0x400))


def _validate_output_path(output: Path) -> None:
    """Reject output paths that reach their destination through a link."""

    lexical = Path(os.path.abspath(output))
    current = Path(lexical.anchor) if lexical.anchor else Path()
    for component in lexical.parts:
        if component == lexical.anchor:
            continue
        current /= component
        if _is_reparse_point(current):
            raise ReleaseError(
                f"release output must not contain symlink or reparse point: {current}"
            )


def _validate_output_tree(output: Path) -> None:
    """Reject existing output entries that could redirect artifact writes."""

    if _is_reparse_point(output):
        raise ReleaseError(f"release output must not be a symlink or reparse point: {output}")
    if not output.exists():
        return
    if not output.is_dir():
        raise ReleaseError(f"release output is not a directory: {output}")
    for path in output.rglob("*"):
        if _is_reparse_point(path):
            raise ReleaseError(
                f"release output must not contain symlink or reparse point: {path}"
            )


def release_files(root: Path = REPO_ROOT, output: Path | None = None) -> list[Path]:
    """Return deterministic release files while excluding generated state."""

    root = root.resolve()
    output_root: Path | None = None
    if output is not None:
        output_root = output.resolve(strict=False)
        if output_root == root:
            raise ReleaseError("release output must be outside the repository root")
        try:
            output_root.relative_to(root)
        except ValueError:
            output_root = None

    files: list[Path] = []
    for path in sorted(root.rglob("*")):
        relative_parts = path.relative_to(root).parts
        if output_root is not None:
            try:
                path.relative_to(output_root)
            except ValueError:
                pass
            else:
                continue
        if any(part.lower() in EXCLUDED_PARTS_LOWER for part in relative_parts):
            continue
        if _is_generated_transaction_path(relative_parts):
            continue
        if path.name.lower().endswith(GENERATED_SUFFIXES):
            continue
        if _is_sensitive_path(relative_parts):
            continue
        if _is_reparse_point(path):
            relative = path.relative_to(root).as_posix()
            raise ReleaseError(
                f"release source must not contain symlink or reparse point: {relative}"
            )
        if not path.is_file():
            continue
        files.append(path)
    return files


def _archive_member(path: Path, root: Path, version: str) -> str:
    relative = path.relative_to(root).as_posix()
    return f"{PRODUCT_ID}-{version}/{relative}"


def _write_zip(path: Path, files: Iterable[Path], root: Path, version: str) -> None:
    with zipfile.ZipFile(path, "w", compression=zipfile.ZIP_DEFLATED) as archive:
        for source in files:
            info = zipfile.ZipInfo(_archive_member(source, root, version))
            info.date_time = (1980, 1, 1, 0, 0, 0)
            info.compress_type = zipfile.ZIP_DEFLATED
            info.external_attr = 0o644 << 16
            archive.writestr(info, source.read_bytes())


def _write_tarball(path: Path, files: Iterable[Path], root: Path, version: str) -> None:
    with path.open("wb") as output:
        with gzip.GzipFile(fileobj=output, mode="wb", mtime=0) as compressed:
            with tarfile.open(fileobj=compressed, mode="w") as archive:
                for source in files:
                    data = source.read_bytes()
                    info = tarfile.TarInfo(_archive_member(source, root, version))
                    info.size = len(data)
                    info.mode = 0o644
                    info.mtime = 0
                    archive.addfile(info, io.BytesIO(data))


def sha256(path: Path) -> str:
    digest = hashlib.sha256()
    with path.open("rb") as source:
        for chunk in iter(lambda: source.read(1024 * 1024), b""):
            digest.update(chunk)
    return digest.hexdigest()


def build_release(
    output: Path,
    root: Path = REPO_ROOT,
    repository: str | None = None,
) -> dict[str, object]:
    validate_release_readiness(root)
    root = root.resolve()
    _validate_output_path(output)
    output = Path(os.path.abspath(output))
    _validate_output_tree(output)
    output = output.resolve(strict=False)
    if output == root:
        raise ReleaseError("release output must be outside the repository root")
    version = read_version(root)
    tag = expected_tag(version)
    repo = repository_name(root, repository)
    output.mkdir(parents=True, exist_ok=True)
    files = release_files(root, output)

    zip_path = output / ARCHIVE_NAMES[0]
    tar_path = output / ARCHIVE_NAMES[1]
    _write_zip(zip_path, files, root, version)
    _write_tarball(tar_path, files, root, version)

    base_url = f"https://github.com/{repo}/releases/download/{tag}"
    release_url = f"https://github.com/{repo}/releases/tag/{tag}"
    assets = [
        {
            "name": name,
            "format": "zip" if name.endswith(".zip") else "tar.gz",
            "download_url": f"{base_url}/{name}",
            "sha256": sha256(output / name),
        }
        for name in ARCHIVE_NAMES
    ]
    manifest = {
        "schema_version": 1,
        "product": PRODUCT_ID,
        "version": version,
        "tag": tag,
        "channel": "stable",
        "installer_contract_version": INSTALLER_CONTRACT_VERSION,
        "release_url": release_url,
        "assets": assets,
    }
    manifest_path = output / MANIFEST_NAME
    manifest_path.write_text(
        json.dumps(manifest, ensure_ascii=False, indent=2) + "\n",
        encoding="utf-8",
    )

    checksum_paths = [output / name for name in (*ARCHIVE_NAMES, MANIFEST_NAME)]
    checksum_text = "".join(f"{sha256(path)}  {path.name}\n" for path in checksum_paths)
    (output / CHECKSUMS_NAME).write_text(checksum_text, encoding="utf-8")
    return {
        "product": PRODUCT_ID,
        "version": version,
        "tag": tag,
        "repository": repo,
        "output": output.as_posix(),
        "files": [name for name in (*ARCHIVE_NAMES, MANIFEST_NAME, CHECKSUMS_NAME)],
        "manifest": manifest,
    }


def build_parser() -> argparse.ArgumentParser:
    parser = argparse.ArgumentParser(prog="release.py")
    subparsers = parser.add_subparsers(dest="action", required=True)

    validate = subparsers.add_parser("validate", help="validate VERSION against a release tag")
    validate.add_argument("--tag", required=True)
    validate.add_argument("--format", choices=("json", "text"), default="text")

    build = subparsers.add_parser("build", help="build release archives and update metadata")
    build.add_argument("--output", type=Path, default=Path("dist"))
    build.add_argument("--repository")
    build.add_argument("--format", choices=("json", "text"), default="text")
    return parser


def main(argv: Sequence[str] | None = None) -> int:
    configure_utf8_stdio()
    args = build_parser().parse_args(argv)
    try:
        if args.action == "validate":
            version = validate_tag(args.tag)
            validate_release_readiness()
            payload = {"ok": True, "version": version, "tag": args.tag}
        else:
            payload = build_release(args.output.absolute(), repository=args.repository)
    except (ReleaseError, OSError, UnicodeError) as exc:
        print(f"release validation failed: {exc}")
        return 2

    if getattr(args, "format", "text") == "json":
        print(json.dumps(payload, ensure_ascii=False, sort_keys=True))
    else:
        print(json.dumps(payload, ensure_ascii=False, indent=2))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
