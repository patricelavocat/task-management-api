from uuid import uuid4

from sqlalchemy import DateTime, String, func, text
from sqlalchemy.dialects.postgresql import UUID
from sqlalchemy.inspection import inspect
from sqlalchemy.orm import Mapped, mapped_column
from sqlalchemy.orm.decl_api import as_declarative

# pylint: disable=not-callable,too-few-public-methods


@as_declarative()
class BaseModel:
    """FastAPI class used to automatically detect tables and their contents."""

    id: Mapped[UUID] = mapped_column(
        UUID(as_uuid=True),
        primary_key=True,
        default=lambda: uuid4(),
        server_default=text("uuid_generate_v4()"),
        unique=True,
    )
    created_at: Mapped[DateTime] = mapped_column(
        DateTime(timezone=True), default=func.current_timestamp()
    )
    modified_at: Mapped[DateTime] = mapped_column(
        DateTime(timezone=True), onupdate=func.current_timestamp(), nullable=True
    )
    created_author: Mapped[str] = mapped_column(String(300), nullable=False)
    modified_author: Mapped[str | None] = mapped_column(String(300), nullable=True)

    def model_to_dict(self, exclude: list[str] | None = None) -> dict:
        if not exclude:
            exclude = []
        return {
            c.key: getattr(self, c.key)
            for c in inspect(self).mapper.column_attrs  # type: ignore
            if c.key not in exclude
        }
