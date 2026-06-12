from sqlalchemy import Boolean, DateTime, ForeignKey, JSON, String, Text
from sqlalchemy.orm import Mapped, mapped_column, relationship

from app.db.base import Base, CreatedAtMixin, new_uuid


class OutboundMessage(Base, CreatedAtMixin):
    __tablename__ = "outbound_messages"

    id: Mapped[str] = mapped_column(String(36), primary_key=True, default=new_uuid)
    campaign_id: Mapped[str] = mapped_column(
        String(36), ForeignKey("rfq_campaigns.id", ondelete="CASCADE"), nullable=False
    )
    company_id: Mapped[str] = mapped_column(
        String(36), ForeignKey("supplier_companies.id", ondelete="CASCADE"), nullable=False
    )
    contact_id: Mapped[str] = mapped_column(
        String(36), ForeignKey("supplier_contacts.id", ondelete="CASCADE"), nullable=False
    )
    channel: Mapped[str | None] = mapped_column(Text)
    subject: Mapped[str | None] = mapped_column(Text)
    body: Mapped[str | None] = mapped_column(Text)
    status: Mapped[str | None] = mapped_column(Text, default="draft")
    policy_decision: Mapped[str | None] = mapped_column(Text)
    policy_reasons: Mapped[list | None] = mapped_column(JSON, default=list)
    approval_required: Mapped[bool] = mapped_column(Boolean, default=True)
    approved_by: Mapped[str | None] = mapped_column(String(36), nullable=True)
    approved_at: Mapped[DateTime | None] = mapped_column(DateTime(timezone=True), nullable=True)
    sent_at: Mapped[DateTime | None] = mapped_column(DateTime(timezone=True), nullable=True)
    external_message_id: Mapped[str | None] = mapped_column(Text)

    campaign = relationship("RfqCampaign", back_populates="outbound_messages")
    company = relationship("SupplierCompany", back_populates="outbound_messages")
    contact = relationship("SupplierContact", back_populates="outbound_messages")


class InboundMessage(Base):
    __tablename__ = "inbound_messages"

    id: Mapped[str] = mapped_column(String(36), primary_key=True, default=new_uuid)
    company_id: Mapped[str] = mapped_column(
        String(36), ForeignKey("supplier_companies.id", ondelete="CASCADE"), nullable=False
    )
    campaign_id: Mapped[str | None] = mapped_column(
        String(36), ForeignKey("rfq_campaigns.id", ondelete="SET NULL"), nullable=True
    )
    channel: Mapped[str | None] = mapped_column(Text)
    from_address: Mapped[str | None] = mapped_column(Text)
    subject: Mapped[str | None] = mapped_column(Text)
    body: Mapped[str | None] = mapped_column(Text)
    received_at: Mapped[DateTime | None] = mapped_column(DateTime(timezone=True), nullable=True)
    parsed: Mapped[bool] = mapped_column(Boolean, default=False)
    external_message_id: Mapped[str | None] = mapped_column(Text)
    thread_id: Mapped[str | None] = mapped_column(Text)

    company = relationship("SupplierCompany", back_populates="inbound_messages")
    campaign = relationship("RfqCampaign", back_populates="inbound_messages")
