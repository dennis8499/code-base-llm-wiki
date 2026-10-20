"""One Wiki writer, full-snapshot compare-and-swap and recoverable file commits."""
from __future__ import annotations

import hashlib
import json
import os
from pathlib import Path, PurePosixPath
import re
import shutil
import tempfile

from frontmatter import is_reparse_point, validate_regular_tree


class WikiConflict(ValueError):
    """Refresh the preview; no competing Wiki edit may be overwritten."""


class _Lock:
    def __init__(self, root):
        self.path = root / ".codebase-wiki-write.lock"

    def __enter__(self):
        if is_reparse_point(self.path):
            raise WikiConflict("Wiki lock is a link boundary")
        self.fd = os.open(self.path, os.O_CREAT | os.O_RDWR, 0o600)
        try:
            if os.name == "nt":
                import msvcrt
                if os.fstat(self.fd).st_size == 0:
                    os.write(self.fd, b"\0")
                os.lseek(self.fd, 0, os.SEEK_SET)
                msvcrt.locking(self.fd, msvcrt.LK_NBLCK, 1)
            else:
                import fcntl
                fcntl.flock(self.fd, fcntl.LOCK_EX | fcntl.LOCK_NB)
        except BaseException:
            os.close(self.fd)
            raise WikiConflict("another writer owns this Wiki; retry after refreshing its snapshot") from None
        return self

    def __exit__(self, *args):
        os.close(self.fd)


def _digest(data: bytes | None):
    return hashlib.sha256(data).hexdigest() if data is not None else None


def _path(root: Path, relative: str) -> Path:
    pure = PurePosixPath(relative)
    if (not relative or relative != pure.as_posix() or "\\" in relative or pure.is_absolute() or
        any(part in {".", ".."} or ":" in part for part in pure.parts) or
        len(pure.parts) < 2 or pure.parts[0] != "wiki"):
        raise WikiConflict(f"write must be a regular Wiki file: {relative}")
    path = root
    for part in pure.parts:
        path /= part
        if is_reparse_point(path):
            raise WikiConflict(f"Wiki link boundary: {relative}")
    path.resolve().relative_to(root.resolve())
    if path.exists() and not path.is_file():
        raise WikiConflict(f"Wiki destination is not a file: {relative}")
    return path


def _bytes(path):
    return path.read_bytes() if path.exists() else None


def snapshot(root: Path) -> dict[str, str]:
    root = Path(root).absolute()
    validate_regular_tree(root / "wiki")
    result = {}
    for path in sorted((root / "wiki").rglob("*")):
        if path.is_file():
            digest = hashlib.sha256()
            with path.open("rb") as stream:
                for chunk in iter(lambda: stream.read(1024 * 1024), b""):
                    digest.update(chunk)
            result[path.relative_to(root).as_posix()] = digest.hexdigest()
    return result


def _atomic_json(path: Path, value):
    fd, name = tempfile.mkstemp(prefix=path.name + ".", dir=path.parent)
    temporary = Path(name)
    try:
        with os.fdopen(fd, "wb") as stream:
            stream.write((json.dumps(value, ensure_ascii=False, sort_keys=True) + "\n").encode("utf-8"))
            stream.flush()
            os.fsync(stream.fileno())
        os.replace(temporary, path)
    finally:
        temporary.unlink(missing_ok=True)


def _recover(root: Path) -> bool:
    journal = root / ".codebase-wiki-write.transaction.json"
    if is_reparse_point(journal):
        raise WikiConflict("Wiki journal is a link boundary")
    if not journal.exists():
        return False
    value = json.loads(journal.read_text(encoding="utf-8"))
    stage_name = value.get("stage", "")
    if (value.get("schema") != "codebase-wiki-write/v1" or value.get("phase") not in {"active", "committed"} or
        not isinstance(stage_name, str) or not re.fullmatch(r"\.codebase-wiki-write\.[A-Za-z0-9_-]+", stage_name)):
        raise WikiConflict("unrecognized Wiki recovery journal")
    stage = root / stage_name
    validate_regular_tree(stage)
    rows = value.get("files")
    if not isinstance(rows, dict) or not rows:
        raise WikiConflict("invalid Wiki recovery file inventory")
    # Check all candidates before restoring any file. A user's edit made
    # after a crash must remain a visible conflict, including during recovery.
    for relative, hashes in rows.items():
        path = _path(root, relative)
        if not isinstance(hashes, dict) or set(hashes) != {"before", "after"}:
            raise WikiConflict("invalid Wiki recovery hashes")
        current = _digest(_bytes(path))
        if current not in {hashes["before"], hashes["after"]}:
            raise WikiConflict(f"Wiki recovery conflicts with a newer edit: {relative}")
        backup = stage / "before" / relative
        if _digest(_bytes(backup)) != hashes["before"]:
            raise WikiConflict(f"Wiki recovery backup changed: {relative}")
    if value["phase"] == "active":
        for relative, hashes in rows.items():
            path = _path(root, relative)
            if hashes["before"] is None:
                path.unlink(missing_ok=True)
            else:
                path.parent.mkdir(parents=True, exist_ok=True)
                # Copy so another interruption can repeat the same recovery.
                temporary = stage / "restore"
                shutil.copyfile(stage / "before" / relative, temporary)
                os.replace(temporary, path)
    shutil.rmtree(stage)
    journal.unlink()
    return True


