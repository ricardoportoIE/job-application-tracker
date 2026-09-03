from unittest.mock import MagicMock, patch

from fastapi.testclient import TestClient
from sqlalchemy.exc import SQLAlchemyError

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


def test_readiness_returns_503_when_database_is_unavailable() -> None:
    with patch(
        "app.main.engine.connect",
        side_effect=SQLAlchemyError("database unavailable"),
    ):
        response = client.get("/ready")

    assert response.status_code == 503
    assert response.json()["detail"] == "Database unavailable"


def test_database_health_check() -> None:
    connection = MagicMock()

    with patch("app.main.engine.connect") as connect:
        connect.return_value.__enter__.return_value = connection

        response = client.get("/health/db")

    assert response.status_code == 200
    assert response.json() == {"status": "healthy"}

    connection.execute.assert_called_once()


def test_database_health_check_returns_503_when_database_is_unavailable() -> None:
    with patch(
        "app.main.engine.connect",
        side_effect=SQLAlchemyError("database unavailable"),
    ):
        response = client.get("/health/db")

    assert response.status_code == 503
    assert response.json()["detail"] == "Database unavailable"
