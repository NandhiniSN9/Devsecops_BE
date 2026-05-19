"""Main application entry point for the Overview Dashboard API."""

from contextlib import asynccontextmanager

from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware

from src.migrations.migration import Migration
from src.routes import (
    default_route,
    filter_route,
    overview_route,
    projects_route,
    report_route,
    servicenow_route,
    settings_route,
)
from src.services.dependencies import _engine
from src.settings import validate_settings_at_startup
from src.utils.exceptions.exception_handlers import register_exception_handlers
from src.utils.logger import logger


@asynccontextmanager
async def lifespan(app: FastAPI):
    """Application lifespan context manager for startup/shutdown events."""
    logger.info("Application starting up")
    validate_settings_at_startup()
    logger.info("Settings validated successfully")

    async with _engine.connect() as conn:
        await conn.run_sync(lambda sync_conn: Migration(sync_conn).create_tables())
    logger.info("Database migration check completed")

    yield

    logger.info("Application shutting down")


app = FastAPI(
    title="Overview Dashboard API",
    description="Backend API for the DevSecOps Jira Dashboard landing page",
    version="1.0.0",
    lifespan=lifespan,
)

app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["GET", "POST", "PUT", "DELETE", "OPTIONS"],
    allow_headers=["*"],
)

register_exception_handlers(app)

app.include_router(default_route.router)
app.include_router(overview_route.router, prefix="/api/v1")
app.include_router(filter_route.router, prefix="/api/v1")
app.include_router(servicenow_route.router, prefix="/api/v1")
app.include_router(settings_route.router, prefix="/api/v1")
app.include_router(report_route.router, prefix="/api/v1")
app.include_router(projects_route.router, prefix="/api/v1")
