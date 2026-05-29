from collections.abc import AsyncGenerator
from typing import Annotated

from fastapi import Depends
from sqlalchemy.ext.asyncio.engine import create_async_engine
from sqlalchemy.ext.asyncio.session import AsyncSession, async_sessionmaker

from app.settings.config import settings

engine = create_async_engine(
    str(settings.POSTGRES.SQLALCHEMY_DATABASE_URI),
    connect_args=settings.POSTGRES.SQLALCHEMY_ENGINE_OPTIONS,
    pool_pre_ping=True,
    pool_size=30,
    max_overflow=70,
)

async_session_maker = async_sessionmaker(
    bind=engine,
    expire_on_commit=False,
    autoflush=False,
)


async def get_session() -> AsyncGenerator[AsyncSession]:
    """Get a session."""
    async with async_session_maker() as session:
        yield session


SessionDep = Annotated[AsyncSession, Depends(get_session)]
