from sqlalchemy import Boolean, ForeignKey, Integer, JSON, String, Text
from sqlalchemy.orm import Mapped, mapped_column, relationship

from app.db.base import Base, CreatedAtMixin, TimestampMixin, new_uuid


class BulkImportJob(Base, TimestampMixin):
    __tablename__ = "bulk_import_jobs"

    id: Mapped[str] = mapped_column(String(36), primary_key=True, default=new_uuid)
    filename: Mapped[str] = mapped_column(Text, nullable=False)
    original_filename: Mapped[str | None] = mapped_column(Text)
    total_rows: Mapped[int] = mapped_column(Integer, default=0)
    valid_rows: Mapped[int] = mapped_column(Integer, default=0)
    invalid_rows: Mapped[int] = mapped_column(Integer, default=0)
    status: Mapped[str] = mapped_column(Text, default="pending")  # pending, processing, completed, failed
    error_details: Mapped[dict | None] = mapped_column(JSON, default=dict)
    created_by: Mapped[str | None] = mapped_column(String(36), ForeignKey("users.id"))

    items = relationship("BulkImportItem", back_populates="job", cascade="all, delete-orphan")


class BulkImportItem(Base, CreatedAtMixin):
    __tablename__ = "bulk_import_items"

    id: Mapped[str] = mapped_column(String(36), primary_key=True, default=new_uuid)
    job_id: Mapped[str] = mapped_column(
        String(36), ForeignKey("bulk_import_jobs.id", ondelete="CASCADE"), nullable=False, index=True
    )
    row_number: Mapped[int] = mapped_column(Integer, nullable=False)
    cas_raw: Mapped[str] = mapped_column(Text, nullable=False)
    cas_valid: Mapped[bool] = mapped_column(Boolean, default=False)
    substance_id: Mapped[str | None] = mapped_column(
        String(36), ForeignKey("substances.id", ondelete="SET NULL")
    )
    status: Mapped[str] = mapped_column(Text, default="pending")  # pending, created, existing, invalid
    error_message: Mapped[str | None] = mapped_column(Text)

    job = relationship("BulkImportJob", back_populates="items")
    substance = relationship("Substance")
