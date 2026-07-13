from __future__ import annotations

import hashlib
import importlib
from pathlib import Path
from typing import Any

from .constants import SUPPORTED_LANGUAGES
from .text import build_terms


GRAMMARS = {
    "python": ("tree_sitter_python", "language"),
    "javascript": ("tree_sitter_javascript", "language"),
    "jsx": ("tree_sitter_javascript", "language"),
    "typescript": ("tree_sitter_typescript", "language_typescript"),
    "tsx": ("tree_sitter_typescript", "language_tsx"),
    "csharp": ("tree_sitter_c_sharp", "language"),
}


QUERIES = {
    "python": """
        (class_definition name: (identifier) @class_name)
        (function_definition name: (identifier) @function_name)
    """,
    "javascript": """
        (class_declaration name: (identifier) @class_name)
        (function_declaration name: (identifier) @function_name)
        (method_definition name: (property_identifier) @method_name)
    """,
    "jsx": """
        (class_declaration name: (identifier) @class_name)
        (function_declaration name: (identifier) @function_name)
    """,
    "typescript": """
        (class_declaration name: (type_identifier) @class_name)
        (function_declaration name: (identifier) @function_name)
        (interface_declaration name: (type_identifier) @interface_name)
        (type_alias_declaration name: (type_identifier) @type_name)
    """,
    "tsx": """
        (class_declaration name: (type_identifier) @class_name)
        (function_declaration name: (identifier) @function_name)
        (interface_declaration name: (type_identifier) @interface_name)
    """,
    "csharp": """
        (class_declaration name: (identifier) @class_name)
        (interface_declaration name: (identifier) @interface_name)
        (method_declaration name: (identifier) @method_name)
    """,
}


def _language(language_name: str):
    from tree_sitter import Language

    module_name, function_name = GRAMMARS[language_name]
    module = importlib.import_module(module_name)
    return Language(getattr(module, function_name)())


def _query_text(language_name: str) -> str:
    query_path = Path(__file__).resolve().parents[1] / "queries" / f"{language_name}.scm"
    if query_path.exists():
        return query_path.read_text(encoding="utf-8")
    return QUERIES[language_name]


def doctor_tree_sitter() -> dict[str, object]:
    result: dict[str, object] = {}
    for language_name in GRAMMARS:
        try:
            from tree_sitter import Parser, Query

            language = _language(language_name)
            Parser(language)
            Query(language, _query_text(language_name))
            result[language_name] = {"ok": True, "abi_version": language.abi_version}
        except (ImportError, AttributeError, RuntimeError, TypeError, ValueError) as exc:
            result[language_name] = {"ok": False, "error": str(exc)}
    return result


def extract_source_documents(path: Path, language: str | None = None) -> tuple[list[dict[str, Any]], list[dict[str, Any]]]:
    language = language or SUPPORTED_LANGUAGES.get(path.suffix.lower())
    if not language or language not in GRAMMARS:
        return [], [{"code": "unsupported_language", "path": path.as_posix()}]
    try:
        from tree_sitter import Parser, Query, QueryCursor

        language_object = _language(language)
        parser = Parser(language_object)
        source = path.read_bytes()
        tree = parser.parse(source)
        query = Query(language_object, _query_text(language))
        captures = QueryCursor(query).captures(tree.root_node)
    except (ImportError, AttributeError, RuntimeError, TypeError, ValueError) as exc:
        return [], [{"code": "tree_sitter_unavailable", "path": path.as_posix(), "detail": str(exc)}]

    diagnostics: list[dict[str, Any]] = []
    if tree.root_node.has_error:
        diagnostics.append({"code": "parse_error", "path": path.as_posix()})

    documents: list[dict[str, Any]] = []
    for capture_name, nodes in captures.items():
        kind = capture_name.removesuffix("_name")
        for node in nodes:
            name = source[node.start_byte : node.end_byte].decode("utf-8", errors="replace")
            line = node.start_point[0] + 1
            identifier = hashlib.sha256(
                f"{path.as_posix()}:{kind}:{name}:{line}".encode("utf-8")
            ).hexdigest()[:24]
            documents.append(
                {
                    "id": f"source:{identifier}",
                    "kind": "symbol",
                    "path": path.as_posix(),
                    "title": name,
                    "heading": kind,
                    "body": name,
                    "terms": build_terms(name, kind, path.as_posix()),
                    "language": language,
                    "name": name,
                    "qualified_name": name,
                    "signature": source[node.parent.start_byte : node.parent.end_byte]
                    .decode("utf-8", errors="replace")
                    .splitlines()[0][:500],
                    "parse_quality": "tree_sitter",
                    "line_start": line,
                    "line_end": node.end_point[0] + 1,
                }
            )
    return documents, diagnostics
