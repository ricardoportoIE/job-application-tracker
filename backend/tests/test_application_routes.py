import uuid
from collections.abc import Generator
from decimal import Decimal
from uuid import uuid4

import pytest
from fastapi.testclient import TestClient
from sqlalchemy import delete, select

from app.core.security import create_access_token
from app.db.session import SessionLocal
from app.main import app
from app.models.application import Application
from app.models.application_event import ApplicationEvent
from app.models.company import Company
from app.models.enums import ApplicationEventType, ApplicationStatus
from app.models.user import User
from app.schemas.application import ApplicationCreate
from app.schemas.company import CompanyCreate
from app.schemas.user import UserCreate
from app.services.application import ApplicationService
from app.services.company import CompanyService
from app.services.user import UserService

TEST_EMAIL_PREFIX = "application-route-test-"

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
) -> uuid.UUID:
    with SessionLocal() as session:
        company = CompanyService.create(
            session,
            user_id,
            CompanyCreate(
                name=name,
            ),
        )

        return company.id


def create_application_directly(
    user_id: uuid.UUID,
    company_id: uuid.UUID,
    *,
    position: str = "Backend Engineer",
    status: ApplicationStatus = ApplicationStatus.SAVED,
    salary_min: Decimal | None = None,
    salary_max: Decimal | None = None,
    currency: str | None = None,
) -> uuid.UUID:
    with SessionLocal() as session:
        application = ApplicationService.create(
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

        return application.id


def test_create_application_returns_created_application() -> None:
    user_id, token = create_authenticated_user()
    company_id = create_company_directly(user_id)

    response = client.post(
        "/api/v1/applications",
        headers=auth_headers(token),
        json={
            "company_id": str(company_id),
            "position": "Backend Engineer",
            "status": "saved",
            "location": "Dublin, Ireland",
            "source": "linkedin",
            "work_model": "hybrid",
        },
    )

    assert response.status_code == 201

    body = response.json()

    assert body["id"]
    assert body["user_id"] == str(user_id)
    assert body["company_id"] == str(company_id)
    assert body["position"] == "Backend Engineer"
    assert body["status"] == "saved"
    assert body["source"] == "linkedin"
    assert body["work_model"] == "hybrid"
    assert body["location"] == "Dublin, Ireland"
    assert body["created_at"]
    assert body["updated_at"]


def test_create_application_requires_authentication() -> None:
    response = client.post(
        "/api/v1/applications",
        json={
            "company_id": str(uuid4()),
            "position": "Backend Engineer",
        },
    )

    assert response.status_code == 401

    body = response.json()

    assert body["detail"] == "Could not validate credentials"
    assert body["request_id"]
    assert response.headers["X-Request-ID"] == body["request_id"]
    assert response.headers["www-authenticate"] == "Bearer"


def test_create_application_rejects_another_users_company() -> None:
    owner_id, _ = create_authenticated_user()
    _, other_user_token = create_authenticated_user()

    company_id = create_company_directly(
        owner_id,
    )

    response = client.post(
        "/api/v1/applications",
        headers=auth_headers(other_user_token),
        json={
            "company_id": str(company_id),
            "position": "Backend Engineer",
        },
    )

    assert response.status_code == 404

    body = response.json()

    assert body["detail"] == "Company not found"
    assert body["request_id"]
    assert response.headers["X-Request-ID"] == body["request_id"]


def test_create_application_rejects_invalid_salary_range() -> None:
    user_id, token = create_authenticated_user()
    company_id = create_company_directly(user_id)

    response = client.post(
        "/api/v1/applications",
        headers=auth_headers(token),
        json={
            "company_id": str(company_id),
            "position": "Backend Engineer",
            "salary_min": "80000.00",
            "salary_max": "50000.00",
            "currency": "EUR",
        },
    )

    assert response.status_code == 422

    body = response.json()

    assert body["detail"] == "salary_min cannot be greater than salary_max"
    assert body["request_id"]
    assert response.headers["X-Request-ID"] == body["request_id"]


def test_create_application_normalizes_currency() -> None:
    user_id, token = create_authenticated_user()
    company_id = create_company_directly(user_id)

    response = client.post(
        "/api/v1/applications",
        headers=auth_headers(token),
        json={
            "company_id": str(company_id),
            "position": "Backend Engineer",
            "salary_min": "50000.00",
            "salary_max": "70000.00",
            "currency": "eur",
        },
    )

    assert response.status_code == 201

    body = response.json()

    assert body["currency"] == "EUR"
    assert Decimal(str(body["salary_min"])) == Decimal("50000.00")
    assert Decimal(str(body["salary_max"])) == Decimal("70000.00")


def test_create_applied_application_sets_applied_at_and_created_event() -> None:
    user_id, token = create_authenticated_user()
    company_id = create_company_directly(user_id)

    response = client.post(
        "/api/v1/applications",
        headers=auth_headers(token),
        json={
            "company_id": str(company_id),
            "position": "Backend Engineer",
            "status": "applied",
        },
    )

    assert response.status_code == 201

    body = response.json()

    assert body["status"] == "applied"
    assert body["applied_at"] is not None

    application_id = uuid.UUID(body["id"])

    with SessionLocal() as session:
        events = list(
            session.scalars(
                select(ApplicationEvent).where(
                    ApplicationEvent.application_id == application_id
                )
            )
        )

        assert len(events) == 1

        event = events[0]

        assert event.event_type is ApplicationEventType.CREATED
        assert event.from_status is None
        assert event.to_status is ApplicationStatus.APPLIED


def test_create_saved_application_leaves_applied_at_null() -> None:

    user_id, token = create_authenticated_user()
    company_id = create_company_directly(user_id)

    response = client.post(
        "/api/v1/applications",
        headers=auth_headers(token),
        json={
            "company_id": str(company_id),
            "position": "Backend Engineer",
            "status": "saved",
        },
    )

    assert response.status_code == 201
    assert response.json()["applied_at"] is None


def test_list_applications_returns_only_current_users_applications() -> None:
    first_user_id, first_token = create_authenticated_user()
    second_user_id, _ = create_authenticated_user()

    first_company_id = create_company_directly(
        first_user_id,
        name="Stripe",
    )

    second_company_id = create_company_directly(
        second_user_id,
        name="GitHub",
    )

    first_application_id = create_application_directly(
        first_user_id,
        first_company_id,
        position="Backend Engineer",
    )

    second_application_id = create_application_directly(
        first_user_id,
        first_company_id,
        position="Platform Engineer",
    )

    other_users_application_id = create_application_directly(
        second_user_id,
        second_company_id,
        position="Software Engineer",
    )

    response = client.get(
        "/api/v1/applications",
        headers=auth_headers(first_token),
    )

    assert response.status_code == 200

    body = response.json()

    assert body["total"] == 2
    assert body["limit"] == 20
    assert body["offset"] == 0

    application_ids = {application["id"] for application in body["items"]}

    assert application_ids == {
        str(first_application_id),
        str(second_application_id),
    }

    assert str(other_users_application_id) not in application_ids


def test_get_application_returns_owned_application() -> None:
    user_id, token = create_authenticated_user()
    company_id = create_company_directly(user_id)

    application_id = create_application_directly(
        user_id,
        company_id,
        position="Backend Engineer",
    )

    response = client.get(
        f"/api/v1/applications/{application_id}",
        headers=auth_headers(token),
    )

    assert response.status_code == 200

    body = response.json()

    assert body["id"] == str(application_id)
    assert body["user_id"] == str(user_id)
    assert body["company_id"] == str(company_id)
    assert body["position"] == "Backend Engineer"


def test_get_application_returns_404_for_nonexistent_application() -> None:
    _, token = create_authenticated_user()

    response = client.get(
        f"/api/v1/applications/{uuid4()}",
        headers=auth_headers(token),
    )

    assert response.status_code == 404

    body = response.json()

    assert body["detail"] == "Application not found"
    assert body["request_id"]
    assert response.headers["X-Request-ID"] == body["request_id"]


def test_get_application_does_not_expose_another_users_application() -> None:
    owner_id, _ = create_authenticated_user()
    _, other_user_token = create_authenticated_user()

    company_id = create_company_directly(owner_id)

    application_id = create_application_directly(
        owner_id,
        company_id,
    )

    response = client.get(
        f"/api/v1/applications/{application_id}",
        headers=auth_headers(other_user_token),
    )

    assert response.status_code == 404

    body = response.json()

    assert body["detail"] == "Application not found"
    assert body["request_id"]
    assert response.headers["X-Request-ID"] == body["request_id"]


def test_update_application_changes_only_provided_fields() -> None:
    user_id, token = create_authenticated_user()
    company_id = create_company_directly(user_id)

    application_id = create_application_directly(
        user_id,
        company_id,
        position="Backend Engineer",
    )

    response = client.patch(
        f"/api/v1/applications/{application_id}",
        headers=auth_headers(token),
        json={
            "position": "Senior Backend Engineer",
            "location": "Cork, Ireland",
        },
    )

    assert response.status_code == 200

    body = response.json()

    assert body["position"] == "Senior Backend Engineer"
    assert body["location"] == "Cork, Ireland"

    # company_id não foi enviado no PATCH e deve permanecer intacto.
    assert body["company_id"] == str(company_id)


def test_update_status_creates_status_change_event() -> None:
    user_id, token = create_authenticated_user()
    company_id = create_company_directly(user_id)

    application_id = create_application_directly(
        user_id,
        company_id,
        status=ApplicationStatus.SAVED,
    )

    response = client.patch(
        f"/api/v1/applications/{application_id}",
        headers=auth_headers(token),
        json={
            "status": "applied",
        },
    )

    assert response.status_code == 200

    body = response.json()

    assert body["status"] == "applied"
    assert body["applied_at"] is not None

    with SessionLocal() as session:
        events = list(
            session.scalars(
                select(ApplicationEvent).where(
                    ApplicationEvent.application_id == application_id,
                    ApplicationEvent.event_type == ApplicationEventType.STATUS_CHANGED,
                )
            )
        )

        assert len(events) == 1

        event = events[0]

        assert event.from_status is ApplicationStatus.SAVED
        assert event.to_status is ApplicationStatus.APPLIED


def test_update_application_rejects_another_users_company() -> None:
    user_id, token = create_authenticated_user()
    other_user_id, _ = create_authenticated_user()

    company_id = create_company_directly(
        user_id,
        name="Stripe",
    )

    other_company_id = create_company_directly(
        other_user_id,
        name="GitHub",
    )

    application_id = create_application_directly(
        user_id,
        company_id,
    )

    response = client.patch(
        f"/api/v1/applications/{application_id}",
        headers=auth_headers(token),
        json={
            "company_id": str(other_company_id),
        },
    )

    assert response.status_code == 404

    body = response.json()

    assert body["detail"] == "Company not found"
    assert body["request_id"]
    assert response.headers["X-Request-ID"] == body["request_id"]

    with SessionLocal() as session:
        application = session.get(
            Application,
            application_id,
        )

        assert application is not None
        assert application.company_id == company_id


def test_update_application_rejects_invalid_salary_range() -> None:
    user_id, token = create_authenticated_user()
    company_id = create_company_directly(user_id)

    application_id = create_application_directly(
        user_id,
        company_id,
        salary_min=Decimal("50000.00"),
        salary_max=Decimal("70000.00"),
        currency="EUR",
    )

    response = client.patch(
        f"/api/v1/applications/{application_id}",
        headers=auth_headers(token),
        json={
            "salary_min": "80000.00",
        },
    )

    assert response.status_code == 422

    body = response.json()

    assert body["detail"] == "salary_min cannot be greater than salary_max"
    assert body["request_id"]
    assert response.headers["X-Request-ID"] == body["request_id"]


def test_update_application_does_not_modify_another_users_application() -> None:
    owner_id, _ = create_authenticated_user()
    _, other_user_token = create_authenticated_user()

    company_id = create_company_directly(owner_id)

    application_id = create_application_directly(
        owner_id,
        company_id,
        position="Backend Engineer",
    )

    response = client.patch(
        f"/api/v1/applications/{application_id}",
        headers=auth_headers(other_user_token),
        json={
            "position": "Not Allowed",
        },
    )

    assert response.status_code == 404

    body = response.json()

    assert body["detail"] == "Application not found"
    assert body["request_id"]
    assert response.headers["X-Request-ID"] == body["request_id"]

    with SessionLocal() as session:
        application = session.get(
            Application,
            application_id,
        )

        assert application is not None
        assert application.position == "Backend Engineer"


def test_delete_application_removes_application_and_events() -> None:
    user_id, token = create_authenticated_user()
    company_id = create_company_directly(user_id)

    application_id = create_application_directly(
        user_id,
        company_id,
    )

    with SessionLocal() as session:
        event_ids = list(
            session.scalars(
                select(ApplicationEvent.id).where(
                    ApplicationEvent.application_id == application_id
                )
            )
        )

    assert event_ids

    response = client.delete(
        f"/api/v1/applications/{application_id}",
        headers=auth_headers(token),
    )

    assert response.status_code == 204
    assert response.content == b""

    with SessionLocal() as session:
        assert (
            session.get(
                Application,
                application_id,
            )
            is None
        )

        remaining_events = list(
            session.scalars(
                select(ApplicationEvent).where(
                    ApplicationEvent.application_id == application_id
                )
            )
        )

        assert remaining_events == []


def test_delete_application_does_not_delete_another_users_application() -> None:
    owner_id, _ = create_authenticated_user()
    _, other_user_token = create_authenticated_user()

    company_id = create_company_directly(owner_id)

    application_id = create_application_directly(
        owner_id,
        company_id,
    )

    response = client.delete(
        f"/api/v1/applications/{application_id}",
        headers=auth_headers(other_user_token),
    )

    assert response.status_code == 404

    body = response.json()

    assert body["detail"] == "Application not found"
    assert body["request_id"]
    assert response.headers["X-Request-ID"] == body["request_id"]

    with SessionLocal() as session:
        assert (
            session.get(
                Application,
                application_id,
            )
            is not None
        )


def test_application_route_rejects_invalid_application_uuid() -> None:
    _, token = create_authenticated_user()

    response = client.get(
        "/api/v1/applications/not-a-uuid",
        headers=auth_headers(token),
    )

    assert response.status_code == 422


def test_list_applications_filters_by_status() -> None:
    user_id, token = create_authenticated_user()
    company_id = create_company_directly(user_id)

    applied_id = create_application_directly(
        user_id,
        company_id,
        position="Backend Engineer",
        status=ApplicationStatus.APPLIED,
    )

    create_application_directly(
        user_id,
        company_id,
        position="Platform Engineer",
        status=ApplicationStatus.SAVED,
    )

    response = client.get(
        "/api/v1/applications?status=applied",
        headers=auth_headers(token),
    )

    assert response.status_code == 200

    body = response.json()

    assert body["total"] == 1
    assert len(body["items"]) == 1
    assert body["items"][0]["id"] == str(applied_id)
    assert body["items"][0]["status"] == "applied"


def test_list_applications_filters_by_company() -> None:
    user_id, token = create_authenticated_user()

    stripe_id = create_company_directly(
        user_id,
        name="Stripe",
    )
    github_id = create_company_directly(
        user_id,
        name="GitHub",
    )

    expected_id = create_application_directly(
        user_id,
        stripe_id,
        position="Backend Engineer",
    )

    create_application_directly(
        user_id,
        github_id,
        position="Platform Engineer",
    )

    response = client.get(
        f"/api/v1/applications?company_id={stripe_id}",
        headers=auth_headers(token),
    )

    assert response.status_code == 200

    body = response.json()

    assert body["total"] == 1
    assert len(body["items"]) == 1
    assert body["items"][0]["id"] == str(expected_id)
    assert body["items"][0]["company_id"] == str(stripe_id)


def test_list_applications_searches_case_insensitively() -> None:
    user_id, token = create_authenticated_user()
    company_id = create_company_directly(user_id)

    expected_id = create_application_directly(
        user_id,
        company_id,
        position="Senior Backend Engineer",
    )

    create_application_directly(
        user_id,
        company_id,
        position="Platform Engineer",
    )

    response = client.get(
        "/api/v1/applications?search=BACKEND",
        headers=auth_headers(token),
    )

    assert response.status_code == 200

    body = response.json()

    assert body["total"] == 1
    assert len(body["items"]) == 1
    assert body["items"][0]["id"] == str(expected_id)
    assert body["items"][0]["position"] == "Senior Backend Engineer"


def test_list_applications_applies_pagination() -> None:
    user_id, token = create_authenticated_user()
    company_id = create_company_directly(user_id)

    for position in [
        "Alpha Engineer",
        "Bravo Engineer",
        "Charlie Engineer",
        "Delta Engineer",
        "Echo Engineer",
    ]:
        create_application_directly(
            user_id,
            company_id,
            position=position,
        )

    response = client.get(
        ("/api/v1/applications?limit=2&offset=2&sort_by=position&sort_order=asc"),
        headers=auth_headers(token),
    )

    assert response.status_code == 200

    body = response.json()

    assert body["total"] == 5
    assert body["limit"] == 2
    assert body["offset"] == 2

    assert [application["position"] for application in body["items"]] == [
        "Charlie Engineer",
        "Delta Engineer",
    ]


def test_list_applications_sorts_by_position_descending() -> None:
    user_id, token = create_authenticated_user()
    company_id = create_company_directly(user_id)

    for position in [
        "Alpha Engineer",
        "Charlie Engineer",
        "Bravo Engineer",
    ]:
        create_application_directly(
            user_id,
            company_id,
            position=position,
        )

    response = client.get(
        ("/api/v1/applications?sort_by=position&sort_order=desc"),
        headers=auth_headers(token),
    )

    assert response.status_code == 200

    body = response.json()

    assert body["total"] == 3

    assert [application["position"] for application in body["items"]] == [
        "Charlie Engineer",
        "Bravo Engineer",
        "Alpha Engineer",
    ]


def test_list_applications_rejects_invalid_pagination() -> None:
    _, token = create_authenticated_user()

    response = client.get(
        "/api/v1/applications?limit=101&offset=-1",
        headers=auth_headers(token),
    )

    assert response.status_code == 422
