from decimal import Decimal

from sqlalchemy import ForeignKey, JSON, Numeric, String, Text
from sqlalchemy.orm import Mapped, mapped_column, relationship

from app.db.base import Base, TimestampMixin, new_uuid


class SubstanceManufacturingAnalysis(Base, TimestampMixin):
    __tablename__ = "substance_manufacturing_analyses"

    id: Mapped[str] = mapped_column(String(36), primary_key=True, default=new_uuid)
    substance_id: Mapped[str] = mapped_column(
        String(36), ForeignKey("substances.id", ondelete="CASCADE"), nullable=False, index=True
    )
    target_quantity: Mapped[str | None] = mapped_column(Text)
    target_grade: Mapped[str | None] = mapped_column(Text)
    intended_use: Mapped[str | None] = mapped_column(Text)
    destination_country: Mapped[str | None] = mapped_column(Text)
    status: Mapped[str] = mapped_column(Text, default="draft")
    route_type: Mapped[str | None] = mapped_column(Text)
    process_overview: Mapped[str | None] = mapped_column(Text)
    required_equipment: Mapped[list | None] = mapped_column(JSON, default=list)
    input_materials: Mapped[list | None] = mapped_column(JSON, default=list)
    cost_drivers: Mapped[list | None] = mapped_column(JSON, default=list)
    cost_model: Mapped[dict | None] = mapped_column(JSON, default=dict)
    sourcing_queries: Mapped[list | None] = mapped_column(JSON, default=list)
    compliance_notes: Mapped[list | None] = mapped_column(JSON, default=list)
    safety_notes: Mapped[list | None] = mapped_column(JSON, default=list)
    blocked_reasons: Mapped[list | None] = mapped_column(JSON, default=list)
    confidence: Mapped[Decimal | None] = mapped_column(Numeric)

    substance = relationship("Substance", back_populates="manufacturing_analyses")
