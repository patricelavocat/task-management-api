# type: ignore
from typing import Any, Generic, Sequence, TypeVar

from sqlalchemy import delete, select
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy.orm import DeclarativeMeta
from sqlalchemy.sql.base import ExecutableOption

ModelType = TypeVar("ModelType", bound=DeclarativeMeta)  # pylint: disable=invalid-name


class BaseRepository(Generic[ModelType]):
    """Base repository to be implemented by all repositories"""

    def __init__(self, model: type[ModelType]):
        self.model = model

    async def get(
            self,
            session: AsyncSession,
            obj_id: Any,
            *options: ExecutableOption,
    ) -> ModelType | None:
        """Fetch a single record by primary key."""
        query = select(self.model).where(self.model.id == obj_id)
        if options:
            query = query.options(*options)

        result = await session.execute(query)
        return result.scalars().first()

    async def list(
            self,
            session: AsyncSession,
            skip: int = 0,
            limit: int = 100,
            filters: dict | None = None,
            *options: ExecutableOption,
    ) -> Sequence[ModelType]:
        """Fetch multiple records with optional equality filters."""
        query = select(self.model)
        if options:
            query = query.options(*options)

        if filters:
            for field, value in filters.items():
                if hasattr(self.model, field):
                    query = query.where(getattr(self.model, field) == value)

        query = query.offset(skip).limit(limit)

        result = await session.execute(query)
        return result.scalars().unique().all()

    async def create(self, session: AsyncSession, obj_in: dict) -> ModelType:
        """Create a new record."""
        db_obj = self.model(**obj_in)
        session.add(db_obj)
        await session.commit()
        await session.refresh(db_obj)
        return db_obj

    async def update(self, session: AsyncSession, db_obj: ModelType, obj_in: dict) -> ModelType:
        """Update an existing record."""
        for field, value in obj_in.items():
            if hasattr(db_obj, field):
                setattr(db_obj, field, value)
        session.add(db_obj)
        await session.commit()
        await session.refresh(db_obj)
        return db_obj

    async def delete(self, session: AsyncSession, obj_id: Any) -> bool:
        """Delete a record by primary key."""
        result = await session.execute(delete(self.model).where(self.model.id == obj_id))
        await session.commit()
        return result.rowcount > 0