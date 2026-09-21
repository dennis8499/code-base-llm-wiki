# Expected history-aware static review

The isolated Git fixture should yield these evidence categories when the
current tree is reviewed together with its targeted history:

- `BUG-*`: `src/config_loader.py` still requires `config/payment.yml` after the
  commit deleted it, and the current source has no environment injection,
  generator, or fallback. The deleted path is cited with the full commit SHA,
  but is not included in `frontmatter.sources`.
- `BUG-*`: `src/payments.py` sends a receipt inside the database transaction
  even though `docs/payment-rules.md` has an explicit post-commit notification
  rule requiring notification only after a successful commit. The later
  commit's claim is compared with its actual diff.
- `BUG-*`: `src/transaction_cases.py` swallows a ledger exception, commits the
  payment write, and returns success despite the explicit rollback rule.
- `BUG-*`: `src/state_cases.py` returns `completed` for a failed payment and
  inserts the same payment id twice on a retry, contrary to the explicit state
  and idempotency rules.
- `RISK-*`: `src/unknown_boundary.py` updates storage and sends an external
  notification without enough caller/framework evidence to decide whether the
  transaction boundary is owned elsewhere. State the condition, missing framework
  evidence, and smallest confirmation rather than reporting a definite BUG.
- `BUG-*`: `src/refund_cli.py` calls the changed `refund_payment` interface
  without the now-required `actor` argument.
- `src/framework_managed.py` is a valid transaction contrast: the framework
  decorator owns the boundary, so the audit must not report a missing explicit
  transaction. `src/config_fallback.py` and `deploy/payment.env.example` are
  valid injection/generated-default/fallback producers for the receipt channel;
  they must not be reported as missing configuration.
- The renamed rules path must be followed to its current name, and the later
  settlement fix must be recorded as no longer observed rather than a current
  `BUG-*`. The follow-up fix is evidence of current behavior only after the
  diff is checked. The report separately records the uncommitted source edit,
  dirty worktree, and the fact that targeted history is incomplete by design.
- The report must include the full HEAD, dirty/clean worktree state, the
  `current-first-targeted` query scope, every deeply reviewed commit's complete
  body/message and diff location, and any unreviewed history limitation.
- For a merge commit, the report must compare every parent with the merge result,
  list the full merge/parent SHAs and affected path, and confirm the suspected
  loss remains in current source. Without parent evidence, a squash/rebase issue
  is a behavior finding only and is not attributed to manual merging.
- The merge fixture explicitly covers a lost authorization guard, a follow-up
  restoration, a worktree repair, and a separate guarded caller. A missing
  parent row is invalid evidence, and no parent evidence means no manual merge
  attribution.
- A rerun must merge the shared root cause, continue finding IDs, preserve the
  user-notes block, and retain an old record with a link to a new ID if a
  finding classification changes between `BUG-*`, `RISK-*`, and `BIZ-*`.
- Functional review rows group the payment, settlement, configuration, state,
  and refund entrypoints under stable `FUNC-*` IDs; every entrypoint remains
  linked even when a shared root cause affects more than one capability.
- A same-scope rerun keeps each finding ID and records `new`, `still-present`,
  `rechecked-no-longer-observed`, or `not-rechecked` rather than inferring a
  fix from missing evidence.
- v4 findings use P0–P3, plain-language impact, and a code-derived/not-executed
  operation/input, expected-result, and actual or conditional-result example;
  old `not-rechecked` findings retain their original severity and appear last.

The expected v2 report also includes a function table with checked scenarios and
limitations, a ten-column entrypoint table whose first column is the function
ID, and `受影響功能` / `重跑狀態` on every finding. `FUNC-state-and-idempotency`
links the cross-step state and retry cases, while `FUNC-UNCLASSIFIED-refund-cli`
is retained when the CLI's business capability cannot be established from source.

The fixture intentionally does not prove that every historical commit was
reviewed. It also contains no runtime tests and must not be executed.
