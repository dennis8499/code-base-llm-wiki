#!/usr/bin/env python3
"""Optional source structure indexer for Codebase LLM Wiki.

The indexer never writes wiki pages or source files. It emits a stable JSON
summary that ingest, query, and lint workflows can use as pre-scan evidence.
Tree-sitter parsing is attempted when bindings and language parsers are
available; otherwise the script falls back to lightweight text extraction and
reports the fallback in `unsupported_reason` and `warnings`.
"""

from __future__ import annotations

import argparse
import ast
import datetime as _datetime
import importlib
import json
from pathlib import Path
import re
import sys
from typing import Any, Iterable


VERSION = "1.0"
SUPPORTED_EXTENSIONS = {
    ".ts": "typescript",
    ".tsx": "typescript",
    ".js": "javascript",
    ".jsx": "javascript",
    ".py": "python",
    ".cs": "csharp",
}
SKIP_DIRS = {
    ".git",
    ".hg",
    ".svn",
    ".venv",
    "venv",
    "node_modules",
    "__pycache__",
    "bin",
    "obj",
    "dist",
    "build",
}
TREE_SITTER_PACKAGES = {
    "python": [("tree_sitter_python", "language")],
    "javascript": [("tree_sitter_javascript", "language")],
    "typescript": [
        ("tree_sitter_typescript", "language_typescript"),
        ("tree_sitter_typescript", "language_tsx"),
    ],
    "csharp": [("tree_sitter_c_sharp", "language")],
}


TS_IMPORT_FROM_RE = re.compile(r"^\s*import\s+(?:type\s+)?(?:.+?\s+from\s+)?[\"']([^\"']+)[\"']")
TS_EXPORT_FROM_RE = re.compile(r"^\s*export\s+.+?\s+from\s+[\"']([^\"']+)[\"']")
TS_REQUIRE_RE = re.compile(r"\brequire\(\s*[\"']([^\"']+)[\"']\s*\)")
TS_CLASS_RE = re.compile(r"\b(?:export\s+)?(?:abstract\s+)?class\s+([A-Za-z_$][\w$]*)")
TS_INTERFACE_RE = re.compile(r"\b(?:export\s+)?interface\s+([A-Za-z_$][\w$]*)")
TS_TYPE_RE = re.compile(r"\b(?:export\s+)?type\s+([A-Za-z_$][\w$]*)\s*=")
TS_FUNCTION_RE = re.compile(r"\b(?:export\s+)?(?:async\s+)?function\s+([A-Za-z_$][\w$]*)\s*\(")
TS_ARROW_FUNCTION_RE = re.compile(r"\b(?:export\s+)?(?:const|let|var)\s+([A-Za-z_$][\w$]*)\s*=\s*(?:async\s*)?\([^)]*\)\s*=>")
TS_METHOD_RE = re.compile(r"^\s*(?:(?:public|private|protected|static|async|readonly)\s+)*([A-Za-z_$][\w$]*)\s*\([^)]*\)\s*(?::[^{]+)?\{?\s*$")
TS_ROUTE_RE = re.compile(r"\b(router|app)\.(get|post|put|delete|patch)\(\s*[\"']([^\"']+)[\"']", re.IGNORECASE)
TS_SCHEMA_RE = re.compile(r"\b(?:export\s+)?(?:const|let|var)\s+([A-Za-z_$][\w$]*)\s*=\s*(?:z\.object|new\s+Schema)\b")

PY_IMPORT_RE = re.compile(r"^\s*import\s+([A-Za-z_][\w.]*)")
PY_FROM_RE = re.compile(r"^\s*from\s+([A-Za-z_][\w.]*)\s+import\s+(.+)")
PY_CLASS_RE = re.compile(r"^\s*class\s+([A-Za-z_]\w*)\s*(?:\(([^)]*)\))?:")
PY_FUNCTION_RE = re.compile(r"^\s*(?:async\s+)?def\s+([A-Za-z_]\w*)\s*\(")
PY_ROUTE_RE = re.compile(r"^\s*@(?:\w+\.)?(?:router|app)\.(get|post|put|delete|patch)\(\s*[\"']([^\"']+)[\"']", re.IGNORECASE)
PY_ALL_RE = re.compile(r"__all__\s*=\s*\[([^\]]*)\]")

