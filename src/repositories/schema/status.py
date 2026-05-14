"""SQLAlchemy ORM model for the statuses table."""

import uuid
from datetime import datetime

from sqlalchemy import Integer, String, func
from sqlalchemy.orm import Mapped, mapped_column, relationship

from src.repositories.schema.base import Base


class Status(Base):
    """ORM model for the statuses table."""

    __tablename__ = "statuses"

    status_id: Mapped[uuid.UUID] = mapped_column(primary_key=True, default=uuid.uuid4)
    status_name: Mapped[str] = mapped_column(String(255), nullable=False)
    created_at: Mapped[datetime | None] = mapped_column(default=func.current_timestamp())
    created_by: Mapped[str | None] = mapped_column(String(255))
    modified_at: Mapped[datetime | None] = mapped_column()
    modified_by: Mapped[str | None] = mapped_column(String(255))
    is_active: Mapped[int | None] = mapped_column(Integer, default=1)

    # Relationships
    projects: Mapped[list["Project"]] = relationship(back_populates="status")


from src.repositories.schema.project import Project  # noqa: E402
