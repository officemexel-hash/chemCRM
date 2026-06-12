from decimal import Decimal

from sqlalchemy import Boolean, ForeignKey, Numeric, String, Text
from sqlalchemy.orm import Mapped, mapped_column, relationship

from app.db.base import Base, CreatedAtMixin, TimestampMixin, new_uuid


class Substance(Base, TimestampMixin):
    __tablename__ = "substances"

    id: Mapped[str] = mapped_column(String(36), primary_key=True, default=new_uuid)
    cas: Mapped[str] = mapped_column(Text, unique=True, nullable=False, index=True)
    primary_name: Mapped[str | None] = mapped_column(Text)
    iupac_name: Mapped[str | None] = mapped_column(Text)
    molecular_formula: Mapped[str | None] = mapped_column(Text)
    molecular_weight: Mapped[Decimal | None] = mapped_column(Numeric)
    pubchem_cid: Mapped[str | None] = mapped_column(Text)
    ec_number: Mapped[str | None] = mapped_column(Text)
    hs_code_suggested: Mapped[str | None] = mapped_column(Text)
    hs_code_confirmed: Mapped[str | None] = mapped_column(Text)
    hs_code_confidence: Mapped[Decimal | None] = mapped_column(Numeric)
    regulatory_status: Mapped[str | None] = mapped_column(Text, default="unknown")
    requires_manual_review: Mapped[bool] = mapped_column(Boolean, default=False)

    synonyms = relationship(
        "SubstanceSynonym", back_populates="substance", cascade="all, delete-orphan"
    )
    regulatory_flags = relationship(
        "RegulatoryFlag", back_populates="substance", cascade="all, delete-orphan"
    )
    product_offers = relationship("ProductOffer", back_populates="substance")
    campaigns = relationship("RfqCampaign", back_populates="substance")
    quotes = relationship("Quote", back_populates="substance")
    hs_code_entries = relationship("HsCodeEntry", back_populates="substance")
    legal_use_descriptions = relationship("LegalUseDescription", back_populates="substance")
    generated_documents = relationship("GeneratedDocument", back_populates="substance")
    manufacturing_analyses = relationship(
        "SubstanceManufacturingAnalysis", back_populates="substance", cascade="all, delete-orphan"
    )


class SubstanceSynonym(Base):
    __tablename__ = "substance_synonyms"

    id: Mapped[str] = mapped_column(String(36), primary_key=True, default=new_uuid)
    substance_id: Mapped[str] = mapped_column(
        String(36), ForeignKey("substances.id", ondelete="CASCADE"), nullable=False, index=True
    )
    synonym: Mapped[str] = mapped_column(Text, nullable=False)
    source: Mapped[str | None] = mapped_column(Text)

    substance = relationship("Substance", back_populates="synonyms")


class RegulatoryFlag(Base, CreatedAtMixin):
    __tablename__ = "regulatory_flags"

    id: Mapped[str] = mapped_column(String(36), primary_key=True, default=new_uuid)
    substance_id: Mapped[str] = mapped_column(
        String(36), ForeignKey("substances.id", ondelete="CASCADE"), nullable=False, index=True
    )
    flag_type: Mapped[str | None] = mapped_column(Text)
    severity: Mapped[str | None] = mapped_column(Text)
    source: Mapped[str | None] = mapped_column(Text)
    description: Mapped[str | None] = mapped_column(Text)

    substance = relationship("Substance", back_populates="regulatory_flags")
