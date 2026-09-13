from pydantic import SecretStr
from pytest import MonkeyPatch, raises

from app.core.config import Settings


def test_database_url_is_preserved_when_provided() -> None:
    database_url = "postgresql+psycopg://user:password@localhost:5432/jobtracker"

    settings = Settings(  # type: ignore[call-arg]
        database_url=database_url,
        jwt_secret_key=SecretStr("test-jwt-secret-key"),
        _env_file=None,  # type: ignore[call-arg]
    )

    assert settings.database_url == database_url


def test_database_url_is_built_from_components(
    monkeypatch: MonkeyPatch,
) -> None:
    monkeypatch.delenv("DATABASE_URL", raising=False)

    settings = Settings(  # type: ignore[call-arg]
        db_host="database.internal",
        db_port=5432,
        db_name="jobtracker",
        db_user="jobtracker",
        db_password=SecretStr("database-password"),
        jwt_secret_key=SecretStr("test-jwt-secret-key"),
        _env_file=None,  # type: ignore[call-arg]
    )

    assert (
        settings.database_url == "postgresql+psycopg://"
        "jobtracker:database-password"
        "@database.internal:5432/jobtracker"
    )


def test_database_configuration_requires_all_components(
    monkeypatch: MonkeyPatch,
) -> None:
    monkeypatch.delenv("DATABASE_URL", raising=False)

    with raises(
        ValueError,
        match="Database configuration is incomplete",
    ):
        Settings(  # type: ignore[call-arg]
            db_host="database.internal",
            db_name="jobtracker",
            db_user="jobtracker",
            jwt_secret_key=SecretStr("test-jwt-secret-key"),
            _env_file=None,  # type: ignore[call-arg]
        )
