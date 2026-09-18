# Expected Static Review Result

## Result Summary

- Scope: all files and entrypoint registrations in this fixture
- Method: read-only source review; no fixture code or tests executed
- Functional coverage: checked 5, partial 1, not checked 0; the plugin capability is partial because its downstream module is selected at runtime
- Entrypoint coverage: checked 6, partial 1, not checked 0
- Functional review: `FUNC-order-summary` links the API and CLI summary entrypoints to `BUG-001`; the plugin registration remains a partial capability review and any unclassified registration is retained with a `FUNC-UNCLASSIFIED-*` ID
- Findings: 2 confirmed defects and 1 unresolved business question
- Rerun state: first scan findings are `new`; later scans reuse the same IDs and distinguish `still-present`, `rechecked-no-longer-observed`, and `not-rechecked`
- Limitation: the plugin module is selected at runtime, so plugin-owned routes and handlers are unavailable

## Scope and Exclusions

Reviewed API routes, the CLI command, draft-order storage, service calls, plugin registration, and the fixture's business rules. No runtime modules outside this fixture were available. Application execution and tests are excluded.

## Functional Review

| Function ID | Capability / scenario | Related entrypoints | Status | Checked scenarios | Findings | Limitations |
| --- | --- | --- | --- | --- | --- | --- |
| `FUNC-order-draft` | Create and retain an order draft | `POST /orders/drafts` | checked | normal, boundary, validation, state, transaction, error | none | none |
| `FUNC-order-summary` | Calculate an order summary | `GET /orders/{order_id}/summary`; `orders summary` | checked | normal, empty draft, boundary, state, shared service, error | `BUG-001` | none |
| `FUNC-account-cancellation` | Cancel an account | `POST /accounts/{account_id}/cancel` | checked | normal, unpaid-invoice boundary, authorization, transaction, side effect | `BUG-002` | none |
| `FUNC-checkout` | Submit checkout quantity | `POST /checkout` | checked | normal, invalid quantity, validation, error | none | upstream route validation prevents the tested false positive |
| `FUNC-return` | Return an order | `POST /orders/{order_id}/return` | checked | normal, eligibility boundary, state, policy gap, error | `BIZ-001` | fee policy is absent |
| `FUNC-plugin-extension-hook` | Load runtime plugin routes | Runtime plugin registration | partial | registration, dynamic boundary, error | none | selected plugin module and handlers are unavailable |

## Entrypoint Coverage

| Function ID | Entrypoint | Type | Status | Transaction / consistency | Configuration / references | Logic / state | History cross-check | Trace | Limitation |
| --- | --- | --- | --- | --- | --- | --- | --- | --- | --- |
| `FUNC-order-draft` | `POST /orders/drafts` | API | checked | checked | not applicable | checked | evidence-gap | `src/api/orders.py:10` → `src/data/orders.py:12`, `src/data/orders.py:13`, `src/data/orders.py:14` stores a draft with zero lines | none |
| `FUNC-order-summary` | `GET /orders/{order_id}/summary` | API | checked | checked | not applicable | checked | evidence-gap | `src/api/orders.py:14`, `src/api/orders.py:18` → `src/data/orders.py:17`, `src/data/orders.py:18` → `src/services/orders.py:1`, `src/services/orders.py:2` | none |
| `FUNC-order-summary` | `orders summary` | CLI | checked | checked | not applicable | checked | evidence-gap | `src/cli/orders.py:9`, `src/cli/orders.py:13` → same repository and summary service as the API | none |
| `FUNC-account-cancellation` | `POST /accounts/{account_id}/cancel` | API | checked | checked | not applicable | checked | evidence-gap | `src/api/accounts.py:9`, `src/api/accounts.py:10` → `src/services/accounts.py:1`, `src/services/accounts.py:5` deletes the account | none |
| `FUNC-checkout` | `POST /checkout` | API | checked | checked | not applicable | checked | evidence-gap | `src/api/checkout.py:9`, `src/api/checkout.py:11`, `src/api/checkout.py:13` rejects non-positive quantity before `src/services/checkout.py:1` | none |
| `FUNC-return` | `POST /orders/{order_id}/return` | API | checked | checked | not applicable | checked | evidence-gap | `src/api/returns.py:9`, `src/api/returns.py:11`, `src/api/returns.py:13` → `src/services/returns.py:1`, `src/services/returns.py:2` | none |
| `FUNC-plugin-extension-hook` | Runtime plugin registration | other | partial | evidence-gap | checked | evidence-gap | not applicable | `src/plugins/loader.py:5`, `src/plugins/loader.py:6`, `src/plugins/loader.py:7`, `src/plugins/loader.py:8` imports an environment-selected module | plugin routes are unavailable for tracing |

## Confirmed Defects

### BUG-001 — Empty draft order summary divides by zero

- 重跑狀態: `new`
- 受影響功能: `FUNC-order-summary`
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

- 重跑狀態: `new`
- 受影響功能: `FUNC-account-cancellation`
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

- 重跑狀態: `new`
- 受影響功能: `FUNC-return`
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
