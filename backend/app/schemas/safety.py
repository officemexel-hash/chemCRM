from datetime import datetime
from typing import Literal

from pydantic import BaseModel, Field


DEFAULT_ALLOWED_TEST_OVERRIDES = [
    "default_approval",
    "missing_contact_evidence",
    "unknown_substance_review",
    "regulatory_review",
    "high_risk_manual_review",
    "marketplace_manual_review",
    "free_email_review",
]

HARD_BLOCKS = [
    "invalid_cas",
    "fraud_or_evasion",
    "restricted_or_blocked_substance",
    "messenger_without_consent",
    "manual_only_messenger",
    "captcha_or_login_bypass",
    "portal_terms_bypass",
    "automatic_account_registration",
    "real_external_send",
]


class SafetyOverrideUpdate(BaseModel):
    enabled: bool = True
    reason: str = Field(min_length=12, max_length=2000)
    expires_in_minutes: int = Field(default=60, ge=1, le=1440)
    confirm_test_only: Literal[True]
    allowed_overrides: list[str] = Field(default_factory=lambda: DEFAULT_ALLOWED_TEST_OVERRIDES.copy())


class SafetyOverrideRead(BaseModel):
    enabled: bool = False
    active: bool = False
    mode: str = "strict"
    reason: str | None = None
    enabled_by: str | None = None
    expires_at: datetime | None = None
    allowed_overrides: list[str] = Field(default_factory=list)
    hard_blocks: list[str] = Field(default_factory=lambda: HARD_BLOCKS.copy())
    production_locked: bool = False