def _append_log(previous: bytes, addition: bytes) -> bytes:
    text = addition.decode("utf-8")
    match = re.match(r"\s*## \[(\d{4}-\d{2}-\d{2})\] ([a-z-]+) \| \S", text)
    if not match or not re.search(r"(?:Affected pages:|受影響頁面：).*\[\[.+?\]\]", text):
        raise WikiConflict("log_append requires a dated operation and affected-page wikilinks")
    if re.search(r"^## ", text[match.end():], re.MULTILINE):
        raise WikiConflict("append exactly one Wiki log operation per transaction")
    import datetime
    datetime.date.fromisoformat(match[1])
    if match[2] not in {"ingest", "query", "lint", "update", "init", "adr", "synthesis", "archaeology"}:
        raise WikiConflict("unsupported Wiki log operation")
    # Only the frontmatter date can change. The complete old body stays intact.
    old = previous.decode("utf-8")
    header = re.match(r"\A---\r?\n.*?\r?\n---(?:\r?\n)?", old, re.DOTALL)
    if not header:
        raise WikiConflict("existing Wiki log has no valid frontmatter")
    dates = re.findall(r"^## \[(\d{4}-\d{2}-\d{2})\]", old[header.end():], re.MULTILINE)
    if dates and match[1] < max(dates):
        raise WikiConflict("log operation date precedes existing history")
    prefix = re.sub(r"(?m)^(last_updated:\s*)\d{4}-\d{2}-\d{2}", lambda m: m[1] + match[1], header[0])
    return prefix.encode("utf-8") + previous[len(header[0].encode("utf-8")):] + b"\n\n" + addition.strip() + b"\n"


def commit(root: Path, writes: dict[str, bytes | None], expected: dict[str, str], *, log_append: bytes) -> dict:
    root = Path(root).absolute()
    if is_reparse_point(root) or root.resolve() != root:
        raise WikiConflict("Wiki root must have no link ancestors")
    with _Lock(root):
        _recover(root)
        if snapshot(root) != expected:
            raise WikiConflict("Wiki changed after the preview; refresh and preserve the newer content")
        if not writes or "wiki/log.md" in writes:
            raise WikiConflict("provide Wiki changes and append the log through log_append")
        if any(path != "wiki/index.md" for path in writes) and "wiki/index.md" not in writes:
            raise WikiConflict("Wiki page changes require the index in the same transaction")
        if writes.get("wiki/index.md", b"") is None or len({path.casefold() for path in writes}) != len(writes):
            raise WikiConflict("preserve the Wiki index and use unique portable paths")
        paths = {relative: _path(root, relative) for relative in writes}
        log_path = _path(root, "wiki/log.md")
        old_log = _bytes(log_path)
        if old_log is None:
            date = re.search(rb"## \[(\d{4}-\d{2}-\d{2})\]", log_append)
            if date is None:
                raise WikiConflict("log_append requires a dated operation")
            old_log = (b"---\ntitle: Wiki Log\ntype: log\nsources: []\nlast_updated: " + date[1] +
                       b"\ntags: [log]\nstatus: active\n---\n\n# Wiki Log\n\n<!-- codebase-wiki:log-contract-v1 -->\n")
        writes = {**writes, "wiki/log.md": _append_log(old_log, log_append)}
        paths["wiki/log.md"] = log_path
        stage = Path(tempfile.mkdtemp(prefix=".codebase-wiki-write.", dir=root))
        journal = root / ".codebase-wiki-write.transaction.json"
        rows = {}
        try:
            for relative, after in writes.items():
                if after is not None and not isinstance(after, bytes):
                    raise WikiConflict("Wiki write contents must be bytes or deletion")
                before = _bytes(paths[relative])
                rows[relative] = {"before": _digest(before), "after": _digest(after)}
                for kind, data in (("before", before), ("after", after)):
                    if data is not None:
                        target = stage / kind / relative
                        target.parent.mkdir(parents=True, exist_ok=True)
                        target.write_bytes(data)
            value = {"schema": "codebase-wiki-write/v1", "phase": "active", "stage": stage.name, "files": rows}
            _atomic_json(journal, value)
            try:
                for relative, data in writes.items():
                    path = paths[relative]
                    # Include index and log in the same CAS scope. Detect edits
                    # by tools that do not participate in our writer lock.
                    if _digest(_bytes(path)) != rows[relative]["before"]:
                        raise WikiConflict(f"Wiki file changed during commit: {relative}")
                    if data is None:
                        path.unlink(missing_ok=True)
                    else:
                        path.parent.mkdir(parents=True, exist_ok=True)
                        os.replace(stage / "after" / relative, path)
                _atomic_json(journal, {**value, "phase": "committed"})
            except BaseException:
                _recover(root)
                raise
            _recover(root)
        finally:
            if not journal.exists() and stage.exists():
                shutil.rmtree(stage)
        return {"ok": True, "files": sorted(writes), "snapshot": snapshot(root)}
