"""SQLAlchemy ORM model for the email_recipient table."""

import uuid
from datetime import datetime
from sqlalchemy import ForeignKey, Integer, String, func
from sqlalchemy.orm import Mapped, mapped_column
from src.repositories.schema.base import Base


class EmailRecipient(Base):
    """ORM model for the email_recipient table."""

    __tablename__ = "email_recipient"

    email_recipient_id: Mapped[uuid.UUID] = mapped_column(primary_key=True, default=uuid.uuid4)
    setting_id: Mapped[uuid.UUID | None] = mapped_column(ForeignKey("settings.setting_id"))
    specialization_id: Mapped[uuid.UUID | None] = mapped_column(ForeignKey("specializations.specialization_id"))
    alert_recipient: Mapped[str] = mapped_column(String(255), nullable=False)
    created_at: Mapped[datetime | None] = mapped_column(default=func.current_timestamp())
    created_by: Mapped[str | None] = mapped_column(String(255))
    modified_at: Mapped[datetime | None] = mapped_column()
    modified_by: Mapped[str | None] = mapped_column(String(255))
    is_active: Mapped[int | None] = mapped_column(Integer, default=1)