CS_USING_RE = re.compile(r"^\s*using\s+([A-Za-z_][\w.]*)\s*;")
CS_TYPE_RE = re.compile(r"\b(?:(?:public|internal|private|protected)\s+)?(?:partial\s+)?(class|record|interface|enum|struct)\s+([A-Za-z_]\w*)")
CS_METHOD_RE = re.compile(
    r"^\s*(?:public|private|protected|internal)\s+"
    r"(?:static\s+)?(?:async\s+)?[A-Za-z_][\w.<>,\[\]?]*\s+([A-Za-z_]\w*)\s*\("
)
CS_ROUTE_RE = re.compile(r"^\s*\[(Route|HttpGet|HttpPost|HttpPut|HttpDelete|HttpPatch)(?:\(\s*[\"']([^\"']*)[\"']\s*\))?\]", re.IGNORECASE)


def configure_utf8_stdio() -> None:
    for stream in (sys.stdout, sys.stderr):
        try:
            stream.reconfigure(encoding="utf-8")
        except Exception:
            pass


def utc_now() -> str:
    value = _datetime.datetime.now(_datetime.timezone.utc).replace(microsecond=0)
    return value.isoformat().replace("+00:00", "Z")


def repo_relative(path: Path, repo_root: Path) -> str:
    try:
        return path.resolve().relative_to(repo_root.resolve()).as_posix()
    except ValueError:
        try:
            return path.resolve().relative_to(Path.cwd().resolve()).as_posix()
        except ValueError:
            return path.as_posix()


def unique_append(items: list[dict[str, Any]], item: dict[str, Any], keys: tuple[str, ...] = ("name", "line", "kind")) -> None:
    signature = tuple(item.get(key) for key in keys)
    for existing in items:
        if tuple(existing.get(key) for key in keys) == signature:
            return
    items.append(item)


def unique_import(items: list[dict[str, Any]], target: str, line: int, kind: str) -> None:
    unique_append(items, {"target": target, "line": line, "kind": kind}, ("target", "line", "kind"))


def symbol(name: str, line: int, kind: str) -> dict[str, Any]:
    return {"name": name, "line": line, "kind": kind}


def route(method: str, path: str, line: int, source: str) -> dict[str, Any]:
    return {"method": method.upper(), "path": path, "line": line, "source": source}


def iter_source_files(target: Path) -> Iterable[Path]:
    if target.is_file():
        yield target
        return

    for path in sorted(target.rglob("*")):
        if not path.is_file():
            continue
        if any(part in SKIP_DIRS for part in path.parts):
            continue
        yield path


def detect_language(path: Path) -> str:
    return SUPPORTED_EXTENSIONS.get(path.suffix.lower(), "unsupported")


def load_tree_sitter_parser(language: str) -> tuple[Any | None, str]:
    if language not in TREE_SITTER_PACKAGES:
        return None, "tree_sitter_language_not_configured"

    try:
        from tree_sitter import Language, Parser  # type: ignore
    except Exception:
        return None, "tree_sitter_unavailable"

    errors: list[str] = []
    for module_name, function_name in TREE_SITTER_PACKAGES[language]:
        try:
            module = importlib.import_module(module_name)
            language_factory = getattr(module, function_name)
            raw_language = language_factory()
            try:
                tree_sitter_language = Language(raw_language)
            except Exception:
                tree_sitter_language = raw_language

            parser = Parser()
            if hasattr(parser, "set_language"):
                parser.set_language(tree_sitter_language)
            else:
                parser.language = tree_sitter_language
            return parser, ""
        except Exception as exc:
            errors.append(f"{module_name}.{function_name}: {exc}")

    if errors:
        return None, "tree_sitter_parser_unavailable"
    return None, "tree_sitter_parser_unavailable"


def collect_tree_sitter_errors(parser: Any, text: str) -> list[dict[str, Any]]:
    try:
        tree = parser.parse(text.encode("utf-8"))
        root = tree.root_node
    except Exception as exc:
        return [{"line": 1, "column": 1, "message": f"tree-sitter parse failed: {exc}", "source": "tree_sitter"}]

    errors: list[dict[str, Any]] = []
    stack = [root]
    while stack:
        node = stack.pop()
        node_type = getattr(node, "type", "")
        is_missing = bool(getattr(node, "is_missing", False))
        is_error = node_type == "ERROR" or is_missing
        if is_error:
            point = getattr(node, "start_point", None)
            line = getattr(point, "row", 0) + 1 if point is not None else 1
            column = getattr(point, "column", 0) + 1 if point is not None else 1
            errors.append({
                "line": line,
                "column": column,
                "message": f"{'missing ' if is_missing else ''}{node_type or 'syntax error'}",
                "source": "tree_sitter",
            })
        stack.extend(reversed(getattr(node, "children", [])))
    return errors


