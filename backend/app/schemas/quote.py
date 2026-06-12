from decimal import Decimal

from pydantic import BaseModel, Field


class QuotePatch(BaseModel):
    status: str | None = None
    price: Decimal | None = None
    currency: str | None = None
    incoterms: str | None = None
    lead_time: str | None = None
    payment_terms: str | None = None
    red_flags: list | None = None
    missing_questions: list | None = None


class QuoteRead(BaseModel):
    id: str
    company_id: str
    substance_id: str
    campaign_id: str
    quantity: str | None = None
    price: Decimal | None = None
    currency: str | None = None
    unit: str | None = None
    incoterms: str | None = None
    lead_time: str | None = None
    moq: str | None = None
    payment_terms: str | None = None
    sample_available: bool | None = None
    sample_price: str | None = None
    packaging: str | None = None
    coa_available: bool | None = None
    sds_available: bool | None = None
    reach_status: str | None = None
    adr_class: str | None = None
    un_number: str | None = None
    hs_code: str | None = None
    shelf_life: str | None = None
    certificates: list = Field(default_factory=list)
    production_capacity: str | None = None
    red_flags: list = Field(default_factory=list)
    missing_questions: list = Field(default_factory=list)
    confidence: Decimal | None = None
    status: str | None = None
    extracted_from_message_id: str | None = None

    model_config = {"from_attributes": True}
