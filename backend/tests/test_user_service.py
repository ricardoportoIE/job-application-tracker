from collections.abc import Generator
from uuid import uuid4

import pytest
from sqlalchemy import delete, func, select
from sqlalchemy.orm import Session

from app.core.security import verify_password
from app.db.session import SessionLocal
from app.models.user import User
from app.schemas.user import UserCreate
from app.services.user import UserAlreadyExistsError, UserService

TEST_EMAIL_PREFIX = "user-service-test-"


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


def test_create_user_persists_user_with_hashed_password(
    db_session: Session,
) -> None:
    email = make_test_email()

    data = UserCreate(
        email=email.upper(),
        password="secure-password-123",
    )

    user = UserService.create(
        db_session,
        data,
    )

    assert user.id is not None
    assert user.email == email
    assert user.password_hash != data.password
    assert verify_password(data.password, user.password_hash) is True
    assert user.is_active is True

    db_session.expire_all()

    persisted_user = db_session.get(User, user.id)

    assert persisted_user is not None
    assert persisted_user.email == email
    assert persisted_user.password_hash == user.password_hash


def test_get_by_email_finds_user_with_normalized_lookup(
    db_session: Session,
) -> None:
    email = make_test_email()

    created_user = UserService.create(
        db_session,
        UserCreate(
            email=email,
            password="secure-password-123",
        ),
    )

    found_user = UserService.get_by_email(
        db_session,
        f"  {email.upper()}  ",
    )

    assert found_user is not None
    assert found_user.id == created_user.id
    assert found_user.email == email


def test_get_by_email_returns_none_when_user_does_not_exist(
    db_session: Session,
) -> None:
    result = UserService.get_by_email(
        db_session,
        make_test_email(),
    )

    assert result is None


def test_create_user_rejects_duplicate_email(
    db_session: Session,
) -> None:
    email = make_test_email()

    UserService.create(
        db_session,
        UserCreate(
            email=email,
            password="secure-password-123",
        ),
    )

    with pytest.raises(UserAlreadyExistsError):
        UserService.create(
            db_session,
            UserCreate(
                email=email.upper(),
                password="another-secure-password",
            ),
        )

    user_count = db_session.scalar(
        select(func.count()).select_from(User).where(User.email == email)
    )

    assert user_count == 1
