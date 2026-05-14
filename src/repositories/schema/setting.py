"""SQLAlchemy ORM model for the settings table."""

import uuid
from datetime import datetime

from sqlalchemy import ForeignKey, Integer, String, func
from sqlalchemy.orm import Mapped, mapped_column, relationship

from src.repositories.schema.base import Base


class Setting(Base):
    """ORM model for the settings table."""

    __tablename__ = "settings"

    setting_id: Mapped[uuid.UUID] = mapped_column(primary_key=True, default=uuid.uuid4)
    specialization_id: Mapped[uuid.UUID | None] = mapped_column(ForeignKey("specializations.specialization_id"))
    at_risk_threshold: Mapped[int] = mapped_column(Integer, nullable=False)
    email_digest: Mapped[str | None] = mapped_column(String(50))
    at_risk_alert: Mapped[str | None] = mapped_column(String(50))
    last_synced: Mapped[datetime | None] = mapped_column()
    created_at: Mapped[datetime | None] = mapped_column(default=func.current_timestamp())
    created_by: Mapped[str | None] = mapped_column(String(255))
    modified_at: Mapped[datetime | None] = mapped_column()
    modified_by: Mapped[str | None] = mapped_column(String(255))
    is_active: Mapped[int | None] = mapped_column(Integer, default=1)

    # Relationships
    specialization: Mapped["Specialization | None"] = relationship(back_populates="settings")


from src.repositories.schema.specialization import Specialization  # noqa: E402
