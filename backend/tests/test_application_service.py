from collections.abc import Generator
from datetime import UTC, datetime
from decimal import Decimal
from uuid import UUID, uuid4

import pytest
from sqlalchemy import delete, select
from sqlalchemy.orm import Session

from app.db.session import SessionLocal
from app.models.application import Application
from app.models.application_event import ApplicationEvent
from app.models.company import Company
from app.models.enums import ApplicationEventType, ApplicationStatus
from app.models.user import User
from app.schemas.application import ApplicationCreate, ApplicationUpdate
from app.schemas.company import CompanyCreate
from app.schemas.user import UserCreate
from app.services.application import (
    ApplicationNotFoundError,
    ApplicationService,
    InvalidSalaryRangeError,
)
from app.services.company import CompanyNotFoundError, CompanyService
from app.services.user import UserService

TEST_EMAIL_PREFIX = "application-service-test-"


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
    *,
    position: str = "Backend Engineer",
    status: ApplicationStatus = ApplicationStatus.SAVED,
    salary_min: Decimal | None = None,
    salary_max: Decimal | None = None,
    currency: str | None = None,
) -> Application:
    return ApplicationService.create(
        session,
        user_id,
        ApplicationCreate(
            company_id=company_id,
            position=position,
            status=status,
            salary_min=salary_min,
            salary_max=salary_max,
            currency=currency,
        ),
    )


def test_create_application_persists_owned_application(
    db_session: Session,
) -> None:
    user = create_test_user(db_session)
    company = create_test_company(
        db_session,
        user.id,
    )

    application = ApplicationService.create(
        db_session,
        user.id,
        ApplicationCreate(
            company_id=company.id,
            position="Backend Engineer",
            status=ApplicationStatus.SAVED,
            location="Dublin, Ireland",
        ),
    )

    assert application.id is not None
    assert application.user_id == user.id
    assert application.company_id == company.id
    assert application.position == "Backend Engineer"
    assert application.status is ApplicationStatus.SAVED
    assert application.location == "Dublin, Ireland"

    application_id = application.id

    db_session.expire_all()

    persisted_application = db_session.get(
        Application,
        application_id,
    )

    assert persisted_application is not None
    assert persisted_application.user_id == user.id
    assert persisted_application.company_id == company.id


