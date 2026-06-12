from decimal import Decimal

from pydantic import BaseModel, Field


class SubstanceCreate(BaseModel):
    cas: str
    primary_name: str | None = None


class SubstanceSynonymRead(BaseModel):
    id: str
    synonym: str
    source: str | None = None

    model_config = {"from_attributes": True}


class RegulatoryFlagRead(BaseModel):
    id: str
    flag_type: str | None = None
    severity: str | None = None
    source: str | None = None
    description: str | None = None

    model_config = {"from_attributes": True}


class SubstanceRead(BaseModel):
    id: str
    cas: str
    primary_name: str | None = None
    iupac_name: str | None = None
    molecular_formula: str | None = None
    molecular_weight: Decimal | None = None
    pubchem_cid: str | None = None
    ec_number: str | None = None
    hs_code_suggested: str | None = None
    hs_code_confidence: Decimal | None = None
    regulatory_status: str | None = None
    requires_manual_review: bool = False
    synonyms: list[SubstanceSynonymRead] = Field(default_factory=list)
    regulatory_flags: list[RegulatoryFlagRead] = Field(default_factory=list)

    model_config = {"from_attributes": True}


class SubstanceEnrichmentRead(BaseModel):
    cas: str
    primary_name: str | None = None
    iupac_name: str | None = None
    molecular_formula: str | None = None
    molecular_weight: float | None = None
    pubchem_cid: str | None = None
    synonyms: list[str] = Field(default_factory=list)
    ec_number: str | None = None
    data_sources: list[str] = Field(default_factory=list)
    confidence: float = 0.0
    requires_manual_review: bool = False
    warnings: list[str] = Field(default_factory=list)
