from collections.abc import Generator
from datetime import UTC, datetime, timedelta
from uuid import UUID, uuid4

import pytest
from sqlalchemy import delete, select
from sqlalchemy.orm import Session

from app.db.session import SessionLocal
from app.models.application import Application
from app.models.application_event import ApplicationEvent
from app.models.company import Company
from app.models.enums import (
    ApplicationEventType,
    ApplicationStatus,
)
from app.models.user import User
from app.schemas.application import ApplicationCreate
from app.schemas.application_event import (
    ApplicationEventCreate,
    ApplicationEventUpdate,
)
from app.schemas.company import CompanyCreate
from app.schemas.user import UserCreate
from app.services.application import (
    ApplicationNotFoundError,
    ApplicationService,
)
from app.services.application_event import (
    ApplicationEventImmutableError,
    ApplicationEventNotFoundError,
    ApplicationEventService,
    ApplicationEventStatusFieldsNotAllowedError,
    ApplicationEventTypeNotAllowedError,
)
from app.services.company import CompanyService
from app.services.user import UserService

TEST_EMAIL_PREFIX = "application-event-service-test-"


@pytest.fixture
def db_session() -> Generator[Session]:
    with SessionLocal() as session:
        yield session

        session.rollback()

        user_ids = list(
            session.scalars(
                select(User.id).where(
                    User.email.like(f"{TEST_EMAIL_PREFIX}%@example.com")
                )
            )
        )

        if user_ids:
            session.execute(
                delete(Application).where(Application.user_id.in_(user_ids))
            )

            session.execute(delete(Company).where(Company.user_id.in_(user_ids)))

            session.execute(delete(User).where(User.id.in_(user_ids)))

        session.commit()


def make_test_email() -> str:
    return f"{TEST_EMAIL_PREFIX}{uuid4()}@example.com"


def create_test_user(
    session: Session,
) -> User:
    return UserService.create(
        session,
        UserCreate(
            email=make_test_email(),
            password="secure-password-123",
        ),
    )


def create_test_company(
    session: Session,
    user_id: UUID,
    name: str = "Stripe",
) -> Company:
    return CompanyService.create(
        session,
        user_id,
        CompanyCreate(
            name=name,
        ),
    )


def create_test_application(
    session: Session,
    user_id: UUID,
    company_id: UUID,
    position: str = "Backend Engineer",
) -> Application:
    return ApplicationService.create(
        session,
        user_id,
        ApplicationCreate(
            company_id=company_id,
            position=position,
        ),
    )


def get_created_event(
    session: Session,
    application_id: UUID,
) -> ApplicationEvent:
    event = session.scalar(
        select(ApplicationEvent).where(
            ApplicationEvent.application_id == application_id,
            ApplicationEvent.event_type == ApplicationEventType.CREATED,
        )
    )

    if event is None:
        raise RuntimeError("CREATED event was not found")

    return event


def test_create_manual_event_persists_event(
    db_session: Session,
) -> None:
    user = create_test_user(db_session)
    company = create_test_company(
        db_session,
        user.id,
    )
    application = create_test_application(
        db_session,
        user.id,
        company.id,
    )

    occurred_at = datetime.now(UTC)

    event = ApplicationEventService.create(
        db_session,
        user.id,
        application.id,
        ApplicationEventCreate(
            event_type=ApplicationEventType.INTERVIEW_SCHEDULED,
            occurred_at=occurred_at,
            notes="Technical interview scheduled.",
        ),
    )

    assert event.id is not None
    assert event.application_id == application.id
    assert event.event_type is ApplicationEventType.INTERVIEW_SCHEDULED
    assert event.from_status is None
    assert event.to_status is None
    assert event.occurred_at == occurred_at
    assert event.notes == "Technical interview scheduled."

    event_id = event.id

    db_session.expire_all()

    persisted_event = db_session.get(
        ApplicationEvent,
        event_id,
    )

    assert persisted_event is not None
    assert persisted_event.application_id == application.id


@pytest.mark.parametrize(
    "event_type",
    [
        ApplicationEventType.CREATED,
        ApplicationEventType.STATUS_CHANGED,
    ],
)
def test_create_rejects_automatic_event_types(
    db_session: Session,
    event_type: ApplicationEventType,
) -> None:
    user = create_test_user(db_session)
    company = create_test_company(
        db_session,
        user.id,
    )
    application = create_test_application(
        db_session,
        user.id,
        company.id,
    )

    with pytest.raises(ApplicationEventTypeNotAllowedError):
        ApplicationEventService.create(
            db_session,
            user.id,
            application.id,
            ApplicationEventCreate(
                event_type=event_type,
            ),
        )


