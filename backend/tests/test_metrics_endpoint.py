from fastapi.testclient import TestClient

from app.main import app

client = TestClient(app)


def test_metrics_endpoint_returns_prometheus_metrics() -> None:
    response = client.get("/metrics")

    assert response.status_code == 200

    content_type = response.headers["content-type"]

    assert "text/plain" in content_type
    assert "http_requests_total" in response.text
    assert "http_request_duration_seconds" in response.text
