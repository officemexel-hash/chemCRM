from enum import StrEnum

from pydantic import BaseModel, Field


class PolicyDecisionValue(StrEnum):
    DRAFT_ONLY = "DRAFT_ONLY"
    REQUIRES_APPROVAL = "REQUIRES_APPROVAL"
    ALLOW_AUTO_SEND = "ALLOW_AUTO_SEND"
    TEST_OVERRIDE_ALLOW = "TEST_OVERRIDE_ALLOW"
    LOG_ONLY = "LOG_ONLY"
    BLOCK = "BLOCK"


class PolicyDecision(BaseModel):
    decision: PolicyDecisionValue
    reasons: list[str] = Field(default_factory=list)
    required_actions: list[str] = Field(default_factory=list)


class ChannelPolicyConfig(BaseModel):
    channel: str  # email, telegram, whatsapp, alibaba_internal, etc.
    strictness: str = "standard"  # strict, standard, log_only
    auto_approve_low_risk: bool = False
    require_documents: bool = True
