"""SQLAlchemy ORM model for the pull_requests table."""

import uuid
from datetime import datetime

from sqlalchemy import ForeignKey, Integer, String, func
from sqlalchemy.orm import Mapped, mapped_column

from src.repositories.schema.base import Base


class PullRequest(Base):
    """ORM model for the pull_requests table."""

    __tablename__ = "pull_requests"

    pull_request_id: Mapped[uuid.UUID] = mapped_column(primary_key=True, default=uuid.uuid4)
    repository_id: Mapped[uuid.UUID] = mapped_column(ForeignKey("repositories.repository_id"), nullable=False)
    title: Mapped[str] = mapped_column(String(500), nullable=False)
    author: Mapped[str] = mapped_column(String(255), nullable=False)
    status: Mapped[str] = mapped_column(String(50), nullable=False)
    updated_at: Mapped[datetime | None] = mapped_column()
    created_at: Mapped[datetime | None] = mapped_column(default=func.current_timestamp())
    created_by: Mapped[str | None] = mapped_column(String(255))
    modified_at: Mapped[datetime | None] = mapped_column()
    modified_by: Mapped[str | None] = mapped_column(String(255))
    is_active: Mapped[int | None] = mapped_column(Integer, default=1)
