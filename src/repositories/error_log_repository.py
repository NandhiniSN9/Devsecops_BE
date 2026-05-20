"""Repository for persisting error logs to the database."""

import asyncio
from sqlalchemy.exc import SQLAlchemyError
from sqlalchemy.ext.asyncio import AsyncSession
from src.repositories.schema.error_log import ErrorLog
from src.utils.logger import logger

# Maximum length for text fields before truncation
_MAX_TEXT_LENGTH = 65_535

# Timeout for DB insert operations (seconds)
_DB_INSERT_TIMEOUT = 10


class ErrorLogRepository:
    """Handles asynchronous, non-blocking error log persistence."""

    def __init__(self, session: AsyncSession) -> None:
        self._session = session

    async def log_error(
        self,
        error_message: str,
        error_function: str,
        error_file: str,
        stack_trace: str,
        created_by: str,
    ) -> None:
        """Persist an error log record to the database.

        Truncates error_message and stack_trace to 65,535 characters.
        Enforces a 10-second timeout; abandoned if exceeded.
        If the DB insert fails, logs the error details to structured
        JSON application logs as a fallback.

        This method is designed to be called via asyncio.create_task
        from the global exception handler to ensure non-blocking execution.
        """
        try:
            truncated_message = error_message[:_MAX_TEXT_LENGTH]
            truncated_stack_trace = stack_trace[:_MAX_TEXT_LENGTH]

            await asyncio.wait_for(
                self._insert_error_log(
                    error_message=truncated_message,
                    error_function=error_function,
                    error_file=error_file,
                    stack_trace=truncated_stack_trace,
                    created_by=created_by,
                ),
                timeout=_DB_INSERT_TIMEOUT,
            )

        except TimeoutError:
            logger.error(
                "Error log DB insert timed out after 10 seconds",
                error_message=truncated_message,
                error_function=error_function,
                error_file=error_file,
                created_by=created_by,
            )

        except Exception as exc:
            logger.error(
                "Failed to persist error log to database",
                error_message=truncated_message,
                error_function=error_function,
                error_file=error_file,
                created_by=created_by,
                db_error=str(exc),
            )

    async def _insert_error_log(
        self,
        error_message: str,
        error_function: str,
        error_file: str,
        stack_trace: str,
        created_by: str,
    ) -> None:
        """Execute the actual database insert."""
        error_log = ErrorLog(
            error_message=error_message,
            error_function=error_function,
            error_file=error_file,
            stack_trace=stack_trace,
            created_by=created_by,
        )
        self._session.add(error_log)
        await self._session.commit()
