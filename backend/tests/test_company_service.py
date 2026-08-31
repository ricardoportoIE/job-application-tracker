from collections.abc import Generator
from uuid import uuid4

import pytest
from sqlalchemy import delete, select
from sqlalchemy.orm import Session

from app.db.session import SessionLocal
from app.models.application import Application
from app.models.company import Company
from app.models.user import User
from app.schemas.company import CompanyCreate, CompanyUpdate
from app.schemas.user import UserCreate
from app.services.company import (
    CompanyInUseError,
    CompanyNotFoundError,
    CompanyService,
)
from app.services.user import UserService

TEST_EMAIL_PREFIX = "company-service-test-"


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


def test_create_company_persists_company_for_user(
    db_session: Session,
) -> None:
    user = create_test_user(db_session)

    company = CompanyService.create(
        db_session,
        user.id,
        CompanyCreate(
            name="Stripe",
            website="https://stripe.com",
            industry="Fintech",
            location="Dublin, Ireland",
        ),
    )

    assert company.id is not None
    assert company.user_id == user.id
    assert company.name == "Stripe"
    assert company.website == "https://stripe.com"
    assert company.industry == "Fintech"
    assert company.location == "Dublin, Ireland"

    db_session.expire_all()

    persisted_company = db_session.get(
        Company,
        company.id,
    )

    assert persisted_company is not None
    assert persisted_company.user_id == user.id
    assert persisted_company.name == "Stripe"


def test_list_for_user_returns_only_owned_companies(
    db_session: Session,
) -> None:
    first_user = create_test_user(db_session)
    second_user = create_test_user(db_session)

    first_company = CompanyService.create(
        db_session,
        first_user.id,
        CompanyCreate(
            name="Stripe",
        ),
    )

    second_company = CompanyService.create(
        db_session,
        first_user.id,
        CompanyCreate(
            name="Datadog",
        ),
    )

    other_users_company = CompanyService.create(
        db_session,
        second_user.id,
        CompanyCreate(
            name="GitHub",
        ),
    )

    companies = CompanyService.list_for_user(
        db_session,
        first_user.id,
    )

    company_ids = {company.id for company in companies}

    assert company_ids == {
        first_company.id,
        second_company.id,
    }
    assert other_users_company.id not in company_ids


def test_get_returns_owned_company(
    db_session: Session,
) -> None:
    user = create_test_user(db_session)

    created_company = CompanyService.create(
        db_session,
        user.id,
        CompanyCreate(
            name="Stripe",
        ),
    )

    company = CompanyService.get(
        db_session,
        user.id,
        created_company.id,
    )

    assert company.id == created_company.id
    assert company.user_id == user.id
    assert company.name == "Stripe"


def test_get_by_id_returns_none_for_nonexistent_company(
    db_session: Session,
) -> None:
    user = create_test_user(db_session)

    company = CompanyService.get_by_id(
        db_session,
        user.id,
        uuid4(),
    )

    assert company is None


def test_get_does_not_expose_another_users_company(
    db_session: Session,
) -> None:
    owner = create_test_user(db_session)
    other_user = create_test_user(db_session)

    company = CompanyService.create(
        db_session,
        owner.id,
        CompanyCreate(
            name="Stripe",
        ),
    )

    assert (
        CompanyService.get_by_id(
            db_session,
            other_user.id,
            company.id,
        )
        is None
    )

    with pytest.raises(CompanyNotFoundError):
        CompanyService.get(
            db_session,
            other_user.id,
            company.id,
        )


def test_update_company_changes_provided_fields(
    db_session: Session,
) -> None:
    user = create_test_user(db_session)

    company = CompanyService.create(
        db_session,
        user.id,
        CompanyCreate(
            name="Stripe",
            website="https://stripe.com",
            location="Dublin, Ireland",
        ),
    )

    updated_company = CompanyService.update(
        db_session,
        user.id,
        company.id,
        CompanyUpdate(
            name="Stripe Ireland",
            location="Cork, Ireland",
        ),
    )

    assert updated_company.name == "Stripe Ireland"
    assert updated_company.location == "Cork, Ireland"

    # Campo não enviado no PATCH permanece intacto.
    assert updated_company.website == "https://stripe.com"


def test_update_company_allows_clearing_optional_field(
    db_session: Session,
) -> None:
    user = create_test_user(db_session)

    company = CompanyService.create(
        db_session,
        user.id,
        CompanyCreate(
            name="Stripe",
            website="https://stripe.com",
        ),
    )

    updated_company = CompanyService.update(
        db_session,
        user.id,
        company.id,
        CompanyUpdate(
            website=None,
        ),
    )

    assert updated_company.website is None


def test_update_rejects_another_users_company(
    db_session: Session,
) -> None:
    owner = create_test_user(db_session)
    other_user = create_test_user(db_session)

    company = CompanyService.create(
        db_session,
        owner.id,
        CompanyCreate(
            name="Stripe",
        ),
    )

    with pytest.raises(CompanyNotFoundError):
        CompanyService.update(
            db_session,
            other_user.id,
            company.id,
            CompanyUpdate(
                name="Not Allowed",
            ),
        )

    db_session.refresh(company)

    assert company.name == "Stripe"


def test_delete_company_removes_owned_company(
    db_session: Session,
) -> None:
    user = create_test_user(db_session)

    company = CompanyService.create(
        db_session,
        user.id,
        CompanyCreate(
            name="Stripe",
        ),
    )

    company_id = company.id

    CompanyService.delete(
        db_session,
        user.id,
        company_id,
    )

    assert db_session.get(Company, company_id) is None


def test_delete_rejects_another_users_company(
    db_session: Session,
) -> None:
    owner = create_test_user(db_session)
    other_user = create_test_user(db_session)

    company = CompanyService.create(
        db_session,
        owner.id,
        CompanyCreate(
            name="Stripe",
        ),
    )

    with pytest.raises(CompanyNotFoundError):
        CompanyService.delete(
            db_session,
            other_user.id,
            company.id,
        )

    assert db_session.get(Company, company.id) is not None


def test_delete_company_with_application_raises_company_in_use(
    db_session: Session,
) -> None:
    user = create_test_user(db_session)

    company = CompanyService.create(
        db_session,
        user.id,
        CompanyCreate(
            name="Stripe",
        ),
    )

    application = Application(
        user_id=user.id,
        company_id=company.id,
        position="Backend Engineer",
    )

    db_session.add(application)
    db_session.commit()

    application_id = application.id
    company_id = company.id

    with pytest.raises(CompanyInUseError):
        CompanyService.delete(
            db_session,
            user.id,
            company_id,
        )

    assert db_session.get(Company, company_id) is not None
    assert db_session.get(Application, application_id) is not None
