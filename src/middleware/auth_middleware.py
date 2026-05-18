"""Authentication middleware for encrypted token validation with Jira email verification."""

import json
import uuid

from cryptography.fernet import Fernet, InvalidToken
from starlette.middleware.base import BaseHTTPMiddleware
from starlette.requests import Request
from starlette.responses import JSONResponse
from starlette.types import ASGIApp

from src.client.jira_client import JiraClient
from src.settings import get_settings
from src.utils.logger import logger

# Paths excluded from authentication
EXCLUDED_PATHS: set[str] = {"/health", "/ready", "/docs", "/openapi.json"}


class AuthMiddleware(BaseHTTPMiddleware):
    """Middleware that validates encrypted bearer tokens and Jira email.

    For every request:
    - Generates a trace_id (UUID v4) and attaches it to request.state.trace_id
    - Skips authentication for excluded paths (health, ready, docs, openapi.json)
    - Extracts Bearer token from Authorization header
    - Decrypts token using TOKEN_PRIVATE_KEY (Fernet symmetric encryption)
    - Parses decrypted payload as JSON to extract email field
    - Validates email via Jira REST API
    - On success: attaches email to request.state.user_email
    - On failure: returns 401 with BaseResponse body
    """

    def __init__(self, app: ASGIApp) -> None:
        super().__init__(app)
        self._jira_client = JiraClient()

    async def dispatch(self, request: Request, call_next):  # noqa: ANN001
        """Process each request through authentication logic."""
        # Generate trace_id for every request
        trace_id = str(uuid.uuid4())
        request.state.trace_id = trace_id

        # Skip auth for excluded paths
        if request.url.path in EXCLUDED_PATHS:
            response = await call_next(request)
            return response

        # Extract Authorization header
        auth_header = request.headers.get("Authorization")
        if not auth_header or not auth_header.startswith("Bearer "):
            logger.warning("Missing or invalid Authorization header", trace_id=trace_id, path=request.url.path)
            return self._build_401_response("Authentication token is missing or expired")

        token = auth_header[len("Bearer ") :]

        # Decrypt token using Fernet
        email = self._decrypt_and_extract_email(token, trace_id)
        if email is None:
            return self._build_401_response("Authentication failed or user not found in Jira")

        # Validate email is not empty
        if not email.strip():
            logger.warning("Empty email in decrypted token payload", trace_id=trace_id)
            return self._build_401_response("Authentication failed or user not found in Jira")

        # Validate email via Jira
        is_valid = await self._jira_client.validate_email(email)
        if not is_valid:
            logger.warning("Jira email validation failed", trace_id=trace_id, email=email)
            return self._build_401_response("Authentication failed or user not found in Jira")

        # Authentication successful
        request.state.user_email = email
        response = await call_next(request)
        return response

    def _decrypt_and_extract_email(self, token: str, trace_id: str) -> str | None:
        """Decrypt the token and extract the email field from the payload.

        Args:
            token: The encrypted bearer token string.
            trace_id: Request trace ID for logging.

        Returns:
            The email string if decryption and extraction succeed, None otherwise.
        """
        try:
            settings = get_settings()            
            fernet = Fernet(settings.TOKEN_PRIVATE_KEY.encode())
            decrypted_bytes = fernet.decrypt(token.encode())
            payload = json.loads(decrypted_bytes.decode())
            return payload.get("email", "")
        except (InvalidToken, ValueError, json.JSONDecodeError, Exception) as exc:
            logger.warning("Token decryption failed", trace_id=trace_id, error=str(exc))
            return None

    @staticmethod
    def _build_401_response(message: str) -> JSONResponse:
        """Build a 401 JSONResponse with BaseResponse body.

        Args:
            message: The error message to include in the response.

        Returns:
            JSONResponse with 401 status and BaseResponse-formatted body.
        """
        return JSONResponse(
            status_code=401,
            content={
                "status_code": 401,
                "status": "failed",
                "message": message,
                "data": [],
            },
        )
