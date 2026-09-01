from fastapi.testclient import TestClient

from app.main import app

client = TestClient(app)


def test_cors_allows_configured_origin() -> None:
    response = client.options(
        "/api/v1/applications",
        headers={
            "Origin": "http://localhost:5173",
            "Access-Control-Request-Method": "GET",
            "Access-Control-Request-Headers": "Authorization",
        },
    )

    assert response.status_code == 200
    assert response.headers["access-control-allow-origin"] == "http://localhost:5173"
    assert response.headers["access-control-allow-credentials"] == "true"


def test_cors_allows_second_configured_origin() -> None:
    response = client.options(
        "/api/v1/applications",
        headers={
            "Origin": "http://127.0.0.1:5173",
            "Access-Control-Request-Method": "GET",
        },
    )

    assert response.status_code == 200
    assert response.headers["access-control-allow-origin"] == "http://127.0.0.1:5173"


def test_cors_rejects_unconfigured_origin() -> None:
    response = client.options(
        "/api/v1/applications",
        headers={
            "Origin": "https://malicious.example.com",
            "Access-Control-Request-Method": "GET",
        },
    )

    assert response.status_code == 400
    assert "access-control-allow-origin" not in response.headers


def test_cors_allows_authorization_header() -> None:
    response = client.options(
        "/api/v1/applications",
        headers={
            "Origin": "http://localhost:5173",
            "Access-Control-Request-Method": "GET",
            "Access-Control-Request-Headers": "Authorization",
        },
    )

    assert response.status_code == 200

    allowed_headers = response.headers["access-control-allow-headers"].lower()

    assert "authorization" in allowed_headers


def test_cors_allows_content_type_header() -> None:
    response = client.options(
        "/api/v1/applications",
        headers={
            "Origin": "http://localhost:5173",
            "Access-Control-Request-Method": "POST",
            "Access-Control-Request-Headers": "Content-Type",
        },
    )

    assert response.status_code == 200

    allowed_headers = response.headers["access-control-allow-headers"].lower()

    assert "content-type" in allowed_headers
