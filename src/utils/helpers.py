"""Utility helper functions for the DevSecOps Dashboard API."""

from src.repositories.database import _async_session_factory
from src.repositories.error_log_repository import ErrorLogRepository
from src.utils.logger import logger
from src.utils.text import normalize_project_name

__all__ = [
    "normalize_project_name",
    "get_function_name",
    "get_file_name",
    "log_error_to_db",
]

def get_function_name(exc: Exception) -> str:
    """Extract the function name where the exception originated."""
    tb = exc.__traceback__
    if tb is not None:
        while tb.tb_next is not None:
            tb = tb.tb_next
        return tb.tb_frame.f_code.co_name
    return "unknown"

def get_file_name(exc: Exception) -> str:
    """Extract the file name where the exception originated."""
    tb = exc.__traceback__
    if tb is not None:
        while tb.tb_next is not None:
            tb = tb.tb_next
        return tb.tb_frame.f_code.co_filename
    return "unknown"


async def log_error_to_db(
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
