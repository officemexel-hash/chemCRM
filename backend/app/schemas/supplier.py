from decimal import Decimal

from pydantic import BaseModel, Field, HttpUrl


class SupplierContactCreate(BaseModel):
    channel: str
    value: str
    contact_person: str | None = None
    source_url: str | None = None
    evidence_text: str | None = None
    consent_status: str | None = "unknown"
    consent_evidence_id: str | None = None
    is_primary: bool = False


class SupplierContactRead(SupplierContactCreate):
    id: str
    company_id: str

    model_config = {"from_attributes": True}


class SupplierCreate(BaseModel):
    name: str
    website: str | None = None
    country: str | None = None
    address: str | None = None
    company_type: str | None = "UNKNOWN"
    registration_number: str | None = None
    vat_number: str | None = None
    eori_number: str | None = None
    verified_status: str | None = None
    notes: str | None = None
    contacts: list[SupplierContactCreate] = Field(default_factory=list)


class SupplierUpdate(BaseModel):
    name: str | None = None
    website: str | None = None
    country: str | None = None
    address: str | None = None
    company_type: str | None = None
    registration_number: str | None = None
    vat_number: str | None = None
    eori_number: str | None = None
    verified_status: str | None = None
    supplier_score: Decimal | None = None
    risk_score: Decimal | None = None
    risk_level: str | None = None
    notes: str | None = None


class SupplierRead(BaseModel):
    id: str
    name: str
    website: str | None = None
    country: str | None = None
    address: str | None = None
    company_type: str | None = None
    registration_number: str | None = None
    vat_number: str | None = None
    eori_number: str | None = None
    verified_status: str | None = None
    supplier_score: Decimal = 0
    risk_score: Decimal = 0
    risk_level: str | None = None
    notes: str | None = None
    contacts: list[SupplierContactRead] = Field(default_factory=list)

    model_config = {"from_attributes": True}


class SupplierClassificationRead(BaseModel):
    company_type: str
    supplier_score: int
    risk_score: int
    risk_level: str
    risk_flags: list[str]
    confidence: float
