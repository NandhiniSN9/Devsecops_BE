"""Unit tests for ErrorLogRepository."""

import asyncio
import sys
from unittest.mock import AsyncMock, MagicMock, patch

import pytest

# Mock structlog to avoid import errors from logger setup
mock_structlog = MagicMock()
mock_structlog.get_logger.return_value = MagicMock()
sys.modules.setdefault("structlog", mock_structlog)

from src.repositories.error_log_repository import ErrorLogRepository, _MAX_TEXT_LENGTH  # noqa: E402, I001


@pytest.fixture
def mock_session():
    """Create a mock AsyncSession."""
    session = AsyncMock()
    session.add = MagicMock()
    session.commit = AsyncMock()
    return session


@pytest.fixture
def repository(mock_session):
    """Create an ErrorLogRepository with a mock session."""
    return ErrorLogRepository(session=mock_session)


class TestLogError:
    """Tests for ErrorLogRepository.log_error method."""

    async def test_log_error_success(self, repository, mock_session):
        """Test successful error log insertion."""
        await repository.log_error(
            error_message="Test error",
            error_function="test_func",
            error_file="test_file.py",
            stack_trace="Traceback ...",
            created_by="overview_service",
        )

        mock_session.add.assert_called_once()
        mock_session.commit.assert_awaited_once()

        # Verify the ErrorLog object was created with correct values
        error_log = mock_session.add.call_args[0][0]
        assert error_log.error_message == "Test error"
        assert error_log.error_function == "test_func"
        assert error_log.error_file == "test_file.py"
        assert error_log.stack_trace == "Traceback ..."
        assert error_log.created_by == "overview_service"

    async def test_log_error_truncates_error_message(self, repository, mock_session):
        """Test that error_message is truncated to 65,535 characters."""
        long_message = "x" * 100_000

        await repository.log_error(
            error_message=long_message,
            error_function="test_func",
            error_file="test_file.py",
            stack_trace="short trace",
            created_by="overview_service",
        )

        error_log = mock_session.add.call_args[0][0]
        assert len(error_log.error_message) == _MAX_TEXT_LENGTH

    async def test_log_error_truncates_stack_trace(self, repository, mock_session):
        """Test that stack_trace is truncated to 65,535 characters."""
        long_trace = "y" * 100_000

        await repository.log_error(
            error_message="short message",
            error_function="test_func",
            error_file="test_file.py",
            stack_trace=long_trace,
            created_by="overview_service",
        )

        error_log = mock_session.add.call_args[0][0]
        assert len(error_log.stack_trace) == _MAX_TEXT_LENGTH

    async def test_log_error_does_not_truncate_short_fields(self, repository, mock_session):
        """Test that fields within limit are not truncated."""
        message = "Short message"
        trace = "Short trace"

        await repository.log_error(
            error_message=message,
            error_function="test_func",
            error_file="test_file.py",
            stack_trace=trace,
            created_by="overview_service",
        )

        error_log = mock_session.add.call_args[0][0]
        assert error_log.error_message == message
        assert error_log.stack_trace == trace

    @patch("src.repositories.error_log_repository.logger")
    async def test_log_error_handles_db_failure(self, mock_logger, repository, mock_session):
        """Test that DB insert failure is logged to application logs."""
        mock_session.commit.side_effect = Exception("Connection refused")

        await repository.log_error(
            error_message="Test error",
            error_function="test_func",
            error_file="test_file.py",
            stack_trace="Traceback ...",
            created_by="overview_service",
        )

        mock_logger.error.assert_called_once()
        call_kwargs = mock_logger.error.call_args
        assert "Failed to persist error log to database" in call_kwargs[0][0]
        assert call_kwargs[1]["db_error"] == "Connection refused"

    @patch("src.repositories.error_log_repository.logger")
    async def test_log_error_handles_timeout(self, mock_logger, repository, mock_session):
        """Test that timeout is handled gracefully."""

        async def slow_commit():
            await asyncio.sleep(20)

        mock_session.commit = slow_commit

        await repository.log_error(
            error_message="Test error",
            error_function="test_func",
            error_file="test_file.py",
            stack_trace="Traceback ...",
            created_by="overview_service",
        )

        mock_logger.error.assert_called_once()
        assert "timed out" in mock_logger.error.call_args[0][0]

    async def test_log_error_exact_boundary_length(self, repository, mock_session):
        """Test that a message exactly at the limit is not truncated."""
        exact_message = "a" * _MAX_TEXT_LENGTH

        await repository.log_error(
            error_message=exact_message,
            error_function="test_func",
            error_file="test_file.py",
            stack_trace="trace",
            created_by="overview_service",
        )

        error_log = mock_session.add.call_args[0][0]
        assert len(error_log.error_message) == _MAX_TEXT_LENGTH
        assert error_log.error_message == exact_message
