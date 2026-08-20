# Follow-up Action Recommendations

Use this contract after a Wiki-first Query answer or a Wiki Lint report when
the result suggests a useful, independent next operation.

## Purpose

The recommendation block improves discoverability without changing the
authorization model. It is a text-based cross-platform hand-off: the agent
suggests an action, the user selects it, and the selected workflow applies its
own write and confirmation rules.

Query remains read-only until the user selects a follow-up. The agent must not
automatically write, invoke another agent, or hand off to a different workflow.

## Eligibility

### Query

Offer a recommendation block only when at least one condition is true:

- The answer combines evidence across modules or sources and has durable
  explanatory value.
- The answer contains a reusable procedure, debugging sequence, runbook, or
  onboarding path.
- The Wiki has a stale source, missing page, unresolved contradiction, or
  evidence gap that the answer materially exposes.
- The answer identifies a broken link, frontmatter, orphan, index, or coverage
  concern that merits a full Lint pass.

Do not show the block for a simple lookup, one-off location answer, or answer
with no durable recommendation.

### Lint

After reporting findings, offer only actions supported by the findings:

- deterministic repair confirmation for safe stale, link, or index fixes;
- re-Ingest confirmation for stale or missing knowledge;
- a read-only follow-up Lint pass when semantic review remains unresolved;
- no action when the report is clean or the user does not want changes.

## User-facing format

Place the block after the evidence, findings, and gaps. Use Traditional Chinese
labels, show at most three actionable choices, rank the strongest recommendation
first, and always include the no-action choice:

```markdown
### 建議後續操作（可選）

1. {action label} — {why it is recommended}
2. {action label} — {why it is recommended}
0. 暫不處理
```

When known, include the target path or scope in the action label. Do not claim
that an option was executed; the block is only a recommendation until the user
selects a choice.

## Action mapping and authorization

| Canonical action ID | User-facing action | Existing operation | Default target | Authorization |
| --- | --- | --- | --- | --- |
| `save-synthesis` | 保存為 Wiki Synthesis | `synthesis` | `wiki/synthesis/` | User selection is an explicit creation request; report target and sources. |
| `save-guide` | 保存為操作 Guide | `guide` | `wiki/guides/` | User selection is an explicit creation request; report target and sources. |
| `reingest` | 更新 Wiki／重新 Ingest | `ingest` | Relevant Wiki pages | Use Interactive Ingest preview, then wait for confirmation before writing. |
| `lint` | 執行 Wiki Lint | `lint` | `wiki/` | Initial pass is read-only; repairs require confirmation. |
| `none` | 暫不處理 | none | none | No file, database, agent, index, or log state changes. |

All durable writes retain the normal coupling rules: update `wiki/index.md`
when page navigation changes, preserve existing user-authored content, and use
the matching append-only `wiki/log.md` operation. A report-only Query or Lint
does not append a log entry.

## Completion Criterion

The recommendation contract is satisfied when an eligible Query or Lint result
contains a reasoned, bounded action block; an ineligible result remains concise;
each selected action enters the matching existing workflow; and no action is
executed or delegated implicitly.
