"""Main application entry point for the Overview Dashboard API.

Creates the FastAPI app instance, registers middleware, exception handlers,
and includes all route routers with appropriate prefixes.
"""

import asyncio
import traceback
import uuid
from contextlib import asynccontextmanager

from fastapi import FastAPI, Request
from fastapi.responses import JSONResponse

from src.middleware.auth_middleware import AuthMiddleware
from src.repositories.error_log_repository import ErrorLogRepository
from src.routes import default_route, filter_route, overview_route, servicenow_route
from src.services.dependencies import _async_session_factory
from src.settings import OVERVIEW_SERVICE_IDENTIFIER, validate_settings_at_startup
from src.utils.exceptions.exceptions import AuthenticationError, InvalidParameterError
from src.utils.logger import logger

# ============================================================
# Lifespan Context Manager
# ============================================================


@asynccontextmanager
async def lifespan(app: FastAPI):
    """Application lifespan context manager for startup/shutdown events.

    Startup:
        - Validates all required settings (exits on failure).

    Shutdown:
        - Performs graceful cleanup.
    """
    # Startup
    logger.info("Application starting up")
    validate_settings_at_startup()
    logger.info("Settings validated successfully")

    yield

    # Shutdown
    logger.info("Application shutting down")


# ============================================================
# FastAPI App Instance
# ============================================================

app = FastAPI(
    title="Overview Dashboard API",
    description="Backend API for the DevSecOps Jira Dashboard landing page",
    version="1.0.0",
    lifespan=lifespan,
)


# ============================================================
# Middleware Registration
# ============================================================

# NOTE: Auth middleware disabled temporarily for local testing
# app.add_middleware(AuthMiddleware)


# ============================================================
# Helper Functions for Error Logging
# ============================================================


def _get_function_name(exc: Exception) -> str:
    """Extract the function name where the exception originated."""
    tb = exc.__traceback__
    if tb is not None:
        # Walk to the deepest frame
        while tb.tb_next is not None:
            tb = tb.tb_next
        return tb.tb_frame.f_code.co_name
    return "unknown"


def _get_file_name(exc: Exception) -> str:
    """Extract the file name where the exception originated."""
    tb = exc.__traceback__
    if tb is not None:
        # Walk to the deepest frame
        while tb.tb_next is not None:
            tb = tb.tb_next
        return tb.tb_frame.f_code.co_filename
    return "unknown"


async def _log_error_to_db(
    error_message: str,
    error_function: str,
    error_file: str,
    stack_trace: str,
    created_by: str,
) -> None:
    """Persist error details to the error_log table.

    Creates a new database session for the error log insert.
    Falls back to structlog if the DB insert fails.
    """
    try:
        async with _async_session_factory() as session:
            repo = ErrorLogRepository(session)
            await repo.log_error(
                error_message=error_message,
                error_function=error_function,
                error_file=error_file,
                stack_trace=stack_trace,
                created_by=created_by,
            )
    except Exception as db_exc:
        logger.error(
            "Failed to log error to database, falling back to structured log",
            original_error=error_message,
            db_error=str(db_exc),
            error_function=error_function,
            error_file=error_file,
        )


# ============================================================
# Exception Handlers
# ============================================================


@app.exception_handler(InvalidParameterError)
async def invalid_parameter_exception_handler(request: Request, exc: InvalidParameterError) -> JSONResponse:
    """Handle InvalidParameterError exceptions with HTTP 400 response."""
    return JSONResponse(
        status_code=400,
        content={
            "status_code": 400,
            "status": "failed",
            "message": exc.message,
            "data": [],
        },
    )


@app.exception_handler(AuthenticationError)
async def authentication_exception_handler(request: Request, exc: AuthenticationError) -> JSONResponse:
    """Handle AuthenticationError exceptions with HTTP 401 response."""
    return JSONResponse(
        status_code=401,
        content={
            "status_code": 401,
            "status": "failed",
            "message": exc.message,
            "data": [],
        },
    )


@app.exception_handler(Exception)
async def global_exception_handler(request: Request, exc: Exception) -> JSONResponse:
    """Handle all unhandled exceptions with HTTP 500 response and async error logging.

    - Gets trace_id from request.state (set by AuthMiddleware)
    - Returns generic error message to client
    - Logs full error details to error_log table via asyncio.create_task (non-blocking)
    - Falls back to structlog if DB logging fails
    """
    trace_id = getattr(request.state, "trace_id", str(uuid.uuid4()))
    error_message = f"[trace_id:{trace_id}] {str(exc)}"

    logger.error(
        "Unhandled exception occurred",
        trace_id=trace_id,
        error=str(exc),
        path=str(request.url.path),
    )

    # Non-blocking async error logging to database
    asyncio.create_task(
        _log_error_to_db(
            error_message=error_message,
            error_function=_get_function_name(exc),
            error_file=_get_file_name(exc),
            stack_trace=traceback.format_exc(),
            created_by=OVERVIEW_SERVICE_IDENTIFIER,
        )
    )

    return JSONResponse(
        status_code=500,
        content={
            "status_code": 500,
            "status": "error",
            "message": "An unexpected error occurred. Please try again later",
            "data": [],
        },
    )


# ============================================================
# Router Registration
# ============================================================

# Health and readiness endpoints at root level (no prefix, no auth required)
app.include_router(default_route.router)

# Overview and filter endpoints under /api/v1 prefix
app.include_router(overview_route.router, prefix="/api/v1")
app.include_router(filter_route.router, prefix="/api/v1")

# ServiceNow sync endpoints under /api/v1 prefix
app.include_router(servicenow_route.router, prefix="/api/v1")
