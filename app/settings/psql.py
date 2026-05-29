import ssl

from pydantic import field_validator
from pydantic_core.core_schema import ValidationInfo
from pydantic_settings import BaseSettings, SettingsConfigDict


class PostgresSettings(BaseSettings):
    HOST: str
    PORT: int
    USER: str
    PASSWORD: str
    DB: str
    SQLALCHEMY_DATABASE_URI: str | None = None
    SSL_MODE: str = "allow"
    CA_CERT_OPTIONNAL: str = ""
    SQLALCHEMY_ENGINE_OPTIONS: dict | None = None

    model_config = SettingsConfigDict(env_prefix="POSTGRES_")

    @field_validator("SQLALCHEMY_DATABASE_URI", mode="before")
    @classmethod
    def assemble_db_connection(cls, v: str | None, values: ValidationInfo) -> str:
        """Make the database URI"""
        if isinstance(v, str):
            return v

        return (
            f"postgresql+asyncpg://{values.data.get('USER')}:"
            f"{values.data.get('PASSWORD')}"
            f"@{values.data.get('HOST')}:{values.data.get('PORT')}"
            f"/{values.data.get('DB')}"
        )

    @field_validator("SQLALCHEMY_ENGINE_OPTIONS", mode="before")
    @classmethod
    def assemble_engine_options(
        cls,
        v: str | None,
        values: ValidationInfo,  # pylint: disable=unused-argument
    ) -> dict | None:
        """Prepare the ssl context"""
        ssl_mode = str(values.data.get("SSL_MODE", "allow"))
        ca_cert = str(values.data.get("CA_CERT_OPTIONNAL", ""))
        ssl_context = None

        if ssl_mode in ("require", "verify-ca", "verify-full"):
            ssl_context = ssl.create_default_context(cafile=ca_cert if ca_cert else None)

            if ssl_mode == "require":
                # on ne valide pas le hostname ni la CA
                ssl_context.check_hostname = False
                ssl_context.verify_mode = ssl.CERT_NONE

            elif ssl_mode == "verify-ca":
                ssl_context.check_hostname = False
                ssl_context.verify_mode = ssl.CERT_REQUIRED

            elif ssl_mode == "verify-full":
                ssl_context.check_hostname = True
                ssl_context.verify_mode = ssl.CERT_REQUIRED

        return {"ssl": ssl_context}
