import uuid
from datetime import UTC, datetime, timedelta
from types import SimpleNamespace

import pytest
from pydantic import ValidationError

from app.models.enums import ApplicationEventType, ApplicationStatus
from app.schemas.application_event import (
    ApplicationEventCreate,
    ApplicationEventRead,
    ApplicationEventUpdate,
)


def test_application_event_create_with_valid_data() -> None:
    occurred_at = datetime.now(UTC)

    event = ApplicationEventCreate(
        event_type=ApplicationEventType.STATUS_CHANGED,
        from_status=ApplicationStatus.SAVED,
        to_status=ApplicationStatus.APPLIED,
        occurred_at=occurred_at,
        notes="Application submitted.",
    )

    assert event.event_type is ApplicationEventType.STATUS_CHANGED
    assert event.from_status is ApplicationStatus.SAVED
    assert event.to_status is ApplicationStatus.APPLIED
    assert event.occurred_at == occurred_at
    assert event.notes == "Application submitted."


def test_application_event_create_sets_default_occurred_at() -> None:
    before = datetime.now(UTC)

    event = ApplicationEventCreate(
        event_type=ApplicationEventType.CREATED,
    )

    after = datetime.now(UTC)

    assert before <= event.occurred_at <= after


def test_application_event_create_allows_null_statuses() -> None:
    event = ApplicationEventCreate(
        event_type=ApplicationEventType.NOTE_ADDED,
        from_status=None,
        to_status=None,
        notes="Recruiter contacted me.",
    )

    assert event.from_status is None
    assert event.to_status is None


def test_application_event_create_strips_whitespace_from_notes() -> None:
    event = ApplicationEventCreate(
        event_type=ApplicationEventType.NOTE_ADDED,
        notes="  Follow up next week.  ",
    )

    assert event.notes == "Follow up next week."


def test_application_event_update_contains_only_provided_fields() -> None:
    update = ApplicationEventUpdate(
        notes="Interview moved to Friday.",
    )

    assert update.model_dump(exclude_unset=True) == {
        "notes": "Interview moved to Friday.",
    }


def test_application_event_update_allows_explicit_null_notes() -> None:
    update = ApplicationEventUpdate(
        notes=None,
    )

    assert update.model_dump(exclude_unset=True) == {
        "notes": None,
    }


def test_application_event_update_allows_occurred_at_change() -> None:
    occurred_at = datetime.now(UTC) - timedelta(days=1)

    update = ApplicationEventUpdate(
        occurred_at=occurred_at,
    )

    assert update.model_dump(exclude_unset=True) == {
        "occurred_at": occurred_at,
    }


def test_application_event_update_rejects_null_occurred_at() -> None:
    with pytest.raises(ValidationError):
        ApplicationEventUpdate(
            occurred_at=None,
        )


def test_application_event_update_distinguishes_missing_from_null() -> None:
    missing = ApplicationEventUpdate()
    explicit_null = ApplicationEventUpdate(notes=None)

    assert missing.model_dump(exclude_unset=True) == {}
    assert explicit_null.model_dump(exclude_unset=True) == {
        "notes": None,
    }


def test_application_event_update_rejects_immutable_event_fields() -> None:
    with pytest.raises(ValidationError):
        ApplicationEventUpdate.model_validate(
            {
                "event_type": ApplicationEventType.OFFER_RECEIVED,
            }
        )


def test_application_event_read_from_attributes() -> None:
    event_id = uuid.uuid4()
    application_id = uuid.uuid4()
    occurred_at = datetime.now(UTC) - timedelta(hours=2)
    created_at = datetime.now(UTC)

    event = SimpleNamespace(
        id=event_id,
        application_id=application_id,
        event_type=ApplicationEventType.STATUS_CHANGED,
        from_status=ApplicationStatus.APPLIED,
        to_status=ApplicationStatus.SCREENING,
        occurred_at=occurred_at,
        notes="Moved to screening.",
        created_at=created_at,
    )

    result = ApplicationEventRead.model_validate(event)

    assert result.id == event_id
    assert result.application_id == application_id
    assert result.event_type is ApplicationEventType.STATUS_CHANGED
    assert result.from_status is ApplicationStatus.APPLIED
    assert result.to_status is ApplicationStatus.SCREENING
    assert result.occurred_at == occurred_at
    assert result.notes == "Moved to screening."
    assert result.created_at == created_at
