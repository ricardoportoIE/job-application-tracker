import logging
from time import perf_counter

from starlette.datastructures import Headers, MutableHeaders
from starlette.types import (
    ASGIApp,
    Message,
    Receive,
    Scope,
    Send,
)

from app.core.request_context import (
    generate_request_id,
    is_valid_request_id,
    reset_request_id,
    set_request_id,
)

REQUEST_ID_HEADER = "X-Request-ID"

logger = logging.getLogger(__name__)


class RequestIdMiddleware:
    def __init__(
        self,
        app: ASGIApp,
    ) -> None:
        self.app = app

    async def __call__(
        self,
        scope: Scope,
        receive: Receive,
        send: Send,
    ) -> None:
        if scope["type"] != "http":
            await self.app(
                scope,
                receive,
                send,
            )
            return

        request_headers = Headers(
            scope=scope,
        )

        supplied_request_id = request_headers.get(
            REQUEST_ID_HEADER,
        )

        if supplied_request_id is not None and is_valid_request_id(supplied_request_id):
            request_id = supplied_request_id
        else:
            request_id = generate_request_id()

        state = scope.setdefault(
            "state",
            {},
        )
        state["request_id"] = request_id
        token = set_request_id(
            request_id,
        )

        started_at = perf_counter()
        status_code = 500

        async def send_with_request_id(
            message: Message,
        ) -> None:
            nonlocal status_code

            if message["type"] == "http.response.start":
                status_code = message["status"]

                response_headers = MutableHeaders(
                    scope=message,
                )
                response_headers[REQUEST_ID_HEADER] = request_id

            await send(message)

        try:
            await self.app(
                scope,
                receive,
                send_with_request_id,
            )
        finally:
            duration_ms = (perf_counter() - started_at) * 1000

            logger.info(
                "HTTP request completed",
                extra={
                    "http_method": scope["method"],
                    "http_path": scope["path"],
                    "status_code": status_code,
                    "duration_ms": round(
                        duration_ms,
                        2,
                    ),
                },
            )

            reset_request_id(token)
