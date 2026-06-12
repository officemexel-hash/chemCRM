from datetime import datetime

from pydantic import BaseModel


class POParameters(BaseModel):
    transport_type: str = "sea"  # sea, air, road, rail, courier
    incoterms: str = "FOB"  # EXW, FOB, CIF, DAP, DDP, etc.
    hs_code_override: str | None = None  # Override auto-detected HS code
    legal_use_description: str | None = None
    payment_terms: str | None = None
    delivery_address: str | None = None
    special_instructions: str | None = None


class RfqLetterRequest(BaseModel):
    campaign_id: str
    supplier_id: str


class LoiRequest(BaseModel):
    campaign_id: str
    quote_id: str


class PoRequest(BaseModel):
    campaign_id: str
    quote_id: str
    parameters: POParameters = POParameters()


class DocumentRead(BaseModel):
    id: str
    doc_type: str
    template_id: str | None
    campaign_id: str | None
    quote_id: str | None
    company_id: str | None
    substance_id: str | None
    file_path: str | None
    file_size_bytes: int | None
    parameters: dict | None
    status: str
    created_at: datetime

    model_config = {"from_attributes": True}
