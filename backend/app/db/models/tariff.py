from datetime import datetime
from decimal import Decimal

from sqlalchemy import DateTime, ForeignKey, Numeric, String, Text
from sqlalchemy.orm import Mapped, mapped_column, relationship

from app.db.base import Base, CreatedAtMixin, TimestampMixin, new_uuid


class HsCodeEntry(Base, TimestampMixin):
    __tablename__ = "hs_code_entries"

    id: Mapped[str] = mapped_column(String(36), primary_key=True, default=new_uuid)
    hs_code: Mapped[str] = mapped_column(Text, nullable=False, index=True)  # e.g. "2905.19.00"
    chapter: Mapped[str | None] = mapped_column(Text)  # first 2 digits
    heading: Mapped[str | None] = mapped_column(Text)  # first 4 digits
    subheading: Mapped[str | None] = mapped_column(Text)
    description: Mapped[str | None] = mapped_column(Text)
    cas_pattern: Mapped[str | None] = mapped_column(Text)  # CAS this code maps to
    substance_id: Mapped[str | None] = mapped_column(
        String(36), ForeignKey("substances.id", ondelete="SET NULL")
    )
    source_database: Mapped[str] = mapped_column(Text, default="manual")  # eu_taric, us_hts, manual, pubchem, llm
    confidence: Mapped[Decimal | None] = mapped_column(Numeric)

    substance = relationship("Substance", back_populates="hs_code_entries")
    tariff_rates = relationship("TariffRate", back_populates="hs_code", cascade="all, delete-orphan")
    legal_uses = relationship("LegalUseDescription", back_populates="hs_code")


class TariffRate(Base, TimestampMixin):
    __tablename__ = "tariff_rates"

    id: Mapped[str] = mapped_column(String(36), primary_key=True, default=new_uuid)
    hs_code_id: Mapped[str] = mapped_column(
        String(36), ForeignKey("hs_code_entries.id", ondelete="CASCADE"), nullable=False, index=True
    )
    origin_country: Mapped[str] = mapped_column(Text, nullable=False, index=True)  # ISO 2-letter
    destination_country: Mapped[str] = mapped_column(Text, nullable=False, index=True)
    duty_rate_percent: Mapped[Decimal | None] = mapped_column(Numeric)
    duty_type: Mapped[str | None] = mapped_column(Text)  # ad_valorem, specific, compound
    preferential_rate: Mapped[Decimal | None] = mapped_column(Numeric)
    preferential_source: Mapped[str | None] = mapped_column(Text)  # e.g. "EU-Japan EPA"
    anti_dumping_rate: Mapped[Decimal | None] = mapped_column(Numeric)
    effective_from: Mapped[datetime | None] = mapped_column(DateTime(timezone=True))
    effective_to: Mapped[datetime | None] = mapped_column(DateTime(timezone=True))
    source_database: Mapped[str] = mapped_column(Text, default="manual")

    hs_code = relationship("HsCodeEntry", back_populates="tariff_rates")


class LegalUseDescription(Base, CreatedAtMixin):
    __tablename__ = "legal_use_descriptions"

    id: Mapped[str] = mapped_column(String(36), primary_key=True, default=new_uuid)
    substance_id: Mapped[str] = mapped_column(
        String(36), ForeignKey("substances.id", ondelete="CASCADE"), nullable=False, index=True
    )
    hs_code_id: Mapped[str | None] = mapped_column(
        String(36), ForeignKey("hs_code_entries.id", ondelete="SET NULL")
    )
    description: Mapped[str] = mapped_column(Text, nullable=False)
    category: Mapped[str | None] = mapped_column(Text)  # industrial_reagent, pharmaceutical_intermediate, etc.
    destination_country: Mapped[str | None] = mapped_column(Text)  # ISO 2-letter, None = universal
    source: Mapped[str | None] = mapped_column(Text)

    substance = relationship("Substance", back_populates="legal_use_descriptions")
    hs_code = relationship("HsCodeEntry", back_populates="legal_uses")
