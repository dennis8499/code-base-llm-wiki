# Git history acceptance fixture

This directory is copied into an isolated temporary repository by the audit
contract tests. The test creates a small, controlled history without changing
the framework repository:

1. Commit the initial payment code, its explicit post-commit notification rule,
   the refund interface, transaction contrast cases, fallback configuration,
   and `config/payment.yml`.
2. Delete `config/payment.yml` in a commit whose message says the setting moved
   to environment injection, without adding an injection or fallback path.
3. Commit a change described as making notifications transactional while the
   current diff still sends the receipt before the database transaction commits.
4. Rename `docs/payment-rules.md` in the test-created history and inspect it with
   `git log --follow`; this exercises a historical path that still exists under a
   new name.
5. Create a legacy settlement path with a transaction bug, then commit a follow-up
   fix. The fixed path must not be reported as a current `BUG-*`.
6. Commit a refund interface change that adds a required `actor`, while the CLI
   caller still supplies only `payment_id`; finally leave an uncommitted source edit so
   the report has to record a dirty worktree. The test intentionally queries only
   targeted paths, so it also demonstrates that a history index is not a claim
   that every commit was reviewed.

The transaction cases include a swallowed ledger exception followed by an
explicit commit (a current defect) and a `@db.transactional` framework boundary
(a false-positive guard). The configuration cases include deployment injection,
generated defaults, and an explicit fallback; those valid producers must not be
reported as a missing setting.

The state cases cover a failed operation returned as success and duplicate
inserts on retry, each paired with an explicit rule so the findings are
classified as defects rather than style advice.

`src/unknown_boundary.py` is a technical-risk contrast: it updates storage and
sends an external notification, but the fixture does not establish whether the
caller or framework owns a transaction. The audit must state the failure
condition and missing framework evidence as `RISK-*`, not assert a BUG.

The expected audit must compare the current source with the commit title,
complete body, parent, and diff. A commit message alone is never a defect
claim. The deleted path belongs in historical evidence only; current
`frontmatter.sources` may contain only files that still exist.

When a finding is revisited, the report keeps the same root-cause record and
finding ID where the issue is unchanged, continues IDs without recycling them,
preserves the user-notes block, and links an old ID to a new `BUG-*`, `RISK-*`,
or `BIZ-*` ID when its classification changes.

Do not execute these modules. They are source evidence for a read-only static
review.
