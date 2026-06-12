from datetime import datetime
from decimal import Decimal

from pydantic import BaseModel, Field


class SubstanceProfileSummary(BaseModel):
    id: str
    cas: str
    primary_name: str | None = None
    regulatory_status: str | None = None
    requires_manual_review: bool = False
    supplier_count: int = 0
    contact_count: int = 0
    quote_count: int = 0
    offer_count: int = 0
    countries: list[str] = Field(default_factory=list)
    best_price: Decimal | None = None
    best_price_currency: str | None = None
    best_price_unit: str | None = None


class SubstanceContactRecord(BaseModel):
    id: str
    channel: str
    value: str
    contact_person: str | None = None
    source_url: str | None = None
    evidence_text: str | None = None
    consent_status: str | None = None


class SubstanceContactHistoryItem(BaseModel):
    id: str
    direction: str
    company_id: str
    channel: str | None = None
    subject: str | None = None
    status: str | None = None
    policy_decision: str | None = None
    timestamp: datetime | None = None
    summary: str | None = None


class SubstanceQuoteTerms(BaseModel):
    id: str
    campaign_id: str
    quantity: str | None = None
    price: Decimal | None = None
    currency: str | None = None
    unit: str | None = None
    incoterms: str | None = None
    transport_mode: str | None = None
    lead_time: str | None = None
    moq: str | None = None
    payment_terms: str | None = None
    packaging: str | None = None
    coa_available: bool | None = None
    sds_available: bool | None = None
    reach_status: str | None = None
    adr_class: str | None = None
    un_number: str | None = None
    hs_code: str | None = None
    confidence: Decimal | None = None
    status: str | None = None


class SubstanceProductOfferRecord(BaseModel):
    id: str
    source_url: str | None = None
    listed_name: str | None = None
    listed_cas: str | None = None
    grade: str | None = None
    purity: str | None = None
    moq: str | None = None
    price_text: str | None = None
    currency: str | None = None
    last_seen_at: datetime | None = None


class SubstanceSupplierRecord(BaseModel):
    id: str
    name: str
    website: str | None = None
    country: str | None = None
    company_type: str | None = None
    supplier_score: Decimal | None = None
    risk_score: Decimal | None = None
    risk_level: str | None = None
    contacts: list[SubstanceContactRecord] = Field(default_factory=list)
    quotes: list[SubstanceQuoteTerms] = Field(default_factory=list)
    product_offers: list[SubstanceProductOfferRecord] = Field(default_factory=list)
    contact_history: list[SubstanceContactHistoryItem] = Field(default_factory=list)
    latest_contact_at: datetime | None = None
    quoted_packaging: list[str] = Field(default_factory=list)
    quoted_incoterms: list[str] = Field(default_factory=list)


class IncotermsTransportProfile(BaseModel):
    transport_mode: str
    recommended_incoterms: list[str]
    responsibility_matrix: dict[str, dict[str, str]]


class SubstanceSourcingProfileRead(BaseModel):
    summary: SubstanceProfileSummary
    suppliers: list[SubstanceSupplierRecord] = Field(default_factory=list)
    incoterms_by_transport: list[IncotermsTransportProfile] = Field(default_factory=list)
    open_questions: list[str] = Field(default_factory=list)


class ManufacturingAnalysisRequest(BaseModel):
    target_quantity: str | None = None
    target_grade: str | None = None
    intended_use: str | None = None
    destination_country: str | None = None
    include_raw_material_sourcing: bool = True
    create_raw_material_tasks: bool = False
    save_to_crm: bool = True


class SubstanceManufacturingAnalysisRead(BaseModel):
    id: str | None = None
    substance_id: str
    target_quantity: str | None = None
    target_grade: str | None = None
    intended_use: str | None = None
    destination_country: str | None = None
    status: str
    route_type: str | None = None
    process_overview: str | None = None
    required_equipment: list[dict] = Field(default_factory=list)
    input_materials: list[dict] = Field(default_factory=list)
    cost_drivers: list[dict] = Field(default_factory=list)
    cost_model: dict = Field(default_factory=dict)
    sourcing_queries: list[dict] = Field(default_factory=list)
    compliance_notes: list[str] = Field(default_factory=list)
    safety_notes: list[str] = Field(default_factory=list)
    blocked_reasons: list[str] = Field(default_factory=list)
    confidence: Decimal | None = None
    created_at: datetime | None = None
    updated_at: datetime | None = None

    model_config = {"from_attributes": True}
