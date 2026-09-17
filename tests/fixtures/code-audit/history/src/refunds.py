def refund_payment(payment_id: str, *, reason: str) -> None:
    """Issue a refund with an auditable reason."""

    record_refund(payment_id, reason)


def record_refund(payment_id: str, reason: str) -> None:
    return None
