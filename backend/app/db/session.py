"""Async database engine and session management.

Exposes a single async engine plus a session factory, and a FastAPI dependency
(:func:`get_db`) that yields a request-scoped session and guarantees cleanup.
"""

from __future__ import annotations

from collections.abc import AsyncGenerator

from sqlalchemy.ext.asyncio import (
    AsyncSession,
    async_sessionmaker,
    create_async_engine,
)

from app.core.config import settings

# ``pool_pre_ping`` transparently recovers from dropped connections, which
# matters once this points at a managed cloud Postgres instance.
engine = create_async_engine(
    settings.database_url,
    echo=False,
    pool_pre_ping=True,
    future=True,
)

SessionLocal = async_sessionmaker(
    bind=engine,
    class_=AsyncSession,
    expire_on_commit=False,
    autoflush=False,
)


async def get_db() -> AsyncGenerator[AsyncSession, None]:
    """FastAPI dependency yielding a database session.

    The session is committed on success and rolled back on any exception, then
    always closed. Routes therefore never manage transactions manually.
    """
    async with SessionLocal() as session:
        try:
            yield session
            await session.commit()
        except Exception:
            await session.rollback()
            raise
