import io
import json
import logging
import uuid
from collections.abc import Generator
from typing import Any

import pytest
from fastapi import FastAPI
from fastapi.testclient import TestClient

from app.core.logging import JsonFormatter
from app.middleware.request_id import (
    REQUEST_ID_HEADER,
    RequestIdMiddleware,
)

request_logging_app = FastAPI()

request_logging_app.add_middleware(
    RequestIdMiddleware,
)


@request_logging_app.get("/success")
def success() -> dict[str, str]:
    return {
        "status": "ok",
    }


client = TestClient(
    request_logging_app,
)


@pytest.fixture
def captured_request_logs() -> Generator[io.StringIO]:
    logger = logging.getLogger(
        "app.middleware.request_id",
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
    logger.setLevel(logging.INFO)
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
    log_lines = [line for line in stream.getvalue().splitlines() if line.strip()]

    assert len(log_lines) == 1

    payload = json.loads(log_lines[0])

    assert isinstance(payload, dict)

    return payload


def test_completed_request_is_logged_with_http_metadata(
    captured_request_logs: io.StringIO,
) -> None:
    response = client.get(
        "/success?secret=do-not-log",
        headers={
            REQUEST_ID_HEADER: "request-123",
        },
    )

    assert response.status_code == 200

    payload = read_single_log(
        captured_request_logs,
    )

    assert payload["message"] == "HTTP request completed"
    assert payload["level"] == "INFO"
    assert payload["logger"] == "app.middleware.request_id"

    assert payload["request_id"] == "request-123"
    assert payload["http_method"] == "GET"
    assert payload["http_path"] == "/success"
    assert payload["status_code"] == 200

    assert isinstance(
        payload["duration_ms"],
        float,
    )
    assert payload["duration_ms"] >= 0

    assert "secret" not in payload["http_path"]
    assert "do-not-log" not in payload["http_path"]


def test_not_found_request_is_logged_with_404(
    captured_request_logs: io.StringIO,
) -> None:
    response = client.get(
        "/does-not-exist",
        headers={
            REQUEST_ID_HEADER: "request-404",
        },
    )

    assert response.status_code == 404

    payload = read_single_log(
        captured_request_logs,
    )

    assert payload["request_id"] == "request-404"
    assert payload["http_method"] == "GET"
    assert payload["http_path"] == "/does-not-exist"
    assert payload["status_code"] == 404


def test_generated_request_id_matches_response_and_log(
    captured_request_logs: io.StringIO,
) -> None:
    response = client.get(
        "/success",
    )

    assert response.status_code == 200

    response_request_id = response.headers[REQUEST_ID_HEADER]

    parsed_request_id = uuid.UUID(
        response_request_id,
    )

    assert str(parsed_request_id) == response_request_id

    payload = read_single_log(
        captured_request_logs,
    )

    assert payload["request_id"] == response_request_id
    assert payload["status_code"] == 200
