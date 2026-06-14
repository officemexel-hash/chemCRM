import re

from fastapi import HTTPException, status


CAS_PATTERN = re.compile(r"^(\d{2,7})-(\d{2})-(\d)$")


def normalize_cas(cas: str) -> str:
    cleaned = cas.strip().replace("–", "-").replace("—", "-")
    cleaned = re.sub(r"\s+", "", cleaned)
    if "-" not in cleaned and cleaned.isdigit() and 5 <= len(cleaned) <= 10:
        return f"{cleaned[:-3]}-{cleaned[-3:-1]}-{cleaned[-1]}"
    return cleaned


def is_valid_cas(cas: str) -> bool:
    normalized = normalize_cas(cas)
    match = CAS_PATTERN.match(normalized)
    if not match:
        return False
    first, second, check_digit_text = match.groups()
    digits = f"{first}{second}"
    checksum = sum(int(digit) * multiplier for multiplier, digit in enumerate(reversed(digits), 1))
    return checksum % 10 == int(check_digit_text)


def validate_cas_or_raise(cas: str) -> str:
    normalized = normalize_cas(cas)
    if not is_valid_cas(normalized):
        raise HTTPException(
            status_code=status.HTTP_422_UNPROCESSABLE_CONTENT,
            detail="Invalid CAS number format or checksum",
        )
    return normalized
