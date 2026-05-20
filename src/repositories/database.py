"""Database engine and session factory configuration.

Creates the async SQLAlchemy engine and session factory at module level.
Separated from dependencies.py to avoid circular imports with client modules.
"""

from sqlalchemy.ext.asyncio import AsyncSession, async_sessionmaker, create_async_engine

from src.settings import get_settings

# Create async engine and session factory at module level
_settings = get_settings()
_engine = create_async_engine(
    _settings.DATABASE_URL,
    pool_pre_ping=True,
    pool_size=10,
    max_overflow=20,
)
_async_session_factory = async_sessionmaker(
    bind=_engine,
    class_=AsyncSession,
    expire_on_commit=False,
)
