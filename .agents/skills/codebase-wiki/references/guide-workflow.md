# Guide Workflow

Use this workflow when the user asks to save durable guidance under
`wiki/guides/`, including onboarding, debugging, operations, local setup,
contribution, or runbook-style guidance.

## Source Order

1. Read `wiki/index.md` and recent `wiki/log.md`.
2. Read `wiki/overview.md` and the most relevant architecture/module/entity
   pages.
3. Inspect raw sources only when wiki evidence is missing, stale, or too vague
   for actionable guidance.

## Output

- Path: `wiki/guides/{kebab-topic}.md`.
- Frontmatter type: `guide`.
- Log operation: `guide`.

## Writing Rules

- Write for the stated audience. If no audience is given, infer the smallest
  practical audience and state it in the guide.
- Use actionable steps, prerequisites, common pitfalls, and related pages.
- Use `[[page-name]]` wikilinks for wiki references and source paths in
  backticks for raw source evidence.
- Mark gaps instead of inventing setup commands, owners, secrets, or runtime
  behavior.
- Update `wiki/index.md` and append `wiki/log.md`.

## Onboarding Guides

When the user specifically asks for newcomer onboarding, keep using the
specialized onboarding workflow and prompt. Use the general guide workflow for
all other durable guide topics.

## Completion Criterion

The guide is complete when its audience, prerequisites, actionable steps,
pitfalls, gaps, and related pages are present; commands and runtime claims are
evidence-backed; frontmatter validates; the index links it; and one append-only
`guide` entry records it.
