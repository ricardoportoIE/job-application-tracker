from fastapi import FastAPI
from fastapi.testclient import TestClient


def create_test_app(*, docs_enabled: bool) -> FastAPI:
    return FastAPI(
        docs_url="/docs" if docs_enabled else None,
        redoc_url="/redoc" if docs_enabled else None,
        openapi_url="/openapi.json" if docs_enabled else None,
    )


def test_docs_are_available_when_enabled() -> None:
    app = create_test_app(docs_enabled=True)
    client = TestClient(app)

    assert client.get("/docs").status_code == 200
    assert client.get("/redoc").status_code == 200
    assert client.get("/openapi.json").status_code == 200


def test_docs_are_disabled_when_not_enabled() -> None:
    app = create_test_app(docs_enabled=False)
    client = TestClient(app)

    assert client.get("/docs").status_code == 404
    assert client.get("/redoc").status_code == 404
    assert client.get("/openapi.json").status_code == 404
