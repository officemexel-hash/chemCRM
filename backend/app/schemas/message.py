from datetime import datetime

from pydantic import BaseModel, Field


class OutboundMessageCreate(BaseModel):
    campaign_id: str
    company_id: str
    contact_id: str
    channel: str
    subject: str | None = None
    body: str


class OutboundMessageRead(BaseModel):
    id: str
    campaign_id: str
    company_id: str
    contact_id: str
    channel: str | None = None
    subject: str | None = None
    body: str | None = None
    status: str | None = None
    policy_decision: str | None = None
    policy_reasons: list = Field(default_factory=list)
    approval_required: bool = True
    approved_by: str | None = None
    approved_at: datetime | None = None
    sent_at: datetime | None = None
    external_message_id: str | None = None

    model_config = {"from_attributes": True}


class InboundMessageCreate(BaseModel):
    company_id: str
    campaign_id: str | None = None
    channel: str = "email"
    from_address: str | None = None
    subject: str | None = None
    body: str
    external_message_id: str | None = None
    thread_id: str | None = None


class InboundMessageRead(BaseModel):
    id: str
    company_id: str
    campaign_id: str | None = None
    channel: str | None = None
    from_address: str | None = None
    subject: str | None = None
    body: str | None = None
    received_at: datetime | None = None
    parsed: bool = False
    external_message_id: str | None = None
    thread_id: str | None = None

    model_config = {"from_attributes": True}


class BatchApproveRequest(BaseModel):
    campaign_id: str
    message_ids: list[str] | None = None  # None = all pending for campaign


class BatchApproveResultItem(BaseModel):
    message_id: str
    status: str  # approved, skipped, blocked


class BatchApproveResponse(BaseModel):
    approved: int
    skipped: int
    blocked: int
    results: list[BatchApproveResultItem]