def fallback_parse_errors(language: str, text: str) -> list[dict[str, Any]]:
    if language == "python":
        try:
            ast.parse(text)
        except SyntaxError as exc:
            return [{
                "line": exc.lineno or 1,
                "column": exc.offset or 1,
                "message": exc.msg,
                "source": "python_ast",
            }]
        return []

    opening = {"(": ")", "{": "}", "[": "]"}
    closing = {")": "(", "}": "{", "]": "["}
    stack: list[tuple[str, int, int]] = []
    errors: list[dict[str, Any]] = []

    for line_number, line in enumerate(text.splitlines(), start=1):
        for column, char in enumerate(line, start=1):
            if char in opening:
                stack.append((char, line_number, column))
            elif char in closing:
                if not stack or stack[-1][0] != closing[char]:
                    errors.append({
                        "line": line_number,
                        "column": column,
                        "message": f"unmatched closing delimiter {char}",
                        "source": "text_balance",
                    })
                else:
                    stack.pop()

    for char, line_number, column in stack:
        errors.append({
            "line": line_number,
            "column": column,
            "message": f"unclosed delimiter {char}",
            "source": "text_balance",
        })
    return errors


def resolve_relative_import(source: Path, target: str) -> str | None:
    if not target.startswith("."):
        return None

    base = (source.parent / target).resolve()
    candidates = [
        base,
        base.with_suffix(".ts"),
        base.with_suffix(".tsx"),
        base.with_suffix(".js"),
        base.with_suffix(".jsx"),
        base / "index.ts",
        base / "index.tsx",
        base / "index.js",
        base / "index.jsx",
    ]
    for candidate in candidates:
        if candidate.exists():
            return repo_relative(candidate, Path.cwd())
    return None


def extract_typescript(text: str, path: Path) -> dict[str, list[dict[str, Any]]]:
    imports: list[dict[str, Any]] = []
    exports: list[dict[str, Any]] = []
    classes: list[dict[str, Any]] = []
    functions: list[dict[str, Any]] = []
    routes: list[dict[str, Any]] = []
    schemas: list[dict[str, Any]] = []

    for line_number, line in enumerate(text.splitlines(), start=1):
        for pattern, kind in ((TS_IMPORT_FROM_RE, "import"), (TS_EXPORT_FROM_RE, "export_from"), (TS_REQUIRE_RE, "require")):
            match = pattern.search(line)
            if match:
                unique_import(imports, match.group(1), line_number, kind)

        class_match = TS_CLASS_RE.search(line)
        if class_match:
            name = class_match.group(1)
            unique_append(classes, symbol(name, line_number, "class"))
            if "export" in line:
                unique_append(exports, symbol(name, line_number, "class"))

        for pattern, kind in ((TS_INTERFACE_RE, "interface"), (TS_TYPE_RE, "type")):
            match = pattern.search(line)
            if match:
                name = match.group(1)
                unique_append(schemas, symbol(name, line_number, kind))
                if "export" in line:
                    unique_append(exports, symbol(name, line_number, kind))

        for pattern, kind in ((TS_FUNCTION_RE, "function"), (TS_ARROW_FUNCTION_RE, "arrow_function"), (TS_METHOD_RE, "method")):
            match = pattern.search(line)
            if not match:
                continue
            name = match.group(1)
            if name in {"if", "for", "while", "switch", "catch", "return"}:
                continue
            unique_append(functions, symbol(name, line_number, kind))
            if "export" in line:
                unique_append(exports, symbol(name, line_number, kind))

        schema_match = TS_SCHEMA_RE.search(line)
        if schema_match:
            name = schema_match.group(1)
            unique_append(schemas, symbol(name, line_number, "schema"))
            if "export" in line:
                unique_append(exports, symbol(name, line_number, "schema"))

        route_match = TS_ROUTE_RE.search(line)
        if route_match:
            routes.append(route(route_match.group(2), route_match.group(3), line_number, route_match.group(1)))

    return {
        "imports": imports,
        "exports": exports,
        "classes": classes,
        "functions": functions,
        "routes": routes,
        "schemas": schemas,
    }


