import pytest
from fastapi import HTTPException

from app.services.cas_validator import is_valid_cas, normalize_cas, validate_cas_or_raise


def test_valid_cas_numbers() -> None:
    assert is_valid_cas("64-17-5")
    assert is_valid_cas("7732-18-5")
    assert is_valid_cas("50-00-0")


def test_normalize_cas_without_dashes() -> None:
    assert normalize_cas("64175") == "64-17-5"


def test_invalid_cas_numbers() -> None:
    assert not is_valid_cas("64-17-4")
    assert not is_valid_cas("1-22-3")
    assert not is_valid_cas("not-a-cas")
    with pytest.raises(HTTPException):
        validate_cas_or_raise("64-17-4")
