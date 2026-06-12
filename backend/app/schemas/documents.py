"""Document generation schemas — letterhead, Letter of Intent, Purchase Order."""

from pydantic import BaseModel, Field


# ── Transport modes affecting Incoterms ──

TRANSPORT_INCOTERMS: dict[str, list[str]] = {
    "sea": ["FOB", "CIF", "CFR", "FAS"],
    "air": ["FCA", "CPT", "CIP", "DAP"],
    "road": ["FCA", "CPT", "DAP", "DDP"],
    "rail": ["FCA", "CPT", "DAP"],
    "courier": ["DAP", "DDP"],
    "multimodal": ["FCA", "CPT", "CIP", "DAP", "DDP"],
}

INCOTERMS_RESPONSIBILITY: dict[str, dict[str, str]] = {
    "EXW": {"transport": "Buyer", "insurance": "Buyer", "customs_export": "Buyer", "customs_import": "Buyer", "unloading": "Buyer"},
    "FOB": {"transport": "Buyer", "insurance": "Buyer", "customs_export": "Seller", "customs_import": "Buyer", "unloading": "Buyer"},
    "CIF": {"transport": "Seller", "insurance": "Seller", "customs_export": "Seller", "customs_import": "Buyer", "unloading": "Buyer"},
    "FCA": {"transport": "Buyer", "insurance": "Buyer", "customs_export": "Seller", "customs_import": "Buyer", "unloading": "Buyer"},
    "CPT": {"transport": "Seller", "insurance": "Buyer", "customs_export": "Seller", "customs_import": "Buyer", "unloading": "Buyer"},
    "CIP": {"transport": "Seller", "insurance": "Seller", "customs_export": "Seller", "customs_import": "Buyer", "unloading": "Buyer"},
    "DAP": {"transport": "Seller", "insurance": "Seller", "customs_export": "Seller", "customs_import": "Buyer", "unloading": "Buyer"},
    "DDP": {"transport": "Seller", "insurance": "Seller", "customs_export": "Seller", "customs_import": "Seller", "unloading": "Seller"},
    "CFR": {"transport": "Seller", "insurance": "Buyer", "customs_export": "Seller", "customs_import": "Buyer", "unloading": "Buyer"},
    "FAS": {"transport": "Buyer", "insurance": "Buyer", "customs_export": "Seller", "customs_import": "Buyer", "unloading": "Buyer"},
}


# ── Letterhead ──

class CompanyLetterheadData(BaseModel):
    legal_name: str = ""
    trading_name: str | None = None
    registration_number: str | None = None
    vat_number: str | None = None
    eori_number: str | None = None
    website: str | None = None
    address: str | None = None
    country: str | None = None
    phone: str | None = None
    email: str | None = None


class LetterheadRequest(BaseModel):
    company: CompanyLetterheadData | None = None
    reference_number: str | None = None
    date: str | None = None
    title: str | None = None


class LetterheadResponse(BaseModel):
    html: str
    text: str
    generated_document_id: str | None = None


# ── Letter of Intent (LOI) ──

class LetterOfIntentRequest(BaseModel):
    company: CompanyLetterheadData | None = None
    recipient_name: str
    recipient_company: str
    substance_name: str
    substance_cas: str
    quantity: str = ""
    intended_use: str = ""
    destination_country: str = ""
    additional_notes: str = ""
    reference_number: str | None = None
    campaign_id: str | None = None
    company_id: str | None = None
    substance_id: str | None = None
    save_to_crm: bool = False


class LetterOfIntentResponse(BaseModel):
    subject: str
    html: str
    text: str
    pdf_ready: bool = False
    generated_document_id: str | None = None


# ── Purchase Order (PO) ──

class PurchaseOrderRequest(BaseModel):
    company: CompanyLetterheadData | None = None
    supplier_name: str
    supplier_address: str = ""
    supplier_contact: str = ""
    substance_name: str
    substance_cas: str
    quantity: str
    unit: str = "kg"
    price_per_unit: str = ""
    currency: str = "USD"
    incoterms: str = "EXW"
    transport_mode: str = "road"
    payment_terms: str = "T/T 30% advance, 70% against B/L copy"
    delivery_address: str = ""
    delivery_deadline: str = ""
    special_requirements: str = ""
    hs_code: str = ""
    customs_duty_rate: str = ""
    legal_use_description: str = ""
    reference_number: str | None = None
    campaign_id: str | None = None
    quote_id: str | None = None
    company_id: str | None = None
    substance_id: str | None = None
    save_to_crm: bool = False


class PurchaseOrderResponse(BaseModel):
    po_number: str
    subject: str
    html: str
    text: str
    incoterms_responsibility: dict[str, str]
    transport_mode: str
    suggested_incoterms: list[str]
    pdf_ready: bool = False
    generated_document_id: str | None = None


class IncotermsGuideResponse(BaseModel):
    transport_mode: str
    available_incoterms: list[str]
    responsibility_matrix: dict[str, dict[str, str]]


# ── Customs duty ──

class CustomsDutyRequest(BaseModel):
    hs_code: str = ""
    substance_name: str = ""
    cas: str = ""
    origin_country: str = ""
    destination_country: str = ""


class CustomsDutyResponse(BaseModel):
    hs_code: str
    hs_code_description: str
    duty_rate: str
    vat_rate: str
    additional_taxes: list[str]
    legal_uses: list[str]
    regulatory_notes: list[str]
    source: str = "mock"
    source_url: str | None = None
    effective_date: str | None = None
    confidence: float = 0.0
    manual_review_required: bool = True
    assumptions: list[str] = Field(default_factory=list)


# ── Substance analogs ──

class SubstanceAnalog(BaseModel):
    cas: str
    name: str
    iupac_name: str | None = None
    molecular_formula: str | None = None
    structural_similarity: str = ""
    functional_similarity: str = ""
    price_indication: str = ""
    advantages: list[str] = Field(default_factory=list)
    disadvantages: list[str] = Field(default_factory=list)
    similarity_basis: list[str] = Field(default_factory=list)
    requires_validation: bool = True


class SubstanceAnalogsRequest(BaseModel):
    cas: str
    primary_name: str = ""
    target_application: str = ""


class SubstanceAnalogsResponse(BaseModel):
    source_cas: str
    source_name: str
    analogs: list[SubstanceAnalog]
    recommendation: str = ""
