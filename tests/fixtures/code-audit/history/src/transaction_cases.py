def save_payment_with_swallowed_error(db, payment) -> str:
    transaction = db.begin()
    transaction.insert_payment(payment)
    try:
        transaction.insert_ledger(payment)
    except Exception:
        pass
    transaction.commit()
    return "accepted"
