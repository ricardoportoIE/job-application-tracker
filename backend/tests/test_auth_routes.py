from collections.abc import Generator
from uuid import uuid4

import pytest
from fastapi.testclient import TestClient
from sqlalchemy import delete

from app.core.security import decode_access_token
from app.db.session import SessionLocal
from app.main import app
from app.models.user import User
from app.schemas.user import UserCreate
from app.services.user import UserService

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


def test_login_returns_access_token() -> None:
    email = make_test_email()
    password = "secure-password-123"

    with SessionLocal() as session:
        user = UserService.create(
            session,
            UserCreate(
                email=email,
                password=password,
            ),
        )
        user_id = user.id

    response = client.post(
        "/auth/login",
        json={
            "email": email,
            "password": password,
        },
    )

    assert response.status_code == 200

    body = response.json()

    assert body["access_token"]
    assert body["token_type"] == "bearer"

    subject = decode_access_token(body["access_token"])

    assert subject == str(user_id)


def test_login_rejects_incorrect_password() -> None:
    email = make_test_email()

    with SessionLocal() as session:
        UserService.create(
            session,
            UserCreate(
                email=email,
                password="correct-password",
            ),
        )

    response = client.post(
        "/auth/login",
        json={
            "email": email,
            "password": "wrong-password",
        },
    )

    assert response.status_code == 401
    assert response.json() == {
        "detail": "Invalid credentials",
    }
    assert response.headers["www-authenticate"] == "Bearer"


def test_login_rejects_nonexistent_user() -> None:
    response = client.post(
        "/auth/login",
        json={
            "email": make_test_email(),
            "password": "secure-password-123",
        },
    )

    assert response.status_code == 401
    assert response.json() == {
        "detail": "Invalid credentials",
    }


def test_login_rejects_inactive_user() -> None:
    email = make_test_email()
    password = "secure-password-123"

    with SessionLocal() as session:
        user = UserService.create(
            session,
            UserCreate(
                email=email,
                password=password,
            ),
        )

        user.is_active = False
        session.commit()

    response = client.post(
        "/auth/login",
        json={
            "email": email,
            "password": password,
        },
    )

    assert response.status_code == 403
    assert response.json() == {
        "detail": "Inactive user",
    }


def test_login_rejects_invalid_email() -> None:
    response = client.post(
        "/auth/login",
        json={
            "email": "not-an-email",
            "password": "secure-password-123",
        },
    )

    assert response.status_code == 422


def test_login_rejects_empty_password() -> None:
    response = client.post(
        "/auth/login",
        json={
            "email": make_test_email(),
            "password": "",
        },
    )

    assert response.status_code == 422


def test_login_rejects_extra_fields() -> None:
    response = client.post(
        "/auth/login",
        json={
            "email": make_test_email(),
            "password": "secure-password-123",
            "remember_me": True,
        },
    )

    assert response.status_code == 422
