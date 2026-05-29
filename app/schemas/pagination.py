from typing import Generic, TypeVar

from fastapi import Query
from pydantic import BaseModel

T = TypeVar("T")


class Pagination:
    def __init__(
        self,
        skip: int = Query(0, ge=0, description="Skip the N first elements"),
        limit: int = Query(1000, ge=1, le=10000, description="Items per page (max 10000)"),
    ):
        self.skip = skip
        self.limit = limit


class Page(BaseModel, Generic[T]):
    """Paginated response wrapper."""

    items: list[T]
    total: int
    skip: int
    limit: int
