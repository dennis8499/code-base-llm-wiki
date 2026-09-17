def update_and_notify(db, notifier, payment) -> None:
    db.update(payment)
    notifier.send(payment.id)
