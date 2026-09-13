from pydantic import SecretStr
from pytest import raises

from app.core.config import Settings


def test_database_url_is_preserved_when_provided() -> None:
    database_url = "postgresql+psycopg://user:password@localhost:5432/jobtracker"

    settings = Settings(
        database_url=database_url,
        jwt_secret_key=SecretStr("test-jwt-secret-key"),
        _env_file=None,
    )

    assert settings.database_url == database_url


def test_database_url_is_built_from_components() -> None:
    settings = Settings(
        db_host="database.internal",
        db_port=5432,
        db_name="jobtracker",
        db_user="jobtracker",
        db_password=SecretStr("database-password"),
        jwt_secret_key=SecretStr("test-jwt-secret-key"),
        _env_file=None,
    )

    assert (
        settings.database_url == "postgresql+psycopg://"
        "jobtracker:database-password"
        "@database.internal:5432/jobtracker"
    )


def test_database_configuration_requires_all_components() -> None:
    with raises(
        ValueError,
        match="Database configuration is incomplete",
    ):
        Settings(
            db_host="database.internal",
            db_name="jobtracker",
            db_user="jobtracker",
            jwt_secret_key=SecretStr("test-jwt-secret-key"),
            _env_file=None,
        )
