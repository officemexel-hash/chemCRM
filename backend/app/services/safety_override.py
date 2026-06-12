from datetime import datetime, timedelta, timezone

from sqlalchemy.orm import Session

from app.db.models.settings import Setting
from app.db.models.user import User
from app.schemas.safety import (
    DEFAULT_ALLOWED_TEST_OVERRIDES,
    HARD_BLOCKS,
    SafetyOverrideRead,
    SafetyOverrideUpdate,
)


SAFETY_OVERRIDE_KEY = "safety_override"


class SafetyOverrideService:
    def __init__(self, db: Session, app_env: str = "development") -> None:
        self.db = db
        self.app_env = app_env.lower()

    def get(self) -> SafetyOverrideRead:
        row = self.db.get(Setting, SAFETY_OVERRIDE_KEY)
        if row is None or row.value is None:
            return SafetyOverrideRead(
                hard_blocks=HARD_BLOCKS.copy(),
                production_locked=self.app_env == "production",
            )
        state = SafetyOverrideRead.model_validate(row.value)
        active = state.enabled and state.expires_at is not None and state.expires_at > datetime.now(timezone.utc)
        if self.app_env == "production":
            active = False
        return state.model_copy(
            update={
                "active": active,
                "mode": "test_simulation" if active else "strict",
                "production_locked": self.app_env == "production",
                "hard_blocks": HARD_BLOCKS.copy(),
            }
        )

    def enable(self, payload: SafetyOverrideUpdate, user: User) -> SafetyOverrideRead:
        if self.app_env == "production":
            raise ValueError("Safety override cannot be enabled in production")
        if not payload.confirm_test_only:
            raise ValueError("confirm_test_only must be true")
        allowed = [
            item for item in payload.allowed_overrides if item in DEFAULT_ALLOWED_TEST_OVERRIDES
        ] or DEFAULT_ALLOWED_TEST_OVERRIDES.copy()
        state = SafetyOverrideRead(
            enabled=payload.enabled,
            active=payload.enabled,
            mode="test_simulation" if payload.enabled else "strict",
            reason=payload.reason,
            enabled_by=user.email,
            expires_at=datetime.now(timezone.utc) + timedelta(minutes=payload.expires_in_minutes)
            if payload.enabled
            else None,
            allowed_overrides=allowed,
            hard_blocks=HARD_BLOCKS.copy(),
            production_locked=False,
        )
        self._save(state)
        return self.get()

    def disable(self, user: User, reason: str) -> SafetyOverrideRead:
        state = SafetyOverrideRead(
            enabled=False,
            active=False,
            mode="strict",
            reason=reason,
            enabled_by=user.email,
            expires_at=None,
            allowed_overrides=[],
            hard_blocks=HARD_BLOCKS.copy(),
            production_locked=self.app_env == "production",
        )
        self._save(state)
        return self.get()

    def _save(self, state: SafetyOverrideRead) -> None:
        row = self.db.get(Setting, SAFETY_OVERRIDE_KEY)
        value = state.model_dump(mode="json")
        if row is None:
            row = Setting(key=SAFETY_OVERRIDE_KEY, value=value, updated_at=datetime.now(timezone.utc))
            self.db.add(row)
        else:
            row.value = value
            row.updated_at = datetime.now(timezone.utc)
        self.db.flush()
