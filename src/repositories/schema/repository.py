"""SQLAlchemy ORM model for the repositories table."""

import uuid
from datetime import datetime
from sqlalchemy import Float, ForeignKey, Integer, String, func
from sqlalchemy.orm import Mapped, mapped_column
from src.repositories.schema.base import Base


class Repository(Base):
    """ORM model for the repositories table."""

    __tablename__ = "repositories"

    repository_id: Mapped[uuid.UUID] = mapped_column(primary_key=True, default=uuid.uuid4)
    ticket_id: Mapped[uuid.UUID | None] = mapped_column(ForeignKey("devsecops_tickets.ticket_id"))
    repository_name: Mapped[str] = mapped_column(String(255), nullable=False)
    ado_repo_id: Mapped[str | None] = mapped_column(String(255))
    specialization_name: Mapped[str | None] = mapped_column(String(500))
    lead_approvers: Mapped[str | None] = mapped_column(String(1000))
    pipeline_runs_count: Mapped[int | None] = mapped_column(Integer, default=0)
    success_rate: Mapped[float | None] = mapped_column(Float, default=0)
    last_run_at: Mapped[datetime | None] = mapped_column()
    created_at: Mapped[datetime | None] = mapped_column(default=func.current_timestamp())
    created_by: Mapped[str | None] = mapped_column(String(255))
    modified_at: Mapped[datetime | None] = mapped_column()
    modified_by: Mapped[str | None] = mapped_column(String(255))
    is_active: Mapped[int | None] = mapped_column(Integer, default=1)
