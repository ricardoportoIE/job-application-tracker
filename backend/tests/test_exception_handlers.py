import io
import json
import logging
import uuid
from collections.abc import Generator
from typing import Any

import pytest
from fastapi import FastAPI
from fastapi.testclient import TestClient

from app.api.exception_handlers import unhandled_exception_handler
from app.core.logging import JsonFormatter
from app.middleware.request_id import (
    REQUEST_ID_HEADER,
    RequestIdMiddleware,
)

exception_test_app = FastAPI()

exception_test_app.add_exception_handler(
    Exception,
    unhandled_exception_handler,
)

exception_test_app.add_middleware(
    RequestIdMiddleware,
)


@exception_test_app.get("/explode")
def explode() -> None:
    raise ValueError("sensitive internal failure")


exception_client = TestClient(
    exception_test_app,
    raise_server_exceptions=False,
)


@pytest.fixture
def captured_exception_logs() -> Generator[io.StringIO]:
    logger = logging.getLogger(
        "app.api.exception_handlers",
    )

    original_handlers = logger.handlers.copy()
    original_level = logger.level
    original_propagate = logger.propagate

    stream = io.StringIO()

    handler = logging.StreamHandler(
        stream,
    )
    handler.setFormatter(
        JsonFormatter(),
    )

    logger.handlers.clear()
    logger.addHandler(handler)
    logger.setLevel(logging.ERROR)
    logger.propagate = False

    yield stream

    logger.handlers.clear()
    logger.handlers.extend(
        original_handlers,
    )
    logger.setLevel(
        original_level,
    )
    logger.propagate = original_propagate


def read_single_log(
    stream: io.StringIO,
) -> dict[str, Any]:
    lines = [line for line in stream.getvalue().splitlines() if line.strip()]

    assert len(lines) == 1

    payload = json.loads(lines[0])

    assert isinstance(payload, dict)

    return payload


def test_unhandled_exception_returns_safe_response() -> None:
    response = exception_client.get(
        "/explode",
        headers={
            REQUEST_ID_HEADER: "request-500",
        },
    )

    assert response.status_code == 500

    assert response.json() == {
        "detail": "Internal server error",
        "request_id": "request-500",
    }

    assert response.headers[REQUEST_ID_HEADER] == "request-500"

    response_text = response.text.lower()

    assert "valueerror" not in response_text
    assert "sensitive internal failure" not in response_text
    assert "traceback" not in response_text


def test_unhandled_exception_generates_request_id_when_missing() -> None:
    response = exception_client.get(
        "/explode",
    )

    assert response.status_code == 500

    body = response.json()

    response_request_id = response.headers[REQUEST_ID_HEADER]

    assert body["request_id"] == response_request_id

    parsed_request_id = uuid.UUID(
        response_request_id,
    )

    assert str(parsed_request_id) == response_request_id


def test_unhandled_exception_is_logged_with_stack_trace(
    captured_exception_logs: io.StringIO,
) -> None:
    response = exception_client.get(
        "/explode",
        headers={
            REQUEST_ID_HEADER: "request-error-log",
        },
    )

    assert response.status_code == 500

    payload = read_single_log(
        captured_exception_logs,
    )

    assert payload["level"] == "ERROR"
    assert payload["logger"] == "app.api.exception_handlers"
    assert payload["message"] == "Unhandled application exception"

    assert payload["request_id"] == "request-error-log"
    assert payload["http_method"] == "GET"
    assert payload["http_path"] == "/explode"
    assert payload["status_code"] == 500

    assert "exception" in payload
    assert "ValueError" in payload["exception"]
    assert "sensitive internal failure" in payload["exception"]
    assert "Traceback" in payload["exception"]


def test_exception_log_does_not_include_query_string(
    captured_exception_logs: io.StringIO,
) -> None:
    response = exception_client.get(
        "/explode?token=super-secret-value",
        headers={
            REQUEST_ID_HEADER: "request-query-test",
        },
    )

    assert response.status_code == 500

    payload = read_single_log(
        captured_exception_logs,
    )

    assert payload["http_path"] == "/explode"
    assert "token" not in payload["http_path"]
    assert "super-secret-value" not in payload["http_path"]
