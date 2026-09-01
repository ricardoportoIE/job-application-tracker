from collections.abc import Generator
from datetime import UTC, datetime, timedelta
from uuid import UUID, uuid4

import pytest
from sqlalchemy import delete, select
from sqlalchemy.orm import Session

from app.db.session import SessionLocal
from app.models.application import Application
from app.models.company import Company
from app.models.enums import (
    ApplicationStatus,
    JobSource,
    WorkModel,
)
from app.models.user import User
from app.schemas.application import ApplicationCreate
from app.schemas.application_query import ApplicationListParams
from app.schemas.company import CompanyCreate
from app.schemas.user import UserCreate
from app.services.application import ApplicationService
from app.services.company import CompanyService
from app.services.user import UserService

TEST_EMAIL_PREFIX = "application-list-service-test-"


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
    name: str,
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
    position: str,
    status: ApplicationStatus = ApplicationStatus.SAVED,
    source: JobSource | None = None,
    work_model: WorkModel | None = None,
    location: str | None = None,
    applied_at: datetime | None = None,
) -> Application:
    return ApplicationService.create(
        session,
        user_id,
        ApplicationCreate(
            company_id=company_id,
            position=position,
            status=status,
            source=source,
            work_model=work_model,
            location=location,
            applied_at=applied_at,
        ),
    )


def test_list_page_returns_only_current_users_applications(
    db_session: Session,
) -> None:
    user = create_test_user(db_session)
    other_user = create_test_user(db_session)

    company = create_test_company(
        db_session,
        user.id,
        "Stripe",
    )
    other_company = create_test_company(
        db_session,
        other_user.id,
        "GitHub",
    )

    first = create_test_application(
        db_session,
        user.id,
        company.id,
        position="Backend Engineer",
    )
    second = create_test_application(
        db_session,
        user.id,
        company.id,
        position="Platform Engineer",
    )
    other = create_test_application(
        db_session,
        other_user.id,
        other_company.id,
        position="Software Engineer",
    )

    applications, total = ApplicationService.list_page_for_user(
        db_session,
        user.id,
        ApplicationListParams(
            sort_by="position",
            sort_order="asc",
        ),
    )

    ids = {application.id for application in applications}

    assert ids == {
        first.id,
        second.id,
    }
    assert other.id not in ids
    assert total == 2


def test_list_page_filters_by_status(
    db_session: Session,
) -> None:
    user = create_test_user(db_session)
    company = create_test_company(
        db_session,
        user.id,
        "Stripe",
    )

    applied = create_test_application(
        db_session,
        user.id,
        company.id,
        position="Backend Engineer",
        status=ApplicationStatus.APPLIED,
    )

    create_test_application(
        db_session,
        user.id,
        company.id,
        position="Platform Engineer",
        status=ApplicationStatus.SAVED,
    )

    applications, total = ApplicationService.list_page_for_user(
        db_session,
        user.id,
        ApplicationListParams(
            status=ApplicationStatus.APPLIED,
        ),
    )

    assert [application.id for application in applications] == [applied.id]
    assert total == 1


def test_list_page_filters_by_company(
    db_session: Session,
) -> None:
    user = create_test_user(db_session)

    stripe = create_test_company(
        db_session,
        user.id,
        "Stripe",
    )
    github = create_test_company(
        db_session,
        user.id,
        "GitHub",
    )

    expected = create_test_application(
        db_session,
        user.id,
        stripe.id,
        position="Backend Engineer",
    )

    create_test_application(
        db_session,
        user.id,
        github.id,
        position="Platform Engineer",
    )

    applications, total = ApplicationService.list_page_for_user(
        db_session,
        user.id,
        ApplicationListParams(
            company_id=stripe.id,
        ),
    )

    assert [application.id for application in applications] == [expected.id]
    assert total == 1


def test_list_page_filters_by_work_model_and_source(
    db_session: Session,
) -> None:
    user = create_test_user(db_session)
    company = create_test_company(
        db_session,
        user.id,
        "Stripe",
    )

    expected = create_test_application(
        db_session,
        user.id,
        company.id,
        position="Backend Engineer",
        source=JobSource.LINKEDIN,
        work_model=WorkModel.REMOTE,
    )

    create_test_application(
        db_session,
        user.id,
        company.id,
        position="Platform Engineer",
        source=JobSource.INDEED,
        work_model=WorkModel.REMOTE,
    )

    create_test_application(
        db_session,
        user.id,
        company.id,
        position="Software Engineer",
        source=JobSource.LINKEDIN,
        work_model=WorkModel.HYBRID,
    )

    applications, total = ApplicationService.list_page_for_user(
        db_session,
        user.id,
        ApplicationListParams(
            source=JobSource.LINKEDIN,
            work_model=WorkModel.REMOTE,
        ),
    )

    assert [application.id for application in applications] == [expected.id]
    assert total == 1


def test_list_page_combines_multiple_filters(
    db_session: Session,
) -> None:
    user = create_test_user(db_session)

    stripe = create_test_company(
        db_session,
        user.id,
        "Stripe",
    )
    github = create_test_company(
        db_session,
        user.id,
        "GitHub",
    )

    expected = create_test_application(
        db_session,
        user.id,
        stripe.id,
        position="Backend Engineer",
        status=ApplicationStatus.INTERVIEW,
        source=JobSource.LINKEDIN,
        work_model=WorkModel.HYBRID,
    )

    create_test_application(
        db_session,
        user.id,
        stripe.id,
        position="Backend Engineer II",
        status=ApplicationStatus.APPLIED,
        source=JobSource.LINKEDIN,
        work_model=WorkModel.HYBRID,
    )

    create_test_application(
        db_session,
        user.id,
        github.id,
        position="Backend Engineer",
        status=ApplicationStatus.INTERVIEW,
        source=JobSource.LINKEDIN,
        work_model=WorkModel.HYBRID,
    )

    applications, total = ApplicationService.list_page_for_user(
        db_session,
        user.id,
        ApplicationListParams(
            company_id=stripe.id,
            status=ApplicationStatus.INTERVIEW,
            source=JobSource.LINKEDIN,
            work_model=WorkModel.HYBRID,
        ),
    )

    assert [application.id for application in applications] == [expected.id]
    assert total == 1


