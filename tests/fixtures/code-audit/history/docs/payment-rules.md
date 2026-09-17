# Payment rules

The payment database transaction must commit before a receipt is sent. A
rollback must not leave a customer-facing receipt for a payment that was not
stored.

If the ledger write fails, the payment operation must roll back and return a
failure; swallowing the exception and committing the payment is invalid. The
`@db.transactional` wrapper owns begin, commit, and rollback for its callback.
`PAYMENT_RECEIPT_CHANNEL` may come from deployment injection, generated
defaults, or the `email` fallback.

A failed payment must return a failure status, and the same payment id must be
recorded at most once when a delivery is retried.
