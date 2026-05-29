from datetime import UTC, datetime

from pydantic_settings import BaseSettings, SettingsConfigDict

from app.settings.psql import PostgresSettings


class Settings(BaseSettings):
    """This class contains all environment variables required"""

    PROJECT_NAME: str = "task-management"
    VERSION: str = "0.1.0"
    START_API_DATE: datetime = datetime.now(UTC)
    POSTGRES: PostgresSettings = PostgresSettings()  # type: ignore

    model_config = SettingsConfigDict(extra="allow")


settings = Settings()  # type: ignore
