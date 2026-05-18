"""SQLAlchemy ORM model for the security_scans table."""

import uuid
from datetime import datetime

from sqlalchemy import ForeignKey, Integer, String, func
from sqlalchemy.orm import Mapped, mapped_column

from src.repositories.schema.base import Base


class SecurityScan(Base):
    """ORM model for the security_scans table."""

    __tablename__ = "security_scans"

    security_scan_id: Mapped[uuid.UUID] = mapped_column(primary_key=True, default=uuid.uuid4)
    repository_id: Mapped[uuid.UUID] = mapped_column(ForeignKey("repositories.repository_id"), nullable=False)
    scan_type: Mapped[str] = mapped_column(String(50), nullable=False)
    findings_count: Mapped[int] = mapped_column(Integer, default=0)
    description: Mapped[str | None] = mapped_column(String(500))
    scanned_at: Mapped[datetime] = mapped_column(nullable=False)
    created_at: Mapped[datetime | None] = mapped_column(default=func.current_timestamp())
    created_by: Mapped[str | None] = mapped_column(String(255))
    modified_at: Mapped[datetime | None] = mapped_column()
    modified_by: Mapped[str | None] = mapped_column(String(255))
    is_active: Mapped[int | None] = mapped_column(Integer, default=1)
