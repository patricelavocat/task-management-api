from pydantic import BaseModel, ConfigDict
from stringcase import camelcase


class CamelModel(BaseModel):
    """Shared schema config: camelCase aliases, ORM loading, no extra fields."""

    model_config = ConfigDict(
        extra="forbid",
        from_attributes=True,
        alias_generator=camelcase,
        populate_by_name=True,
    )
