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

from src.client.graph_client import GraphClient
from src.client.s3_client import S3Client
from src.repositories.filters_repository import ClientRepository
from src.repositories.overview_repository import OverviewRepository
from src.repositories.report_repository import ReportRepository
from src.repositories.servicenow_repository import ServiceNowRepository
from src.repositories.settings_repository import SettingsRepository
from src.services.filter_service import FilterService
from src.services.overview_service import OverviewService
from src.services.report_service import ReportService
from src.services.servicenow_service import ServiceNowService
from src.services.settings_service import SettingsService
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


def get_settings_repository(
    session: AsyncSession = Depends(get_db_session),
) -> SettingsRepository:
    """Factory for SettingsRepository with injected database session."""
    return SettingsRepository(session)


def get_settings_service(
    settings_repo: SettingsRepository = Depends(get_settings_repository),
) -> SettingsService:
    """Factory for SettingsService with injected repository dependency."""
    return SettingsService(settings_repo=settings_repo)


def get_report_repository(
    session: AsyncSession = Depends(get_db_session),
) -> ReportRepository:
    """Factory for ReportRepository with injected database session."""
    return ReportRepository(session)


def get_graph_client() -> GraphClient:
    """Factory for GraphClient with credentials from settings."""
    settings = get_settings()
    return GraphClient(
        tenant_id=settings.GRAPH_TENANT_ID,
        client_id=settings.GRAPH_CLIENT_ID,
        client_secret=settings.GRAPH_CLIENT_SECRET,
        sender_email=settings.GRAPH_SENDER_EMAIL,
    )


def get_s3_client() -> S3Client:
    """Factory for S3Client with configuration from settings."""
    settings = get_settings()
    return S3Client(
        bucket_name=settings.S3_BUCKET_NAME,
        region=settings.AWS_REGION,
        url_expiry_days=settings.S3_URL_EXPIRY_DAYS,
    )


def get_report_service(
    report_repo: ReportRepository = Depends(get_report_repository),
    graph_client: GraphClient = Depends(get_graph_client),
    s3_client: S3Client = Depends(get_s3_client),
) -> ReportService:
    """Factory for ReportService with injected dependencies."""
    return ReportService(
        report_repo=report_repo,
        graph_client=graph_client,
        s3_client=s3_client,
    )
