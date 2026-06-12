from sqlalchemy import Boolean, ForeignKey, Integer, JSON, String, Text
from sqlalchemy.orm import Mapped, mapped_column, relationship

from app.db.base import Base, CreatedAtMixin, TimestampMixin, new_uuid


class DocumentTemplate(Base, TimestampMixin):
    __tablename__ = "document_templates"

    id: Mapped[str] = mapped_column(String(36), primary_key=True, default=new_uuid)
    doc_type: Mapped[str] = mapped_column(Text, nullable=False, index=True)  # rfq_letter, loi, po
    name: Mapped[str] = mapped_column(Text, nullable=False)
    html_template: Mapped[str] = mapped_column(Text, nullable=False)
    css_template: Mapped[str | None] = mapped_column(Text)
    is_default: Mapped[bool] = mapped_column(Boolean, default=False)

    generated_documents = relationship("GeneratedDocument", back_populates="template")


class GeneratedDocument(Base, CreatedAtMixin):
    __tablename__ = "generated_documents"

    id: Mapped[str] = mapped_column(String(36), primary_key=True, default=new_uuid)
    doc_type: Mapped[str] = mapped_column(Text, nullable=False, index=True)  # rfq_letter, loi, po, report
    template_id: Mapped[str | None] = mapped_column(
        String(36), ForeignKey("document_templates.id", ondelete="SET NULL")
    )
    campaign_id: Mapped[str | None] = mapped_column(
        String(36), ForeignKey("rfq_campaigns.id", ondelete="SET NULL")
    )
    quote_id: Mapped[str | None] = mapped_column(
        String(36), ForeignKey("quotes.id", ondelete="SET NULL")
    )
    company_id: Mapped[str | None] = mapped_column(
        String(36), ForeignKey("supplier_companies.id", ondelete="SET NULL")
    )
    substance_id: Mapped[str | None] = mapped_column(
        String(36), ForeignKey("substances.id", ondelete="SET NULL")
    )
    file_path: Mapped[str | None] = mapped_column(Text)
    file_size_bytes: Mapped[int | None] = mapped_column(Integer)
    parameters: Mapped[dict | None] = mapped_column(JSON, default=dict)
    status: Mapped[str] = mapped_column(Text, default="generated")  # generated, sent, archived

    template = relationship("DocumentTemplate", back_populates="generated_documents")
    campaign = relationship("RfqCampaign", back_populates="generated_documents")
    quote = relationship("Quote", back_populates="generated_documents")
    company = relationship("SupplierCompany", back_populates="generated_documents")
    substance = relationship("Substance", back_populates="generated_documents")