def test_create_application_creates_created_event(
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

    events = list(
        db_session.scalars(
            select(ApplicationEvent).where(
                ApplicationEvent.application_id == application.id
            )
        )
    )

    assert len(events) == 1

    event = events[0]

    assert event.event_type is ApplicationEventType.CREATED
    assert event.from_status is None
    assert event.to_status is ApplicationStatus.SAVED


def test_create_application_rejects_another_users_company(
    db_session: Session,
) -> None:
    owner = create_test_user(db_session)
    other_user = create_test_user(db_session)

    company = create_test_company(
        db_session,
        owner.id,
    )

    with pytest.raises(CompanyNotFoundError):
        ApplicationService.create(
            db_session,
            other_user.id,
            ApplicationCreate(
                company_id=company.id,
                position="Backend Engineer",
            ),
        )

    application_count = db_session.scalar(
        select(Application)
        .where(Application.user_id == other_user.id)
        .with_only_columns(
            Application.id,
        )
        .limit(1)
    )

    assert application_count is None


def test_create_application_rejects_invalid_salary_range(
    db_session: Session,
) -> None:
    user = create_test_user(db_session)
    company = create_test_company(
        db_session,
        user.id,
    )

    with pytest.raises(InvalidSalaryRangeError):
        ApplicationService.create(
            db_session,
            user.id,
            ApplicationCreate(
                company_id=company.id,
                position="Backend Engineer",
                salary_min=Decimal("80000.00"),
                salary_max=Decimal("50000.00"),
                currency="EUR",
            ),
        )


def test_create_application_normalizes_currency(
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
        salary_min=Decimal("50000.00"),
        salary_max=Decimal("70000.00"),
        currency="eur",
    )

    assert application.currency == "EUR"


def test_create_applied_application_sets_applied_at(
    db_session: Session,
) -> None:
    user = create_test_user(db_session)
    company = create_test_company(
        db_session,
        user.id,
    )

    before = datetime.now(UTC)

    application = create_test_application(
        db_session,
        user.id,
        company.id,
        status=ApplicationStatus.APPLIED,
    )

    after = datetime.now(UTC)

    assert application.applied_at is not None
    assert before <= application.applied_at <= after


def test_create_saved_application_leaves_applied_at_null(
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
        status=ApplicationStatus.SAVED,
    )

    assert application.applied_at is None


def test_list_for_user_returns_only_owned_applications(
    db_session: Session,
) -> None:
    first_user = create_test_user(db_session)
    second_user = create_test_user(db_session)

    first_company = create_test_company(
        db_session,
        first_user.id,
        name="Stripe",
    )

    second_company = create_test_company(
        db_session,
        second_user.id,
        name="GitHub",
    )

    first_application = create_test_application(
        db_session,
        first_user.id,
        first_company.id,
        position="Backend Engineer",
    )

    second_application = create_test_application(
        db_session,
        first_user.id,
        first_company.id,
        position="Platform Engineer",
    )

    other_users_application = create_test_application(
        db_session,
        second_user.id,
        second_company.id,
        position="Software Engineer",
    )

    applications = ApplicationService.list_for_user(
        db_session,
        first_user.id,
    )

    application_ids = {application.id for application in applications}

    assert application_ids == {
        first_application.id,
        second_application.id,
    }

    assert other_users_application.id not in application_ids


def test_get_returns_owned_application(
    db_session: Session,
) -> None:
    user = create_test_user(db_session)
    company = create_test_company(
        db_session,
        user.id,
    )

    created_application = create_test_application(
        db_session,
        user.id,
        company.id,
    )

    application = ApplicationService.get(
        db_session,
        user.id,
        created_application.id,
    )

    assert application.id == created_application.id
    assert application.user_id == user.id


def test_get_does_not_expose_another_users_application(
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

    assert (
        ApplicationService.get_by_id(
            db_session,
            other_user.id,
            application.id,
        )
        is None
    )

    with pytest.raises(ApplicationNotFoundError):
        ApplicationService.get(
            db_session,
            other_user.id,
            application.id,
        )


def test_update_application_changes_only_provided_fields(
    db_session: Session,
) -> None:
    user = create_test_user(db_session)
    company = create_test_company(
        db_session,
        user.id,
    )

    application = ApplicationService.create(
        db_session,
        user.id,
        ApplicationCreate(
            company_id=company.id,
            position="Backend Engineer",
            location="Dublin, Ireland",
            notes="Original notes",
        ),
    )

    updated_application = ApplicationService.update(
        db_session,
        user.id,
        application.id,
        ApplicationUpdate(
            position="Senior Backend Engineer",
            location="Cork, Ireland",
        ),
    )

    assert updated_application.position == "Senior Backend Engineer"
    assert updated_application.location == "Cork, Ireland"

    # Campo não enviado permanece intacto.
    assert updated_application.notes == "Original notes"


def test_update_application_rejects_another_users_company(
    db_session: Session,
) -> None:
    user = create_test_user(db_session)
    other_user = create_test_user(db_session)

    company = create_test_company(
        db_session,
        user.id,
        name="Stripe",
    )

    other_company = create_test_company(
        db_session,
        other_user.id,
        name="GitHub",
    )

    application = create_test_application(
        db_session,
        user.id,
        company.id,
    )

    with pytest.raises(CompanyNotFoundError):
        ApplicationService.update(
            db_session,
            user.id,
            application.id,
            ApplicationUpdate(
                company_id=other_company.id,
            ),
        )

    db_session.refresh(application)

    assert application.company_id == company.id


def test_update_application_validates_salary_against_existing_values(
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
        salary_min=Decimal("50000.00"),
        salary_max=Decimal("70000.00"),
        currency="EUR",
    )

    with pytest.raises(InvalidSalaryRangeError):
        ApplicationService.update(
            db_session,
            user.id,
            application.id,
            ApplicationUpdate(
                salary_min=Decimal("80000.00"),
            ),
        )


def test_update_application_normalizes_currency(
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
        currency="EUR",
    )

    updated_application = ApplicationService.update(
        db_session,
        user.id,
        application.id,
        ApplicationUpdate(
            currency="gbp",
        ),
    )

    assert updated_application.currency == "GBP"


def test_status_change_creates_event_and_sets_applied_at(
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
        status=ApplicationStatus.SAVED,
    )

    assert application.applied_at is None

    before = datetime.now(UTC)

    updated_application = ApplicationService.update(
        db_session,
        user.id,
        application.id,
        ApplicationUpdate(
            status=ApplicationStatus.APPLIED,
        ),
    )

    after = datetime.now(UTC)

    assert updated_application.status is ApplicationStatus.APPLIED
    assert updated_application.applied_at is not None
    assert before <= updated_application.applied_at <= after

    status_events = list(
        db_session.scalars(
            select(ApplicationEvent).where(
                ApplicationEvent.application_id == application.id,
                ApplicationEvent.event_type == ApplicationEventType.STATUS_CHANGED,
            )
        )
    )

    assert len(status_events) == 1

    event = status_events[0]

    assert event.from_status is ApplicationStatus.SAVED
    assert event.to_status is ApplicationStatus.APPLIED


def test_update_without_status_change_does_not_create_status_event(
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

    ApplicationService.update(
        db_session,
        user.id,
        application.id,
        ApplicationUpdate(
            notes="Recruiter contacted me.",
        ),
    )

    status_events = list(
        db_session.scalars(
            select(ApplicationEvent).where(
                ApplicationEvent.application_id == application.id,
                ApplicationEvent.event_type == ApplicationEventType.STATUS_CHANGED,
            )
        )
    )

    assert status_events == []


def test_update_does_not_modify_another_users_application(
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
        position="Backend Engineer",
    )

    with pytest.raises(ApplicationNotFoundError):
        ApplicationService.update(
            db_session,
            other_user.id,
            application.id,
            ApplicationUpdate(
                position="Not Allowed",
            ),
        )

    db_session.refresh(application)

    assert application.position == "Backend Engineer"


def test_delete_application_removes_application_and_events(
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

    application_id = application.id

    event_ids = list(
        db_session.scalars(
            select(ApplicationEvent.id).where(
                ApplicationEvent.application_id == application_id
            )
        )
    )

    assert event_ids

    ApplicationService.delete(
        db_session,
        user.id,
        application_id,
    )

    assert (
        db_session.get(
            Application,
            application_id,
        )
        is None
    )

    remaining_events = list(
        db_session.scalars(
            select(ApplicationEvent).where(
                ApplicationEvent.application_id == application_id
            )
        )
    )

    assert remaining_events == []


def test_delete_does_not_remove_another_users_application(
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
        ApplicationService.delete(
            db_session,
            other_user.id,
            application.id,
        )

    assert (
        db_session.get(
            Application,
            application.id,
        )
        is not None
    )
