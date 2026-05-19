"""Exception handlers for the FastAPI application."""

import asyncio
import traceback
import uuid

from fastapi import FastAPI, Request
from fastapi.responses import JSONResponse

from src.settings import OVERVIEW_SERVICE_IDENTIFIER
from src.utils.exceptions.exceptions import AuthenticationError, InvalidParameterError, NotFoundError
from src.utils.helpers import get_file_name, get_function_name, log_error_to_db
from src.utils.logger import logger


def register_exception_handlers(app: FastAPI) -> None:
    """Register all exception handlers on the FastAPI app instance."""

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

    @app.exception_handler(NotFoundError)
    async def not_found_exception_handler(request: Request, exc: NotFoundError) -> JSONResponse:
        """Handle NotFoundError exceptions with HTTP 404 response."""
        return JSONResponse(
            status_code=404,
            content={
                "status_code": 404,
                "status": "failed",
                "message": exc.message,
                "data": [],
            },
        )

    @app.exception_handler(Exception)
    async def global_exception_handler(request: Request, exc: Exception) -> JSONResponse:
        """Handle all unhandled exceptions with HTTP 500 response and async error logging."""
        trace_id = getattr(request.state, "trace_id", str(uuid.uuid4()))
        error_message = f"[trace_id:{trace_id}] {str(exc)}"

        logger.error(
            "Unhandled exception occurred",
            trace_id=trace_id,
            error=str(exc),
            path=str(request.url.path),
        )

        asyncio.create_task(
            log_error_to_db(
                error_message=error_message,
                error_function=get_function_name(exc),
                error_file=get_file_name(exc),
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
