from sqlalchemy import DateTime, JSON, Text
from sqlalchemy.orm import Mapped, mapped_column

from app.db.base import Base, utc_now


class Setting(Base):
    __tablename__ = "settings"

    key: Mapped[str] = mapped_column(Text, primary_key=True)
    value: Mapped[dict | list | str | int | float | bool | None] = mapped_column(JSON)
    updated_at: Mapped[DateTime] = mapped_column(
        DateTime(timezone=True), default=utc_now, onupdate=utc_now
    )
