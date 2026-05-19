"""
Health and readiness check routes for container orchestrator probes.

These endpoints are excluded from authentication middleware and provide
liveness (/health)
readiness (/ready) which signals for the service.

"""

import asyncio
from fastapi import APIRouter, Depends
from sqlalchemy import text
from sqlalchemy.ext.asyncio import AsyncSession
from starlette.responses import JSONResponse
from src.services.dependencies import get_db_session
from src.utils.logger import logger

router = APIRouter()

@router.get("/health")
async def health_check() -> JSONResponse:

    """Liveness probe endpoint.

    Returns HTTP 200 with {"status": "healthy"} under normal conditions.
    Returns HTTP 503 with {"status": "unhealthy"} if an unexpected error occurs.

    """
    try:
        return JSONResponse(status_code=200, content={"status": "healthy"})
    except Exception as exc:
        logger.error("Unexpected error in health_check endpoint", error=str(exc))
        return JSONResponse(status_code=503, content={"status": "unhealthy"})


@router.get("/ready")
async def readiness_check(session: AsyncSession = Depends(get_db_session)) -> JSONResponse:

    """Readiness probe endpoint with database connectivity check.

    Executes a simple SELECT 1 query with a 5-second timeout to verify
    database connectivity. Returns HTTP 200 if the database responds,
    or HTTP 503 if the check fails or times out.

    Args:
        session: Injected async database session.

    Returns:
        JSONResponse with readiness status.
    """
    try:
        await asyncio.wait_for(session.execute(text("SELECT 1")), timeout=5.0)
        return JSONResponse(status_code=200, content={"status": "ready"})
    except (TimeoutError, Exception) as exc:
        logger.warning("Readiness check failed: database connectivity issue", error=str(exc))
        return JSONResponse(status_code=503, content={"status": "unavailable"})
