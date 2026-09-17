# Expected Static Review Result

## Result Summary

- Scope: all files and entrypoint registrations in this fixture
- Method: read-only source review; no fixture code or tests executed
- Coverage: checked 6 entrypoints, partial 1, not checked 0; Partial coverage is limited to the runtime plugin boundary
- Findings: 2 confirmed defects and 1 unresolved business question
- Limitation: the plugin module is selected at runtime, so plugin-owned routes and handlers are unavailable

## Scope and Exclusions

Reviewed API routes, the CLI command, draft-order storage, service calls, plugin registration, and the fixture's business rules. No runtime modules outside this fixture were available. Application execution and tests are excluded.

## Entrypoint Coverage

| Entrypoint | Status | Trace |
| --- | --- | --- |
| `POST /orders/drafts` | checked | `src/api/orders.py:10` → `src/data/orders.py:12`, `src/data/orders.py:13`, `src/data/orders.py:14` stores a draft with zero lines |
| `GET /orders/{order_id}/summary` | checked | `src/api/orders.py:14`, `src/api/orders.py:18` → `src/data/orders.py:17`, `src/data/orders.py:18` → `src/services/orders.py:1`, `src/services/orders.py:2` |
| `orders summary` | checked | `src/cli/orders.py:9`, `src/cli/orders.py:13` → same repository and summary service as the API |
| `POST /accounts/{account_id}/cancel` | checked | `src/api/accounts.py:9`, `src/api/accounts.py:10` → `src/services/accounts.py:1`, `src/services/accounts.py:5` deletes the account |
| `POST /checkout` | checked | `src/api/checkout.py:9`, `src/api/checkout.py:11`, `src/api/checkout.py:13` rejects non-positive quantity before `src/services/checkout.py:1` |
| `POST /orders/{order_id}/return` | checked | `src/api/returns.py:9`, `src/api/returns.py:11`, `src/api/returns.py:13` → `src/services/returns.py:1`, `src/services/returns.py:2` |
| Runtime plugin registration | partial | `src/plugins/loader.py:5`, `src/plugins/loader.py:6`, `src/plugins/loader.py:7`, `src/plugins/loader.py:8` imports an environment-selected module; plugin routes are unavailable for tracing |

## Confirmed Defects

### BUG-001 — Empty draft order summary divides by zero

- Status: `open`
- Evidence certainty: `confirmed`
- Impact: `medium`
- Affected entrypoints: `GET /orders/{order_id}/summary`; `orders summary`
- Trigger: Create a draft through `POST /orders/drafts`, then request its summary through either entrypoint.
- Call path: `src/api/orders.py:10`, `src/api/orders.py:11` → `src/data/orders.py:12`, `src/data/orders.py:13`, `src/data/orders.py:14` stores `line_count = 0`; the API or CLI loads it at `src/api/orders.py:14` or `src/cli/orders.py:9` and calls `summarize_order` at `src/api/orders.py:18` or `src/cli/orders.py:13`.
- Evidence: `src/services/orders.py:2` divides `order.total` by `order.line_count`. Neither summary entrypoint handles this case before calling the shared service.
- Expected behavior: Return a defined empty-order summary or a deliberate validation error.
- Actual behavior and impact: The shared service raises division by zero; both entrypoints fail for a valid stored draft.
- Suggested fix direction: Define empty-draft summary behavior and handle zero line count in the shared service.
- Suggested validation: Cover an empty draft through both API and CLI, plus a non-empty order regression case.

### BUG-002 — Account cancellation ignores the unpaid-invoice rule

- Status: `open`
- Evidence certainty: `confirmed`
- Impact: `high`
- Affected entrypoint: `POST /accounts/{account_id}/cancel`
- Trigger: Cancel an existing account that has at least one unpaid invoice.
- Call path: `src/api/accounts.py:9`, `src/api/accounts.py:10` → `src/services/accounts.py:1`, `src/services/accounts.py:2`, `src/services/accounts.py:5` loads the account and deletes it without checking invoices.
- Evidence: `docs/business-rules.md:3` explicitly forbids cancellation while an unpaid invoice exists. The reachable handler calls deletion unconditionally after checking only that the account exists.
- Expected behavior: Reject cancellation while an unpaid invoice exists and retain the account.
- Actual behavior and impact: The account is deleted despite the explicit rule, potentially disrupting financial reconciliation.
- Suggested fix direction: Check unpaid invoices before deletion and preserve the account on rejection.
- Suggested validation: Verify an unpaid-invoice account is retained and rejected; verify an eligible account can still be cancelled.

## Business Questions

### BIZ-001 — Is a zero return fee the intended policy?

- Status: `needs-business-confirmation`
- Evidence certainty: `unresolved`
- Possible impact: `medium`
- Affected entrypoint: `POST /orders/{order_id}/return`
- Call path: `src/api/returns.py:9`, `src/api/returns.py:10`, `src/api/returns.py:11`, `src/api/returns.py:13` → `src/services/returns.py:1`, `src/services/returns.py:2`
- Current behavior: The service records a return fee of zero.
- Inference evidence: `src/services/returns.py:2` establishes the implementation; `docs/business-rules.md:6` describes the return window but says no fee policy.
- Unspecified expected policy: The available documents do not say whether eligible returns are free or fee-bearing.
- Question for the business owner: Is a zero fee required for every eligible return?
- Suggested validation: After policy confirmation, cover the expected fee for eligible and ineligible returns.

## False Positive Check

No invalid-quantity defect is reported for checkout: `src/api/checkout.py:11` validates positive quantity before calling the service, and no other service caller is present in the fixture.

## Remaining Work and Verification Suggestions

Plugin-owned routes and handlers remain unverified because the module is chosen through `APP_PLUGIN_MODULE`. Inspect the selected plugin source in the target repository before marking that entry checked. This static review did not execute the application or tests.
