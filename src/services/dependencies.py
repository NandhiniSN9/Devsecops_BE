"""Dependency injection configuration for FastAPI route handlers.

Centralizes the wiring of service and repository instances using
FastAPI's Depends() mechanism. Creates an async SQLAlchemy engine
and session factory at module level, and provides async generator
and factory functions for injecting database sessions, repositories,
and services into route handlers.
"""

from collections.abc import AsyncGenerator

from fastapi import Depends
from sqlalchemy.ext.asyncio import AsyncSession

from src.client.ado_client import AdoClient
from src.client.graph_client import GraphClient
from src.client.jira_client import JiraClient
from src.client.s3_client import S3Client
from src.repositories.database import _async_session_factory
from src.repositories.ado_sync_repository import AdoSyncRepository
from src.repositories.filters_repository import ClientRepository
from src.repositories.overview_repository import OverviewRepository
from src.repositories.projects_repository import ProjectsRepository
from src.repositories.report_repository import ReportRepository
from src.repositories.repository_detail_repository import RepositoryDetailRepository
from src.repositories.servicenow_repository import ServiceNowRepository
from src.repositories.settings_repository import SettingsRepository
from src.services.ado_sync_service import AdoSyncService
from src.services.filter_service import FilterService
from src.services.overview_service import OverviewService
from src.services.projects_service import ProjectsService
from src.services.report_service import ReportService
from src.services.repository_detail_service import RepositoryDetailService
from src.services.servicenow_service import ServiceNowService
from src.services.settings_service import SettingsService
from src.settings import get_settings


async def get_db_session() -> AsyncGenerator[AsyncSession, None]:
    """Yield an async database session with auto-commit/rollback lifecycle.

    Used as a FastAPI dependency to provide a scoped session per request.
    Commits on success, rolls back on exception, and closes on exit.
    """
    async with _async_session_factory() as session:
        try:
            yield session
            await session.commit()
        except Exception:
            await session.rollback()
            raise
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


def get_projects_repository(
    session: AsyncSession = Depends(get_db_session),
) -> ProjectsRepository:
    """Factory for ProjectsRepository with injected database session."""
    return ProjectsRepository(session)


def get_jira_client() -> JiraClient:
    """Factory for JiraClient (uses settings for credentials)."""
    return JiraClient()


def get_projects_service(
    projects_repo: ProjectsRepository = Depends(get_projects_repository),
    s3_client: S3Client = Depends(get_s3_client),
    jira_client: JiraClient = Depends(get_jira_client),
) -> ProjectsService:
    """Factory for ProjectsService with injected dependencies."""
    return ProjectsService(
        projects_repo=projects_repo,
        s3_client=s3_client,
        jira_client=jira_client,
    )


def get_ado_client() -> AdoClient:
    """Factory for AdoClient with configuration from settings."""
    settings = get_settings()
    return AdoClient(
        org_url=settings.ADO_ORG_URL,
        pat=settings.ADO_PAT,
    )


def get_ado_sync_repository(
    session: AsyncSession = Depends(get_db_session),
) -> AdoSyncRepository:
    """Factory for AdoSyncRepository with injected database session."""
    return AdoSyncRepository(session)


def get_ado_sync_service(
    repo: AdoSyncRepository = Depends(get_ado_sync_repository),
    ado_client: AdoClient = Depends(get_ado_client),
) -> AdoSyncService:
    """Factory for AdoSyncService with injected dependencies."""
    return AdoSyncService(repo=repo, ado_client=ado_client)


def get_repository_detail_repository(
    session: AsyncSession = Depends(get_db_session),
) -> RepositoryDetailRepository:
    """Factory for RepositoryDetailRepository with injected database session."""
    return RepositoryDetailRepository(session)


def get_repository_detail_service(
    repo: RepositoryDetailRepository = Depends(get_repository_detail_repository),
) -> RepositoryDetailService:
    """Factory for RepositoryDetailService with injected repository."""
    return RepositoryDetailService(repo=repo)
