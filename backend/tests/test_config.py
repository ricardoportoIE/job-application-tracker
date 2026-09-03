from typing import Literal, cast

import pytest
from pydantic import SecretStr, ValidationError

from app.core.config import Settings

Environment = Literal[
    "development",
    "test",
    "production",
]

JwtAlgorithm = Literal["HS256"]


def test_settings_accepts_supported_environment() -> None:
    settings = Settings(
        database_url="postgresql+psycopg://user:pass@localhost:5432/db",
        jwt_secret_key=SecretStr("a" * 32),
        environment="production",
        cors_allowed_origins=[
            "https://app.example.com",
        ],
    )

    assert settings.environment == "production"


def test_settings_rejects_unsupported_environment() -> None:
    with pytest.raises(ValidationError):
        Settings(
            database_url="postgresql+psycopg://user:pass@localhost:5432/db",
            jwt_secret_key=SecretStr("a" * 32),
            environment=cast(
                Environment,
                "prodction",
            ),
        )


def test_settings_accepts_hs256_algorithm() -> None:
    settings = Settings(
        database_url="postgresql+psycopg://user:pass@localhost:5432/db",
        jwt_secret_key=SecretStr("secret"),
        jwt_algorithm="HS256",
    )

    assert settings.jwt_algorithm == "HS256"


def test_settings_rejects_unsupported_jwt_algorithm() -> None:
    with pytest.raises(ValidationError):
        Settings(
            database_url="postgresql+psycopg://user:pass@localhost:5432/db",
            jwt_secret_key=SecretStr("secret"),
            jwt_algorithm=cast(
                JwtAlgorithm,
                "RS256",
            ),
        )


def test_production_requires_cors_origin() -> None:
    with pytest.raises(ValidationError):
        Settings(
            database_url="postgresql+psycopg://user:pass@localhost:5432/db",
            jwt_secret_key=SecretStr("secret"),
            environment="production",
            cors_allowed_origins=[],
        )


def test_production_rejects_localhost_cors_origin() -> None:
    with pytest.raises(ValidationError):
        Settings(
            database_url="postgresql+psycopg://user:pass@localhost:5432/db",
            jwt_secret_key=SecretStr("secret"),
            environment="production",
            cors_allowed_origins=[
                "http://localhost:5173",
            ],
        )


def test_production_accepts_non_local_cors_origin() -> None:
    settings = Settings(
        database_url="postgresql+psycopg://user:pass@localhost:5432/db",
        jwt_secret_key=SecretStr("a" * 32),
        environment="production",
        cors_allowed_origins=[
            "https://app.example.com",
        ],
    )

    assert settings.cors_allowed_origins == [
        "https://app.example.com",
    ]


def test_production_rejects_short_jwt_secret() -> None:
    with pytest.raises(ValidationError):
        Settings(
            database_url="postgresql+psycopg://user:pass@localhost:5432/db",
            jwt_secret_key=SecretStr("too-short"),
            environment="production",
            cors_allowed_origins=[
                "https://app.example.com",
            ],
        )


def test_production_accepts_strong_jwt_secret() -> None:
    strong_secret = "a" * 32

    settings = Settings(
        database_url="postgresql+psycopg://user:pass@localhost:5432/db",
        jwt_secret_key=SecretStr(strong_secret),
        environment="production",
        cors_allowed_origins=[
            "https://app.example.com",
        ],
    )

    assert settings.jwt_secret_key.get_secret_value() == strong_secret
