import uuid

from fastapi import FastAPI, HTTPException, status
from fastapi.testclient import TestClient
from starlette.exceptions import HTTPException as StarletteHTTPException

from app.api.exception_handlers import http_exception_handler
from app.middleware.request_id import (
    REQUEST_ID_HEADER,
    RequestIdMiddleware,
)

http_error_app = FastAPI()

http_error_app.add_exception_handler(
    StarletteHTTPException,
    http_exception_handler,
)

http_error_app.add_middleware(
    RequestIdMiddleware,
)


@http_error_app.get("/not-found")
def not_found() -> None:
    raise HTTPException(
        status_code=status.HTTP_404_NOT_FOUND,
        detail="Resource not found",
    )


@http_error_app.get("/unauthorized")
def unauthorized() -> None:
    raise HTTPException(
        status_code=status.HTTP_401_UNAUTHORIZED,
        detail="Could not validate credentials",
        headers={
            "WWW-Authenticate": "Bearer",
        },
    )


@http_error_app.get("/conflict")
def conflict() -> None:
    raise HTTPException(
        status_code=status.HTTP_409_CONFLICT,
        detail="Resource conflict",
    )


http_error_client = TestClient(
    http_error_app,
)


def test_http_exception_includes_request_id() -> None:
    response = http_error_client.get(
        "/not-found",
        headers={
            REQUEST_ID_HEADER: "request-404",
        },
    )

    assert response.status_code == 404

    assert response.json() == {
        "detail": "Resource not found",
        "request_id": "request-404",
    }

    assert response.headers[REQUEST_ID_HEADER] == "request-404"


def test_http_exception_generates_request_id_when_missing() -> None:
    response = http_error_client.get(
        "/not-found",
    )

    assert response.status_code == 404

    body = response.json()

    request_id = response.headers[REQUEST_ID_HEADER]

    assert body["request_id"] == request_id

    parsed_request_id = uuid.UUID(
        request_id,
    )

    assert str(parsed_request_id) == request_id


def test_http_exception_preserves_existing_headers() -> None:
    response = http_error_client.get(
        "/unauthorized",
        headers={
            REQUEST_ID_HEADER: "request-401",
        },
    )

    assert response.status_code == 401

    assert response.json() == {
        "detail": "Could not validate credentials",
        "request_id": "request-401",
    }

    assert response.headers["www-authenticate"] == "Bearer"

    assert response.headers[REQUEST_ID_HEADER] == "request-401"


def test_http_exception_preserves_status_and_detail() -> None:
    response = http_error_client.get(
        "/conflict",
        headers={
            REQUEST_ID_HEADER: "request-409",
        },
    )

    assert response.status_code == 409

    assert response.json() == {
        "detail": "Resource conflict",
        "request_id": "request-409",
    }

    assert response.headers[REQUEST_ID_HEADER] == "request-409"
