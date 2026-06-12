from datetime import datetime

from sqlalchemy import Boolean, DateTime, ForeignKey, JSON, String, Text
from sqlalchemy.orm import Mapped, mapped_column, relationship

from app.db.base import Base, TimestampMixin, new_uuid


class RfqCampaign(Base, TimestampMixin):
    __tablename__ = "rfq_campaigns"

    id: Mapped[str] = mapped_column(String(36), primary_key=True, default=new_uuid)
    substance_id: Mapped[str] = mapped_column(
        String(36), ForeignKey("substances.id", ondelete="CASCADE"), nullable=False
    )
    quantity: Mapped[str | None] = mapped_column(Text)
    destination_country: Mapped[str | None] = mapped_column(Text)
    required_grade: Mapped[str | None] = mapped_column(Text)
    intended_use: Mapped[str | None] = mapped_column(Text)
    requirements: Mapped[dict | None] = mapped_column(JSON, default=dict)
    status: Mapped[str | None] = mapped_column(Text, default="draft")
    auto_send_enabled: Mapped[bool] = mapped_column(Boolean, default=False)
    created_by: Mapped[str | None] = mapped_column(String(36), ForeignKey("users.id"))

    transport_type: Mapped[str | None] = mapped_column(Text)  # sea, air, road, rail, courier
    incoterms: Mapped[str | None] = mapped_column(Text)  # FOB, CIF, EXW, DDP, etc.
    batch_approved: Mapped[bool] = mapped_column(Boolean, default=False)
    batch_approved_by: Mapped[str | None] = mapped_column(String(36), ForeignKey("users.id"))
    batch_approved_at: Mapped[datetime | None] = mapped_column(DateTime(timezone=True))

    creator = relationship("User", back_populates="campaigns", foreign_keys=[created_by])
    substance = relationship("Substance", back_populates="campaigns")
    outbound_messages = relationship(
        "OutboundMessage", back_populates="campaign", cascade="all, delete-orphan"
    )
    inbound_messages = relationship("InboundMessage", back_populates="campaign")
    quotes = relationship("Quote", back_populates="campaign")
    generated_documents = relationship("GeneratedDocument", back_populates="campaign")
