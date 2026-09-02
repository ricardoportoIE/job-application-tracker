from typing import Any

from app.main import app


def get_response_schema(
    response: dict[str, Any],
) -> dict[str, Any]:
    return response["content"]["application/json"]["schema"]


def get_response_schema_ref(
    response: dict[str, Any],
) -> str:
    return str(get_response_schema(response)["$ref"])


def get_any_of_schema_refs(
    response: dict[str, Any],
) -> set[str]:
    schema = get_response_schema(response)

    return {str(item["$ref"]) for item in schema["anyOf"]}


def test_create_application_openapi_documents_expected_responses() -> None:
    schema = app.openapi()

    responses = schema["paths"]["/api/v1/applications"]["post"]["responses"]

    assert set(responses) == {
        "201",
        "401",
        "403",
        "404",
        "422",
        "500",
    }


def test_list_applications_openapi_documents_expected_responses() -> None:
    schema = app.openapi()

    responses = schema["paths"]["/api/v1/applications"]["get"]["responses"]

    assert set(responses) == {
        "200",
        "401",
        "403",
        "422",
        "500",
    }


def test_get_application_openapi_documents_expected_responses() -> None:
    schema = app.openapi()

    responses = schema["paths"]["/api/v1/applications/{application_id}"]["get"][
        "responses"
    ]

    assert set(responses) == {
        "200",
        "401",
        "403",
        "404",
        "422",
        "500",
    }


def test_update_application_openapi_documents_expected_responses() -> None:
    schema = app.openapi()

    responses = schema["paths"]["/api/v1/applications/{application_id}"]["patch"][
        "responses"
    ]

    assert set(responses) == {
        "200",
        "401",
        "403",
        "404",
        "422",
        "500",
    }


def test_delete_application_openapi_documents_expected_responses() -> None:
    schema = app.openapi()

    responses = schema["paths"]["/api/v1/applications/{application_id}"]["delete"][
        "responses"
    ]

    assert set(responses) == {
        "204",
        "401",
        "403",
        "404",
        "422",
        "500",
    }


def test_application_openapi_uses_expected_error_schemas() -> None:
    schema = app.openapi()

    create_responses = schema["paths"]["/api/v1/applications"]["post"]["responses"]

    list_responses = schema["paths"]["/api/v1/applications"]["get"]["responses"]

    get_responses = schema["paths"]["/api/v1/applications/{application_id}"]["get"][
        "responses"
    ]

    update_responses = schema["paths"]["/api/v1/applications/{application_id}"][
        "patch"
    ]["responses"]

    delete_responses = schema["paths"]["/api/v1/applications/{application_id}"][
        "delete"
    ]["responses"]

    expected_mixed_422_refs = {
        "#/components/schemas/ErrorResponse",
        "#/components/schemas/ValidationErrorResponse",
    }

    assert (
        get_any_of_schema_refs(
            create_responses["422"],
        )
        == expected_mixed_422_refs
    )

    assert (
        get_any_of_schema_refs(
            update_responses["422"],
        )
        == expected_mixed_422_refs
    )

    assert (
        get_response_schema_ref(
            list_responses["422"],
        )
        == "#/components/schemas/ValidationErrorResponse"
    )

    assert (
        get_response_schema_ref(
            get_responses["422"],
        )
        == "#/components/schemas/ValidationErrorResponse"
    )

    assert (
        get_response_schema_ref(
            delete_responses["422"],
        )
        == "#/components/schemas/ValidationErrorResponse"
    )

    assert (
        get_response_schema_ref(
            create_responses["404"],
        )
        == "#/components/schemas/ErrorResponse"
    )

    assert (
        get_response_schema_ref(
            update_responses["404"],
        )
        == "#/components/schemas/ErrorResponse"
    )

    assert (
        get_response_schema_ref(
            delete_responses["404"],
        )
        == "#/components/schemas/ErrorResponse"
    )

    assert (
        get_response_schema_ref(
            create_responses["500"],
        )
        == "#/components/schemas/ErrorResponse"
    )
