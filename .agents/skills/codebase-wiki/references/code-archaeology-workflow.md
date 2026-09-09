# Code Archaeology Workflow

Use this workflow when the user asks why behavior exists, how legacy logic
evolved, when a field or rule was introduced, or what git history says about a
code path.

## Source Order

1. Start from a concrete entrypoint: route, UI page, command, handler, field,
   public API, or function name.
2. Read `wiki/index.md` and relevant wiki pages for routing context.
3. Trace current source behavior read-only.
4. When source locations are hard to locate, optionally use the bounded
   [Source Discovery with tgrep](source-discovery-workflow.md) wrapper. Treat
   its output as candidate locators and re-read current files before analysis.
5. Use non-destructive git history commands:
   - `git log --oneline -- path/to/file`
   - `git log --all --oneline --grep "{keyword}"`
   - `git blame -L start,end path/to/file`
   - `git show <commit> -- path/to/file`
6. Persist findings only when the user asks or the task explicitly includes
   wiki updates.

## Writing Rules

- Distinguish evidence-backed facts, inference, and speculation.
- Explain current behavior before historical interpretation.
- Do not use destructive git commands such as `reset`, `checkout`, `clean`,
  `rebase`, or branch-changing operations.
- If persisted, write to an appropriate existing page or
  `wiki/synthesis/{topic}.md`, add a meaningful inbound `[[wikilink]]` from a
  related content page, update `wiki/index.md`, and append `wiki/log.md` with
  operation `archaeology`. Index and log links do not satisfy the semantic
  inbound-link requirement; when no better content page exists, add a small
  related-findings link to `wiki/overview.md` without inventing new claims.

## Completion Criterion

Archaeology is complete when the current call path is explained before its
history, every historical claim cites a Git command result, inference and
uncertainty are labeled, and the working tree remains unchanged unless
persistence was explicit. Persisted output also requires valid frontmatter, a
semantic inbound wikilink from a related content page, index coupling, one
append-only `archaeology` entry, and deterministic lint with no Critical or
Warning findings.
