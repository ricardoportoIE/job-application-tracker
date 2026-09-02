from collections.abc import Generator
from datetime import timedelta
from uuid import uuid4

import pytest
from fastapi.testclient import TestClient
from sqlalchemy import delete

from app.core.security import create_access_token, decode_access_token
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
        "/api/v1/auth/register",
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
        "/api/v1/auth/register",
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
        "/api/v1/auth/register",
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
        "/api/v1/auth/register",
        json={
            "email": email,
            "password": "secure-password-123",
        },
    )

    second_response = client.post(
        "/api/v1/auth/register",
        json={
            "email": email.upper(),
            "password": "another-secure-password",
        },
    )

    assert first_response.status_code == 201
    assert second_response.status_code == 409

    body = second_response.json()

    assert body["detail"] == "Email already registered"
    assert body["request_id"]
    assert second_response.headers["X-Request-ID"] == body["request_id"]


def test_register_user_rejects_invalid_email() -> None:
    response = client.post(
        "/api/v1/auth/register",
        json={
            "email": "not-an-email",
            "password": "secure-password-123",
        },
    )

    assert response.status_code == 422

    body = response.json()

    assert isinstance(body["detail"], list)
    assert body["detail"]
    assert body["request_id"]
    assert response.headers["X-Request-ID"] == body["request_id"]
    assert any(error["loc"] == ["body", "email"] for error in body["detail"])


def test_register_user_rejects_short_password() -> None:
    response = client.post(
        "/api/v1/auth/register",
        json={
            "email": make_test_email(),
            "password": "short",
        },
    )

    assert response.status_code == 422

    body = response.json()

    assert isinstance(body["detail"], list)
    assert body["detail"]
    assert body["request_id"]
    assert response.headers["X-Request-ID"] == body["request_id"]
    assert any(error["loc"] == ["body", "password"] for error in body["detail"])


def test_register_user_rejects_extra_fields() -> None:
    response = client.post(
        "/api/v1/auth/register",
        json={
            "email": make_test_email(),
            "password": "secure-password-123",
            "is_active": False,
        },
    )

    assert response.status_code == 422

    body = response.json()

    assert isinstance(body["detail"], list)
    assert body["detail"]
    assert body["request_id"]
    assert response.headers["X-Request-ID"] == body["request_id"]
    assert any(error["loc"] == ["body", "is_active"] for error in body["detail"])


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
        "/api/v1/auth/login",
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
        "/api/v1/auth/login",
        json={
            "email": email,
            "password": "wrong-password",
        },
    )

    assert response.status_code == 401

    body = response.json()

    assert body["detail"] == "Invalid credentials"
    assert body["request_id"]
    assert response.headers["X-Request-ID"] == body["request_id"]
    assert response.headers["www-authenticate"] == "Bearer"


def test_login_rejects_nonexistent_user() -> None:
    response = client.post(
        "/api/v1/auth/login",
        json={
            "email": make_test_email(),
            "password": "secure-password-123",
        },
    )

    assert response.status_code == 401

    body = response.json()

    assert body["detail"] == "Invalid credentials"
    assert body["request_id"]
    assert response.headers["X-Request-ID"] == body["request_id"]
    assert response.headers["www-authenticate"] == "Bearer"


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
        "/api/v1/auth/login",
        json={
            "email": email,
            "password": password,
        },
    )

    assert response.status_code == 403

    body = response.json()

    assert body["detail"] == "Inactive user"
    assert body["request_id"]
    assert response.headers["X-Request-ID"] == body["request_id"]


def test_login_rejects_invalid_email() -> None:
    response = client.post(
        "/api/v1/auth/login",
        json={
            "email": "not-an-email",
            "password": "secure-password-123",
        },
    )

    assert response.status_code == 422

    body = response.json()

    assert isinstance(body["detail"], list)
    assert body["detail"]
    assert body["request_id"]
    assert response.headers["X-Request-ID"] == body["request_id"]
    assert any(error["loc"] == ["body", "email"] for error in body["detail"])


