from decimal import Decimal

from sqlalchemy import Boolean, ForeignKey, JSON, Numeric, String, Text
from sqlalchemy.orm import Mapped, mapped_column, relationship

from app.db.base import Base, CreatedAtMixin, new_uuid


class Quote(Base, CreatedAtMixin):
    __tablename__ = "quotes"

    id: Mapped[str] = mapped_column(String(36), primary_key=True, default=new_uuid)
    company_id: Mapped[str] = mapped_column(
        String(36), ForeignKey("supplier_companies.id", ondelete="CASCADE"), nullable=False
    )
    substance_id: Mapped[str] = mapped_column(
        String(36), ForeignKey("substances.id", ondelete="CASCADE"), nullable=False
    )
    campaign_id: Mapped[str] = mapped_column(
        String(36), ForeignKey("rfq_campaigns.id", ondelete="CASCADE"), nullable=False
    )
    quantity: Mapped[str | None] = mapped_column(Text)
    price: Mapped[Decimal | None] = mapped_column(Numeric)
    currency: Mapped[str | None] = mapped_column(Text)
    unit: Mapped[str | None] = mapped_column(Text)
    incoterms: Mapped[str | None] = mapped_column(Text)
    lead_time: Mapped[str | None] = mapped_column(Text)
    moq: Mapped[str | None] = mapped_column(Text)
    payment_terms: Mapped[str | None] = mapped_column(Text)
    sample_available: Mapped[bool | None] = mapped_column(Boolean, nullable=True)
    sample_price: Mapped[str | None] = mapped_column(Text)
    packaging: Mapped[str | None] = mapped_column(Text)
    coa_available: Mapped[bool | None] = mapped_column(Boolean, nullable=True)
    sds_available: Mapped[bool | None] = mapped_column(Boolean, nullable=True)
    reach_status: Mapped[str | None] = mapped_column(Text)
    adr_class: Mapped[str | None] = mapped_column(Text)
    un_number: Mapped[str | None] = mapped_column(Text)
    hs_code: Mapped[str | None] = mapped_column(Text)
    shelf_life: Mapped[str | None] = mapped_column(Text)
    certificates: Mapped[list | None] = mapped_column(JSON, default=list)
    production_capacity: Mapped[str | None] = mapped_column(Text)
    red_flags: Mapped[list | None] = mapped_column(JSON, default=list)
    missing_questions: Mapped[list | None] = mapped_column(JSON, default=list)
    confidence: Mapped[Decimal | None] = mapped_column(Numeric)
    status: Mapped[str | None] = mapped_column(Text, default="needs_review")
    extracted_from_message_id: Mapped[str | None] = mapped_column(String(36), nullable=True)

    company = relationship("SupplierCompany", back_populates="quotes")
    substance = relationship("Substance", back_populates="quotes")
    campaign = relationship("RfqCampaign", back_populates="quotes")
    generated_documents = relationship("GeneratedDocument", back_populates="quote")
