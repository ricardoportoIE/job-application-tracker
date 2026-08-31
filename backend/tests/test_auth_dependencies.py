from collections.abc import Generator
from datetime import timedelta
from uuid import uuid4

import pytest
from fastapi import HTTPException
from fastapi.security import HTTPAuthorizationCredentials
from sqlalchemy import delete
from sqlalchemy.orm import Session

from app.api.dependencies import get_current_user
from app.core.security import create_access_token
from app.db.session import SessionLocal
from app.models.user import User
from app.schemas.user import UserCreate
from app.services.user import UserService

TEST_EMAIL_PREFIX = "auth-dependency-test-"


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


def make_credentials(token: str) -> HTTPAuthorizationCredentials:
    return HTTPAuthorizationCredentials(
        scheme="Bearer",
        credentials=token,
    )


def test_get_current_user_returns_authenticated_user(
    db_session: Session,
) -> None:
    user = UserService.create(
        db_session,
        UserCreate(
            email=make_test_email(),
            password="secure-password-123",
        ),
    )

    token = create_access_token(
        subject=str(user.id),
    )

    current_user = get_current_user(
        credentials=make_credentials(token),
        session=db_session,
    )

    assert current_user.id == user.id
    assert current_user.email == user.email
    assert current_user.is_active is True


def test_get_current_user_rejects_missing_credentials(
    db_session: Session,
) -> None:
    with pytest.raises(HTTPException) as exc_info:
        get_current_user(
            credentials=None,
            session=db_session,
        )

    assert exc_info.value.status_code == 401
    assert exc_info.value.detail == "Could not validate credentials"
    assert exc_info.value.headers == {
        "WWW-Authenticate": "Bearer",
    }


def test_get_current_user_rejects_expired_token(
    db_session: Session,
) -> None:
    token = create_access_token(
        subject=str(uuid4()),
        expires_delta=timedelta(seconds=-1),
    )

    with pytest.raises(HTTPException) as exc_info:
        get_current_user(
            credentials=make_credentials(token),
            session=db_session,
        )

    assert exc_info.value.status_code == 401
    assert exc_info.value.detail == "Could not validate credentials"


def test_get_current_user_rejects_malformed_token(
    db_session: Session,
) -> None:
    with pytest.raises(HTTPException) as exc_info:
        get_current_user(
            credentials=make_credentials("not-a-valid-jwt"),
            session=db_session,
        )

    assert exc_info.value.status_code == 401
    assert exc_info.value.detail == "Could not validate credentials"


def test_get_current_user_rejects_invalid_uuid_subject(
    db_session: Session,
) -> None:
    token = create_access_token(
        subject="not-a-valid-uuid",
    )

    with pytest.raises(HTTPException) as exc_info:
        get_current_user(
            credentials=make_credentials(token),
            session=db_session,
        )

    assert exc_info.value.status_code == 401
    assert exc_info.value.detail == "Could not validate credentials"


def test_get_current_user_rejects_nonexistent_user(
    db_session: Session,
) -> None:
    token = create_access_token(
        subject=str(uuid4()),
    )

    with pytest.raises(HTTPException) as exc_info:
        get_current_user(
            credentials=make_credentials(token),
            session=db_session,
        )

    assert exc_info.value.status_code == 401
    assert exc_info.value.detail == "Could not validate credentials"


def test_get_current_user_rejects_inactive_user(
    db_session: Session,
) -> None:
    user = UserService.create(
        db_session,
        UserCreate(
            email=make_test_email(),
            password="secure-password-123",
        ),
    )

    user.is_active = False
    db_session.commit()

    token = create_access_token(
        subject=str(user.id),
    )

    with pytest.raises(HTTPException) as exc_info:
        get_current_user(
            credentials=make_credentials(token),
            session=db_session,
        )

    assert exc_info.value.status_code == 403
    assert exc_info.value.detail == "Inactive user"
