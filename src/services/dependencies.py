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

from src.repositories.filters_repository import ClientRepository
from src.repositories.overview_repository import OverviewRepository
from src.repositories.servicenow_repository import ServiceNowRepository
from src.services.filter_service import FilterService
from src.services.overview_service import OverviewService
from src.services.servicenow_service import ServiceNowService
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


def get_overview_repository(
    session: AsyncSession = Depends(get_db_session),
) -> OverviewRepository:
    """Factory for OverviewRepository with injected database session."""
    return OverviewRepository(session)


def get_client_repository(
    session: AsyncSession = Depends(get_db_session),
) -> ClientRepository:
    """Factory for ClientRepository with injected database session."""
    return ClientRepository(session)


def get_overview_service(
    overview_repo: OverviewRepository = Depends(get_overview_repository),
) -> OverviewService:
    """Factory for OverviewService with injected repository dependency."""
    return OverviewService(overview_repo=overview_repo)


def get_filter_service(
    client_repo: ClientRepository = Depends(get_client_repository),
) -> FilterService:
    """Factory for FilterService with injected repository dependency."""
    return FilterService(client_repo=client_repo)


def get_servicenow_repository(
    session: AsyncSession = Depends(get_db_session),
) -> ServiceNowRepository:
    """Factory for ServiceNowRepository with injected database session."""
    return ServiceNowRepository(session)


def get_servicenow_service(
    servicenow_repo: ServiceNowRepository = Depends(get_servicenow_repository),
) -> ServiceNowService:
    """Factory for ServiceNowService with injected repository dependency."""
    return ServiceNowService(servicenow_repo=servicenow_repo)
