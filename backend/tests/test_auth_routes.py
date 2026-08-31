from collections.abc import Generator
from uuid import uuid4

import pytest
from fastapi.testclient import TestClient
from sqlalchemy import delete

from app.db.session import SessionLocal
from app.main import app
from app.models.user import User

TEST_EMAIL_PREFIX = "auth-route-test-"

client = TestClient(app)


@pytest.fixture(autouse=True)
def cleanup_test_users() -> Generator[None]:
    yield

    with SessionLocal() as session:
        session.execute(
            delete(User).where(User.email.like(f"{TEST_EMAIL_PREFIX}%@example.com"))
        )
        session.commit()


def make_test_email() -> str:
    return f"{TEST_EMAIL_PREFIX}{uuid4()}@example.com"


def test_register_user_returns_created_user() -> None:
    email = make_test_email()

    response = client.post(
        "/auth/register",
        json={
            "email": email,
            "password": "secure-password-123",
        },
    )

    assert response.status_code == 201

    body = response.json()

    assert body["email"] == email
    assert body["is_active"] is True
    assert body["id"]
    assert body["created_at"]
    assert body["updated_at"]


def test_register_user_does_not_expose_password() -> None:
    response = client.post(
        "/auth/register",
        json={
            "email": make_test_email(),
            "password": "secure-password-123",
        },
    )

    assert response.status_code == 201

    body = response.json()

    assert "password" not in body
    assert "password_hash" not in body


def test_register_user_normalizes_email() -> None:
    email = make_test_email()

    response = client.post(
        "/auth/register",
        json={
            "email": email.upper(),
            "password": "secure-password-123",
        },
    )

    assert response.status_code == 201
    assert response.json()["email"] == email


def test_register_user_rejects_duplicate_email() -> None:
    email = make_test_email()

    first_response = client.post(
        "/auth/register",
        json={
            "email": email,
            "password": "secure-password-123",
        },
    )

    second_response = client.post(
        "/auth/register",
        json={
            "email": email.upper(),
            "password": "another-secure-password",
        },
    )

    assert first_response.status_code == 201
    assert second_response.status_code == 409
    assert second_response.json() == {
        "detail": "Email already registered",
    }


def test_register_user_rejects_invalid_email() -> None:
    response = client.post(
        "/auth/register",
        json={
            "email": "not-an-email",
            "password": "secure-password-123",
        },
    )

    assert response.status_code == 422


def test_register_user_rejects_short_password() -> None:
    response = client.post(
        "/auth/register",
        json={
            "email": make_test_email(),
            "password": "short",
        },
    )

    assert response.status_code == 422


def test_register_user_rejects_extra_fields() -> None:
    response = client.post(
        "/auth/register",
        json={
            "email": make_test_email(),
            "password": "secure-password-123",
            "is_active": False,
        },
    )

    assert response.status_code == 422
