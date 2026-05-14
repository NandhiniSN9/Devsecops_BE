"""Middleware package for cross-cutting concerns."""

from src.middleware.auth_middleware import AuthMiddleware

__all__ = ["AuthMiddleware"]
