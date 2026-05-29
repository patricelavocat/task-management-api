from datetime import UTC, datetime

from pydantic_settings import BaseSettings, SettingsConfigDict

from app.settings.psql import PostgresSettings


class Settings(BaseSettings):
    """This class contains all environment variables required"""

    PROJECT_NAME: str = "task-management"
    VERSION: str = "0.1.0"
    START_API_DATE: datetime = datetime.now(UTC)
    SECRET_KEY: str = "change-me-in-production"
    ALGORITHM: str = "HS256"
    ACCESS_TOKEN_EXPIRE_MINUTES: int = 15
    REFRESH_TOKEN_EXPIRE_MINUTES: int = 1440
    POSTGRES: PostgresSettings = PostgresSettings()  # type: ignore

    model_config = SettingsConfigDict(extra="allow")


settings = Settings()  # type: ignore
