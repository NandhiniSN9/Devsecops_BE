"""SQLAlchemy ORM model for the error_log table."""

import uuid
from datetime import datetime

from sqlalchemy import Integer, String, Text, func
from sqlalchemy.orm import Mapped, mapped_column

from src.repositories.schema.base import Base


class ErrorLog(Base):
    """ORM model for the error_log table."""

    __tablename__ = "error_log"

    error_id: Mapped[uuid.UUID] = mapped_column(primary_key=True, default=uuid.uuid4)
    error_message: Mapped[str] = mapped_column(Text, nullable=False)
    error_function: Mapped[str] = mapped_column(Text, nullable=False)
    error_file: Mapped[str] = mapped_column(Text, nullable=False)
    stack_trace: Mapped[str | None] = mapped_column(Text)
    created_at: Mapped[datetime | None] = mapped_column(default=func.current_timestamp())
    created_by: Mapped[str | None] = mapped_column(String(255))
    modified_at: Mapped[datetime | None] = mapped_column()
    modified_by: Mapped[str | None] = mapped_column(String(255))
    is_active: Mapped[int | None] = mapped_column(Integer, default=1)
