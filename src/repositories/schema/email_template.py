"""SQLAlchemy ORM model for the email_templates table."""

import uuid
from datetime import datetime

from sqlalchemy import Integer, String, Text, func
from sqlalchemy.orm import Mapped, mapped_column

from src.repositories.schema.base import Base


class EmailTemplate(Base):
    """ORM model for the email_templates table."""

    __tablename__ = "email_templates"

    email_template_id: Mapped[uuid.UUID] = mapped_column(primary_key=True, default=uuid.uuid4)
    template_name: Mapped[str] = mapped_column(String(255), nullable=False)
    template_content: Mapped[str] = mapped_column(Text, nullable=False)
    created_at: Mapped[datetime | None] = mapped_column(default=func.current_timestamp())
    created_by: Mapped[str | None] = mapped_column(String(255))
    modified_at: Mapped[datetime | None] = mapped_column()
    modified_by: Mapped[str | None] = mapped_column(String(255))
    is_active: Mapped[int | None] = mapped_column(Integer, default=1)
