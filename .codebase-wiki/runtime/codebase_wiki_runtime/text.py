from __future__ import annotations

import re


_CJK_RE = re.compile(r"[\u3400-\u4dbf\u4e00-\u9fff\uf900-\ufaff]")
_IDENTIFIER_RE = re.compile(r"[A-Za-z_$][A-Za-z0-9_$]*")
_CAMEL_BOUNDARY_RE = re.compile(r"(?<=[a-z0-9])(?=[A-Z])")


def _cjk_bigrams(value: str) -> list[str]:
    terms: list[str] = []
    run: list[str] = []
    for char in value:
        if _CJK_RE.fullmatch(char):
            run.append(char)
            continue
        if len(run) >= 2:
            terms.extend("".join(run[index : index + 2]) for index in range(len(run) - 1))
        run = []
    if len(run) >= 2:
        terms.extend("".join(run[index : index + 2]) for index in range(len(run) - 1))
    return terms


def build_terms(*values: str) -> str:
    """Create deterministic FTS aliases for mixed natural/code text."""

    terms: list[str] = []
    for value in values:
        if not value:
            continue
        terms.extend(value.split())
        terms.extend(_cjk_bigrams(value))
        for identifier in _IDENTIFIER_RE.findall(value):
            terms.append(identifier)
            terms.extend(part for part in re.split(r"[_$-]+", identifier) if part)
            terms.extend(part for part in _CAMEL_BOUNDARY_RE.split(identifier) if part)
    return " ".join(dict.fromkeys(term for term in terms if term))


def build_literal_query(value: str) -> str:
    """Build a quoted FTS5 expression without exposing MATCH operators."""
    raw_tokens = re.findall(r"[A-Za-z0-9_$.-]+|[\u3400-\u4dbf\u4e00-\u9fff\uf900-\ufaff]+", value)
    words: list[str] = []
    for raw_token in raw_tokens:
        if raw_token and all(_CJK_RE.fullmatch(char) for char in raw_token):
            if len(raw_token) == 1:
                words.append(raw_token)
            else:
                words.extend(raw_token[index : index + 2] for index in range(len(raw_token) - 1))
        else:
            words.append(raw_token)
    if not words:
        return ""
    return " AND ".join('"' + word.replace('"', '""') + '"' for word in words)
