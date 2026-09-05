# Wiki-First Query Workflow

Query is read-only.

Query uses only Wiki pages and repository source files. It must not connect to
live databases or invoke database tools, MCP servers, apps, or CLI fallbacks.
Questions that require current database state remain explicit unverified gaps.

## Steps

1. Read `wiki/index.md`.
2. Read the 1–5 pages most likely to answer the question.
3. Inspect their listed sources only when the Wiki is missing, stale,
   contradictory, or too vague.
4. Answer with `[[wiki-page]]` references, backticked source paths, and labeled
   inference or gaps.
5. When the result meets the eligibility rules, append the bounded
   recommendation block from `follow-up-actions.md`.

The recommendation block suggests a separate operation; it does not write or
enter another workflow automatically. Persistence remains an explicit operation.

## Completion Criterion

The query is complete when every material conclusion is supported by a Wiki
page or source path; contradictions and gaps are
visible; eligible durable or corrective follow-ups are clearly offered; and no
file state was changed.
