# type: ignore
from typing import Any, Generic, Sequence, TypeVar

from sqlalchemy import delete, func, select
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy.orm import DeclarativeMeta
from sqlalchemy.sql import Select
from sqlalchemy.sql.base import ExecutableOption

ModelType = TypeVar("ModelType", bound=DeclarativeMeta)  # pylint: disable=invalid-name


class BaseRepository(Generic[ModelType]):
    """Base repository to be implemented by all repositories"""

    def __init__(self, model: type[ModelType]):
        self.model = model

    def _apply_filters(self, query: Select, filters: dict | None) -> Select:
        """Apply ``field`` / ``field__op`` filters to a query.

        Supported operators: ``in``, ``gte``, ``lte``, ``gt``, ``lt`` and bare
        equality (no suffix). Unknown fields are ignored.
        """
        if not filters:
            return query

        for key, value in filters.items():
            field, _, operator = key.partition("__")
            column = getattr(self.model, field, None)
            if column is None:
                continue
            if operator in ("", "eq"):
                query = query.where(column == value)
            elif operator == "in":
                query = query.where(column.in_(value if isinstance(value, list) else [value]))
            elif operator == "gte":
                query = query.where(column >= value)
            elif operator == "lte":
                query = query.where(column <= value)
            elif operator == "gt":
                query = query.where(column > value)
            elif operator == "lt":
                query = query.where(column < value)
        return query

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

        query = self._apply_filters(query, filters)
        query = query.offset(skip).limit(limit)

        result = await session.execute(query)
        return result.scalars().unique().all()

    async def count(self, session: AsyncSession, filters: dict | None = None) -> int:
        """Count records matching the optional filters."""
        query = select(func.count()).select_from(self.model)
        query = self._apply_filters(query, filters)
        result = await session.execute(query)
        return result.scalar_one()

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