def test_create_rejects_manual_status_fields(
    db_session: Session,
) -> None:
    user = create_test_user(db_session)
    company = create_test_company(
        db_session,
        user.id,
    )
    application = create_test_application(
        db_session,
        user.id,
        company.id,
    )

    with pytest.raises(ApplicationEventStatusFieldsNotAllowedError):
        ApplicationEventService.create(
            db_session,
            user.id,
            application.id,
            ApplicationEventCreate(
                event_type=ApplicationEventType.NOTE_ADDED,
                from_status=ApplicationStatus.SAVED,
                to_status=ApplicationStatus.APPLIED,
                notes="Attempted fake status transition.",
            ),
        )


def test_create_rejects_another_users_application(
    db_session: Session,
) -> None:
    owner = create_test_user(db_session)
    other_user = create_test_user(db_session)

    company = create_test_company(
        db_session,
        owner.id,
    )
    application = create_test_application(
        db_session,
        owner.id,
        company.id,
    )

    with pytest.raises(ApplicationNotFoundError):
        ApplicationEventService.create(
            db_session,
            other_user.id,
            application.id,
            ApplicationEventCreate(
                event_type=ApplicationEventType.NOTE_ADDED,
                notes="Not allowed.",
            ),
        )


def test_list_for_application_returns_timeline_in_descending_order(
    db_session: Session,
) -> None:
    user = create_test_user(db_session)
    company = create_test_company(
        db_session,
        user.id,
    )
    application = create_test_application(
        db_session,
        user.id,
        company.id,
    )

    now = datetime.now(UTC)

    older_event = ApplicationEventService.create(
        db_session,
        user.id,
        application.id,
        ApplicationEventCreate(
            event_type=ApplicationEventType.NOTE_ADDED,
            occurred_at=now + timedelta(hours=1),
            notes="Older manual event.",
        ),
    )

    newer_event = ApplicationEventService.create(
        db_session,
        user.id,
        application.id,
        ApplicationEventCreate(
            event_type=ApplicationEventType.INTERVIEW_SCHEDULED,
            occurred_at=now + timedelta(hours=2),
            notes="Newer manual event.",
        ),
    )

    events = ApplicationEventService.list_for_application(
        db_session,
        user.id,
        application.id,
    )

    event_ids = [event.id for event in events]

    assert event_ids.index(newer_event.id) < event_ids.index(older_event.id)


def test_list_for_application_rejects_another_users_application(
    db_session: Session,
) -> None:
    owner = create_test_user(db_session)
    other_user = create_test_user(db_session)

    company = create_test_company(
        db_session,
        owner.id,
    )
    application = create_test_application(
        db_session,
        owner.id,
        company.id,
    )

    with pytest.raises(ApplicationNotFoundError):
        ApplicationEventService.list_for_application(
            db_session,
            other_user.id,
            application.id,
        )


def test_get_returns_event_from_owned_application(
    db_session: Session,
) -> None:
    user = create_test_user(db_session)
    company = create_test_company(
        db_session,
        user.id,
    )
    application = create_test_application(
        db_session,
        user.id,
        company.id,
    )

    event = ApplicationEventService.create(
        db_session,
        user.id,
        application.id,
        ApplicationEventCreate(
            event_type=ApplicationEventType.NOTE_ADDED,
            notes="Recruiter called.",
        ),
    )

    result = ApplicationEventService.get(
        db_session,
        user.id,
        application.id,
        event.id,
    )

    assert result.id == event.id
    assert result.application_id == application.id


def test_get_rejects_event_from_different_application(
    db_session: Session,
) -> None:
    user = create_test_user(db_session)

    first_company = create_test_company(
        db_session,
        user.id,
        name="Stripe",
    )
    second_company = create_test_company(
        db_session,
        user.id,
        name="GitHub",
    )

    first_application = create_test_application(
        db_session,
        user.id,
        first_company.id,
        position="Backend Engineer",
    )
    second_application = create_test_application(
        db_session,
        user.id,
        second_company.id,
        position="Platform Engineer",
    )

    event = ApplicationEventService.create(
        db_session,
        user.id,
        first_application.id,
        ApplicationEventCreate(
            event_type=ApplicationEventType.NOTE_ADDED,
            notes="First application event.",
        ),
    )

    with pytest.raises(ApplicationEventNotFoundError):
        ApplicationEventService.get(
            db_session,
            user.id,
            second_application.id,
            event.id,
        )


