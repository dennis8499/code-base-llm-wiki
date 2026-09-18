# Codebase Audit Acceptance Fixture

Read this fixture as a small target repository. Do not execute it. Use it to
manually verify the `code_audit` workflow and compare the result with
`expected-findings.md`.

Expected coverage and classification:

- Present the result by stable `FUNC-*` capabilities while keeping every route,
  CLI command, plugin registration, and other source registration in the
  entrypoint coverage table. The order-summary capability must link both the
  API and CLI entrypoints to the shared `BUG-*` root cause.
- A function with a dynamic or external boundary is `partial`; an entrypoint
  that cannot be assigned a business name uses `FUNC-UNCLASSIFIED-{slug}` and
  remains in the review. A rerun preserves finding IDs and records one of
  `new`, `still-present`, `rechecked-no-longer-observed`, or `not-rechecked`.

- The API and CLI order-summary entrypoints converge on one root cause. The
  draft API stores an order with zero lines; that value reaches division by zero
  in the shared service, so report one
  confirmed `BUG-*` finding that names both entrypoints.
- Account cancellation bypasses the explicit unpaid-invoice rule in
  `docs/business-rules.md`; report it as a confirmed rule violation with the
  reachable API and source locations.
- Return eligibility is implemented, but the sources do not say whether a fee
  should be charged. Report this as a `BIZ-*` question, not as a defect.
- Checkout accepts a service argument without its own validation, but the only
  registered route validates positive quantity before calling it. Do not report
  an invalid-quantity bug for that entrypoint.
- Plugin routes depend on a module name supplied at runtime. Mark that entry
  partial and state why its downstream path cannot be audited from this fixture.
- Do not run application functions or tests. Do not modify fixture sources.

This scenario also checks root-cause deduplication, evidence paths, coverage
gaps, and the distinction between current behavior and confirmed business
policy.

Source-first discovery cases:

- **No Wiki baseline**: this fixture has no `wiki/` directory; the current
  Codebase inventory must still discover and trace every listed entrypoint.
- The current Codebase inventory remains authoritative even when Wiki context
  is absent or incomplete.
- **Wiki omits a current entrypoint**: if a target Wiki lists only the order
  routes, the account, checkout, return, and plugin registrations still come
  from the current source tree and remain in coverage.
- **Wiki page is stale**: an old page must be treated as context evidence only;
  re-read the current source and record the stale page as a gap when behavior
  differs.
- **Existing audit report omits a newly registered entrypoint**: re-running the
  same scope must discover the new registration from current source, add its
  coverage row, and continue tracing the remaining entries while preserving
  prior finding IDs and user notes.
