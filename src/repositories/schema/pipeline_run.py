"""SQLAlchemy ORM model for the pipeline_runs table."""

import uuid
from datetime import datetime

from sqlalchemy import ForeignKey, Integer, String, func
from sqlalchemy.orm import Mapped, mapped_column

from src.repositories.schema.base import Base


class PipelineRun(Base):
    """ORM model for the pipeline_runs table."""

    __tablename__ = "pipeline_runs"

    pipeline_run_id: Mapped[uuid.UUID] = mapped_column(primary_key=True, default=uuid.uuid4)
    repository_id: Mapped[uuid.UUID] = mapped_column(ForeignKey("repositories.repository_id"), nullable=False)
    run_number: Mapped[int] = mapped_column(Integer, nullable=False)
    status: Mapped[str] = mapped_column(String(50), nullable=False)
    branch: Mapped[str] = mapped_column(String(255), nullable=False)
    duration_seconds: Mapped[int | None] = mapped_column(Integer)
    triggered_at: Mapped[datetime] = mapped_column(nullable=False)
    created_at: Mapped[datetime | None] = mapped_column(default=func.current_timestamp())
    created_by: Mapped[str | None] = mapped_column(String(255))
    modified_at: Mapped[datetime | None] = mapped_column()
    modified_by: Mapped[str | None] = mapped_column(String(255))
    is_active: Mapped[int | None] = mapped_column(Integer, default=1)
