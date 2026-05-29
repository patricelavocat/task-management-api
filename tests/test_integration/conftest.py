import os
from pathlib import Path
from typing import AsyncGenerator

import pytest
import pytest_asyncio
from alembic import command
from alembic.config import Config
from dotenv import load_dotenv
from httpx import AsyncClient, ASGITransport
from sqlalchemy import event
from sqlalchemy.ext.asyncio import create_async_engine, async_sessionmaker, AsyncSession

from db.session import get_session
from main import app
from settings.config import settings


engine = create_async_engine(
    str(settings.POSTGRES.SQLALCHEMY_DATABASE_URI),
    connect_args=settings.POSTGRES.SQLALCHEMY_ENGINE_OPTIONS,
    pool_pre_ping=True,
    pool_size=30,
    max_overflow=70,
)

TestingAsyncSessionLocal = async_sessionmaker(
    engine,
    expire_on_commit=False,
    autoflush=False,
    autocommit=False,
    class_=AsyncSession,
)

def _drop_all_tables(connection):
    from app.models.base import BaseModel

    for table in reversed(BaseModel.metadata.sorted_tables):
        connection.execute(table.delete())


@pytest_asyncio.fixture(scope="function", autouse=True)
async def prepare_database():
    """Run once before test. Clean db and apply migrations"""
    back_path = Path(__file__).parent.parent.parent
    config_path = back_path / "alembic.ini"
    alembic_path = back_path / "alembic"
    config_path.resolve(strict=True)
    alembic_cfg = Config(str(config_path))
    alembic_cfg.set_main_option("script_location", str(alembic_path))

    def _execute_alembic_upgrade(connection):
        alembic_cfg.attributes["connection"] = connection
        command.upgrade(alembic_cfg, "head")

    async with engine.connect() as conn:
        await conn.run_sync(_execute_alembic_upgrade)
        await conn.run_sync(_drop_all_tables)

    yield
    await engine.dispose()


@pytest_asyncio.fixture(scope="function")
async def db_session() -> AsyncGenerator[AsyncSession]:
    """
    Provides an async DB session with nested transactions for test isolation.
    Rolls back everything after the test.
    """
    async with engine.connect() as connection:
        # Start outer transaction
        trans = await connection.begin()
        async_session = TestingAsyncSessionLocal(bind=connection)

        # Start nested transaction (savepoint)
        nested = await connection.begin_nested()

        # Recreate savepoint after each commit
        @event.listens_for(async_session.sync_session, "after_transaction_end")
        def end_savepoint(session, transaction):
            nonlocal nested
            if not nested.is_active:
                nested = connection.sync_connection.begin_nested()

        try:
            yield async_session
        finally:
            await trans.rollback()  # Rollback to initial state
            await async_session.close()

@pytest_asyncio.fixture
async def client(db_session) -> AsyncGenerator[AsyncClient]:
    def fake_current_user():
        return "admin"

    def override_get_session():
        yield db_session

    app.dependency_overrides[get_session] = override_get_session
    async with AsyncClient(transport=ASGITransport(app=app), base_url="http://test") as client:
        yield client
    app.dependency_overrides.clear()
