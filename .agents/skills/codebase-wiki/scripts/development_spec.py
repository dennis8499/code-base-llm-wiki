"""Structural checks and recorded (not automated) semantic review for specifications."""
from __future__ import annotations

import hashlib
import json
import re
from urllib.parse import unquote

from frontmatter import FRONTMATTER_PATTERN, parse_frontmatter_text

SECTIONS = ("目的與範圍", "適用專案", "功能行為與限制", "相依契約與確認決策", "驗收情境")


def body_text(text: str) -> str:
    return FRONTMATTER_PATTERN.sub("", text.replace("\r\n", "\n"), count=1).strip() + "\n"


def prose_text(text: str) -> str:
    """Keep line numbers while ignoring code examples and comments as instructions."""
    result: list[str] = []
    fence = ""
    for line in text.splitlines():
        marker = re.match(r"^\s*(`{3,}|~{3,})", line)
        if marker:
            if not fence:
                fence = marker[1]
            elif marker[1][0] == fence[0] and len(marker[1]) >= len(fence):
                fence = ""
            result.append("")
        else:
            result.append("" if fence else line)
    return re.sub(r"<!--.*?-->", "", "\n".join(result), flags=re.S)


def review_digest(text: str) -> str:
    payload = {"spec_revision": str(parse_frontmatter_text(text).get("spec_revision", "")), "body": body_text(text)}
    return "sha256:" + hashlib.sha256(json.dumps(payload, ensure_ascii=False, sort_keys=True).encode("utf-8")).hexdigest()


