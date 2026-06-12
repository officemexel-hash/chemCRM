"""Research schemas — substance research dossier, supplier interactions, production analysis."""

from pydantic import BaseModel, Field


# ── Incoterms by transport mode ──

INCOTERMS_BY_TRANSPORT = {
    "sea": {
        "available": ["FOB", "CIF", "CFR", "FAS"],
        "responsibility": {
            "FOB": {"export_clearance": "seller", "freight": "buyer", "insurance": "buyer", "import_clearance": "buyer", "unloading": "buyer"},
            "CIF": {"export_clearance": "seller", "freight": "seller", "insurance": "seller", "import_clearance": "buyer", "unloading": "buyer"},
            "CFR": {"export_clearance": "seller", "freight": "seller", "insurance": "buyer", "import_clearance": "buyer", "unloading": "buyer"},
            "FAS": {"export_clearance": "seller", "freight": "buyer", "insurance": "buyer", "import_clearance": "buyer", "unloading": "buyer"},
        },
    },
    "air": {
        "available": ["FCA", "CPT", "CIP", "DAP"],
        "responsibility": {
            "FCA": {"export_clearance": "seller", "freight": "buyer", "insurance": "buyer", "import_clearance": "buyer", "unloading": "buyer"},
            "CPT": {"export_clearance": "seller", "freight": "seller", "insurance": "buyer", "import_clearance": "buyer", "unloading": "buyer"},
            "CIP": {"export_clearance": "seller", "freight": "seller", "insurance": "seller", "import_clearance": "buyer", "unloading": "buyer"},
            "DAP": {"export_clearance": "seller", "freight": "seller", "insurance": "seller", "import_clearance": "buyer", "unloading": "buyer"},
        },
    },
    "road": {
        "available": ["FCA", "CPT", "DAP", "DDP"],
        "responsibility": {
            "FCA": {"export_clearance": "seller", "freight": "buyer", "insurance": "buyer", "import_clearance": "buyer", "unloading": "buyer"},
            "CPT": {"export_clearance": "seller", "freight": "seller", "insurance": "buyer", "import_clearance": "buyer", "unloading": "buyer"},
            "DAP": {"export_clearance": "seller", "freight": "seller", "insurance": "seller", "import_clearance": "buyer", "unloading": "buyer"},
            "DDP": {"export_clearance": "seller", "freight": "seller", "insurance": "seller", "import_clearance": "seller", "unloading": "seller"},
        },
    },
    "rail": {
        "available": ["FCA", "CPT", "DAP"],
        "responsibility": {
            "FCA": {"export_clearance": "seller", "freight": "buyer", "insurance": "buyer", "import_clearance": "buyer", "unloading": "buyer"},
            "CPT": {"export_clearance": "seller", "freight": "seller", "insurance": "buyer", "import_clearance": "buyer", "unloading": "buyer"},
            "DAP": {"export_clearance": "seller", "freight": "seller", "insurance": "seller", "import_clearance": "buyer", "unloading": "buyer"},
        },
    },
    "multimodal": {
        "available": ["FCA", "CPT", "CIP", "DAP", "DDP"],
        "responsibility": {
            "FCA": {"export_clearance": "seller", "freight": "buyer", "insurance": "buyer", "import_clearance": "buyer", "unloading": "buyer"},
            "CPT": {"export_clearance": "seller", "freight": "seller", "insurance": "buyer", "import_clearance": "buyer", "unloading": "buyer"},
            "CIP": {"export_clearance": "seller", "freight": "seller", "insurance": "seller", "import_clearance": "buyer", "unloading": "buyer"},
            "DAP": {"export_clearance": "seller", "freight": "seller", "insurance": "seller", "import_clearance": "buyer", "unloading": "buyer"},
            "DDP": {"export_clearance": "seller", "freight": "seller", "insurance": "seller", "import_clearance": "seller", "unloading": "seller"},
        },
    },
}


# ── Schemas ──

class SubProductSource(BaseModel):
    cas: str = ""
    name: str = ""
    quantity_per_kg: str = ""
    estimated_price: str = ""
    supplier_found: bool = False
    supplier_id: str | None = None
    supplier_name: str | None = None
    supplier_contact: str | None = None


class EquipmentItem(BaseModel):
    name: str
    estimated_cost_usd: float = 0
    type: str = ""


