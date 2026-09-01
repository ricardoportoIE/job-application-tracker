import json
import logging
import sys
from datetime import UTC, datetime
from typing import Any

from app.core.config import settings
from app.core.request_context import get_request_id


class JsonFormatter(logging.Formatter):
    def format(self, record: logging.LogRecord) -> str:
        payload: dict[str, Any] = {
            "timestamp": datetime.now(UTC).isoformat(),
            "level": record.levelname,
            "logger": record.name,
            "message": record.getMessage(),
            "service": settings.app_name,
            "environment": settings.environment,
        }

        request_id = get_request_id()

        if request_id is not None:
            payload["request_id"] = request_id

        for field in (
            "http_method",
            "http_path",
            "status_code",
            "duration_ms",
        ):
            value = getattr(
                record,
                field,
                None,
            )

            if value is not None:
                payload[field] = value

        if record.exc_info is not None:
            payload["exception"] = self.formatException(
                record.exc_info,
            )

        return json.dumps(
            payload,
            ensure_ascii=False,
        )


def configure_logging() -> None:
    handler = logging.StreamHandler(
        sys.stdout,
    )
    handler.setFormatter(
        JsonFormatter(),
    )

    root_logger = logging.getLogger()
    root_logger.handlers.clear()
    root_logger.addHandler(handler)
    root_logger.setLevel(settings.log_level)

    for logger_name in (
        "uvicorn",
        "uvicorn.error",
        "uvicorn.access",
    ):
        logger = logging.getLogger(
            logger_name,
        )
        logger.handlers.clear()
        logger.addHandler(handler)
        logger.setLevel(settings.log_level)
        logger.propagate = False
