from datetime import datetime
from decimal import Decimal

from pydantic import BaseModel, Field


class HsCodeRead(BaseModel):
    id: str
    hs_code: str
    chapter: str | None
    heading: str | None
    subheading: str | None
    description: str | None
    cas_pattern: str | None
    source_database: str
    confidence: Decimal | None

    model_config = {"from_attributes": True}


class TariffRateRead(BaseModel):
    id: str
    hs_code_id: str
    origin_country: str
    destination_country: str
    duty_rate_percent: Decimal | None
    duty_type: str | None
    preferential_rate: Decimal | None
    preferential_source: str | None
    anti_dumping_rate: Decimal | None
    source_database: str

    model_config = {"from_attributes": True}


class LegalUseRead(BaseModel):
    id: str
    substance_id: str
    description: str
    category: str | None
    destination_country: str | None
    source: str | None

    model_config = {"from_attributes": True}


class ResponsibilityMatrixRow(BaseModel):
    cost_type: str  # freight, insurance, customs_clearance, import_duty, terminal_handling, delivery, export_clearance
    responsible_party: str  # buyer, seller
    notes: str | None = None


class TariffLookupRequest(BaseModel):
    substance_id: str | None = None
    cas: str | None = None
    hs_code: str | None = None
    origin_country: str | None = None
    destination_country: str | None = None
