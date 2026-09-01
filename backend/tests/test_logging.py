import json
import logging
import sys
from collections.abc import Generator
from datetime import datetime

import pytest

from app.core.config import settings
from app.core.logging import JsonFormatter, configure_logging
from app.core.request_context import (
    reset_request_id,
    set_request_id,
)


@pytest.fixture
def preserve_logging_configuration() -> Generator[None]:
    logger_names = (
        "",
        "uvicorn",
        "uvicorn.error",
        "uvicorn.access",
    )

    original_configuration: dict[
        str,
        tuple[
            list[logging.Handler],
            int,
            bool,
        ],
    ] = {}

    for logger_name in logger_names:
        logger = logging.getLogger(logger_name)

        original_configuration[logger_name] = (
            logger.handlers.copy(),
            logger.level,
            logger.propagate,
        )

    yield

    for (
        logger_name,
        (
            handlers,
            level,
            propagate,
        ),
    ) in original_configuration.items():
        logger = logging.getLogger(logger_name)

        logger.handlers.clear()
        logger.handlers.extend(handlers)
        logger.setLevel(level)
        logger.propagate = propagate


def test_json_formatter_outputs_structured_log() -> None:
    formatter = JsonFormatter()

    record = logging.LogRecord(
        name="app.test",
        level=logging.INFO,
        pathname=__file__,
        lineno=1,
        msg="Application configured",
        args=(),
        exc_info=None,
    )

    payload = json.loads(formatter.format(record))

    assert payload["level"] == "INFO"
    assert payload["logger"] == "app.test"
    assert payload["message"] == "Application configured"
    assert payload["service"] == settings.app_name
    assert payload["environment"] == settings.environment
    assert "timestamp" in payload
    assert "exception" not in payload
    assert "request_id" not in payload
    timestamp = datetime.fromisoformat(payload["timestamp"])

    assert timestamp.tzinfo is not None


def test_json_formatter_formats_message_arguments() -> None:
    formatter = JsonFormatter()

    record = logging.LogRecord(
        name="app.test",
        level=logging.INFO,
        pathname=__file__,
        lineno=1,
        msg="User %s authenticated",
        args=("123",),
        exc_info=None,
    )

    payload = json.loads(formatter.format(record))

    assert payload["message"] == "User 123 authenticated"


def test_json_formatter_includes_exception_information() -> None:
    formatter = JsonFormatter()

    try:
        raise ValueError("test error")
    except ValueError:
        exc_info = sys.exc_info()

    record = logging.LogRecord(
        name="app.test",
        level=logging.ERROR,
        pathname=__file__,
        lineno=1,
        msg="Unexpected failure",
        args=(),
        exc_info=exc_info,
    )

    payload = json.loads(formatter.format(record))

    assert payload["level"] == "ERROR"
    assert payload["message"] == "Unexpected failure"
    assert "exception" in payload
    assert "ValueError: test error" in payload["exception"]


def test_configure_logging_configures_root_logger(
    preserve_logging_configuration: None,
) -> None:
    configure_logging()

    root_logger = logging.getLogger()

    assert root_logger.level == getattr(
        logging,
        settings.log_level,
    )

    assert len(root_logger.handlers) == 1

    handler = root_logger.handlers[0]

    assert isinstance(
        handler,
        logging.StreamHandler,
    )
    assert isinstance(
        handler.formatter,
        JsonFormatter,
    )


def test_configure_logging_configures_uvicorn_loggers(
    preserve_logging_configuration: None,
) -> None:
    configure_logging()

    expected_level = getattr(
        logging,
        settings.log_level,
    )

    for logger_name in (
        "uvicorn",
        "uvicorn.error",
        "uvicorn.access",
    ):
        logger = logging.getLogger(
            logger_name,
        )

        assert logger.level == expected_level
        assert logger.propagate is False
        assert len(logger.handlers) == 1
        assert isinstance(
            logger.handlers[0].formatter,
            JsonFormatter,
        )


def test_json_formatter_includes_request_id_from_context() -> None:
    formatter = JsonFormatter()

    token = set_request_id(
        "request-123",
    )

    try:
        record = logging.LogRecord(
            name="app.test",
            level=logging.INFO,
            pathname=__file__,
            lineno=1,
            msg="Request processed",
            args=(),
            exc_info=None,
        )

        payload = json.loads(formatter.format(record))
    finally:
        reset_request_id(token)

    assert payload["message"] == "Request processed"
    assert payload["request_id"] == "request-123"
