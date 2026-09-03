from fastapi import FastAPI
from fastapi.testclient import TestClient
from prometheus_client import generate_latest

from app.middleware.request_id import RequestIdMiddleware

metrics_app = FastAPI()

metrics_app.add_middleware(
    RequestIdMiddleware,
)


@metrics_app.get("/metric-test/{application_id}")
def read_metric_test(application_id: str) -> dict[str, str]:
    return {
        "application_id": application_id,
    }


metrics_client = TestClient(metrics_app)


def test_http_metrics_use_route_template_instead_of_dynamic_path() -> None:
    response = metrics_client.get(
        "/metric-test/123",
    )

    assert response.status_code == 200

    metrics = generate_latest().decode()

    assert 'path="/metric-test/{application_id}"' in metrics
    assert 'path="/metric-test/123"' not in metrics


def test_http_request_counter_includes_method_and_status() -> None:
    response = metrics_client.get(
        "/metric-test/456",
    )

    assert response.status_code == 200

    metrics = generate_latest().decode()

    assert (
        "http_requests_total{"
        'method="GET",'
        'path="/metric-test/{application_id}",'
        'status_code="200"'
        "}"
    ) in metrics


def test_http_request_duration_histogram_is_recorded() -> None:
    response = metrics_client.get(
        "/metric-test/789",
    )

    assert response.status_code == 200

    metrics = generate_latest().decode()

    assert "http_request_duration_seconds_count" in metrics
    assert 'path="/metric-test/{application_id}"' in metrics
