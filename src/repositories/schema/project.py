"""SQLAlchemy ORM model for the projects table."""

import uuid
from datetime import date, datetime

from sqlalchemy import Boolean, Date, ForeignKey, Integer, String, func
from sqlalchemy.orm import Mapped, mapped_column, relationship

from src.repositories.schema.base import Base


class Project(Base):
    """ORM model for the projects table."""

    __tablename__ = "projects"

    project_id: Mapped[uuid.UUID] = mapped_column(primary_key=True, default=uuid.uuid4)
    status_id: Mapped[uuid.UUID | None] = mapped_column(ForeignKey("statuses.status_id"))
    sn_project_id: Mapped[str | None] = mapped_column(String(255))
    project_name: Mapped[str] = mapped_column(String(255), nullable=False)
    onboarded_date: Mapped[date] = mapped_column(Date, nullable=False)
    project_type: Mapped[str] = mapped_column(String(255), nullable=False)
    specialization_name: Mapped[str | None] = mapped_column(String(255))
    is_applicable: Mapped[bool | None] = mapped_column(Boolean, default=True)
    client: Mapped[str | None] = mapped_column(String(255))
    completed_at: Mapped[datetime | None] = mapped_column()
    created_at: Mapped[datetime | None] = mapped_column(default=func.current_timestamp())
    created_by: Mapped[str | None] = mapped_column(String(255))
    modified_at: Mapped[datetime | None] = mapped_column()
    modified_by: Mapped[str | None] = mapped_column(String(255))
    is_active: Mapped[int | None] = mapped_column(Integer, default=1)

    # Relationships
    status: Mapped["Status | None"] = relationship(back_populates="projects")


from src.repositories.schema.status import Status  # noqa: E402
