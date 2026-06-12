from decimal import Decimal

from sqlalchemy import Boolean, DateTime, ForeignKey, Numeric, String, Text
from sqlalchemy.orm import Mapped, mapped_column, relationship

from app.db.base import Base, CreatedAtMixin, TimestampMixin, new_uuid


class SupplierCompany(Base, TimestampMixin):
    __tablename__ = "supplier_companies"

    id: Mapped[str] = mapped_column(String(36), primary_key=True, default=new_uuid)
    name: Mapped[str] = mapped_column(Text, nullable=False, index=True)
    website: Mapped[str | None] = mapped_column(Text)
    country: Mapped[str | None] = mapped_column(Text, index=True)
    address: Mapped[str | None] = mapped_column(Text)
    company_type: Mapped[str | None] = mapped_column(Text, default="UNKNOWN")
    registration_number: Mapped[str | None] = mapped_column(Text)
    vat_number: Mapped[str | None] = mapped_column(Text)
    eori_number: Mapped[str | None] = mapped_column(Text)
    verified_status: Mapped[str | None] = mapped_column(Text)
    supplier_score: Mapped[Decimal] = mapped_column(Numeric, default=0)
    risk_score: Mapped[Decimal] = mapped_column(Numeric, default=0)
    risk_level: Mapped[str | None] = mapped_column(Text, default="unknown")
    notes: Mapped[str | None] = mapped_column(Text)

    contacts = relationship(
        "SupplierContact", back_populates="company", cascade="all, delete-orphan"
    )
    consent_evidence = relationship(
        "ConsentEvidence", back_populates="company", cascade="all, delete-orphan"
    )
    product_offers = relationship("ProductOffer", back_populates="company")
    outbound_messages = relationship("OutboundMessage", back_populates="company")
    inbound_messages = relationship("InboundMessage", back_populates="company")
    quotes = relationship("Quote", back_populates="company")
    generated_documents = relationship("GeneratedDocument", back_populates="company")


class SupplierContact(Base, CreatedAtMixin):
    __tablename__ = "supplier_contacts"

    id: Mapped[str] = mapped_column(String(36), primary_key=True, default=new_uuid)
    company_id: Mapped[str] = mapped_column(
        String(36), ForeignKey("supplier_companies.id", ondelete="CASCADE"), nullable=False
    )
    channel: Mapped[str] = mapped_column(Text, nullable=False, index=True)
    value: Mapped[str] = mapped_column(Text, nullable=False)
    contact_person: Mapped[str | None] = mapped_column(Text)
    source_url: Mapped[str | None] = mapped_column(Text)
    evidence_text: Mapped[str | None] = mapped_column(Text)
    consent_status: Mapped[str | None] = mapped_column(Text, default="unknown")
    consent_evidence_id: Mapped[str | None] = mapped_column(String(36), nullable=True)
    is_primary: Mapped[bool] = mapped_column(Boolean, default=False)

    company = relationship("SupplierCompany", back_populates="contacts")
    outbound_messages = relationship("OutboundMessage", back_populates="contact")


class ConsentEvidence(Base):
    __tablename__ = "consent_evidence"

    id: Mapped[str] = mapped_column(String(36), primary_key=True, default=new_uuid)
    company_id: Mapped[str] = mapped_column(
        String(36), ForeignKey("supplier_companies.id", ondelete="CASCADE"), nullable=False
    )
    contact_channel: Mapped[str | None] = mapped_column(Text)
    evidence_type: Mapped[str | None] = mapped_column(Text)
    source_url: Mapped[str | None] = mapped_column(Text)
    source_text: Mapped[str | None] = mapped_column(Text)
    screenshot_path: Mapped[str | None] = mapped_column(Text)
    collected_at: Mapped[DateTime | None] = mapped_column(DateTime(timezone=True))

    company = relationship("SupplierCompany", back_populates="consent_evidence")


class ProductOffer(Base):
    __tablename__ = "product_offers"

    id: Mapped[str] = mapped_column(String(36), primary_key=True, default=new_uuid)
    company_id: Mapped[str] = mapped_column(
        String(36), ForeignKey("supplier_companies.id", ondelete="CASCADE"), nullable=False
    )
    substance_id: Mapped[str] = mapped_column(
        String(36), ForeignKey("substances.id", ondelete="CASCADE"), nullable=False
    )
    source_url: Mapped[str | None] = mapped_column(Text)
    listed_name: Mapped[str | None] = mapped_column(Text)
    listed_cas: Mapped[str | None] = mapped_column(Text)
    grade: Mapped[str | None] = mapped_column(Text)
    purity: Mapped[str | None] = mapped_column(Text)
    moq: Mapped[str | None] = mapped_column(Text)
    price_text: Mapped[str | None] = mapped_column(Text)
    currency: Mapped[str | None] = mapped_column(Text)
    last_seen_at: Mapped[DateTime | None] = mapped_column(DateTime(timezone=True))
    raw_snapshot_id: Mapped[str | None] = mapped_column(String(36), nullable=True)

    company = relationship("SupplierCompany", back_populates="product_offers")
    substance = relationship("Substance", back_populates="product_offers")
