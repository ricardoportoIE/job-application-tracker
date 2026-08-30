import uuid
from datetime import UTC, datetime
from decimal import Decimal
from types import SimpleNamespace

import pytest
from pydantic import ValidationError

from app.models.enums import ApplicationStatus, JobSource, WorkModel
from app.schemas.application import (
    ApplicationCreate,
    ApplicationRead,
    ApplicationUpdate,
)


def test_application_create_with_valid_data() -> None:
    company_id = uuid.uuid4()

    application = ApplicationCreate(
        company_id=company_id,
        position="Backend Engineer",
        status=ApplicationStatus.APPLIED,
        source=JobSource.LINKEDIN,
        work_model=WorkModel.HYBRID,
        location="Dublin, Ireland",
        salary_min=Decimal("55000.00"),
        salary_max=Decimal("65000.00"),
        currency="EUR",
    )

    assert application.company_id == company_id
    assert application.position == "Backend Engineer"
    assert application.status is ApplicationStatus.APPLIED
    assert application.source is JobSource.LINKEDIN
    assert application.work_model is WorkModel.HYBRID
    assert application.salary_min == Decimal("55000.00")
    assert application.salary_max == Decimal("65000.00")
    assert application.currency == "EUR"


def test_application_create_defaults_to_saved_status() -> None:
    application = ApplicationCreate(
        company_id=uuid.uuid4(),
        position="Backend Engineer",
    )

    assert application.status is ApplicationStatus.SAVED


def test_application_create_rejects_whitespace_only_position() -> None:
    with pytest.raises(ValidationError):
        ApplicationCreate(
            company_id=uuid.uuid4(),
            position="   ",
        )


def test_application_create_strips_whitespace() -> None:
    application = ApplicationCreate(
        company_id=uuid.uuid4(),
        position="  Backend Engineer  ",
        location="  Dublin, Ireland  ",
        currency=" EUR ",
    )

    assert application.position == "Backend Engineer"
    assert application.location == "Dublin, Ireland"
    assert application.currency == "EUR"


def test_application_create_rejects_negative_salary() -> None:
    with pytest.raises(ValidationError):
        ApplicationCreate(
            company_id=uuid.uuid4(),
            position="Backend Engineer",
            salary_min=Decimal("-1.00"),
        )


def test_application_read_from_attributes() -> None:
    application_id = uuid.uuid4()
    user_id = uuid.uuid4()
    company_id = uuid.uuid4()
    now = datetime.now(UTC)

    application = SimpleNamespace(
        id=application_id,
        user_id=user_id,
        company_id=company_id,
        position="Backend Engineer",
        status=ApplicationStatus.APPLIED,
        source=JobSource.LINKEDIN,
        work_model=WorkModel.HYBRID,
        location="Dublin, Ireland",
        job_url=None,
        salary_min=Decimal("55000.00"),
        salary_max=Decimal("65000.00"),
        currency="EUR",
        applied_at=now,
        notes=None,
        created_at=now,
        updated_at=now,
    )

    result = ApplicationRead.model_validate(application)

    assert result.id == application_id
    assert result.user_id == user_id
    assert result.company_id == company_id
    assert result.position == "Backend Engineer"
    assert result.status is ApplicationStatus.APPLIED
    assert result.salary_min == Decimal("55000.00")
    assert result.created_at == now


def test_application_update_contains_only_provided_fields() -> None:
    update = ApplicationUpdate(
        status=ApplicationStatus.INTERVIEW,
    )

    assert update.model_dump(exclude_unset=True) == {
        "status": ApplicationStatus.INTERVIEW,
    }


def test_application_update_allows_explicit_null_for_optional_field() -> None:
    update = ApplicationUpdate(notes=None)

    assert update.model_dump(exclude_unset=True) == {
        "notes": None,
    }


@pytest.mark.parametrize(
    "field_name",
    [
        "company_id",
        "position",
        "status",
    ],
)
def test_application_update_rejects_null_required_fields(
    field_name: str,
) -> None:
    with pytest.raises(ValidationError):
        ApplicationUpdate.model_validate(
            {
                field_name: None,
            }
        )


def test_application_update_rejects_whitespace_only_position() -> None:
    with pytest.raises(ValidationError):
        ApplicationUpdate(
            position="   ",
        )


def test_application_update_strips_whitespace() -> None:
    update = ApplicationUpdate(
        position="  Senior Backend Engineer  ",
        location="  Cork, Ireland  ",
        currency=" EUR ",
    )

    assert update.position == "Senior Backend Engineer"
    assert update.location == "Cork, Ireland"
    assert update.currency == "EUR"


def test_application_update_rejects_negative_salary() -> None:
    with pytest.raises(ValidationError):
        ApplicationUpdate(
            salary_max=Decimal("-1.00"),
        )
