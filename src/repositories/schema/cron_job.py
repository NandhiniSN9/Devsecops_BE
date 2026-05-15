"""SQLAlchemy ORM model for the cron_jobs table."""

import uuid
from datetime import datetime

from sqlalchemy import Integer, String, func
from sqlalchemy.orm import Mapped, mapped_column

from src.repositories.schema.base import Base


class CronJob(Base):
    """ORM model for the cron_jobs table."""

    __tablename__ = "cron_jobs"

    cron_id: Mapped[uuid.UUID] = mapped_column(primary_key=True, default=uuid.uuid4)
    specialization_id: Mapped[str] = mapped_column(String(255), nullable=False)
    type: Mapped[str] = mapped_column(String(50), nullable=False)
    sync_status: Mapped[str] = mapped_column(String(50), nullable=False)
    created_at: Mapped[datetime | None] = mapped_column(default=func.current_timestamp())
    created_by: Mapped[str | None] = mapped_column(String(255))
    modified_at: Mapped[datetime | None] = mapped_column()
    modified_by: Mapped[str | None] = mapped_column(String(255))
    is_active: Mapped[int | None] = mapped_column(Integer, default=1)
