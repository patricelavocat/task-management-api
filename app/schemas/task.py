from datetime import datetime
from uuid import UUID

from fastapi import Query
from pydantic import BaseModel, ConfigDict
from stringcase import camelcase

from app.models.task import TaskStatus


class CamelModel(BaseModel):
    """Shared config for task schemas: camelCase aliases, ORM loading, no extras."""

    model_config = ConfigDict(
        extra="forbid",
        from_attributes=True,
        alias_generator=camelcase,
        populate_by_name=True,
    )


class TaskRead(CamelModel):
    id: UUID
    title: str
    description: str | None = None
    due_date: datetime
    status: TaskStatus

    created_author: str
    modified_author: str | None = None
    created_at: datetime
    modified_at: datetime | None = None


class TaskCreate(CamelModel):
    title: str
    description: str | None = None
    due_date: datetime


class TaskPatch(CamelModel):
    title: str | None = None
    description: str | None = None
    due_date: datetime | None = None
    status: TaskStatus | None = None


class TaskQuery:
    """Filter parameters for listing tasks (used as a FastAPI dependency)."""

    def __init__(
        self,
        title: list[str] | None = Query(None, description="Match any of these exact titles"),
        status: list[TaskStatus] | None = Query(None, description="Match any of these statuses"),
        due_after: datetime | None = Query(None, description="Only tasks due at or after this time"),
        due_before: datetime | None = Query(None, description="Only tasks due at or before this time"),
    ):
        self.title = title
        self.status = status
        self.due_after = due_after
        self.due_before = due_before

    def model_to_filters(self) -> dict:
        filters: dict = {}
        if self.title:
            filters["title__in"] = self.title
        if self.status:
            filters["status__in"] = [status.value for status in self.status]
        if self.due_after:
            filters["due_date__gte"] = self.due_after
        if self.due_before:
            filters["due_date__lte"] = self.due_before
        return filters