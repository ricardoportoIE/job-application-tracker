from typing import Any, Literal

from app.schemas.error import (
    ErrorResponse,
    ValidationErrorResponse,
)

ErrorStatusCode = Literal[
    401,
    403,
    404,
    409,
    422,
    500,
]

type OpenAPIResponseDefinition = dict[str, Any]

type OpenAPIResponses = dict[
    int | str,
    OpenAPIResponseDefinition,
]


ERROR_RESPONSE_CATALOG: dict[
    ErrorStatusCode,
    OpenAPIResponseDefinition,
] = {
    401: {
        "model": ErrorResponse,
        "description": ("Authentication credentials are missing or invalid."),
    },
    403: {
        "model": ErrorResponse,
        "description": (
            "The authenticated user is not allowed to perform this action."
        ),
    },
    404: {
        "model": ErrorResponse,
        "description": ("The requested resource was not found."),
    },
    409: {
        "model": ErrorResponse,
        "description": (
            "The request conflicts with the current state of the resource."
        ),
    },
    422: {
        "model": ValidationErrorResponse,
        "description": ("The request failed validation."),
    },
    500: {
        "model": ErrorResponse,
        "description": ("An unexpected internal server error occurred."),
    },
}


MIXED_UNPROCESSABLE_ENTITY_RESPONSE: OpenAPIResponseDefinition = {
    "model": ErrorResponse | ValidationErrorResponse,
    "description": (
        "The request failed input validation or violates a request-level business rule."
    ),
}


def error_responses(
    *status_codes: ErrorStatusCode,
    mixed_422: bool = False,
) -> OpenAPIResponses:
    responses: OpenAPIResponses = {
        status_code: ERROR_RESPONSE_CATALOG[status_code].copy()
        for status_code in status_codes
    }

    if mixed_422 and 422 in responses:
        responses[422] = MIXED_UNPROCESSABLE_ENTITY_RESPONSE.copy()

    return responses
