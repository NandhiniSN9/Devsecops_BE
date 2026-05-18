"""SQLAlchemy ORM model for the commits table."""

import uuid
from datetime import datetime

from sqlalchemy import ForeignKey, Integer, String, Text, func
from sqlalchemy.orm import Mapped, mapped_column

from src.repositories.schema.base import Base


class Commit(Base):
    """ORM model for the commits table."""

    __tablename__ = "commits"

    commit_id: Mapped[uuid.UUID] = mapped_column(primary_key=True, default=uuid.uuid4)
    repository_id: Mapped[uuid.UUID] = mapped_column(ForeignKey("repositories.repository_id"), nullable=False)
    hash: Mapped[str] = mapped_column(String(255), nullable=False)
    message: Mapped[str] = mapped_column(Text, nullable=False)
    author: Mapped[str] = mapped_column(String(255), nullable=False)
    committed_at: Mapped[datetime] = mapped_column(nullable=False)
    created_at: Mapped[datetime | None] = mapped_column(default=func.current_timestamp())
    created_by: Mapped[str | None] = mapped_column(String(255))
    modified_at: Mapped[datetime | None] = mapped_column()
    modified_by: Mapped[str | None] = mapped_column(String(255))
    is_active: Mapped[int | None] = mapped_column(Integer, default=1)
