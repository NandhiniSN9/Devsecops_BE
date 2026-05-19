"""SQLAlchemy ORM model for the email_history table."""

import uuid
from datetime import datetime
from sqlalchemy import ForeignKey, Integer, String, Text, func
from sqlalchemy.orm import Mapped, mapped_column
from src.repositories.schema.base import Base


class EmailHistory(Base):
    """ORM model for the email_history table."""

    __tablename__ = "email_history"

    email_history_id: Mapped[uuid.UUID] = mapped_column(primary_key=True, default=uuid.uuid4)
    setting_id: Mapped[uuid.UUID | None] = mapped_column(ForeignKey("settings.setting_id"))
    email_status: Mapped[str] = mapped_column(String(50), nullable=False)
    email_type: Mapped[str] = mapped_column(String(100), nullable=False)
    report_url: Mapped[str | None] = mapped_column(Text)
    last_synced: Mapped[datetime | None] = mapped_column()
    created_at: Mapped[datetime | None] = mapped_column(default=func.current_timestamp())
    created_by: Mapped[str | None] = mapped_column(String(255))
    modified_at: Mapped[datetime | None] = mapped_column()
    modified_by: Mapped[str | None] = mapped_column(String(255))
    is_active: Mapped[int | None] = mapped_column(Integer, default=1)
