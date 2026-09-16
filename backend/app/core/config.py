from pathlib import Path
from typing import Literal

from pydantic import Field, SecretStr, model_validator
from pydantic_settings import BaseSettings, SettingsConfigDict
from sqlalchemy.engine import URL

BASE_DIR = Path(__file__).resolve().parents[3]
BACKEND_DIR = Path(__file__).resolve().parents[2]


class Settings(BaseSettings):
    app_name: str = "Job Application Tracker API"
    app_version: str = "0.1.0"
    environment: Literal[
        "development",
        "test",
        "production",
    ] = "development"
    docs_enabled: bool = True
    database_url: str | None = None
    test_database_url: str | None = None

    db_host: str | None = None
    db_port: int = 5432
    db_name: str | None = None
    db_user: str | None = None
    db_password: SecretStr | None = None
    db_admin_user: str | None = None
    db_admin_password: SecretStr | None = None

    jwt_secret_key: SecretStr
    jwt_algorithm: Literal["HS256"] = "HS256"
    access_token_expire_minutes: int = 30

    model_config = SettingsConfigDict(
        env_file=BASE_DIR / ".env",
        env_file_encoding="utf-8",
        env_ignore_empty=True,
        extra="ignore",
    )

    cors_allowed_origins: list[str] = Field(
        default_factory=list,
    )

    cors_allow_credentials: bool = True
    metrics_bearer_token: SecretStr | None = None

    @model_validator(mode="after")
    def build_database_url(self) -> Settings:
        if self.database_url:
            return self

        required_values = {
            "DB_HOST": self.db_host,
            "DB_NAME": self.db_name,
            "DB_USER": self.db_user,
            "DB_PASSWORD": self.db_password,
        }

        missing = [name for name, value in required_values.items() if value is None]

        if missing:
            raise ValueError(
                f"Database configuration is incomplete: missing {', '.join(missing)}"
            )

        assert self.db_password is not None

        password = self.db_password.get_secret_value()

        self.database_url = URL.create(
            drivername="postgresql+psycopg",
            username=self.db_user,
            password=password,
            host=self.db_host,
            port=self.db_port,
            database=self.db_name,
        ).render_as_string(hide_password=False)

        return self

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

        if self.metrics_bearer_token is None:
            raise ValueError("METRICS_BEARER_TOKEN must be configured in production")

        if len(self.metrics_bearer_token.get_secret_value()) < 32:
            raise ValueError(
                "METRICS_BEARER_TOKEN must be at least 32 characters in production"
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
