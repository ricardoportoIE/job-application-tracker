import logging
from time import perf_counter

from starlette.datastructures import Headers, MutableHeaders
from starlette.routing import BaseRoute
from starlette.types import (
    ASGIApp,
    Message,
    Receive,
    Scope,
    Send,
)

from app.core.metrics import (
    HTTP_REQUEST_DURATION_SECONDS,
    HTTP_REQUESTS_TOTAL,
)
from app.core.request_context import (
    generate_request_id,
    is_valid_request_id,
    reset_request_id,
    set_request_id,
)

REQUEST_ID_HEADER = "X-Request-ID"

logger = logging.getLogger(__name__)


def get_route_path(scope: Scope) -> str:
    route = scope.get("route")

    if isinstance(route, BaseRoute):
        path = getattr(
            route,
            "path",
            None,
        )

        if isinstance(path, str):
            return path

    return scope["path"]


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
            duration_seconds = perf_counter() - started_at
            duration_ms = duration_seconds * 1000
            route_path = get_route_path(scope)

            HTTP_REQUESTS_TOTAL.labels(
                method=scope["method"],
                path=route_path,
                status_code=str(status_code),
            ).inc()

            HTTP_REQUEST_DURATION_SECONDS.labels(
                method=scope["method"],
                path=route_path,
            ).observe(duration_seconds)

            logger.info(
                "HTTP request completed",
                extra={
                    "event": "http.request.completed",
                    "http_method": scope["method"],
                    "http_path": route_path,
                    "status_code": status_code,
                    "duration_ms": round(
                        duration_ms,
                        2,
                    ),
                },
            )

            reset_request_id(token)