class ProductionMethodRead(BaseModel):
    id: str
    method_name: str = ""
    method_description: str = ""
    yield_percentage: float | None = None
    difficulty_level: str = "moderate"
    equipment_needed: list[EquipmentItem] = Field(default_factory=list)
    sub_products: list[SubProductSource] = Field(default_factory=list)
    raw_materials_cost: float | None = None
    equipment_amortization: float | None = None
    labor_cost_estimate: float | None = None
    utilities_cost_estimate: float | None = None
    total_production_cost_per_kg: float | None = None
    currency: str = "USD"
    safety_notes: str = ""
    waste_disposal_notes: str = ""
    permits_needed: list[str] = Field(default_factory=list)


class SupplierInteractionRead(BaseModel):
    id: str
    supplier_id: str | None = None
    supplier_name: str = ""
    supplier_country: str = ""
    supplier_type: str = ""
    contact_channel: str = ""
    contact_person: str = ""
    contact_value: str = ""
    outreach_date: str = ""
    response_date: str = ""
    response_received: bool = False
    response_summary: str = ""
    price_per_unit: float | None = None
    currency: str = "USD"
    unit: str = "kg"
    moq: str = ""
    incoterms_offered: list[str] = Field(default_factory=list)
    payment_terms: str = ""
    lead_time: str = ""
    sample_available: bool = False
    coa_available: bool = False
    sds_available: bool = False
    reach_registered: bool = False
    packaging_options: list[str] = Field(default_factory=list)
    transport_modes_available: list[str] = Field(default_factory=list)
    status: str = "contacted"
    rating: int = 0
    notes: str = ""
    follow_up_needed: bool = False


class SubstanceResearchRead(BaseModel):
    id: str
    substance_id: str
    substance_name: str = ""
    substance_cas: str = ""
    status: str = "active"
    total_suppliers_contacted: int = 0
    total_responses: int = 0
    total_quotes_received: int = 0
    best_price: float | None = None
    best_price_currency: str = "USD"
    best_price_incoterms: str = ""
    best_price_supplier_id: str | None = None
    tags: list[str] = Field(default_factory=list)
    research_notes: str = ""
    interactions: list[SupplierInteractionRead] = Field(default_factory=list)
    production_analyses: list[ProductionMethodRead] = Field(default_factory=list)


class SupplierInteractionCreate(BaseModel):
    supplier_name: str = ""
    supplier_country: str = ""
    supplier_type: str = ""
    contact_channel: str = "email"
    contact_person: str = ""
    contact_value: str = ""
    response_received: bool = False
    response_summary: str = ""
    price_per_unit: float | None = None
    currency: str = "USD"
    unit: str = "kg"
    moq: str = ""
    incoterms_offered: list[str] = Field(default_factory=list)
    payment_terms: str = ""
    lead_time: str = ""
    sample_available: bool = False
    coa_available: bool = False
    sds_available: bool = False
    reach_registered: bool = False
    packaging_options: list[str] = Field(default_factory=list)
    transport_modes_available: list[str] = Field(default_factory=list)
    status: str = "contacted"
    rating: int = 0
    notes: str = ""


class ProductionAnalysisCreate(BaseModel):
    method_name: str
    method_description: str = ""
    yield_percentage: float | None = None
    difficulty_level: str = "moderate"
    equipment_needed: list[EquipmentItem] = Field(default_factory=list)
    sub_products: list[SubProductSource] = Field(default_factory=list)
    safety_notes: str = ""
    waste_disposal_notes: str = ""
    permits_needed: list[str] = Field(default_factory=list)


class ResearchDossierResponse(BaseModel):
    substance_id: str
    substance_name: str
    substance_cas: str
    research: SubstanceResearchRead
    incoterms_guide: dict = Field(default_factory=dict)


class IncotermsComparisonRow(BaseModel):
    incoterms: str
    transport_modes: list[str] = Field(default_factory=list)
    export_clearance: str = ""
    freight: str = ""
    insurance: str = ""
    import_clearance: str = ""
    unloading: str = ""
    best_for: str = ""


class IncotermsComparisonResponse(BaseModel):
    substance_id: str
    rows: list[IncotermsComparisonRow] = Field(default_factory=list)
