def load_receipt_channel(environment, generated_defaults) -> str:
    return (
        environment.get("PAYMENT_RECEIPT_CHANNEL")
        or generated_defaults.get("receipt_channel")
        or "email"
    )
