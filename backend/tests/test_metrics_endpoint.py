from unittest.mock import patch

from fastapi.testclient import TestClient
from pydantic import SecretStr

from app.core.config import settings
from app.main import app

client = TestClient(app)


def test_metrics_endpoint_returns_prometheus_metrics() -> None:
    response = client.get("/metrics")

    assert response.status_code == 200

    content_type = response.headers["content-type"]

    assert "text/plain" in content_type
    assert "http_requests_total" in response.text
    assert "http_request_duration_seconds" in response.text


def test_metrics_endpoint_requires_configured_bearer_token() -> None:
    token = "m" * 32

    with patch.object(settings, "metrics_bearer_token", SecretStr(token)):
        unauthorized = client.get("/metrics")
        authorized = client.get(
            "/metrics",
            headers={"Authorization": f"Bearer {token}"},
        )

    assert unauthorized.status_code == 401
    assert unauthorized.headers["www-authenticate"] == "Bearer"
    assert authorized.status_code == 200
