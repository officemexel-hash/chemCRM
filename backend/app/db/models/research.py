"""Substance Research Database — tracks everything learned about a substance:
- Supplier contacts and interactions
- Production analysis (equipment, sub-products, costs)
- Incoterms comparison across transport modes
- Packaging, pricing, and terms from each supplier
"""

from sqlalchemy import Boolean, DateTime, Float, ForeignKey, JSON, String, Text
from sqlalchemy.orm import Mapped, mapped_column, relationship

from app.db.base import Base, CreatedAtMixin, new_uuid, utc_now


# ── Substance Research (one per substance) ──

class SubstanceResearch(Base, CreatedAtMixin):
    """Aggregated research dossier for a single chemical substance."""
    __tablename__ = "substance_research"

    id: Mapped[str] = mapped_column(String(36), primary_key=True, default=new_uuid)
    substance_id: Mapped[str] = mapped_column(
        String(36), ForeignKey("substances.id", ondelete="CASCADE"), nullable=False, unique=True, index=True
    )
    status: Mapped[str] = mapped_column(Text, default="active")  # active, archived, complete

    # Summary stats (denormalized for fast display)
    total_suppliers_contacted: Mapped[int] = mapped_column(default=0)
    total_responses: Mapped[int] = mapped_column(default=0)
    total_quotes_received: Mapped[int] = mapped_column(default=0)
    best_price: Mapped[float | None] = mapped_column(nullable=True)
    best_price_currency: Mapped[str | None] = mapped_column(Text, nullable=True)
    best_price_incoterms: Mapped[str | None] = mapped_column(Text, nullable=True)
    best_price_supplier_id: Mapped[str | None] = mapped_column(String(36), nullable=True)

    # Notes and tags
    tags: Mapped[list | None] = mapped_column(JSON, default=list)
    research_notes: Mapped[str | None] = mapped_column(Text)

    # Relationships
    substance = relationship("Substance", backref="research_dossier")
    interactions = relationship("SupplierInteraction", back_populates="research", cascade="all, delete-orphan")
    production_analyses = relationship("ProductionAnalysis", back_populates="research", cascade="all, delete-orphan")


# ── Supplier Interaction Log ──

class SupplierInteraction(Base, CreatedAtMixin):
    """Records every contact attempt, response, and outcome with a supplier for a substance."""
    __tablename__ = "supplier_interactions"

    id: Mapped[str] = mapped_column(String(36), primary_key=True, default=new_uuid)
    research_id: Mapped[str] = mapped_column(
        String(36), ForeignKey("substance_research.id", ondelete="CASCADE"), nullable=False, index=True
    )
    supplier_id: Mapped[str] = mapped_column(
        String(36), ForeignKey("supplier_companies.id", ondelete="SET NULL"), nullable=True, index=True
    )
    supplier_name: Mapped[str | None] = mapped_column(Text)
    supplier_country: Mapped[str | None] = mapped_column(Text)
    supplier_type: Mapped[str | None] = mapped_column(Text)  # manufacturer, distributor, trader

    # Contact details
    contact_channel: Mapped[str | None] = mapped_column(Text)  # email, whatsapp, alibaba_internal, form, etc.
    contact_person: Mapped[str | None] = mapped_column(Text)
    contact_value: Mapped[str | None] = mapped_column(Text)  # email address, phone number, etc.
    outreach_date: Mapped[str | None] = mapped_column(Text)  # ISO date
    response_date: Mapped[str | None] = mapped_column(Text)
    response_received: Mapped[bool] = mapped_column(default=False)
    response_summary: Mapped[str | None] = mapped_column(Text)  # TLDR of what they said

    # Terms offered
    price_per_unit: Mapped[float | None] = mapped_column(nullable=True)
    currency: Mapped[str | None] = mapped_column(Text, default="USD")
    unit: Mapped[str | None] = mapped_column(Text, default="kg")
    moq: Mapped[str | None] = mapped_column(Text)
    incoterms_offered: Mapped[list | None] = mapped_column(JSON, default=list)  # ["FOB", "CIF", "EXW"]
    payment_terms: Mapped[str | None] = mapped_column(Text)
    lead_time: Mapped[str | None] = mapped_column(Text)
    sample_available: Mapped[bool | None] = mapped_column(default=False)

    # Documentation
    coa_available: Mapped[bool | None] = mapped_column(default=False)
    sds_available: Mapped[bool | None] = mapped_column(default=False)
    reach_registered: Mapped[bool | None] = mapped_column(default=False)
    packaging_options: Mapped[list | None] = mapped_column(JSON, default=list)  # ["25kg drum", "1000kg IBC"]

    # Transport & logistics
    transport_modes_available: Mapped[list | None] = mapped_column(JSON, default=list)  # ["sea", "road", "air"]

    # Outcome
    status: Mapped[str | None] = mapped_column(Text, default="contacted")  # contacted, responded, quoted, negotiating, closed_won, closed_lost, blocked
    rating: Mapped[int | None] = mapped_column(default=0)  # 1-5 star rating
    notes: Mapped[str | None] = mapped_column(Text)
    follow_up_needed: Mapped[bool] = mapped_column(default=False)

    # Relationships
    research = relationship("SubstanceResearch", back_populates="interactions")
    supplier = relationship("SupplierCompany")


