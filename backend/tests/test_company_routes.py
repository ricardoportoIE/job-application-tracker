import uuid
from collections.abc import Generator
from uuid import uuid4

import pytest
from fastapi.testclient import TestClient
from sqlalchemy import delete, select

from app.core.security import create_access_token
from app.db.session import SessionLocal
from app.main import app
from app.models.application import Application
from app.models.company import Company
from app.models.user import User
from app.schemas.company import CompanyCreate
from app.schemas.user import UserCreate
from app.services.company import CompanyService
from app.services.user import UserService

TEST_EMAIL_PREFIX = "company-route-test-"

client = TestClient(app)


@pytest.fixture(autouse=True)
def cleanup_test_data() -> Generator[None]:
    yield

    with SessionLocal() as session:
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


def create_authenticated_user() -> tuple[uuid.UUID, str]:
    with SessionLocal() as session:
        user = UserService.create(
            session,
            UserCreate(
                email=make_test_email(),
                password="secure-password-123",
            ),
        )

        user_id = user.id

    token = create_access_token(
        subject=str(user_id),
    )

    return user_id, token


def auth_headers(token: str) -> dict[str, str]:
    return {
        "Authorization": f"Bearer {token}",
    }


def create_company_directly(
    user_id: uuid.UUID,
    name: str = "Stripe",
    website: str | None = None,
) -> uuid.UUID:
    with SessionLocal() as session:
        company = CompanyService.create(
            session,
            user_id,
            CompanyCreate(
                name=name,
                website=website,
            ),
        )

        return company.id


def test_create_company_returns_created_company() -> None:
    user_id, token = create_authenticated_user()

    response = client.post(
        "/companies",
        headers=auth_headers(token),
        json={
            "name": "Stripe",
            "website": "https://stripe.com",
            "industry": "Fintech",
            "location": "Dublin, Ireland",
        },
    )

    assert response.status_code == 201

    body = response.json()

    assert body["id"]
    assert body["user_id"] == str(user_id)
    assert body["name"] == "Stripe"
    assert body["website"] == "https://stripe.com"
    assert body["industry"] == "Fintech"
    assert body["location"] == "Dublin, Ireland"
    assert body["created_at"]
    assert body["updated_at"]


def test_create_company_requires_authentication() -> None:
    response = client.post(
        "/companies",
        json={
            "name": "Stripe",
        },
    )

    assert response.status_code == 401
    assert response.json() == {
        "detail": "Could not validate credentials",
    }


def test_create_company_rejects_invalid_name() -> None:
    _, token = create_authenticated_user()

    response = client.post(
        "/companies",
        headers=auth_headers(token),
        json={
            "name": "   ",
        },
    )

    assert response.status_code == 422


def test_list_companies_returns_only_current_users_companies() -> None:
    first_user_id, first_token = create_authenticated_user()
    second_user_id, _ = create_authenticated_user()

    first_company_id = create_company_directly(
        first_user_id,
        name="Stripe",
    )

    second_company_id = create_company_directly(
        first_user_id,
        name="Datadog",
    )

    other_users_company_id = create_company_directly(
        second_user_id,
        name="GitHub",
    )

    response = client.get(
        "/companies",
        headers=auth_headers(first_token),
    )

    assert response.status_code == 200

    companies = response.json()
    company_ids = {company["id"] for company in companies}

    assert company_ids == {
        str(first_company_id),
        str(second_company_id),
    }
    assert str(other_users_company_id) not in company_ids


def test_get_company_returns_owned_company() -> None:
    user_id, token = create_authenticated_user()

    company_id = create_company_directly(
        user_id,
        name="Stripe",
        website="https://stripe.com",
    )

    response = client.get(
        f"/companies/{company_id}",
        headers=auth_headers(token),
    )

    assert response.status_code == 200

    body = response.json()

    assert body["id"] == str(company_id)
    assert body["user_id"] == str(user_id)
    assert body["name"] == "Stripe"
    assert body["website"] == "https://stripe.com"


def test_get_company_returns_404_for_nonexistent_company() -> None:
    _, token = create_authenticated_user()

    response = client.get(
        f"/companies/{uuid4()}",
        headers=auth_headers(token),
    )

    assert response.status_code == 404
    assert response.json() == {
        "detail": "Company not found",
    }


