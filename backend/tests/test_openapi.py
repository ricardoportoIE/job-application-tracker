from typing import get_args

from app.api.openapi import (
    ERROR_RESPONSE_CATALOG,
    ErrorStatusCode,
    error_responses,
)
from app.schemas.error import (
    ErrorResponse,
    ValidationErrorResponse,
)


def test_error_response_catalog_uses_standard_error_model() -> None:
    status_codes: tuple[
        ErrorStatusCode,
        ...,
    ] = (
        401,
        403,
        404,
        409,
        500,
    )

    for status_code in status_codes:
        assert ERROR_RESPONSE_CATALOG[status_code]["model"] is ErrorResponse


def test_error_response_catalog_uses_validation_model_for_422() -> None:
    assert ERROR_RESPONSE_CATALOG[422]["model"] is ValidationErrorResponse


def test_error_responses_returns_requested_status_codes() -> None:
    responses = error_responses(
        401,
        404,
        422,
    )

    assert set(responses) == {
        401,
        404,
        422,
    }


def test_error_responses_preserves_models_and_descriptions() -> None:
    responses = error_responses(
        409,
        500,
    )

    assert responses[409]["model"] is ErrorResponse
    assert responses[409]["description"]

    assert responses[500]["model"] is ErrorResponse
    assert responses[500]["description"]


def test_error_responses_returns_independent_response_definitions() -> None:
    first = error_responses(
        404,
    )
    second = error_responses(
        404,
    )

    first[404]["description"] = "Changed only for this test."

    assert second[404]["description"] == ERROR_RESPONSE_CATALOG[404]["description"]


def test_error_responses_uses_mixed_model_for_422_when_requested() -> None:
    responses = error_responses(
        422,
        mixed_422=True,
    )

    model = responses[422]["model"]

    assert set(get_args(model)) == {
        ErrorResponse,
        ValidationErrorResponse,
    }


def test_error_responses_keeps_standard_422_without_mixed_option() -> None:
    responses = error_responses(
        422,
    )

    assert responses[422]["model"] is ValidationErrorResponse


def test_mixed_422_does_not_change_other_response_models() -> None:
    responses = error_responses(
        401,
        404,
        422,
        500,
        mixed_422=True,
    )

    assert responses[401]["model"] is ErrorResponse
    assert responses[404]["model"] is ErrorResponse
    assert responses[500]["model"] is ErrorResponse

    model = responses[422]["model"]

    assert set(get_args(model)) == {
        ErrorResponse,
        ValidationErrorResponse,
    }
