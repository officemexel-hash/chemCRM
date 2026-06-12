from fastapi.testclient import TestClient

from app.core.middleware import validate_production_settings
from app.main import app


def test_security_headers_are_set() -> None:
    with TestClient(app) as client:
        response = client.get("/health")
    assert response.status_code == 200
    assert response.headers["X-Content-Type-Options"] == "nosniff"
    assert response.headers["X-Frame-Options"] == "DENY"
    assert response.headers["X-Request-ID"]


def test_production_settings_reject_default_secret() -> None:
    try:
        validate_production_settings("production", "change-me-in-production", ["https://crm.example"])
    except RuntimeError as exc:
        assert "SECRET_KEY" in str(exc)
    else:
        raise AssertionError("production default SECRET_KEY should fail readiness validation")
