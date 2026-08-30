import uuid
from datetime import UTC, datetime
from types import SimpleNamespace

import pytest
from pydantic import ValidationError

from app.schemas.user import UserCreate, UserRead, UserUpdate


def test_user_create_with_valid_data() -> None:
    user = UserCreate(
        email="ricardo@example.com",
        password="secure-password-123",
    )

    assert str(user.email) == "ricardo@example.com"
    assert user.password == "secure-password-123"


def test_user_create_rejects_invalid_email() -> None:
    with pytest.raises(ValidationError):
        UserCreate(
            email="not-an-email",
            password="secure-password-123",
        )


def test_user_create_rejects_short_password() -> None:
    with pytest.raises(ValidationError):
        UserCreate(
            email="ricardo@example.com",
            password="short",
        )


def test_user_create_rejects_extra_fields() -> None:
    with pytest.raises(ValidationError):
        UserCreate.model_validate(
            {
                "email": "ricardo@example.com",
                "password": "secure-password-123",
                "is_active": False,
            }
        )


def test_user_create_rejects_password_hash() -> None:
    with pytest.raises(ValidationError):
        UserCreate.model_validate(
            {
                "email": "ricardo@example.com",
                "password": "secure-password-123",
                "password_hash": "should-not-be-accepted",
            }
        )


def test_user_update_contains_only_provided_fields() -> None:
    update = UserUpdate(
        email="new-email@example.com",
    )

    assert update.model_dump(exclude_unset=True) == {
        "email": "new-email@example.com",
    }


def test_user_update_allows_password_change() -> None:
    update = UserUpdate(
        password="new-secure-password",
    )

    assert update.model_dump(exclude_unset=True) == {
        "password": "new-secure-password",
    }


@pytest.mark.parametrize(
    "field_name",
    [
        "email",
        "password",
    ],
)
def test_user_update_rejects_null_fields(
    field_name: str,
) -> None:
    with pytest.raises(ValidationError):
        UserUpdate.model_validate(
            {
                field_name: None,
            }
        )


def test_user_update_rejects_protected_fields() -> None:
    with pytest.raises(ValidationError):
        UserUpdate.model_validate(
            {
                "is_active": False,
            }
        )


def test_user_read_from_attributes() -> None:
    user_id = uuid.uuid4()
    now = datetime.now(UTC)

    user = SimpleNamespace(
        id=user_id,
        email="ricardo@example.com",
        password_hash="secret-database-hash",
        is_active=True,
        created_at=now,
        updated_at=now,
    )

    result = UserRead.model_validate(user)

    assert result.id == user_id
    assert str(result.email) == "ricardo@example.com"
    assert result.is_active is True
    assert result.created_at == now
    assert result.updated_at == now


def test_user_read_does_not_expose_password_hash() -> None:
    now = datetime.now(UTC)

    user = SimpleNamespace(
        id=uuid.uuid4(),
        email="ricardo@example.com",
        password_hash="secret-database-hash",
        is_active=True,
        created_at=now,
        updated_at=now,
    )

    result = UserRead.model_validate(user)
    serialized = result.model_dump()

    assert "password" not in serialized
    assert "password_hash" not in serialized