# ── Production Analysis ──

class ProductionAnalysis(Base, CreatedAtMixin):
    """Analysis of what's needed to produce this substance: equipment, sub-products, cost structure."""
    __tablename__ = "production_analyses"

    id: Mapped[str] = mapped_column(String(36), primary_key=True, default=new_uuid)
    research_id: Mapped[str] = mapped_column(
        String(36), ForeignKey("substance_research.id", ondelete="CASCADE"), nullable=False, index=True
    )

    # Production method
    method_name: Mapped[str | None] = mapped_column(Text)  # e.g., "Fischer esterification", "Grignard reaction"
    method_description: Mapped[str | None] = mapped_column(Text)
    yield_percentage: Mapped[float | None] = mapped_column(nullable=True)
    difficulty_level: Mapped[str | None] = mapped_column(Text)  # easy, moderate, difficult, industrial_only

    # Equipment needed
    equipment_needed: Mapped[list | None] = mapped_column(JSON, default=list)
    # [{"name": "Reactor 500L glass-lined", "estimated_cost_usd": 50000, "type": "reactor"},
    #  {"name": "Distillation column", "estimated_cost_usd": 30000, "type": "separation"}]

    # Sub-products / precursors / intermediates needed
    sub_products: Mapped[list | None] = mapped_column(JSON, default=list)
    # [{"cas": "64-19-7", "name": "Acetic acid", "quantity_per_kg": "0.65 kg", "estimated_price": "0.80 USD/kg",
    #   "supplier_found": true, "supplier_id": "xxx", "supplier_name": "Acme Chemicals"}]

    # Cost breakdown
    raw_materials_cost: Mapped[float | None] = mapped_column(nullable=True)
    equipment_amortization: Mapped[float | None] = mapped_column(nullable=True)
    labor_cost_estimate: Mapped[float | None] = mapped_column(nullable=True)
    utilities_cost_estimate: Mapped[float | None] = mapped_column(nullable=True)
    total_production_cost_per_kg: Mapped[float | None] = mapped_column(nullable=True)
    currency: Mapped[str | None] = mapped_column(Text, default="USD")

    # Safety & regulatory
    safety_notes: Mapped[str | None] = mapped_column(Text)
    waste_disposal_notes: Mapped[str | None] = mapped_column(Text)
    permits_needed: Mapped[list | None] = mapped_column(JSON, default=list)

    research = relationship("SubstanceResearch", back_populates="production_analyses")
