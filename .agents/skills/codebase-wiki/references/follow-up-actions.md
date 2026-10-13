# Follow-up Action Recommendations

Use this contract after a Wiki-first Query answer or a Wiki Lint report when
the result suggests a useful, independent next operation.

## Purpose

Answer first, then suggest a concrete change. A user's selection of a previewed
action authorizes that complete bounded operation, including its normal index,
provenance, checks and log updates. Carry this authorization into the selected
workflow; do not repeat an Interactive Ingest or Synthesis confirmation.

Query remains read-only until the user selects a follow-up. The agent must not
automatically write or enter a different workflow.

## Eligibility

### Query

Offer a recommendation block only when at least one condition is true:

- The answer combines evidence across modules or sources and has durable
  explanatory value.
- The answer contains reusable cross-cutting analysis worth preserving.
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

For each actionable choice include all of: reason, checked source evidence,
exact target pages (or a bounded source scope for a read-only Lint), and a
concrete preview of additions/replacements. Check stale or conflicting sources
before previewing a repair. Find existing pages on the same topic before
proposing a new Synthesis. When both correction and reusable analysis are
valuable, offer the combined choice first. Never add a speculative suggestion
merely to fill three slots. This is a preview, not an execution report.

## Action mapping and authorization

| Canonical action ID | User-facing action | Existing operation | Default target | Authorization |
| --- | --- | --- | --- | --- |
| `save-synthesis` | 保存分析／更新既有分析 | `synthesis` | Previewed page in `wiki/synthesis/` | Selection authorizes the previewed write. |
| `reingest` | 更新 Wiki／重新 Ingest | `ingest` | Previewed Wiki pages | Selection is the Interactive Ingest confirmation; execute without a second gate. |
| `refresh-and-save` | 更新 Wiki 並保存分析 | `ingest`, then `synthesis` | Previewed correction and analysis pages | One selection authorizes both subflows in this order. |
| `lint` | 執行 Wiki Lint／修復已預覽問題 | `lint` | Previewed scope | Report-only Lint is read-only; selection authorizes only explicitly previewed repairs. |
| `none` | 暫不處理 | none | none | No file, index, or log state changes. |

All durable writes retain the normal coupling rules: update `wiki/index.md`
when page navigation changes, preserve existing user-authored content, and use
the matching append-only `wiki/log.md` operation. A report-only Query or Lint
does not append a log entry. A combined operation appends one `ingest` and one
`synthesis` entry for the subflows actually completed, never a pretend Query
write or a duplicate log for each page.

## Execute the selected preview

1. Keep the selected action, source paths/digests, target pages and change
   preview in conversation context. No authorization file is written by Query.
2. Recheck relevant evidence against that preview before writing. Ask again
   only if scope must expand, a necessary decision is unanswered, or a material
   source change invalidates the preview. Unrelated source edits do not revoke
   an otherwise valid selection. Silence and elapsed time never authorize work.
3. Load and complete the mapped workflows. Reuse the checked evidence; preserve
   human notes, update existing same-topic pages, refresh sources/digests and
   required index entries, and append the correct log operations.
4. Run each subflow's applicable checks. Report changed files, index/log updates,
   verification and remaining gaps. If a subflow fails, report completed and
   blocked work honestly; do not claim the whole combined choice completed.

Plain Query, `none`, and no selection produce zero writes, including index,
log, coverage ledgers and recommendation records. This contract applies equally
to Codex, Copilot and installed downstream profiles.

## Completion Criterion

The recommendation contract is satisfied when an eligible Query or Lint result
contains a reasoned, bounded action block; an ineligible result remains concise;
each selected action completes the matching workflow with one confirmation for
the previewed scope; and no action is executed implicitly.
