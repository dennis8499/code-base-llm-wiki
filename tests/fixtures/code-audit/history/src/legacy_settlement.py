def settle(db, notifier) -> None:
    with db.transaction():
        db.write("settled")
    notifier.send("settled")