def extract_python(text: str) -> dict[str, list[dict[str, Any]]]:
    imports: list[dict[str, Any]] = []
    exports: list[dict[str, Any]] = []
    classes: list[dict[str, Any]] = []
    functions: list[dict[str, Any]] = []
    routes: list[dict[str, Any]] = []
    schemas: list[dict[str, Any]] = []
    pending_dataclass = False

    for line_number, line in enumerate(text.splitlines(), start=1):
        import_match = PY_IMPORT_RE.search(line)
        if import_match:
            unique_import(imports, import_match.group(1), line_number, "import")
        from_match = PY_FROM_RE.search(line)
        if from_match:
            unique_import(imports, from_match.group(1), line_number, "from")

        if line.strip() == "@dataclass":
            pending_dataclass = True

        class_match = PY_CLASS_RE.search(line)
        if class_match:
            name = class_match.group(1)
            bases = class_match.group(2) or ""
            unique_append(classes, symbol(name, line_number, "class"))
            if pending_dataclass or "BaseModel" in bases or name.endswith(("Dto", "DTO", "Model", "Request", "Response")):
                unique_append(schemas, symbol(name, line_number, "schema"))
            pending_dataclass = False

        function_match = PY_FUNCTION_RE.search(line)
        if function_match:
            unique_append(functions, symbol(function_match.group(1), line_number, "function"))

        route_match = PY_ROUTE_RE.search(line)
        if route_match:
            routes.append(route(route_match.group(1), route_match.group(2), line_number, "decorator"))

        all_match = PY_ALL_RE.search(line)
        if all_match:
            for exported in re.findall(r"[\"']([^\"']+)[\"']", all_match.group(1)):
                unique_append(exports, symbol(exported, line_number, "__all__"))

    return {
        "imports": imports,
        "exports": exports,
        "classes": classes,
        "functions": functions,
        "routes": routes,
        "schemas": schemas,
    }


def extract_csharp(text: str) -> dict[str, list[dict[str, Any]]]:
    imports: list[dict[str, Any]] = []
    exports: list[dict[str, Any]] = []
    classes: list[dict[str, Any]] = []
    functions: list[dict[str, Any]] = []
    routes: list[dict[str, Any]] = []
    schemas: list[dict[str, Any]] = []

    for line_number, line in enumerate(text.splitlines(), start=1):
        using_match = CS_USING_RE.search(line)
        if using_match:
            unique_import(imports, using_match.group(1), line_number, "using")

        type_match = CS_TYPE_RE.search(line)
        if type_match:
            kind = type_match.group(1)
            name = type_match.group(2)
            unique_append(classes, symbol(name, line_number, kind))
            if "public" in line:
                unique_append(exports, symbol(name, line_number, kind))
            if kind == "record" or name.endswith(("Dto", "DTO", "Model", "Request", "Response", "Entity")):
                unique_append(schemas, symbol(name, line_number, kind))

        method_match = None if type_match else CS_METHOD_RE.search(line)
        if method_match:
            unique_append(functions, symbol(method_match.group(1), line_number, "method"))

        route_match = CS_ROUTE_RE.search(line)
        if route_match:
            attribute = route_match.group(1)
            route_path = route_match.group(2) or ""
            method = "ROUTE" if attribute.lower() == "route" else attribute[4:].upper()
            routes.append(route(method, route_path, line_number, "attribute"))

    return {
        "imports": imports,
        "exports": exports,
        "classes": classes,
        "functions": functions,
        "routes": routes,
        "schemas": schemas,
    }


def empty_extract() -> dict[str, list[dict[str, Any]]]:
    return {
        "imports": [],
        "exports": [],
        "classes": [],
        "functions": [],
        "routes": [],
        "schemas": [],
    }


def extract_structure(language: str, text: str, path: Path) -> dict[str, list[dict[str, Any]]]:
    if language in {"typescript", "javascript"}:
        return extract_typescript(text, path)
    if language == "python":
        return extract_python(text)
    if language == "csharp":
        return extract_csharp(text)
    return empty_extract()


def build_dependency_edges(file_entry: dict[str, Any], path: Path) -> list[dict[str, Any]]:
    edges: list[dict[str, Any]] = []
    for item in file_entry["imports"]:
        target = item["target"]
        edge = {
            "source": file_entry["path"],
            "target": target,
            "kind": item["kind"],
            "line": item["line"],
        }
        resolved = resolve_relative_import(path, str(target))
        if resolved:
            edge["resolved_path"] = resolved
        edges.append(edge)
    return edges


