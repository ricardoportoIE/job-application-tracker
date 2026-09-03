from unittest.mock import MagicMock, patch

from fastapi.testclient import TestClient
from sqlalchemy.exc import SQLAlchemyError

from app.core.metrics import DATABASE_HEALTH_FAILURES_TOTAL
from app.main import app

client = TestClient(app)


def test_health_check() -> None:
    response = client.get("/health")

    assert response.status_code == 200
    assert response.json() == {"status": "healthy"}


def test_liveness_check() -> None:
    response = client.get("/live")

    assert response.status_code == 200
    assert response.json() == {"status": "alive"}


def test_readiness_check() -> None:
    connection = MagicMock()

    with patch("app.main.engine.connect") as connect:
        connect.return_value.__enter__.return_value = connection

        response = client.get("/ready")

    assert response.status_code == 200
    assert response.json() == {"status": "ready"}

    connection.execute.assert_called_once()


def test_readiness_returns_503_when_database_is_unavailable(
    caplog,
) -> None:
    counter = DATABASE_HEALTH_FAILURES_TOTAL.labels(
        check="readiness",
    )

    before = counter._value.get()

    with (
        patch(
            "app.main.engine.connect",
            side_effect=SQLAlchemyError("database unavailable"),
        ),
        caplog.at_level("WARNING"),
    ):
        response = client.get("/ready")

    after = counter._value.get()

    assert response.status_code == 503
    assert response.json()["detail"] == "Database unavailable"

    assert after == before + 1

    assert any(
        record.__dict__.get("event") == "database.readiness.failed"
        for record in caplog.records
    )


def test_database_health_check() -> None:
    connection = MagicMock()

    with patch("app.main.engine.connect") as connect:
        connect.return_value.__enter__.return_value = connection

        response = client.get("/health/db")

    assert response.status_code == 200
    assert response.json() == {"status": "healthy"}

    connection.execute.assert_called_once()


def test_database_health_check_returns_503_when_database_is_unavailable(
    caplog,
) -> None:
    counter = DATABASE_HEALTH_FAILURES_TOTAL.labels(
        check="health",
    )

    before = counter._value.get()

    with (
        patch(
            "app.main.engine.connect",
            side_effect=SQLAlchemyError("database unavailable"),
        ),
        caplog.at_level("WARNING"),
    ):
        response = client.get("/health/db")

    after = counter._value.get()

    assert response.status_code == 503
    assert response.json()["detail"] == "Database unavailable"

    assert after == before + 1

    assert any(
        record.__dict__.get("event") == "database.health.failed"
        for record in caplog.records
    )