def structural_errors(text: str, sections: tuple[str, ...] = SECTIONS, *, portable: bool = False) -> list[str]:
    meta = parse_frontmatter_text(text)
    errors: list[str] = []
    if not portable and (meta.get("type") != "synthesis" or meta.get("notebooklm_role") != "exclude"):
        errors.append("development specs must be synthesis pages excluded from NotebookLM")
    if not re.fullmatch(r"[1-9][0-9]*", str(meta.get("spec_revision", ""))):
        errors.append("spec_revision must be a positive integer")
    state = meta.get("spec_status")
    if state not in ("draft", "ready"):
        errors.append("spec_status must be draft or ready")
    questions = meta.get("blocking_questions", [] if portable else None)
    if not isinstance(questions, list) or any(not isinstance(q, str) or not q.strip() for q in questions):
        errors.append("blocking_questions must be a list of unresolved question identifiers")
    if state == "ready" and questions != []:
        errors.append("ready requires every blocking question to be answered")

    body = body_text(text)
    prose = prose_text(body)
    headings = re.findall(r"(?m)^## (.+)$", prose)
    expected = [f"{i}. {title}" for i, title in enumerate(sections, 1)]
    if headings != expected:
        errors.append("the five development-spec sections are required in order")
    scenarios = re.findall(r"(?ms)^[ \t]*-[ \t]+(SCN-[0-9]{3,})[：:][ \t]*([^\n]*(?:\n(?![ \t]*-[ \t]+SCN-|## )[^\n]*)*)", prose)
    if not scenarios or len({s[0] for s in scenarios}) != len(scenarios):
        errors.append("unique SCN acceptance scenarios are required")
    if state == "ready":
        acceptance = prose.rsplit("## 5. ", 1)[-1] if "## 5. " in prose else ""
        if not re.search(r"(?m)^[ \t]*-[ \t]+SCN-[0-9]{3,}[：:]", acceptance):
            errors.append("acceptance scenarios must appear in the fifth section")
        # Literal JSON, types and inline-code examples are not prose placeholders.
        narrative = re.sub(r"`[^`\n]*`", "", prose)
        if re.search(r"\{[^{}:=]+\}", narrative):
            errors.append("ready cannot contain template placeholders")
        # Unresolved API fields remain blockers inside inline or fenced contracts, too.
        content = re.sub(r"<!--.*?-->", "", body, flags=re.S)
        if re.search(r"\b(?:TBD|TODO|FIXME)\b|待(?:確認|補充|決定|填寫)|尚未(?:確認|決定)", content, re.I):
            errors.append("ready cannot contain unresolved decisions or placeholders")
        for identifier, scenario in scenarios:
            match = re.search(r"\bGiven\b(.*?)\bWhen\b(.*?)\bThen\b(.*)", scenario, re.I | re.S)
            if not match or any(not re.search(r"[^\W_]", re.sub(r"<[^>]+>", "", value)) for value in match.groups()):
                errors.append(f"{identifier} needs non-empty Given, When and Then outcomes")
        for section in re.split(r"(?m)^## [1-5]\. .+\n", prose)[1:]:
            if not section.strip():
                errors.append("ready cannot contain an empty section")
            links = r"\[\[[^\]]+\]\]|!?\[[^\]]*\]\([^)]*\)"
            if re.search(links, section):
                remaining = re.sub(links, "", section)
                remaining = re.sub(r"\b(?:see|please|refer|to|implement|as|described|in|according|the|specification|document|above|below)\b|詳見|參見|參考|依照|請|依|實作|內容|文件|規格|辦理|同上", "", remaining, flags=re.I)
                if not re.search(r"[\w\u3400-\u9fff]", remaining):
                    errors.append("required content cannot be replaced by a document link")
            if re.fullmatch(r"\s*(?:詳見|參見|請參考|see|refer to)[^\n。]*\b(?:BA|SA|SD)\b[^\n。]*[。.]?\s*", section, flags=re.I):
                errors.append("required content cannot be replaced by a reference to BA/SA/SD")
    if portable:
        if re.search(r"\[\[[^\]]+\]\]", prose):
            errors.append("portable specifications cannot contain Wiki links")
        if re.search(r"(?:詳見|參見|依照|請參考|refer to|see)\s*[^\n。;；]*(?:\bBA\b|\bSA\b|\bSD\b|附件|其他文件|other document)", prose, re.I):
            errors.append("portable specifications cannot delegate necessary content to other documents")
        if re.search(r"(?:\bwiki/|\bdocs/|\battachments/|file://|[A-Za-z]:[\\/])[^\s`<>]*\.(?:md|docx?|pdf)\b", prose, re.I):
            errors.append("portable specifications cannot depend on a local document path")
        anchors = {re.sub(r"[^\w\s-]", "", title).strip().lower().replace(" ", "-")
                   for title in re.findall(r"(?m)^#{1,6}\s+(.+)$", prose)}
        anchors.update(re.findall(r'<a\s+(?:id|name)=["\']([^"\']+)["\']', prose, flags=re.I))
        reference_key = lambda label: " ".join(label.split()).casefold()
        references = {reference_key(label) for label in re.findall(r"(?m)^\s*\[([^\]]+)\]:", prose)}
        for label, reference in re.findall(r"(?<!!)\[([^\]]+)\]\[([^\]]*)\]", prose):
            if reference_key(reference or label) not in references:
                errors.append("portable specifications cannot contain unresolved reference links")
        targets = re.findall(r"!?\[[^\]]*\]\(([^)]+)\)|(?m:^\s*\[[^\]]+\]:\s*(\S+))", prose)
        for inline, reference in targets:
            target = (inline or reference).strip().strip("<>")
            if target.startswith("#") and unquote(target[1:]) not in anchors:
                errors.append("portable specifications cannot contain unresolved anchors")
            elif not target.startswith("#") and not re.match(r"https?://", target, re.I):
                errors.append("portable specifications cannot depend on local files or attachments")
    return errors


def inspect(text: str, sections: tuple[str, ...] = SECTIONS) -> dict:
    errors = structural_errors(text, sections)
    structural_status = "fail" if errors else "pass"
    meta = parse_frontmatter_text(text)
    digest = review_digest(text)
    recorded = meta.get("self_contained_review") == "passed" and meta.get("reviewed_spec_digest") == digest
    if meta.get("spec_status") == "ready" and not recorded:
        errors.append("ready requires an Agent self-contained review recorded against the current review_digest")
    return {"ok": not errors, "errors": errors, "structural_status": structural_status,
            "semantic_status": "recorded" if recorded else "review_required", "review_digest": digest,
            "ready": meta.get("spec_status") == "ready" and not errors}


def validate(text: str, sections: tuple[str, ...] = SECTIONS) -> list[str]:
    return inspect(text, sections)["errors"]
