from collections.abc import Generator
from uuid import uuid4

import pytest
from sqlalchemy import delete
from sqlalchemy.orm import Session

from app.db.session import SessionLocal
from app.models.user import User
from app.schemas.user import UserCreate
from app.services.auth import (
    AuthService,
    InactiveUserError,
    InvalidCredentialsError,
)
from app.services.user import UserService

TEST_EMAIL_PREFIX = "auth-service-test-"


@pytest.fixture
def db_session() -> Generator[Session]:
    with SessionLocal() as session:
        yield session

        session.rollback()

        session.execute(
            delete(User).where(User.email.like(f"{TEST_EMAIL_PREFIX}%@example.com"))
        )
        session.commit()


def make_test_email() -> str:
    return f"{TEST_EMAIL_PREFIX}{uuid4()}@example.com"


def test_authenticate_returns_user_with_valid_credentials(
    db_session: Session,
) -> None:
    email = make_test_email()
    password = "secure-password-123"

    created_user = UserService.create(
        db_session,
        UserCreate(
            email=email,
            password=password,
        ),
    )

    authenticated_user = AuthService.authenticate(
        db_session,
        email,
        password,
    )

    assert authenticated_user.id == created_user.id
    assert authenticated_user.email == email
    assert authenticated_user.is_active is True


def test_authenticate_normalizes_email(
    db_session: Session,
) -> None:
    email = make_test_email()
    password = "secure-password-123"

    created_user = UserService.create(
        db_session,
        UserCreate(
            email=email,
            password=password,
        ),
    )

    authenticated_user = AuthService.authenticate(
        db_session,
        f"  {email.upper()}  ",
        password,
    )

    assert authenticated_user.id == created_user.id


def test_authenticate_rejects_incorrect_password(
    db_session: Session,
) -> None:
    email = make_test_email()

    UserService.create(
        db_session,
        UserCreate(
            email=email,
            password="correct-password",
        ),
    )

    with pytest.raises(InvalidCredentialsError):
        AuthService.authenticate(
            db_session,
            email,
            "wrong-password",
        )


def test_authenticate_rejects_nonexistent_user(
    db_session: Session,
) -> None:
    with pytest.raises(InvalidCredentialsError):
        AuthService.authenticate(
            db_session,
            make_test_email(),
            "secure-password-123",
        )


def test_authenticate_rejects_inactive_user(
    db_session: Session,
) -> None:
    email = make_test_email()
    password = "secure-password-123"

    user = UserService.create(
        db_session,
        UserCreate(
            email=email,
            password=password,
        ),
    )

    user.is_active = False
    db_session.commit()

    with pytest.raises(InactiveUserError):
        AuthService.authenticate(
            db_session,
            email,
            password,
        )
