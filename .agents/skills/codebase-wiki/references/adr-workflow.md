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

## Template

Use `assets/adr-template.md`. Field validity and decision-specific enums remain
defined only in `frontmatter-spec.md`.

## Writing Rules

- Include background, considered options, decision, rationale, consequences,
  risks, and follow-up.
- Separate evidence-backed facts from inference.
- Put raw repository evidence in `sources` and Wiki evidence in
  `derived_from`; use `sources: []` when no raw source directly supports the
  decision.
- Update `wiki/index.md` and append `wiki/log.md`.

## Completion Criterion

The ADR is complete when its number is unique, required frontmatter validates,
background/options/decision/rationale/consequences/risks are present, evidence
and inference are separated, the index links it, and one append-only `adr` entry
records it.
