import uuid
from typing import Annotated

from fastapi import FastAPI, Path, Query
from fastapi.exceptions import RequestValidationError
from fastapi.testclient import TestClient
from pydantic import BaseModel, ConfigDict, Field

from app.api.exception_handlers import validation_exception_handler
from app.middleware.request_id import (
    REQUEST_ID_HEADER,
    RequestIdMiddleware,
)


class ValidationPayload(BaseModel):
    model_config = ConfigDict(extra="forbid")

    name: str = Field(
        min_length=1,
        max_length=100,
    )
    quantity: int = Field(
        ge=1,
    )


validation_app = FastAPI()

validation_app.add_exception_handler(
    RequestValidationError,
    validation_exception_handler,
)

validation_app.add_middleware(
    RequestIdMiddleware,
)


@validation_app.post("/body")
def validate_body(
    payload: ValidationPayload,
) -> ValidationPayload:
    return payload


@validation_app.get("/items/{item_id}")
def validate_path(
    item_id: Annotated[
        uuid.UUID,
        Path(),
    ],
) -> dict[str, str]:
    return {
        "item_id": str(item_id),
    }


@validation_app.get("/search")
def validate_query(
    limit: Annotated[
        int,
        Query(
            ge=1,
            le=100,
        ),
    ] = 20,
) -> dict[str, int]:
    return {
        "limit": limit,
    }


validation_client = TestClient(
    validation_app,
)


def test_body_validation_returns_standard_error_response() -> None:
    response = validation_client.post(
        "/body",
        json={
            "name": "",
            "quantity": 0,
        },
    )

    assert response.status_code == 422

    body = response.json()

    assert isinstance(
        body["detail"],
        list,
    )
    assert body["detail"]
    assert body["request_id"]

    assert response.headers[REQUEST_ID_HEADER] == body["request_id"]


def test_path_validation_returns_standard_error_response() -> None:
    response = validation_client.get(
        "/items/not-a-uuid",
    )

    assert response.status_code == 422

    body = response.json()

    assert isinstance(
        body["detail"],
        list,
    )
    assert body["detail"]
    assert body["request_id"]

    assert response.headers[REQUEST_ID_HEADER] == body["request_id"]

    error = body["detail"][0]

    assert error["loc"] == [
        "path",
        "item_id",
    ]


def test_query_validation_returns_standard_error_response() -> None:
    response = validation_client.get(
        "/search?limit=101",
    )

    assert response.status_code == 422

    body = response.json()

    assert isinstance(
        body["detail"],
        list,
    )
    assert body["detail"]
    assert body["request_id"]

    assert response.headers[REQUEST_ID_HEADER] == body["request_id"]

    error = body["detail"][0]

    assert error["loc"] == [
        "query",
        "limit",
    ]


def test_validation_error_preserves_client_request_id() -> None:
    request_id = "validation-request-123"

    response = validation_client.post(
        "/body",
        headers={
            REQUEST_ID_HEADER: request_id,
        },
        json={
            "name": "",
            "quantity": 1,
        },
    )

    assert response.status_code == 422

    body = response.json()

    assert body["request_id"] == request_id
    assert response.headers[REQUEST_ID_HEADER] == request_id


def test_validation_error_generates_request_id_when_missing() -> None:
    response = validation_client.post(
        "/body",
        json={
            "name": "Backend Engineer",
            "quantity": 0,
        },
    )

    assert response.status_code == 422

    body = response.json()

    request_id = body["request_id"]

    parsed_request_id = uuid.UUID(
        request_id,
    )

    assert str(parsed_request_id) == request_id
    assert response.headers[REQUEST_ID_HEADER] == request_id


def test_validation_error_preserves_fastapi_error_structure() -> None:
    response = validation_client.post(
        "/body",
        json={
            "name": "",
            "quantity": 0,
        },
    )

    assert response.status_code == 422

    body = response.json()

    assert body["detail"]

    for error in body["detail"]:
        assert "type" in error
        assert "loc" in error
        assert "msg" in error
        assert "input" in error

    locations = {tuple(error["loc"]) for error in body["detail"]}

    assert (
        "body",
        "name",
    ) in locations

    assert (
        "body",
        "quantity",
    ) in locations
