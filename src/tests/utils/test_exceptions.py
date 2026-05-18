"""Unit tests for custom exceptions and error response builders."""

import pytest

from src.utils.exceptions.error_codes import AUTHENTICATION_FAILED, INVALID_PARAMETER, UNEXPECTED_ERROR
from src.utils.exceptions.error_responses import (
    build_authentication_error_response,
    build_invalid_parameter_error_response,
    build_unexpected_error_response,
)
from src.utils.exceptions.exceptions import AuthenticationError, InvalidParameterError, NotFoundError


class TestCustomExceptions:
    """Tests for custom exception classes."""

    def test_invalid_parameter_error(self):
        exc = InvalidParameterError("bad param")
        assert exc.message == "bad param"
        assert str(exc) == "bad param"

    def test_authentication_error_default_message(self):
        exc = AuthenticationError()
        assert "Authentication failed" in exc.message

    def test_authentication_error_custom_message(self):
        exc = AuthenticationError("Token expired")
        assert exc.message == "Token expired"

    def test_not_found_error_default_message(self):
        exc = NotFoundError()
        assert "not found" in exc.message

    def test_not_found_error_custom_message(self):
        exc = NotFoundError("Project not found")
        assert exc.message == "Project not found"


class TestErrorResponseBuilders:
    """Tests for error response builder functions."""

    def test_invalid_parameter_response(self):
        resp = build_invalid_parameter_error_response("Field X is invalid")
        assert resp["status_code"] == 400
        assert resp["status"] == "failed"
        assert "Field X is invalid" in resp["message"]
        assert resp["data"] == []

    def test_invalid_parameter_response_with_trace_id(self):
        resp = build_invalid_parameter_error_response("bad", trace_id="abc-123")
        assert "[trace_id:abc-123]" in resp["message"]

    def test_authentication_error_response(self):
        resp = build_authentication_error_response()
        assert resp["status_code"] == 401
        assert resp["status"] == "failed"
        assert "Authentication" in resp["message"]

    def test_authentication_error_response_custom_message(self):
        resp = build_authentication_error_response(message="Token expired")
        assert "Token expired" in resp["message"]

    def test_authentication_error_response_with_trace_id(self):
        resp = build_authentication_error_response(trace_id="xyz-789")
        assert "[trace_id:xyz-789]" in resp["message"]

    def test_unexpected_error_response(self):
        resp = build_unexpected_error_response()
        assert resp["status_code"] == 500
        assert resp["status"] == "error"
        assert "unexpected error" in resp["message"]

    def test_unexpected_error_response_with_trace_id(self):
        resp = build_unexpected_error_response(trace_id="trace-001")
        assert "[trace_id:trace-001]" in resp["message"]


class TestErrorCodes:
    """Tests for error code constants."""

    def test_error_codes_are_strings(self):
        assert INVALID_PARAMETER == "INVALID_PARAMETER"
        assert AUTHENTICATION_FAILED == "AUTHENTICATION_FAILED"
        assert UNEXPECTED_ERROR == "UNEXPECTED_ERROR"
