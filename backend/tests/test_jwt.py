from datetime import UTC, datetime, timedelta

import jwt
import pytest
from app.core.config import settings
from app.core.security import (
    InvalidAccessTokenError,
    create_access_token,
    decode_access_token,
)


def test_create_and_decode_access_token() -> None:
    token = create_access_token("test-user-id")

    subject = decode_access_token(token)

    assert subject == "test-user-id"


def test_access_token_contains_subject() -> None:
    token = create_access_token("user-123")

    payload = jwt.decode(
        token,
        settings.jwt_secret_key.get_secret_value(),
        algorithms=[settings.jwt_algorithm],
    )

    assert payload["sub"] == "user-123"


def test_access_token_contains_issued_at_and_expiration() -> None:
    token = create_access_token("user-123")

    payload = jwt.decode(
        token,
        settings.jwt_secret_key.get_secret_value(),
        algorithms=[settings.jwt_algorithm],
    )

    assert "iat" in payload
    assert "exp" in payload
    assert payload["exp"] > payload["iat"]


def test_access_token_uses_custom_expiration() -> None:
    token = create_access_token(
        "user-123",
        expires_delta=timedelta(minutes=5),
    )

    payload = jwt.decode(
        token,
        settings.jwt_secret_key.get_secret_value(),
        algorithms=[settings.jwt_algorithm],
    )

    lifetime = payload["exp"] - payload["iat"]

    assert lifetime == 300


def test_decode_access_token_rejects_expired_token() -> None:
    token = create_access_token(
        "user-123",
        expires_delta=timedelta(seconds=-1),
    )

    with pytest.raises(InvalidAccessTokenError):
        decode_access_token(token)


def test_decode_access_token_rejects_token_with_invalid_signature() -> None:
    now = datetime.now(UTC)

    token = jwt.encode(
        {
            "sub": "user-123",
            "iat": now,
            "exp": now + timedelta(minutes=5),
        },
        "different-secret-key-for-testing-only-1234567890",
        algorithm=settings.jwt_algorithm,
    )

    with pytest.raises(InvalidAccessTokenError):
        decode_access_token(token)


def test_decode_access_token_rejects_malformed_token() -> None:
    with pytest.raises(InvalidAccessTokenError):
        decode_access_token("this-is-not-a-valid-jwt")


def test_decode_access_token_rejects_missing_subject() -> None:
    now = datetime.now(UTC)

    token = jwt.encode(
        {
            "iat": now,
            "exp": now + timedelta(minutes=5),
        },
        settings.jwt_secret_key.get_secret_value(),
        algorithm=settings.jwt_algorithm,
    )

    with pytest.raises(InvalidAccessTokenError):
        decode_access_token(token)


def test_decode_access_token_rejects_empty_subject() -> None:
    token = create_access_token("")

    with pytest.raises(InvalidAccessTokenError):
        decode_access_token(token)
