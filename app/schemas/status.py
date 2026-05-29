# pylint: disable=missing-class-docstring,too-few-public-methods
from datetime import datetime

from pydantic import BaseModel, ConfigDict
from pydantic.alias_generators import to_camel


class DbInformation(BaseModel):
    model_config = ConfigDict(alias_generator=to_camel, populate_by_name=True)
    status: str | None = None
    db_version: str | None = None


class Status(BaseModel):
    """Schema for status API"""

    model_config = ConfigDict(alias_generator=to_camel, populate_by_name=True)

    version: str | None = None
    start_date: datetime | None = None
    database: DbInformation | None = None
