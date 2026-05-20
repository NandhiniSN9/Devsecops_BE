"""Authentication middleware for encrypted token validation with Jira email verification."""

import json
import uuid
from cryptography.fernet import Fernet, InvalidToken
from starlette.middleware.base import BaseHTTPMiddleware
from starlette.requests import Request
from starlette.types import ASGIApp
from src.client.jira_client import JiraClient
from src.settings import get_settings
from src.utils.exceptions.exceptions import AuthenticationError
from src.utils.logger import logger




class AuthMiddleware(BaseHTTPMiddleware):
    """Middleware that validates encrypted bearer tokens and Jira email.

    For every request:
    - Generates a trace_id (UUID v4) and attaches it to request.state.trace_id
    - Skips authentication for excluded paths (health, ready, docs, openapi.json)
    - Extracts Bearer token from Authorization header
    - Decrypts token using TOKEN_PRIVATE_KEY (Fernet symmetric encryption)
    - Parses decrypted payload as JSON to extract email and jira_id fields
    - Validates email via Jira REST API
    - On success: attaches email and jira_id to request.state
    - On failure: raises AuthenticationError
    """

    def __init__(self, app: ASGIApp) -> None:
        super().__init__(app)
        self._jira_client = JiraClient()

    async def dispatch(self, request: Request, call_next):
        """Process each request through authentication logic."""
        try:
            # Generate trace_id for every request
            trace_id = str(uuid.uuid4())
            request.state.trace_id = trace_id

            # Paths excluded from authentication
            EXCLUDED_PATHS: set[str] = {"/health", "/ready", "/docs", "/openapi.json"}

            # Skip auth for excluded paths
            if request.url.path in EXCLUDED_PATHS:
                response = await call_next(request)
                return response

            # Extract Authorization header
            auth_header = request.headers.get("Authorization")
            if not auth_header or not auth_header.startswith("Bearer "):
                logger.warning("Missing or invalid Authorization header", trace_id=trace_id, path=request.url.path)
                raise AuthenticationError("Authentication token is missing or expired")

            token = auth_header[len("Bearer "):]

            # Decrypt token and extract payload
            payload = self._decrypt_and_extract_payload(token, trace_id)
            if payload is None:
                raise AuthenticationError("Authentication failed or user not found in Jira")

            email = payload.get("email", "")
            jira_id = payload.get("jira_id") or payload.get("jira_account_id") or ""

            # Validate email is not empty
            if not email.strip():
                logger.warning("Empty email in decrypted token payload", trace_id=trace_id)
                raise AuthenticationError("Authentication failed or user not found in Jira")

            # Validate email via Jira
            is_valid = await self._jira_client.validate_email(email)
            if not is_valid:
                logger.warning("Jira email validation failed", trace_id=trace_id, email=email)
                raise AuthenticationError("Authentication failed or user not found in Jira")

            # Authentication successful — store both email and jira_id on request state
            request.state.email = email
            request.state.jira_id = jira_id
            response = await call_next(request)
            return response

        except AuthenticationError:
            # Re-raise so the registered exception handler returns 401
            raise

        except Exception as e:
            logger.warning("auth_middleware.py", "dispatch()")

    def _decrypt_and_extract_payload(self, token: str, trace_id: str) -> dict | None:
        """Decrypt the token and extract the full payload dict.

        Args:
            token: The encrypted bearer token string.
            trace_id: Request trace ID for logging.

        Returns:
            The payload dict if decryption succeeds, None otherwise.
        """
        try:
            settings = get_settings()
            fernet = Fernet(settings.TOKEN_PRIVATE_KEY.encode())
            decrypted_bytes = fernet.decrypt(token.encode())
            return json.loads(decrypted_bytes.decode())

        except (InvalidToken, ValueError, json.JSONDecodeError, Exception) as exc:
            logger.warning("Token decryption failed", trace_id=trace_id, error=str(exc))
            return None