@pytest.mark.parametrize(
    ("search", "expected_position"),
    [
        ("backend", "Senior Backend Engineer"),
        ("STRIPE", "Platform Engineer"),
        ("dublin", "Cloud Engineer"),
    ],
)
def test_list_page_searches_position_company_and_location_case_insensitively(
    db_session: Session,
    search: str,
    expected_position: str,
) -> None:
    user = create_test_user(db_session)

    stripe = create_test_company(
        db_session,
        user.id,
        "Stripe Technologies",
    )
    github = create_test_company(
        db_session,
        user.id,
        "GitHub",
    )

    create_test_application(
        db_session,
        user.id,
        github.id,
        position="Senior Backend Engineer",
        location="Cork, Ireland",
    )

    create_test_application(
        db_session,
        user.id,
        stripe.id,
        position="Platform Engineer",
        location="London, UK",
    )

    create_test_application(
        db_session,
        user.id,
        github.id,
        position="Cloud Engineer",
        location="Dublin, Ireland",
    )

    applications, total = ApplicationService.list_page_for_user(
        db_session,
        user.id,
        ApplicationListParams(
            search=search,
        ),
    )

    assert total == 1
    assert len(applications) == 1
    assert applications[0].position == expected_position


def test_list_page_search_treats_percent_as_literal(
    db_session: Session,
) -> None:
    user = create_test_user(db_session)
    company = create_test_company(
        db_session,
        user.id,
        "Remote Jobs",
    )

    expected = create_test_application(
        db_session,
        user.id,
        company.id,
        position="100% Remote Engineer",
    )

    create_test_application(
        db_session,
        user.id,
        company.id,
        position="1000 Remote Engineer",
    )

    applications, total = ApplicationService.list_page_for_user(
        db_session,
        user.id,
        ApplicationListParams(
            search="100%",
        ),
    )

    assert total == 1
    assert [application.id for application in applications] == [expected.id]


def test_list_page_applies_limit_offset_and_preserves_total(
    db_session: Session,
) -> None:
    user = create_test_user(db_session)
    company = create_test_company(
        db_session,
        user.id,
        "Stripe",
    )

    for position in [
        "Alpha Engineer",
        "Bravo Engineer",
        "Charlie Engineer",
        "Delta Engineer",
        "Echo Engineer",
    ]:
        create_test_application(
            db_session,
            user.id,
            company.id,
            position=position,
        )

    first_page, first_total = ApplicationService.list_page_for_user(
        db_session,
        user.id,
        ApplicationListParams(
            limit=2,
            offset=0,
            sort_by="position",
            sort_order="asc",
        ),
    )

    second_page, second_total = ApplicationService.list_page_for_user(
        db_session,
        user.id,
        ApplicationListParams(
            limit=2,
            offset=2,
            sort_by="position",
            sort_order="asc",
        ),
    )

    assert [application.position for application in first_page] == [
        "Alpha Engineer",
        "Bravo Engineer",
    ]

    assert [application.position for application in second_page] == [
        "Charlie Engineer",
        "Delta Engineer",
    ]

    assert first_total == 5
    assert second_total == 5


def test_list_page_sorts_position_case_insensitively(
    db_session: Session,
) -> None:
    user = create_test_user(db_session)
    company = create_test_company(
        db_session,
        user.id,
        "Stripe",
    )

    for position in [
        "charlie engineer",
        "Alpha Engineer",
        "bravo Engineer",
    ]:
        create_test_application(
            db_session,
            user.id,
            company.id,
            position=position,
        )

    applications, total = ApplicationService.list_page_for_user(
        db_session,
        user.id,
        ApplicationListParams(
            sort_by="position",
            sort_order="asc",
        ),
    )

    assert total == 3
    assert [application.position for application in applications] == [
        "Alpha Engineer",
        "bravo Engineer",
        "charlie engineer",
    ]


@pytest.mark.parametrize(
    "sort_order",
    [
        "asc",
        "desc",
    ],
)
def test_list_page_sorts_applied_at_with_nulls_last(
    db_session: Session,
    sort_order: str,
) -> None:
    user = create_test_user(db_session)
    company = create_test_company(
        db_session,
        user.id,
        "Stripe",
    )

    now = datetime.now(UTC)

    earlier = create_test_application(
        db_session,
        user.id,
        company.id,
        position="Earlier Application",
        status=ApplicationStatus.APPLIED,
        applied_at=now - timedelta(days=2),
    )

    later = create_test_application(
        db_session,
        user.id,
        company.id,
        position="Later Application",
        status=ApplicationStatus.APPLIED,
        applied_at=now - timedelta(days=1),
    )

    saved = create_test_application(
        db_session,
        user.id,
        company.id,
        position="Saved Application",
        status=ApplicationStatus.SAVED,
    )

    params = ApplicationListParams.model_validate(
        {
            "sort_by": "applied_at",
            "sort_order": sort_order,
        }
    )

    applications, total = ApplicationService.list_page_for_user(
        db_session,
        user.id,
        params,
    )

    assert total == 3
    assert applications[-1].id == saved.id

    if sort_order == "asc":
        assert applications[0].id == earlier.id
        assert applications[1].id == later.id
    else:
        assert applications[0].id == later.id
        assert applications[1].id == earlier.id
