from __future__ import annotations

import hashlib
import sqlite3
from contextlib import closing
from pathlib import Path
from typing import Iterable, Mapping

from . import CONTRACT_VERSION
from .text import build_literal_query


SCHEMA_VERSION = 1


class IndexStore:
    def __init__(self, path: Path):
        self.path = Path(path)

    def _connect(self, readonly: bool = False) -> sqlite3.Connection:
        if readonly:
            uri = f"file:{self.path.resolve().as_posix()}?mode=ro"
            connection = sqlite3.connect(uri, uri=True)
        else:
            self.path.parent.mkdir(parents=True, exist_ok=True)
            connection = sqlite3.connect(self.path)
        connection.row_factory = sqlite3.Row
        connection.execute("PRAGMA busy_timeout=5000")
        if not readonly:
            connection.execute("PRAGMA journal_mode=WAL")
        return connection

    @staticmethod
    def fts5_available() -> bool:
        connection = sqlite3.connect(":memory:")
        try:
            connection.execute("CREATE VIRTUAL TABLE probe USING fts5(value)")
            return True
        except sqlite3.OperationalError:
            return False
        finally:
            connection.close()

    def initialize(self) -> None:
        if not self.fts5_available():
            raise RuntimeError("SQLite FTS5 is not available in this Python runtime")
        with closing(self._connect()) as connection:
            connection.executescript(
                """
                PRAGMA user_version = 1;
                CREATE TABLE IF NOT EXISTS meta (
                    key TEXT PRIMARY KEY,
                    value TEXT NOT NULL
                );
                CREATE TABLE IF NOT EXISTS documents (
                    id TEXT PRIMARY KEY,
                    kind TEXT NOT NULL,
                    path TEXT NOT NULL,
                    title TEXT NOT NULL DEFAULT '',
                    heading TEXT NOT NULL DEFAULT '',
                    body TEXT NOT NULL DEFAULT '',
                    terms TEXT NOT NULL DEFAULT '',
                    tags TEXT NOT NULL DEFAULT '',
                    language TEXT NOT NULL DEFAULT '',
                    name TEXT NOT NULL DEFAULT '',
                    qualified_name TEXT NOT NULL DEFAULT '',
                    signature TEXT NOT NULL DEFAULT '',
                    parse_quality TEXT NOT NULL DEFAULT '',
                    line_start INTEGER NOT NULL DEFAULT 1,
                    line_end INTEGER NOT NULL DEFAULT 1,
                    content_hash TEXT NOT NULL DEFAULT ''
                );
                CREATE VIRTUAL TABLE IF NOT EXISTS documents_fts USING fts5(
                    title, heading, body, terms, path, tags,
                    content='documents', content_rowid='rowid',
                    tokenize='unicode61 remove_diacritics 2 tokenchars ''_$''',
                    prefix='2 3'
                );
                CREATE TRIGGER IF NOT EXISTS documents_ai AFTER INSERT ON documents BEGIN
                    INSERT INTO documents_fts(rowid, title, heading, body, terms, path, tags)
                    VALUES (new.rowid, new.title, new.heading, new.body, new.terms, new.path, new.tags);
                END;
                CREATE TRIGGER IF NOT EXISTS documents_ad AFTER DELETE ON documents BEGIN
                    INSERT INTO documents_fts(documents_fts, rowid, title, heading, body, terms, path, tags)
                    VALUES ('delete', old.rowid, old.title, old.heading, old.body, old.terms, old.path, old.tags);
                END;
                CREATE TRIGGER IF NOT EXISTS documents_au AFTER UPDATE ON documents BEGIN
                    INSERT INTO documents_fts(documents_fts, rowid, title, heading, body, terms, path, tags)
                    VALUES ('delete', old.rowid, old.title, old.heading, old.body, old.terms, old.path, old.tags);
                    INSERT INTO documents_fts(rowid, title, heading, body, terms, path, tags)
                    VALUES (new.rowid, new.title, new.heading, new.body, new.terms, new.path, new.tags);
                END;
                """
            )
            connection.execute(
                "INSERT OR REPLACE INTO meta(key, value) VALUES ('schema_version', ?)",
                (str(SCHEMA_VERSION),),
            )
            connection.execute(
                "INSERT OR REPLACE INTO meta(key, value) VALUES ('contract_version', ?)",
                (str(CONTRACT_VERSION),),
            )
            connection.commit()

    def replace_documents(self, documents: Iterable[Mapping[str, object]]) -> int:
        rows = list(documents)
        self.initialize()
        with closing(self._connect()) as connection:
            connection.execute("BEGIN IMMEDIATE")
            connection.execute("DELETE FROM documents")
            for item in rows:
                body = str(item.get("body", ""))
                title = str(item.get("title", ""))
                heading = str(item.get("heading", ""))
                terms = str(item.get("terms", ""))
                content_hash = hashlib.sha256(
                    "\n".join((title, heading, body, terms)).encode("utf-8")
                ).hexdigest()
                connection.execute(
                    """
                    INSERT INTO documents(
                        id, kind, path, title, heading, body, terms, tags, language,
                        name, qualified_name, signature, parse_quality, line_start,
                        line_end, content_hash
                    ) VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
                    """,
                    (
                        str(item["id"]),
                        str(item.get("kind", "")),
                        str(item.get("path", "")),
                        title,
                        heading,
                        body,
                        terms,
                        str(item.get("tags", "")),
                        str(item.get("language", "")),
                        str(item.get("name", "")),
                        str(item.get("qualified_name", "")),
                        str(item.get("signature", "")),
                        str(item.get("parse_quality", "")),
                        int(item.get("line_start", 1)),
                        int(item.get("line_end", 1)),
                        content_hash,
                    ),
                )
            connection.execute("INSERT OR REPLACE INTO meta(key, value) VALUES ('generation', COALESCE((SELECT CAST(value AS INTEGER) + 1 FROM meta WHERE key = 'generation'), 1))")
            connection.commit()
        return len(rows)

    def search(self, query: str, limit: int = 20, kind: str | None = None) -> list[dict[str, object]]:
        expression = build_literal_query(query)
        if not expression or limit <= 0:
            return []
        with closing(self._connect(readonly=True)) as connection:
            rows = connection.execute(
                """
                SELECT d.id, d.kind, d.path, d.title, d.heading, d.language,
                       d.name, d.qualified_name, d.signature, d.parse_quality,
                       d.line_start, d.line_end,
                       snippet(documents_fts, 2, '<mark>', '</mark>', '…', 18) AS snippet,
                       bm25(documents_fts, 5.0, 4.0, 1.0, 2.0, 4.0, 3.0) AS rank
                FROM documents_fts
                JOIN documents AS d ON d.rowid = documents_fts.rowid
                WHERE documents_fts MATCH ? AND (? IS NULL OR d.kind = ?)
                ORDER BY rank, d.path, d.line_start
                LIMIT ?
                """,
                (expression, kind, kind, min(limit, 100)),
            ).fetchall()
        return [dict(row) for row in rows]

    def generation(self) -> int:
        if not self.path.exists():
            return 0
        with closing(self._connect(readonly=True)) as connection:
            value = connection.execute("SELECT value FROM meta WHERE key = 'generation'").fetchone()
        return int(value[0]) if value else 0

    def get(self, document_id: str) -> dict[str, object] | None:
        if not self.path.exists():
            return None
        with closing(self._connect(readonly=True)) as connection:
            row = connection.execute(
                "SELECT id, kind, path, title, heading, body, language, name, qualified_name, signature, parse_quality, line_start, line_end FROM documents WHERE id = ?",
                (document_id,),
            ).fetchone()
        return dict(row) if row else None
