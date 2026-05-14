"""SQLAlchemy ORM model for the kpi_history table."""

import uuid
from datetime import datetime

from sqlalchemy import ForeignKey, Integer, String, func
from sqlalchemy.orm import Mapped, mapped_column, relationship

from src.repositories.schema.base import Base


class KpiHistory(Base):
    """ORM model for the kpi_history table."""

    __tablename__ = "kpi_history"

    kpi_history_id: Mapped[uuid.UUID] = mapped_column(primary_key=True, default=uuid.uuid4)
    specialization_id: Mapped[uuid.UUID | None] = mapped_column(ForeignKey("specializations.specialization_id"))

    # Project counts
    projects_count: Mapped[int | None] = mapped_column(Integer, default=0)
    projects_increase_count: Mapped[int | None] = mapped_column(Integer, default=0)
    projects_decrease_count: Mapped[int | None] = mapped_column(Integer, default=0)

    # Completed counts
    completed_count: Mapped[int | None] = mapped_column(Integer, default=0)
    completed_increase_count: Mapped[int | None] = mapped_column(Integer, default=0)
    completed_decrease_count: Mapped[int | None] = mapped_column(Integer, default=0)

    # Active counts
    active_count: Mapped[int | None] = mapped_column(Integer, default=0)
    active_increase_count: Mapped[int | None] = mapped_column(Integer, default=0)
    active_decrease_count: Mapped[int | None] = mapped_column(Integer, default=0)

    # Inactive counts
    inactive_count: Mapped[int | None] = mapped_column(Integer, default=0)
    inactive_increase_count: Mapped[int | None] = mapped_column(Integer, default=0)
    inactive_decrease_count: Mapped[int | None] = mapped_column(Integer, default=0)

    # At risk counts
    at_risk_count: Mapped[int | None] = mapped_column(Integer, default=0)
    at_risk_increase_count: Mapped[int | None] = mapped_column(Integer, default=0)
    at_risk_decrease_count: Mapped[int | None] = mapped_column(Integer, default=0)

    # Not applicable counts
    not_applicable_count: Mapped[int | None] = mapped_column(Integer, default=0)
    not_applicable_increase_count: Mapped[int | None] = mapped_column(Integer, default=0)
    not_applicable_decrease_count: Mapped[int | None] = mapped_column(Integer, default=0)

    # Audit fields
    created_at: Mapped[datetime | None] = mapped_column(default=func.current_timestamp())
    created_by: Mapped[str | None] = mapped_column(String(255))
    modified_at: Mapped[datetime | None] = mapped_column()
    modified_by: Mapped[str | None] = mapped_column(String(255))
    is_active: Mapped[int | None] = mapped_column(Integer, default=1)

    # Relationships
    specialization: Mapped["Specialization | None"] = relationship(back_populates="kpi_histories")


from src.repositories.schema.specialization import Specialization  # noqa: E402
