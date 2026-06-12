import time
import uuid
from collections.abc import Awaitable, Callable

from fastapi import Request, Response


async def security_headers_middleware(
    request: Request, call_next: Callable[[Request], Awaitable[Response]]
) -> Response:
    request_id = request.headers.get("x-request-id") or str(uuid.uuid4())
    start = time.perf_counter()
    response = await call_next(request)
    elapsed_ms = int((time.perf_counter() - start) * 1000)

    response.headers["X-Request-ID"] = request_id
    response.headers["X-Process-Time-Ms"] = str(elapsed_ms)
    response.headers["X-Content-Type-Options"] = "nosniff"
    response.headers["X-Frame-Options"] = "DENY"
    response.headers["Referrer-Policy"] = "strict-origin-when-cross-origin"
    response.headers["Permissions-Policy"] = "camera=(), microphone=(), geolocation=()"
    response.headers.setdefault("Cache-Control", "no-store")
    return response


def validate_production_settings(app_env: str, secret_key: str, cors_origins: list[str]) -> None:
    if app_env.lower() != "production":
        return
    if secret_key in {"dev-secret-change-me", "change-me-in-production", ""}:
        raise RuntimeError("SECRET_KEY must be changed for production")
    if "*" in cors_origins:
        raise RuntimeError("BACKEND_CORS_ORIGINS cannot contain '*' in production")
