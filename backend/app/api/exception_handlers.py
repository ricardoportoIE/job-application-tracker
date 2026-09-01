import logging

from fastapi import Request, status
from fastapi.responses import JSONResponse

from app.core.request_context import generate_request_id
from app.middleware.request_id import REQUEST_ID_HEADER

logger = logging.getLogger(__name__)


async def unhandled_exception_handler(
    request: Request,
    exc: Exception,
) -> JSONResponse:
    request_id = getattr(
        request.state,
        "request_id",
        None,
    )

    if not isinstance(request_id, str):
        request_id = generate_request_id()

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
        headers={
            REQUEST_ID_HEADER: request_id,
        },
    )