def test_update_manual_event_changes_allowed_fields(
    db_session: Session,
) -> None:
    user = create_test_user(db_session)
    company = create_test_company(
        db_session,
        user.id,
    )
    application = create_test_application(
        db_session,
        user.id,
        company.id,
    )

    event = ApplicationEventService.create(
        db_session,
        user.id,
        application.id,
        ApplicationEventCreate(
            event_type=ApplicationEventType.INTERVIEW_SCHEDULED,
            notes="Interview at 10:00.",
        ),
    )

    new_occurred_at = datetime.now(UTC) + timedelta(days=1)

    updated_event = ApplicationEventService.update(
        db_session,
        user.id,
        application.id,
        event.id,
        ApplicationEventUpdate(
            occurred_at=new_occurred_at,
            notes="Interview moved to 15:00.",
        ),
    )

    assert updated_event.occurred_at == new_occurred_at
    assert updated_event.notes == "Interview moved to 15:00."

    # Campos estruturais permanecem imutáveis.
    assert updated_event.event_type is ApplicationEventType.INTERVIEW_SCHEDULED
    assert updated_event.from_status is None
    assert updated_event.to_status is None


def test_update_manual_event_allows_clearing_notes(
    db_session: Session,
) -> None:
    user = create_test_user(db_session)
    company = create_test_company(
        db_session,
        user.id,
    )
    application = create_test_application(
        db_session,
        user.id,
        company.id,
    )

    event = ApplicationEventService.create(
        db_session,
        user.id,
        application.id,
        ApplicationEventCreate(
            event_type=ApplicationEventType.NOTE_ADDED,
            notes="Temporary note.",
        ),
    )

    updated_event = ApplicationEventService.update(
        db_session,
        user.id,
        application.id,
        event.id,
        ApplicationEventUpdate(
            notes=None,
        ),
    )

    assert updated_event.notes is None


def test_update_rejects_automatic_event(
    db_session: Session,
) -> None:
    user = create_test_user(db_session)
    company = create_test_company(
        db_session,
        user.id,
    )
    application = create_test_application(
        db_session,
        user.id,
        company.id,
    )

    created_event = get_created_event(
        db_session,
        application.id,
    )

    with pytest.raises(ApplicationEventImmutableError):
        ApplicationEventService.update(
            db_session,
            user.id,
            application.id,
            created_event.id,
            ApplicationEventUpdate(
                notes="Trying to rewrite history.",
            ),
        )


def test_update_rejects_another_users_application(
    db_session: Session,
) -> None:
    owner = create_test_user(db_session)
    other_user = create_test_user(db_session)

    company = create_test_company(
        db_session,
        owner.id,
    )
    application = create_test_application(
        db_session,
        owner.id,
        company.id,
    )

    event = ApplicationEventService.create(
        db_session,
        owner.id,
        application.id,
        ApplicationEventCreate(
            event_type=ApplicationEventType.NOTE_ADDED,
            notes="Owner note.",
        ),
    )

    with pytest.raises(ApplicationNotFoundError):
        ApplicationEventService.update(
            db_session,
            other_user.id,
            application.id,
            event.id,
            ApplicationEventUpdate(
                notes="Not allowed.",
            ),
        )


def test_delete_manual_event_removes_event(
    db_session: Session,
) -> None:
    user = create_test_user(db_session)
    company = create_test_company(
        db_session,
        user.id,
    )
    application = create_test_application(
        db_session,
        user.id,
        company.id,
    )

    event = ApplicationEventService.create(
        db_session,
        user.id,
        application.id,
        ApplicationEventCreate(
            event_type=ApplicationEventType.NOTE_ADDED,
            notes="Temporary note.",
        ),
    )

    event_id = event.id

    ApplicationEventService.delete(
        db_session,
        user.id,
        application.id,
        event_id,
    )

    assert (
        db_session.get(
            ApplicationEvent,
            event_id,
        )
        is None
    )


def test_delete_rejects_automatic_event(
    db_session: Session,
) -> None:
    user = create_test_user(db_session)
    company = create_test_company(
        db_session,
        user.id,
    )
    application = create_test_application(
        db_session,
        user.id,
        company.id,
    )

    created_event = get_created_event(
        db_session,
        application.id,
    )

    with pytest.raises(ApplicationEventImmutableError):
        ApplicationEventService.delete(
            db_session,
            user.id,
            application.id,
            created_event.id,
        )

    assert (
        db_session.get(
            ApplicationEvent,
            created_event.id,
        )
        is not None
    )


def test_delete_rejects_another_users_application(
    db_session: Session,
) -> None:
    owner = create_test_user(db_session)
    other_user = create_test_user(db_session)

    company = create_test_company(
        db_session,
        owner.id,
    )
    application = create_test_application(
        db_session,
        owner.id,
        company.id,
    )

    event = ApplicationEventService.create(
        db_session,
        owner.id,
        application.id,
        ApplicationEventCreate(
            event_type=ApplicationEventType.NOTE_ADDED,
            notes="Owner event.",
        ),
    )

    with pytest.raises(ApplicationNotFoundError):
        ApplicationEventService.delete(
            db_session,
            other_user.id,
            application.id,
            event.id,
        )

    assert (
        db_session.get(
            ApplicationEvent,
            event.id,
        )
        is not None
    )