def test_login_rejects_empty_password() -> None:
    response = client.post(
        "/api/v1/auth/login",
        json={
            "email": make_test_email(),
            "password": "",
        },
    )

    assert response.status_code == 422

    body = response.json()

    assert isinstance(body["detail"], list)
    assert body["detail"]
    assert body["request_id"]
    assert response.headers["X-Request-ID"] == body["request_id"]
    assert any(error["loc"] == ["body", "password"] for error in body["detail"])


def test_login_rejects_extra_fields() -> None:
    response = client.post(
        "/api/v1/auth/login",
        json={
            "email": make_test_email(),
            "password": "secure-password-123",
            "remember_me": True,
        },
    )

    assert response.status_code == 422

    body = response.json()

    assert isinstance(body["detail"], list)
    assert body["detail"]
    assert body["request_id"]
    assert response.headers["X-Request-ID"] == body["request_id"]
    assert any(error["loc"] == ["body", "remember_me"] for error in body["detail"])


def test_get_me_returns_authenticated_user() -> None:
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

    login_response = client.post(
        "/api/v1/auth/login",
        json={
            "email": email,
            "password": password,
        },
    )

    token = login_response.json()["access_token"]

    response = client.get(
        "/api/v1/auth/me",
        headers={
            "Authorization": f"Bearer {token}",
        },
    )

    assert response.status_code == 200

    body = response.json()

    assert body["id"] == str(user_id)
    assert body["email"] == email
    assert body["is_active"] is True
    assert "password" not in body
    assert "password_hash" not in body


def test_get_me_rejects_missing_token() -> None:
    response = client.get("/api/v1/auth/me")

    assert response.status_code == 401

    body = response.json()

    assert body["detail"] == "Could not validate credentials"
    assert body["request_id"]
    assert response.headers["X-Request-ID"] == body["request_id"]
    assert response.headers["www-authenticate"] == "Bearer"


def test_get_me_rejects_malformed_token() -> None:
    response = client.get(
        "/api/v1/auth/me",
        headers={
            "Authorization": "Bearer not-a-valid-jwt",
        },
    )

    assert response.status_code == 401

    body = response.json()

    assert body["detail"] == "Could not validate credentials"
    assert body["request_id"]
    assert response.headers["X-Request-ID"] == body["request_id"]
    assert response.headers["www-authenticate"] == "Bearer"


def test_get_me_rejects_expired_token() -> None:
    token = create_access_token(
        subject=str(uuid4()),
        expires_delta=timedelta(
            seconds=-1,
        ),
    )

    response = client.get(
        "/api/v1/auth/me",
        headers={
            "Authorization": f"Bearer {token}",
        },
    )

    assert response.status_code == 401

    body = response.json()

    assert body["detail"] == "Could not validate credentials"
    assert body["request_id"]
    assert response.headers["X-Request-ID"] == body["request_id"]
    assert response.headers["www-authenticate"] == "Bearer"


def test_get_me_rejects_nonexistent_user() -> None:
    token = create_access_token(
        subject=str(uuid4()),
    )

    response = client.get(
        "/api/v1/auth/me",
        headers={
            "Authorization": f"Bearer {token}",
        },
    )

    assert response.status_code == 401

    body = response.json()

    assert body["detail"] == "Could not validate credentials"
    assert body["request_id"]
    assert response.headers["X-Request-ID"] == body["request_id"]
    assert response.headers["www-authenticate"] == "Bearer"


def test_get_me_rejects_inactive_user() -> None:
    email = make_test_email()

    with SessionLocal() as session:
        user = UserService.create(
            session,
            UserCreate(
                email=email,
                password="secure-password-123",
            ),
        )

        user.is_active = False
        session.commit()

        token = create_access_token(
            subject=str(user.id),
        )

    response = client.get(
        "/api/v1/auth/me",
        headers={
            "Authorization": f"Bearer {token}",
        },
    )

    assert response.status_code == 403

    body = response.json()

    assert body["detail"] == "Inactive user"
    assert body["request_id"]
    assert response.headers["X-Request-ID"] == body["request_id"]
