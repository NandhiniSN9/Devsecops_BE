"""Custom exception classes for the Overview Dashboard API."""


class InvalidParameterError(Exception):
    """Raised when query parameter validation fails. Returns 400."""

    def __init__(self, message: str) -> None:
        self.message = message
        super().__init__(self.message)


class AuthenticationError(Exception):
    """Raised when token decryption or Jira validation fails. Returns 401."""

    def __init__(self, message: str = "Authentication failed or user not found in Jira") -> None:
        self.message = message
        super().__init__(self.message)


class NotFoundError(Exception):
    """Raised when a requested resource is not found. Returns 404."""

    def __init__(self, message: str = "Resource not found") -> None:
        self.message = message
        super().__init__(self.message)
