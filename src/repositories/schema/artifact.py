"""SQLAlchemy ORM model for the artifacts table."""

import uuid
from datetime import datetime

from sqlalchemy import BigInteger, ForeignKey, Integer, String, Text, func
from sqlalchemy.orm import Mapped, mapped_column

from src.repositories.schema.base import Base


class Artifact(Base):
    """ORM model for the artifacts table."""

    __tablename__ = "artifacts"

    artifact_id: Mapped[uuid.UUID] = mapped_column(primary_key=True, default=uuid.uuid4)
    pipeline_run_id: Mapped[uuid.UUID] = mapped_column(ForeignKey("pipeline_runs.pipeline_run_id"), nullable=False)
    artifact_name: Mapped[str] = mapped_column(String(255), nullable=False)
    size_bytes: Mapped[int] = mapped_column(BigInteger, nullable=False)
    url: Mapped[str] = mapped_column(Text, nullable=False)
    uploaded_at: Mapped[datetime] = mapped_column(nullable=False)
    created_at: Mapped[datetime | None] = mapped_column(default=func.current_timestamp())
    created_by: Mapped[str | None] = mapped_column(String(255))
    modified_at: Mapped[datetime | None] = mapped_column()
    modified_by: Mapped[str | None] = mapped_column(String(255))
    is_active: Mapped[int | None] = mapped_column(Integer, default=1)
