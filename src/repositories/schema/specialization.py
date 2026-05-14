"""SQLAlchemy ORM model for the specializations table."""

import uuid
from datetime import datetime

from sqlalchemy import Integer, String, func
from sqlalchemy.orm import Mapped, mapped_column, relationship

from src.repositories.schema.base import Base


class Specialization(Base):
    """ORM model for the specializations table."""

    __tablename__ = "specializations"

    specialization_id: Mapped[uuid.UUID] = mapped_column(primary_key=True, default=uuid.uuid4)
    specialization_name: Mapped[str] = mapped_column(String(255), nullable=False)
    created_at: Mapped[datetime | None] = mapped_column(default=func.current_timestamp())
    created_by: Mapped[str | None] = mapped_column(String(255))
    modified_at: Mapped[datetime | None] = mapped_column()
    modified_by: Mapped[str | None] = mapped_column(String(255))
    is_active: Mapped[int | None] = mapped_column(Integer, default=1)

    # Relationships
    kpi_histories: Mapped[list["KpiHistory"]] = relationship(back_populates="specialization")
    devsecops_tickets: Mapped[list["DevsecopsTicket"]] = relationship(back_populates="specialization")
    settings: Mapped[list["Setting"]] = relationship(back_populates="specialization")


from src.repositories.schema.devsecops_ticket import DevsecopsTicket  # noqa: E402
from src.repositories.schema.kpi_history import KpiHistory  # noqa: E402
from src.repositories.schema.setting import Setting  # noqa: E402
