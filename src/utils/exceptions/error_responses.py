"""Error response builders for standardized API error responses.

All error responses follow the BaseResponse format:
- status_code: int (HTTP status code)
- status: Literal["success", "failed", "error"]
- message: str (max 256 chars)
- data: Any (empty array for errors)

The trace_id (UUID v4) is included as prefix in error_message:
    [trace_id:{uuid}] <message>
"""

from typing import Any


def _format_error_message(trace_id: str | None, message: str) -> str:
    """Format error message with trace_id prefix if available."""
    if trace_id:
        return f"[trace_id:{trace_id}] {message}"
    return message


def build_invalid_parameter_error_response(message: str, trace_id: str | None = None) -> dict[str, Any]:
    """Build a 400 error response for invalid parameter errors.

    Args:
        message: Description of the invalid parameter.
        trace_id: Optional UUID v4 trace identifier for log correlation.

    Returns:
        Dict matching BaseResponse schema with status_code=400, status="failed".
    """
    return {
        "status_code": 400,
        "status": "failed",
        "message": _format_error_message(trace_id, message),
        "data": [],
    }


def build_authentication_error_response(
    trace_id: str | None = None,
    message: str = "Authentication failed or user not found in Jira",
) -> dict[str, Any]:
    """Build a 401 error response for authentication failures.

    Args:
        trace_id: Optional UUID v4 trace identifier for log correlation.
        message: Authentication failure message.

    Returns:
        Dict matching BaseResponse schema with status_code=401, status="failed".
    """
    return {
        "status_code": 401,
        "status": "failed",
        "message": _format_error_message(trace_id, message),
        "data": [],
    }


def build_unexpected_error_response(
    trace_id: str | None = None,
) -> dict[str, Any]:
    """Build a 500 error response for unhandled exceptions.

    Args:
        trace_id: Optional UUID v4 trace identifier for log correlation.

    Returns:
        Dict matching BaseResponse schema with status_code=500, status="error".
    """
    message = "An unexpected error occurred. Please try again later"
    return {
        "status_code": 500,
        "status": "error",
        "message": _format_error_message(trace_id, message),
        "data": [],
    }
