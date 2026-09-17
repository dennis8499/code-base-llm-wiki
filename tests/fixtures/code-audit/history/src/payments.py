def capture_and_notify(db, notifier, payment):
    """Persist a payment and send its receipt."""

    with db.transaction() as transaction:
        transaction.insert(payment)
        notifier.send_receipt(payment.id)
