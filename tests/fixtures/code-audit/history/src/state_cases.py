def complete_payment(payment) -> dict[str, str]:
    if payment.state == "failed":
        return {"status": "completed"}
    return {"status": "completed"}


def record_payment_twice(db, payment) -> None:
    db.insert_payment(payment.id)
    db.insert_payment(payment.id)
