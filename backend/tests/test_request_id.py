import uuid

from fastapi import FastAPI
from fastapi.testclient import TestClient

from app.core.request_context import get_request_id
from app.middleware.request_id import (
    REQUEST_ID_HEADER,
    RequestIdMiddleware,
)

request_id_app = FastAPI()

request_id_app.add_middleware(
    RequestIdMiddleware,
)


@request_id_app.get("/request-id")
def read_request_id() -> dict[str, str | None]:
    return {
        "request_id": get_request_id(),
    }


client = TestClient(request_id_app)


def test_request_id_is_generated_when_header_is_missing() -> None:
    response = client.get(
        "/request-id",
    )

    assert response.status_code == 200

    request_id = response.headers[REQUEST_ID_HEADER]

    assert response.json()["request_id"] == request_id

    parsed_request_id = uuid.UUID(
        request_id,
    )

    assert str(parsed_request_id) == request_id


def test_valid_supplied_request_id_is_propagated() -> None:
    supplied_request_id = "frontend-request-123"

    response = client.get(
        "/request-id",
        headers={
            REQUEST_ID_HEADER: supplied_request_id,
        },
    )

    assert response.status_code == 200

    assert response.headers[REQUEST_ID_HEADER] == supplied_request_id
    assert response.json()["request_id"] == supplied_request_id


def test_invalid_supplied_request_id_is_replaced() -> None:
    invalid_request_id = "invalid request id!"

    response = client.get(
        "/request-id",
        headers={
            REQUEST_ID_HEADER: invalid_request_id,
        },
    )

    assert response.status_code == 200

    request_id = response.headers[REQUEST_ID_HEADER]

    assert request_id != invalid_request_id
    assert response.json()["request_id"] == request_id

    parsed_request_id = uuid.UUID(
        request_id,
    )

    assert str(parsed_request_id) == request_id


def test_request_context_is_isolated_between_requests() -> None:
    assert get_request_id() is None

    first_response = client.get(
        "/request-id",
        headers={
            REQUEST_ID_HEADER: "request-one",
        },
    )

    second_response = client.get(
        "/request-id",
        headers={
            REQUEST_ID_HEADER: "request-two",
        },
    )

    assert first_response.status_code == 200
    assert second_response.status_code == 200

    assert first_response.json()["request_id"] == "request-one"
    assert second_response.json()["request_id"] == "request-two"

    assert first_response.headers[REQUEST_ID_HEADER] == "request-one"
    assert second_response.headers[REQUEST_ID_HEADER] == "request-two"

    assert get_request_id() is None
