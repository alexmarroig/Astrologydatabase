from __future__ import annotations

import pytest
import pytest_asyncio
from httpx import ASGITransport, AsyncClient
from sqlalchemy import event
from sqlalchemy.ext.asyncio import AsyncSession, async_sessionmaker, create_async_engine
from sqlalchemy.pool import StaticPool

import app.models  # noqa: F401 - ensure metadata is populated before create_all()
from app.db.base import Base, get_db
from app.main import create_app

pytest_plugins = ("tests.fixtures",)


@pytest_asyncio.fixture
async def test_engine():
    engine = create_async_engine(
        "sqlite+aiosqlite:///:memory:",
        connect_args={"check_same_thread": False},
        poolclass=StaticPool,
    )

    async with engine.begin() as connection:
        await connection.run_sync(Base.metadata.create_all)

    try:
        yield engine
    finally:
        async with engine.begin() as connection:
            await connection.run_sync(Base.metadata.drop_all)
        await engine.dispose()


@pytest_asyncio.fixture
async def db_session(test_engine) -> AsyncSession:
    async with test_engine.connect() as connection:
        outer_transaction = await connection.begin()
        nested_transaction = await connection.begin_nested()
        session_factory = async_sessionmaker(
            bind=connection,
            class_=AsyncSession,
            expire_on_commit=False,
            autoflush=False,
        )

        async with session_factory() as session:
            @event.listens_for(session.sync_session, "after_transaction_end")
            def restart_savepoint(sync_session, transaction) -> None:
                nonlocal nested_transaction
                if connection.closed:
                    return
                if not nested_transaction.is_active:
                    nested_transaction = connection.sync_connection.begin_nested()

            try:
                yield session
            finally:
                event.remove(
                    session.sync_session,
                    "after_transaction_end",
                    restart_savepoint,
                )
                await session.close()
                await outer_transaction.rollback()


@pytest_asyncio.fixture
async def app(db_session):
    application = create_app()

    async def override_get_db():
        yield db_session

    application.dependency_overrides[get_db] = override_get_db

    try:
        yield application
    finally:
        application.dependency_overrides.clear()


@pytest_asyncio.fixture
async def client(app):
    async with AsyncClient(
        transport=ASGITransport(app=app),
        base_url="http://testserver",
    ) as async_client:
        yield async_client