def test_get_company_does_not_expose_another_users_company() -> None:
    owner_id, _ = create_authenticated_user()
    _, other_user_token = create_authenticated_user()

    company_id = create_company_directly(
        owner_id,
        name="Stripe",
    )

    response = client.get(
        f"/companies/{company_id}",
        headers=auth_headers(other_user_token),
    )

    assert response.status_code == 404
    assert response.json() == {
        "detail": "Company not found",
    }


def test_update_company_changes_only_provided_fields() -> None:
    user_id, token = create_authenticated_user()

    company_id = create_company_directly(
        user_id,
        name="Stripe",
        website="https://stripe.com",
    )

    response = client.patch(
        f"/companies/{company_id}",
        headers=auth_headers(token),
        json={
            "name": "Stripe Ireland",
            "location": "Cork, Ireland",
        },
    )

    assert response.status_code == 200

    body = response.json()

    assert body["name"] == "Stripe Ireland"
    assert body["location"] == "Cork, Ireland"
    assert body["website"] == "https://stripe.com"


def test_update_company_allows_clearing_optional_field() -> None:
    user_id, token = create_authenticated_user()

    company_id = create_company_directly(
        user_id,
        name="Stripe",
        website="https://stripe.com",
    )

    response = client.patch(
        f"/companies/{company_id}",
        headers=auth_headers(token),
        json={
            "website": None,
        },
    )

    assert response.status_code == 200
    assert response.json()["website"] is None


def test_update_company_rejects_null_name() -> None:
    user_id, token = create_authenticated_user()

    company_id = create_company_directly(
        user_id,
        name="Stripe",
    )

    response = client.patch(
        f"/companies/{company_id}",
        headers=auth_headers(token),
        json={
            "name": None,
        },
    )

    assert response.status_code == 422


def test_update_company_does_not_modify_another_users_company() -> None:
    owner_id, _ = create_authenticated_user()
    _, other_user_token = create_authenticated_user()

    company_id = create_company_directly(
        owner_id,
        name="Stripe",
    )

    response = client.patch(
        f"/companies/{company_id}",
        headers=auth_headers(other_user_token),
        json={
            "name": "Not Allowed",
        },
    )

    assert response.status_code == 404
    assert response.json() == {
        "detail": "Company not found",
    }

    with SessionLocal() as session:
        company = session.get(
            Company,
            company_id,
        )

        assert company is not None
        assert company.name == "Stripe"


def test_delete_company_removes_owned_company() -> None:
    user_id, token = create_authenticated_user()

    company_id = create_company_directly(
        user_id,
        name="Stripe",
    )

    response = client.delete(
        f"/companies/{company_id}",
        headers=auth_headers(token),
    )

    assert response.status_code == 204
    assert response.content == b""

    with SessionLocal() as session:
        assert session.get(Company, company_id) is None


def test_delete_company_does_not_delete_another_users_company() -> None:
    owner_id, _ = create_authenticated_user()
    _, other_user_token = create_authenticated_user()

    company_id = create_company_directly(
        owner_id,
        name="Stripe",
    )

    response = client.delete(
        f"/companies/{company_id}",
        headers=auth_headers(other_user_token),
    )

    assert response.status_code == 404
    assert response.json() == {
        "detail": "Company not found",
    }

    with SessionLocal() as session:
        assert session.get(Company, company_id) is not None


def test_delete_company_with_application_returns_conflict() -> None:
    user_id, token = create_authenticated_user()

    company_id = create_company_directly(
        user_id,
        name="Stripe",
    )

    with SessionLocal() as session:
        application = Application(
            user_id=user_id,
            company_id=company_id,
            position="Backend Engineer",
        )

        session.add(application)
        session.commit()

        application_id = application.id

    response = client.delete(
        f"/companies/{company_id}",
        headers=auth_headers(token),
    )

    assert response.status_code == 409
    assert response.json() == {
        "detail": "Company has applications and cannot be deleted",
    }

    with SessionLocal() as session:
        assert session.get(Company, company_id) is not None
        assert session.get(Application, application_id) is not None


def test_company_route_rejects_invalid_company_uuid() -> None:
    _, token = create_authenticated_user()

    response = client.get(
        "/companies/not-a-uuid",
        headers=auth_headers(token),
    )

    assert response.status_code == 422
