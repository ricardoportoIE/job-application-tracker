from typing import Any

from app.main import app


def get_response_schema_ref(
    response: dict[str, Any],
) -> str:
    return str(response["content"]["application/json"]["schema"]["$ref"])


def test_register_openapi_documents_expected_responses() -> None:
    schema = app.openapi()

    responses = schema["paths"]["/api/v1/auth/register"]["post"]["responses"]

    assert set(responses) == {
        "201",
        "409",
        "422",
        "500",
    }


def test_login_openapi_documents_expected_responses() -> None:
    schema = app.openapi()

    responses = schema["paths"]["/api/v1/auth/login"]["post"]["responses"]

    assert set(responses) == {
        "200",
        "401",
        "403",
        "422",
        "500",
    }


def test_me_openapi_documents_expected_responses() -> None:
    schema = app.openapi()

    responses = schema["paths"]["/api/v1/auth/me"]["get"]["responses"]

    assert set(responses) == {
        "200",
        "401",
        "403",
        "500",
    }


def test_auth_openapi_uses_standard_error_schemas() -> None:
    schema = app.openapi()

    register_responses = schema["paths"]["/api/v1/auth/register"]["post"]["responses"]

    login_responses = schema["paths"]["/api/v1/auth/login"]["post"]["responses"]

    me_responses = schema["paths"]["/api/v1/auth/me"]["get"]["responses"]

    assert (
        get_response_schema_ref(register_responses["409"])
        == "#/components/schemas/ErrorResponse"
    )
    assert (
        get_response_schema_ref(register_responses["422"])
        == "#/components/schemas/ValidationErrorResponse"
    )
    assert (
        get_response_schema_ref(register_responses["500"])
        == "#/components/schemas/ErrorResponse"
    )

    assert (
        get_response_schema_ref(login_responses["401"])
        == "#/components/schemas/ErrorResponse"
    )
    assert (
        get_response_schema_ref(login_responses["403"])
        == "#/components/schemas/ErrorResponse"
    )
    assert (
        get_response_schema_ref(login_responses["422"])
        == "#/components/schemas/ValidationErrorResponse"
    )
    assert (
        get_response_schema_ref(login_responses["500"])
        == "#/components/schemas/ErrorResponse"
    )

    assert (
        get_response_schema_ref(me_responses["401"])
        == "#/components/schemas/ErrorResponse"
    )
    assert (
        get_response_schema_ref(me_responses["403"])
        == "#/components/schemas/ErrorResponse"
    )
    assert (
        get_response_schema_ref(me_responses["500"])
        == "#/components/schemas/ErrorResponse"
    )
