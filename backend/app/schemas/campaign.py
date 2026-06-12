from pydantic import BaseModel, Field


class CampaignCreate(BaseModel):
    substance_id: str
    quantity: str | None = None
    destination_country: str | None = None
    required_grade: str | None = None
    intended_use: str | None = None
    requirements: dict = Field(default_factory=dict)
    auto_send_enabled: bool = False


class CampaignRead(BaseModel):
    id: str
    substance_id: str
    quantity: str | None = None
    destination_country: str | None = None
    required_grade: str | None = None
    intended_use: str | None = None
    requirements: dict | None = None
    status: str | None = None
    auto_send_enabled: bool = False
    created_by: str | None = None

    model_config = {"from_attributes": True}


class CampaignComparisonRow(BaseModel):
    quote_id: str
    supplier: str
    country: str | None
    price: float | None
    currency: str | None
    unit: str | None
    moq: str | None
    incoterms: str | None
    lead_time: str | None
    payment_terms: str | None
    coa_available: bool | None
    sds_available: bool | None
    reach_status: str | None
    adr_class: str | None
    risk_level: str | None
    confidence: float | None
    best_quote: bool = False


class AutonomousRunRequest(BaseModel):
    supplier_ids: list[str] = Field(default_factory=list)
    dry_run: bool = False
    allow_duplicates: bool = False


class AutonomousRunItemRead(BaseModel):
    supplier_id: str
    contact_id: str | None = None
    outbound_message_id: str | None = None
    policy_decision: str
    status: str
    actions: list[str] = Field(default_factory=list)
    reasons: list[str] = Field(default_factory=list)


class AutonomousRunResponse(BaseModel):
    campaign_id: str
    dry_run: bool
    generated: int
    sent: int
    simulated: int = 0
    requires_approval: int
    blocked: int
    skipped: int
    items: list[AutonomousRunItemRead] = Field(default_factory=list)
