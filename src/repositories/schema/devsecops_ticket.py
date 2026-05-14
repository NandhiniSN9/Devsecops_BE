"""SQLAlchemy ORM model for the devsecops_tickets table."""

import uuid
from datetime import datetime

from sqlalchemy import ForeignKey, Integer, String, func
from sqlalchemy.orm import Mapped, mapped_column, relationship

from src.repositories.schema.base import Base


class DevsecopsTicket(Base):
    """ORM model for the devsecops_tickets table."""

    __tablename__ = "devsecops_tickets"

    ticket_id: Mapped[uuid.UUID] = mapped_column(primary_key=True, default=uuid.uuid4)
    specialization_id: Mapped[uuid.UUID | None] = mapped_column(ForeignKey("specializations.specialization_id"))
    project_id: Mapped[uuid.UUID | None] = mapped_column()
    sn_project_id: Mapped[str | None] = mapped_column(String(255))
    project_name: Mapped[str] = mapped_column(String(255), nullable=False)
    client: Mapped[str | None] = mapped_column(String(255))
    requested_by: Mapped[str | None] = mapped_column(String(255))
    approver: Mapped[str | None] = mapped_column(String(255))
    sync_method: Mapped[str | None] = mapped_column(String(255))
    requested_at: Mapped[datetime | None] = mapped_column()
    created_at: Mapped[datetime | None] = mapped_column(default=func.current_timestamp())
    created_by: Mapped[str | None] = mapped_column(String(255))
    modified_at: Mapped[datetime | None] = mapped_column()
    modified_by: Mapped[str | None] = mapped_column(String(255))
    is_active: Mapped[int | None] = mapped_column(Integer, default=1)

    # Relationships
    specialization: Mapped["Specialization | None"] = relationship(back_populates="devsecops_tickets")


from src.repositories.schema.specialization import Specialization  # noqa: E402
