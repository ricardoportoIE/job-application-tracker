import pytest
from pydantic import ValidationError

from app.schemas.auth import LoginRequest, TokenResponse


def test_login_request_with_valid_data() -> None:
    login = LoginRequest(
        email="user@example.com",
        password="secret-password",
    )

    assert str(login.email) == "user@example.com"
    assert login.password == "secret-password"


def test_login_request_rejects_invalid_email() -> None:
    with pytest.raises(ValidationError):
        LoginRequest(
            email="not-an-email",
            password="secret-password",
        )


def test_login_request_rejects_empty_password() -> None:
    with pytest.raises(ValidationError):
        LoginRequest(
            email="user@example.com",
            password="",
        )


def test_login_request_does_not_strip_password_whitespace() -> None:
    login = LoginRequest(
        email="user@example.com",
        password="  secret-password  ",
    )

    assert login.password == "  secret-password  "


def test_login_request_rejects_extra_fields() -> None:
    with pytest.raises(ValidationError):
        LoginRequest.model_validate(
            {
                "email": "user@example.com",
                "password": "secret-password",
                "remember_me": True,
            }
        )


def test_token_response_with_valid_data() -> None:
    token = TokenResponse(
        access_token="example.jwt.token",
    )

    assert token.access_token == "example.jwt.token"
    assert token.token_type == "bearer"


def test_token_response_accepts_explicit_bearer_type() -> None:
    token = TokenResponse(
        access_token="example.jwt.token",
        token_type="bearer",
    )

    assert token.token_type == "bearer"


def test_token_response_rejects_empty_access_token() -> None:
    with pytest.raises(ValidationError):
        TokenResponse(
            access_token="",
        )


def test_token_response_rejects_invalid_token_type() -> None:
    with pytest.raises(ValidationError):
        TokenResponse.model_validate(
            {
                "access_token": "example.jwt.token",
                "token_type": "basic",
            }
        )


def test_token_response_rejects_extra_fields() -> None:
    with pytest.raises(ValidationError):
        TokenResponse.model_validate(
            {
                "access_token": "example.jwt.token",
                "token_type": "bearer",
                "refresh_token": "unexpected-token",
            }
        )
