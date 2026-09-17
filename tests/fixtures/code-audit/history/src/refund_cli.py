from .refunds import refund_payment


def refund_command(payment_id: str) -> None:
    refund_payment(payment_id)
