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

- Do not paste a chat transcript directly. Convert it into a structured page:
  summary, detailed analysis, findings, recommendations, sources, and related
  pages.
- Use `[[page-name]]` wikilinks and source paths in backticks.
- Separate evidence, inference, and speculation.
- Keep DB live evidence in a page body evidence block, never in
  `frontmatter.sources`.
- Update `wiki/index.md` and append `wiki/log.md`.
