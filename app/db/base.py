"""
Database engine, session factory, and declarative base.

Design decisions:
- Uses async SQLAlchemy 2.x with asyncpg for PostgreSQL (production)
  and aiosqlite for SQLite (local dev / tests)
- create_async_engine is configured with pool settings from Settings
- Session is provided via dependency injection (get_db)
- All models import Base from this module to ensure Alembic autodiscovery
"""

from __future__ import annotations

from collections.abc import AsyncGenerator

from sqlalchemy import event, text
from sqlalchemy.ext.asyncio import (
    AsyncSession,
    async_sessionmaker,
    create_async_engine,
)
from sqlalchemy.orm import DeclarativeBase

from app.core.config import get_settings

settings = get_settings()


class Base(DeclarativeBase):
    """
    Shared declarative base for all SQLAlchemy ORM models.

    All models must inherit from this class.
    The __tablename__ convention is explicit per model.
    """
    pass


def _build_engine():
    """Build the async engine with appropriate settings per DB type."""
    kwargs: dict = {}

    if settings.is_sqlite:
        # SQLite does not support connection pools in the same way
        kwargs["connect_args"] = {"check_same_thread": False}
    else:
        kwargs.update(
            pool_size=settings.database_pool_size,
            max_overflow=settings.database_max_overflow,
            pool_timeout=settings.database_pool_timeout,
            pool_pre_ping=True,  # Validates connections before use
        )

    return create_async_engine(
        settings.database_async_url,
        echo=settings.debug,
        future=True,
        **kwargs,
    )


engine = _build_engine()

AsyncSessionLocal = async_sessionmaker(
    bind=engine,
    class_=AsyncSession,
    expire_on_commit=False,  # Prevent lazy-load errors after commit
    autoflush=False,
    autocommit=False,
)


async def get_db() -> AsyncGenerator[AsyncSession, None]:
    """
    FastAPI dependency that provides an async database session.

    Usage:
        @router.get("/example")
        async def example(db: AsyncSession = Depends(get_db)):
            ...
    """
    async with AsyncSessionLocal() as session:
        try:
            yield session
            await session.commit()
        except Exception:
            await session.rollback()
            raise
        finally:
            await session.close()


async def create_all_tables() -> None:
    """
    Create all tables from SQLAlchemy metadata.
    Used in tests and local dev startup.
    NOT used in production — Alembic handles migrations there.
    """
    async with engine.begin() as conn:
        await conn.run_sync(Base.metadata.create_all)


async def drop_all_tables() -> None:
    """Drop all tables. Only used in test teardown."""
    async with engine.begin() as conn:
        await conn.run_sync(Base.metadata.drop_all)
