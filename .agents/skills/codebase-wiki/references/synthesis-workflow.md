# Synthesis Workflow

Use this workflow when the user asks to save durable cross-cutting analysis,
technical debt, risk review, architecture summary, or query findings under
`wiki/synthesis/`.

## Source Order

1. Read `wiki/index.md` and recent `wiki/log.md`.
2. Read relevant wiki pages first.
3. Inspect raw sources only when wiki evidence is insufficient, stale, or
   contradictory.
4. Preserve citations to wiki pages and raw source paths used by the analysis.

## Output

- Path: `wiki/synthesis/{kebab-topic}.md`.
- Frontmatter type: `synthesis`.
- Log operation: `synthesis` for durable analysis and SA documents.

## Writing Rules

- A selected concrete Query follow-up preview already authorizes its target
  and content. Do not repeat naming/content confirmation; ask only for an
  unanswered necessary decision or a material change to that preview.
- Search for an existing same-topic Synthesis and update it before creating a
  duplicate. Preserve human notes and distinguish refreshed from new findings.
- Do not paste a chat transcript directly. Convert it into a structured page:
  summary, detailed analysis, findings, recommendations, sources, and related
  pages.
- Use `[[page-name]]` wikilinks and source paths in backticks.
- Separate evidence, inference, and speculation.
- Update `wiki/index.md` and append `wiki/log.md`.

## Completion Criterion

Synthesis is complete when every finding is tied to Wiki/source evidence or
labeled inference, gaps remain visible, frontmatter validates, related pages
resolve, the index links the output, and one append-only `synthesis` entry
records it.
