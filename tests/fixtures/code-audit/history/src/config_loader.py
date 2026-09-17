from pathlib import Path


CONFIG_PATH = Path("config/payment.yml")


def load_payment_config() -> str:
    """Load the required payment configuration file."""

    if not CONFIG_PATH.is_file():
        raise FileNotFoundError(CONFIG_PATH)
    return CONFIG_PATH.read_text(encoding="utf-8")