def index_file(path: Path, repo_root: Path, parser_cache: dict[str, tuple[Any | None, str]]) -> tuple[dict[str, Any], list[dict[str, Any]]]:
    warnings: list[dict[str, Any]] = []
    language = detect_language(path)
    rel_path = repo_relative(path, repo_root)
    unsupported_reason = ""

    try:
        text = path.read_text(encoding="utf-8")
    except UnicodeDecodeError:
        text = path.read_text(encoding="utf-8", errors="replace")
        warnings.append({"path": rel_path, "code": "encoding_replacement", "message": "File contained invalid UTF-8 bytes; replacement characters were used."})

    if language == "unsupported":
        unsupported_reason = "unsupported_extension"
        parse_errors: list[dict[str, Any]] = []
        extracted = empty_extract()
    else:
        if language not in parser_cache:
            parser_cache[language] = load_tree_sitter_parser(language)
        parser, parser_reason = parser_cache[language]

        if parser is not None:
            parse_errors = collect_tree_sitter_errors(parser, text)
            unsupported_reason = "tree_sitter_parse_error" if parse_errors else ""
        else:
            unsupported_reason = parser_reason or "tree_sitter_parser_unavailable"
            parse_errors = fallback_parse_errors(language, text)
            warnings.append({
                "path": rel_path,
                "code": unsupported_reason,
                "message": f"Tree-sitter parser unavailable for {language}; using text fallback.",
            })

        extracted = extract_structure(language, text, path)

    file_entry: dict[str, Any] = {
        "path": rel_path,
        "language": language,
        "imports": extracted["imports"],
        "exports": extracted["exports"],
        "classes": extracted["classes"],
        "functions": extracted["functions"],
        "routes": extracted["routes"],
        "schemas": extracted["schemas"],
        "parse_errors": parse_errors,
        "unsupported_reason": unsupported_reason,
    }
    return file_entry, warnings


def summarize_languages(files: list[dict[str, Any]]) -> dict[str, dict[str, Any]]:
    languages: dict[str, dict[str, Any]] = {}
    for item in files:
        language = item["language"]
        entry = languages.setdefault(language, {
            "files": 0,
            "files_with_parse_errors": 0,
            "files_with_tree_sitter": 0,
            "files_with_fallback": 0,
        })
        entry["files"] += 1
        if item["parse_errors"]:
            entry["files_with_parse_errors"] += 1
        reason = item["unsupported_reason"]
        if reason:
            entry["files_with_fallback"] += 1
        elif language != "unsupported":
            entry["files_with_tree_sitter"] += 1
    return languages


def build_index(target: Path, repo_root: Path) -> dict[str, Any]:
    files: list[dict[str, Any]] = []
    dependency_edges: list[dict[str, Any]] = []
    warnings: list[dict[str, Any]] = []
    parser_cache: dict[str, tuple[Any | None, str]] = {}

    if not target.exists():
        warnings.append({"path": str(target), "code": "target_not_found", "message": "Target path does not exist."})
    else:
        for path in iter_source_files(target):
            entry, file_warnings = index_file(path, repo_root, parser_cache)
            files.append(entry)
            warnings.extend(file_warnings)
            dependency_edges.extend(build_dependency_edges(entry, path))

    return {
        "version": VERSION,
        "target_path": repo_relative(target, repo_root) if target.exists() else str(target),
        "generated_at": utc_now(),
        "languages": summarize_languages(files),
        "files": files,
        "dependency_edges": dependency_edges,
        "warnings": warnings,
    }


def parse_args(argv: list[str]) -> argparse.Namespace:
    parser = argparse.ArgumentParser(description="Emit a JSON source structure index for wiki workflows.")
    parser.add_argument("target_path", help="Source file or directory to scan.")
    parser.add_argument("--format", choices=["json"], default="json", help="Output format. Only json is currently supported.")
    parser.add_argument("--repo-root", default=".", help="Repo root used for relative paths. Defaults to current directory.")
    return parser.parse_args(argv)


def main(argv: list[str] | None = None) -> int:
    configure_utf8_stdio()
    args = parse_args(argv or sys.argv[1:])
    repo_root = Path(args.repo_root).resolve()
    target = Path(args.target_path)
    if not target.is_absolute():
        target = (Path.cwd() / target).resolve()

    payload = build_index(target, repo_root)
    print(json.dumps(payload, ensure_ascii=False, indent=2))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
