import logging
from collections.abc import Mapping

from fastapi import Request, status
from fastapi.responses import JSONResponse
from starlette.exceptions import HTTPException as StarletteHTTPException

from app.core.request_context import generate_request_id
from app.middleware.request_id import REQUEST_ID_HEADER

logger = logging.getLogger(__name__)


def get_request_id_from_request(
    request: Request,
) -> str:
    request_id = getattr(
        request.state,
        "request_id",
        None,
    )

    if isinstance(request_id, str):
        return request_id

    return generate_request_id()


def build_error_headers(
    request_id: str,
    existing_headers: Mapping[str, str] | None = None,
) -> dict[str, str]:
    headers = dict(
        existing_headers or {},
    )

    headers[REQUEST_ID_HEADER] = request_id

    return headers


async def http_exception_handler(
    request: Request,
    exc: Exception,
) -> JSONResponse:
    if not isinstance(
        exc,
        StarletteHTTPException,
    ):
        raise exc

    request_id = get_request_id_from_request(
        request,
    )

    return JSONResponse(
        status_code=exc.status_code,
        content={
            "detail": exc.detail,
            "request_id": request_id,
        },
        headers=build_error_headers(
            request_id,
            exc.headers,
        ),
    )


async def unhandled_exception_handler(
    request: Request,
    exc: Exception,
) -> JSONResponse:
    request_id = get_request_id_from_request(
        request,
    )

    logger.error(
        "Unhandled application exception",
        exc_info=(
            type(exc),
            exc,
            exc.__traceback__,
        ),
        extra={
            "request_id": request_id,
            "http_method": request.method,
            "http_path": request.url.path,
            "status_code": status.HTTP_500_INTERNAL_SERVER_ERROR,
        },
    )

    return JSONResponse(
        status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
        content={
            "detail": "Internal server error",
            "request_id": request_id,
        },
        headers=build_error_headers(
            request_id,
        ),
    )
