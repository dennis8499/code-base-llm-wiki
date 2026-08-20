# Wiki-First Query Workflow

Query is read-only.

## Steps

1. Read `wiki/index.md`.
2. Read the 1–5 pages most likely to answer the question.
3. Inspect their listed sources only when the Wiki is missing, stale,
   contradictory, or too vague.
4. Use `mssql-evidence-rules.md` only when the question requires live SQL Server
   evidence and an approved tool is available.
5. Answer with `[[wiki-page]]` references, backticked source paths, and labeled
   inference or gaps.

6. When the result meets the eligibility rules, append the bounded
   recommendation block from `follow-up-actions.md`.

The recommendation block suggests a separate operation; it does not write,
delegate, or hand off automatically. Persistence remains an explicit operation.

## Completion Criterion

The query is complete when every material conclusion is supported by a Wiki
page, source path, or labeled live-evidence block; contradictions and gaps are
visible; eligible durable or corrective follow-ups are clearly offered; and no
file or database state was changed.
