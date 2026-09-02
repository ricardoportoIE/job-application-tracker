from typing import Any

from app.main import app


def get_response_schema_ref(
    response: dict[str, Any],
) -> str:
    return str(response["content"]["application/json"]["schema"]["$ref"])


def test_create_company_openapi_documents_expected_responses() -> None:
    schema = app.openapi()

    responses = schema["paths"]["/api/v1/companies"]["post"]["responses"]

    assert set(responses) == {
        "201",
        "401",
        "403",
        "422",
        "500",
    }


def test_list_companies_openapi_documents_expected_responses() -> None:
    schema = app.openapi()

    responses = schema["paths"]["/api/v1/companies"]["get"]["responses"]

    assert set(responses) == {
        "200",
        "401",
        "403",
        "500",
    }


def test_get_company_openapi_documents_expected_responses() -> None:
    schema = app.openapi()

    responses = schema["paths"]["/api/v1/companies/{company_id}"]["get"]["responses"]

    assert set(responses) == {
        "200",
        "401",
        "403",
        "404",
        "422",
        "500",
    }


def test_update_company_openapi_documents_expected_responses() -> None:
    schema = app.openapi()

    responses = schema["paths"]["/api/v1/companies/{company_id}"]["patch"]["responses"]

    assert set(responses) == {
        "200",
        "401",
        "403",
        "404",
        "422",
        "500",
    }


def test_delete_company_openapi_documents_expected_responses() -> None:
    schema = app.openapi()

    responses = schema["paths"]["/api/v1/companies/{company_id}"]["delete"]["responses"]

    assert set(responses) == {
        "204",
        "401",
        "403",
        "404",
        "409",
        "422",
        "500",
    }


def test_company_openapi_uses_standard_error_schemas() -> None:
    schema = app.openapi()

    create_responses = schema["paths"]["/api/v1/companies"]["post"]["responses"]

    get_responses = schema["paths"]["/api/v1/companies/{company_id}"]["get"][
        "responses"
    ]

    delete_responses = schema["paths"]["/api/v1/companies/{company_id}"]["delete"][
        "responses"
    ]

    assert (
        get_response_schema_ref(create_responses["401"])
        == "#/components/schemas/ErrorResponse"
    )
    assert (
        get_response_schema_ref(create_responses["403"])
        == "#/components/schemas/ErrorResponse"
    )
    assert (
        get_response_schema_ref(create_responses["422"])
        == "#/components/schemas/ValidationErrorResponse"
    )
    assert (
        get_response_schema_ref(create_responses["500"])
        == "#/components/schemas/ErrorResponse"
    )

    assert (
        get_response_schema_ref(get_responses["404"])
        == "#/components/schemas/ErrorResponse"
    )
    assert (
        get_response_schema_ref(get_responses["422"])
        == "#/components/schemas/ValidationErrorResponse"
    )

    assert (
        get_response_schema_ref(delete_responses["409"])
        == "#/components/schemas/ErrorResponse"
    )
    assert (
        get_response_schema_ref(delete_responses["422"])
        == "#/components/schemas/ValidationErrorResponse"
    )
