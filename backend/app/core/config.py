from pathlib import Path
from typing import Literal

from pydantic import Field, SecretStr, model_validator
from pydantic_settings import BaseSettings, SettingsConfigDict

BASE_DIR = Path(__file__).resolve().parents[3]


class Settings(BaseSettings):
    app_name: str = "Job Application Tracker API"
    app_version: str = "0.1.0"
    environment: Literal[
        "development",
        "test",
        "production",
    ] = "development"
    docs_enabled: bool = True
    database_url: str
    test_database_url: str | None = None

    jwt_secret_key: SecretStr
    jwt_algorithm: Literal["HS256"] = "HS256"
    access_token_expire_minutes: int = 30

    model_config = SettingsConfigDict(
        env_file=BASE_DIR / ".env",
        env_file_encoding="utf-8",
        extra="ignore",
    )

    cors_allowed_origins: list[str] = Field(
        default_factory=list,
    )

    cors_allow_credentials: bool = True

    @model_validator(mode="after")
    def validate_production_security(self) -> Settings:
        if self.environment != "production":
            return self

        if not self.cors_allowed_origins:
            raise ValueError("CORS_ALLOWED_ORIGINS must be configured in production")

        local_origins = {
            "http://localhost",
            "https://localhost",
            "http://127.0.0.1",
            "https://127.0.0.1",
        }

        for origin in self.cors_allowed_origins:
            if any(origin.startswith(local_origin) for local_origin in local_origins):
                raise ValueError("Local CORS origins are not allowed in production")

        if len(self.jwt_secret_key.get_secret_value()) < 32:
            raise ValueError(
                "JWT_SECRET_KEY must be at least 32 characters in production"
            )

        return self

    log_level: Literal[
        "DEBUG",
        "INFO",
        "WARNING",
        "ERROR",
        "CRITICAL",
    ] = "INFO"


settings = Settings()  # type: ignore[call-arg]
