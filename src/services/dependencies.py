"""Dependency injection configuration for FastAPI route handlers.

Centralizes the wiring of service and repository instances using
FastAPI's Depends() mechanism. Creates an async SQLAlchemy engine
and session factory at module level, and provides async generator
and factory functions for injecting database sessions, repositories,
and services into route handlers.
"""

from collections.abc import AsyncGenerator

from fastapi import Depends
from sqlalchemy.ext.asyncio import AsyncSession, async_sessionmaker, create_async_engine

from src.repositories.kpi_history_repository import KpiHistoryRepository
from src.repositories.project_repository import ProjectRepository
from src.repositories.specialization_repository import SpecializationRepository
from src.repositories.status_repository import StatusRepository
from src.services.filter_service import FilterService
from src.services.overview_service import OverviewService
from src.settings import get_settings

# Create async engine and session factory at module level
_settings = get_settings()
_engine = create_async_engine(
    _settings.DATABASE_URL,
    pool_pre_ping=True,
    pool_size=10,
    max_overflow=20,
)
_async_session_factory = async_sessionmaker(
    bind=_engine,
    class_=AsyncSession,
    expire_on_commit=False,
)


async def get_db_session() -> AsyncGenerator[AsyncSession, None]:
    """Yield an async database session and ensure cleanup on exit.

    Used as a FastAPI dependency to provide a scoped session per request.
    The session is automatically closed after the request completes.
    """
    async with _async_session_factory() as session:
        try:
            yield session
        finally:
            await session.close()


def get_kpi_history_repository(
    session: AsyncSession = Depends(get_db_session),
) -> KpiHistoryRepository:
    """Factory for KpiHistoryRepository with injected database session."""
    return KpiHistoryRepository(session)


def get_project_repository(
    session: AsyncSession = Depends(get_db_session),
) -> ProjectRepository:
    """Factory for ProjectRepository with injected database session."""
    return ProjectRepository(session)


def get_specialization_repository(
    session: AsyncSession = Depends(get_db_session),
) -> SpecializationRepository:
    """Factory for SpecializationRepository with injected database session."""
    return SpecializationRepository(session)


def get_status_repository(
    session: AsyncSession = Depends(get_db_session),
) -> StatusRepository:
    """Factory for StatusRepository with injected database session."""
    return StatusRepository(session)


def get_overview_service(
    kpi_repo: KpiHistoryRepository = Depends(get_kpi_history_repository),
    project_repo: ProjectRepository = Depends(get_project_repository),
    specialization_repo: SpecializationRepository = Depends(get_specialization_repository),
) -> OverviewService:
    """Factory for OverviewService with injected repository dependencies."""
    return OverviewService(
        kpi_repo=kpi_repo,
        project_repo=project_repo,
        specialization_repo=specialization_repo,
    )


def get_filter_service(
    specialization_repo: SpecializationRepository = Depends(get_specialization_repository),
    project_repo: ProjectRepository = Depends(get_project_repository),
    status_repo: StatusRepository = Depends(get_status_repository),
) -> FilterService:
    """Factory for FilterService with injected repository dependencies."""
    return FilterService(
        specialization_repo=specialization_repo,
        project_repo=project_repo,
        status_repo=status_repo,
    )
