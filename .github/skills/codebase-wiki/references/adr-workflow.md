# ADR Workflow

Use this workflow when the user asks to record an architecture decision, ADR,
decision rationale, or architectural choice.

## Source Order

1. Read `wiki/index.md` and recent `wiki/log.md`.
2. Inspect existing `wiki/decisions/` entries to choose the next ADR number and
   avoid duplicates.
3. Read relevant wiki pages and raw source evidence when the decision is tied to
   existing behavior.
4. Ask for missing decision context only when the decision cannot be recorded
   without inventing rationale.

## Output

- Path: `wiki/decisions/adr-{nnn}-{kebab-title}.md`.
- Template: `assets/adr-template.md`.
- Log operation: `adr`.

## Required Frontmatter

```yaml
---
title: "ADR-{NNN}: {decision title}"
type: decision
decision_date: YYYY-MM-DD
decision_status: proposed | accepted | deprecated | superseded
sources: []
last_updated: YYYY-MM-DD
tags: [adr]
status: active
---
```

## Writing Rules

- Include background, considered options, decision, rationale, consequences,
  risks, and follow-up.
- Separate evidence-backed facts from inference.
- Use `sources: []` only when no source or wiki evidence directly supports the
  decision.
- Update `wiki/index.md` and append `wiki/log.md`.
