def save_with_framework_boundary(db, payment) -> None:
    @db.transactional
    def persist() -> None:
        db.insert(payment)

    persist()
