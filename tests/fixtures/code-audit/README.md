# Codebase Audit Acceptance Fixture

Read this fixture as a small target repository. Do not execute it. Use it to
manually verify the `code_audit` workflow and compare the result with
`expected-findings.md`.

Expected coverage and classification:

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
