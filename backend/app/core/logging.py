import logging


SENSITIVE_KEYS = {"password", "token", "secret", "api_key", "authorization"}


def scrub_dict(values: dict) -> dict:
    scrubbed: dict = {}
    for key, value in values.items():
        if any(sensitive in key.lower() for sensitive in SENSITIVE_KEYS):
            scrubbed[key] = "***"
        else:
            scrubbed[key] = value
    return scrubbed


def configure_logging() -> None:
    logging.basicConfig(
        level=logging.INFO,
        format="%(asctime)s %(levelname)s [%(name)s] %(message)s",
    )
