import uuid
from collections.abc import Generator
from datetime import UTC, datetime, timedelta
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
from app.models.enums import (
    ApplicationEventType,
    ApplicationStatus,
)
from app.models.user import User
from app.schemas.application import ApplicationCreate
from app.schemas.application_event import ApplicationEventCreate
from app.schemas.company import CompanyCreate
from app.schemas.user import UserCreate
from app.services.application import ApplicationService
from app.services.application_event import ApplicationEventService
from app.services.company import CompanyService
from app.services.user import UserService

TEST_EMAIL_PREFIX = "application-event-route-test-"

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
) -> uuid.UUID:
    with SessionLocal() as session:
        application = ApplicationService.create(
            session,
            user_id,
            ApplicationCreate(
                company_id=company_id,
                position=position,
                status=status,
            ),
        )

        return application.id


def create_event_directly(
    user_id: uuid.UUID,
    application_id: uuid.UUID,
    *,
    event_type: ApplicationEventType = ApplicationEventType.NOTE_ADDED,
    occurred_at: datetime | None = None,
    notes: str | None = "Recruiter contacted me.",
) -> uuid.UUID:
    with SessionLocal() as session:
        data = ApplicationEventCreate(
            event_type=event_type,
            notes=notes,
        )

        if occurred_at is not None:
            data = ApplicationEventCreate(
                event_type=event_type,
                occurred_at=occurred_at,
                notes=notes,
            )

        event = ApplicationEventService.create(
            session,
            user_id,
            application_id,
            data,
        )

        return event.id


def get_created_event_id(
    application_id: uuid.UUID,
) -> uuid.UUID:
    with SessionLocal() as session:
        event_id = session.scalar(
            select(ApplicationEvent.id).where(
                ApplicationEvent.application_id == application_id,
                ApplicationEvent.event_type == ApplicationEventType.CREATED,
            )
        )

        if event_id is None:
            raise RuntimeError("CREATED event was not found")

        return event_id


def test_create_application_event_returns_created_event() -> None:
    user_id, token = create_authenticated_user()
    company_id = create_company_directly(user_id)
    application_id = create_application_directly(
        user_id,
        company_id,
    )

    occurred_at = datetime.now(UTC)

    response = client.post(
        f"/api/v1/applications/{application_id}/events",
        headers=auth_headers(token),
        json={
            "event_type": "interview_scheduled",
            "occurred_at": occurred_at.isoformat(),
            "notes": "Technical interview scheduled.",
        },
    )

    assert response.status_code == 201

    body = response.json()

    assert body["id"]
    assert body["application_id"] == str(application_id)
    assert body["event_type"] == "interview_scheduled"
    assert body["from_status"] is None
    assert body["to_status"] is None
    assert body["notes"] == "Technical interview scheduled."
    assert body["occurred_at"]
    assert body["created_at"]


def test_create_application_event_requires_authentication() -> None:
    response = client.post(
        f"/api/v1/applications/{uuid4()}/events",
        json={
            "event_type": "note_added",
            "notes": "Test note.",
        },
    )

    assert response.status_code == 401

    body = response.json()

    assert body["detail"] == "Could not validate credentials"
    assert body["request_id"]
    assert response.headers["X-Request-ID"] == body["request_id"]
    assert response.headers["www-authenticate"] == "Bearer"


@pytest.mark.parametrize(
    "event_type",
    [
        "created",
        "status_changed",
    ],
)
def test_create_application_event_rejects_automatic_event_types(
    event_type: str,
) -> None:
    user_id, token = create_authenticated_user()
    company_id = create_company_directly(user_id)
    application_id = create_application_directly(
        user_id,
        company_id,
    )

    response = client.post(
        f"/api/v1/applications/{application_id}/events",
        headers=auth_headers(token),
        json={
            "event_type": event_type,
        },
    )

    assert response.status_code == 422

    body = response.json()

    assert body["detail"] == "Event type cannot be created manually"
    assert body["request_id"]
    assert response.headers["X-Request-ID"] == body["request_id"]


def test_create_application_event_rejects_manual_status_fields() -> None:
    user_id, token = create_authenticated_user()
    company_id = create_company_directly(user_id)
    application_id = create_application_directly(
        user_id,
        company_id,
    )

    response = client.post(
        f"/api/v1/applications/{application_id}/events",
        headers=auth_headers(token),
        json={
            "event_type": "note_added",
            "from_status": "saved",
            "to_status": "applied",
            "notes": "Attempted fake transition.",
        },
    )

    assert response.status_code == 422

    body = response.json()

    assert body["detail"] == "from_status and to_status cannot be set manually"
    assert body["request_id"]
    assert response.headers["X-Request-ID"] == body["request_id"]


def test_create_application_event_rejects_another_users_application() -> None:
    owner_id, _ = create_authenticated_user()
    _, other_user_token = create_authenticated_user()

    company_id = create_company_directly(owner_id)
    application_id = create_application_directly(
        owner_id,
        company_id,
    )

    response = client.post(
        f"/api/v1/applications/{application_id}/events",
        headers=auth_headers(other_user_token),
        json={
            "event_type": "note_added",
            "notes": "Not allowed.",
        },
    )

    assert response.status_code == 404

    body = response.json()

    assert body["detail"] == "Application not found"
    assert body["request_id"]
    assert response.headers["X-Request-ID"] == body["request_id"]


def test_list_application_events_returns_timeline() -> None:
    user_id, token = create_authenticated_user()
    company_id = create_company_directly(user_id)
    application_id = create_application_directly(
        user_id,
        company_id,
    )

    now = datetime.now(UTC)

    older_event_id = create_event_directly(
        user_id,
        application_id,
        event_type=ApplicationEventType.NOTE_ADDED,
        occurred_at=now + timedelta(hours=1),
        notes="Older event.",
    )

    newer_event_id = create_event_directly(
        user_id,
        application_id,
        event_type=ApplicationEventType.INTERVIEW_SCHEDULED,
        occurred_at=now + timedelta(hours=2),
        notes="Newer event.",
    )

    response = client.get(
        f"/api/v1/applications/{application_id}/events",
        headers=auth_headers(token),
    )

    assert response.status_code == 200

    events = response.json()

    event_ids = [event["id"] for event in events]

    assert str(newer_event_id) in event_ids
    assert str(older_event_id) in event_ids

    assert event_ids.index(str(newer_event_id)) < event_ids.index(str(older_event_id))

    # A timeline também deve incluir o CREATED automático.
    assert any(event["event_type"] == "created" for event in events)


def test_list_application_events_rejects_another_users_application() -> None:
    owner_id, _ = create_authenticated_user()
    _, other_user_token = create_authenticated_user()

    company_id = create_company_directly(owner_id)
    application_id = create_application_directly(
        owner_id,
        company_id,
    )

    response = client.get(
        f"/api/v1/applications/{application_id}/events",
        headers=auth_headers(other_user_token),
    )

    assert response.status_code == 404

    body = response.json()

    assert body["detail"] == "Application not found"
    assert body["request_id"]
    assert response.headers["X-Request-ID"] == body["request_id"]


def test_get_application_event_returns_owned_event() -> None:
    user_id, token = create_authenticated_user()
    company_id = create_company_directly(user_id)
    application_id = create_application_directly(
        user_id,
        company_id,
    )

    event_id = create_event_directly(
        user_id,
        application_id,
        notes="Recruiter called.",
    )

    response = client.get(
        f"/api/v1/applications/{application_id}/events/{event_id}",
        headers=auth_headers(token),
    )

    assert response.status_code == 200

    body = response.json()

    assert body["id"] == str(event_id)
    assert body["application_id"] == str(application_id)
    assert body["event_type"] == "note_added"
    assert body["notes"] == "Recruiter called."


def test_get_application_event_rejects_event_from_different_application() -> None:
    user_id, token = create_authenticated_user()

    first_company_id = create_company_directly(
        user_id,
        name="Stripe",
    )
    second_company_id = create_company_directly(
        user_id,
        name="GitHub",
    )

    first_application_id = create_application_directly(
        user_id,
        first_company_id,
        position="Backend Engineer",
    )

    second_application_id = create_application_directly(
        user_id,
        second_company_id,
        position="Platform Engineer",
    )

    event_id = create_event_directly(
        user_id,
        first_application_id,
    )

    response = client.get(
        f"/api/v1/applications/{second_application_id}/events/{event_id}",
        headers=auth_headers(token),
    )

    assert response.status_code == 404

    body = response.json()

    assert body["detail"] == "Application event not found"
    assert body["request_id"]
    assert response.headers["X-Request-ID"] == body["request_id"]


def test_get_application_event_rejects_another_users_application() -> None:
    owner_id, _ = create_authenticated_user()
    _, other_user_token = create_authenticated_user()

    company_id = create_company_directly(owner_id)
    application_id = create_application_directly(
        owner_id,
        company_id,
    )

    event_id = create_event_directly(
        owner_id,
        application_id,
    )

    response = client.get(
        f"/api/v1/applications/{application_id}/events/{event_id}",
        headers=auth_headers(other_user_token),
    )

    assert response.status_code == 404

    body = response.json()

    assert body["detail"] == "Application not found"
    assert body["request_id"]
    assert response.headers["X-Request-ID"] == body["request_id"]


def test_update_manual_application_event_changes_allowed_fields() -> None:
    user_id, token = create_authenticated_user()
    company_id = create_company_directly(user_id)
    application_id = create_application_directly(
        user_id,
        company_id,
    )

    event_id = create_event_directly(
        user_id,
        application_id,
        event_type=ApplicationEventType.INTERVIEW_SCHEDULED,
        notes="Interview at 10:00.",
    )

    new_occurred_at = datetime.now(UTC) + timedelta(days=1)

    response = client.patch(
        f"/api/v1/applications/{application_id}/events/{event_id}",
        headers=auth_headers(token),
        json={
            "occurred_at": new_occurred_at.isoformat(),
            "notes": "Interview moved to 15:00.",
        },
    )

    assert response.status_code == 200

    body = response.json()

    assert body["id"] == str(event_id)
    assert body["event_type"] == "interview_scheduled"
    assert body["from_status"] is None
    assert body["to_status"] is None
    assert body["notes"] == "Interview moved to 15:00."


def test_update_automatic_application_event_returns_conflict() -> None:
    user_id, token = create_authenticated_user()
    company_id = create_company_directly(user_id)
    application_id = create_application_directly(
        user_id,
        company_id,
    )

    created_event_id = get_created_event_id(
        application_id,
    )

    response = client.patch(
        (f"/api/v1/applications/{application_id}/events/{created_event_id}"),
        headers=auth_headers(token),
        json={
            "notes": "Trying to rewrite history.",
        },
    )

    assert response.status_code == 409

    body = response.json()

    assert body["detail"] == "Automatic application events cannot be modified"
    assert body["request_id"]
    assert response.headers["X-Request-ID"] == body["request_id"]


def test_update_application_event_rejects_event_from_different_application() -> None:
    user_id, token = create_authenticated_user()

    first_company_id = create_company_directly(
        user_id,
        name="Stripe",
    )
    second_company_id = create_company_directly(
        user_id,
        name="GitHub",
    )

    first_application_id = create_application_directly(
        user_id,
        first_company_id,
    )

    second_application_id = create_application_directly(
        user_id,
        second_company_id,
    )

    event_id = create_event_directly(
        user_id,
        first_application_id,
    )

    response = client.patch(
        f"/api/v1/applications/{second_application_id}/events/{event_id}",
        headers=auth_headers(token),
        json={
            "notes": "Not allowed.",
        },
    )

    assert response.status_code == 404

    body = response.json()

    assert body["detail"] == "Application event not found"
    assert body["request_id"]
    assert response.headers["X-Request-ID"] == body["request_id"]


def test_delete_manual_application_event_removes_event() -> None:
    user_id, token = create_authenticated_user()
    company_id = create_company_directly(user_id)
    application_id = create_application_directly(
        user_id,
        company_id,
    )

    event_id = create_event_directly(
        user_id,
        application_id,
        notes="Temporary note.",
    )

    response = client.delete(
        f"/api/v1/applications/{application_id}/events/{event_id}",
        headers=auth_headers(token),
    )

    assert response.status_code == 204
    assert response.content == b""

    with SessionLocal() as session:
        assert (
            session.get(
                ApplicationEvent,
                event_id,
            )
            is None
        )


def test_delete_automatic_application_event_returns_conflict() -> None:
    user_id, token = create_authenticated_user()
    company_id = create_company_directly(user_id)
    application_id = create_application_directly(
        user_id,
        company_id,
    )

    created_event_id = get_created_event_id(
        application_id,
    )

    response = client.delete(
        (f"/api/v1/applications/{application_id}/events/{created_event_id}"),
        headers=auth_headers(token),
    )

    assert response.status_code == 409

    body = response.json()

    assert body["detail"] == "Automatic application events cannot be deleted"
    assert body["request_id"]
    assert response.headers["X-Request-ID"] == body["request_id"]

    with SessionLocal() as session:
        assert (
            session.get(
                ApplicationEvent,
                created_event_id,
            )
            is not None
        )


def test_delete_application_event_rejects_another_users_application() -> None:
    owner_id, _ = create_authenticated_user()
    _, other_user_token = create_authenticated_user()

    company_id = create_company_directly(owner_id)
    application_id = create_application_directly(
        owner_id,
        company_id,
    )

    event_id = create_event_directly(
        owner_id,
        application_id,
    )

    response = client.delete(
        f"/api/v1/applications/{application_id}/events/{event_id}",
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
                ApplicationEvent,
                event_id,
            )
            is not None
        )


def test_application_event_route_rejects_invalid_application_uuid() -> None:
    _, token = create_authenticated_user()

    response = client.get(
        "/api/v1/applications/not-a-uuid/events",
        headers=auth_headers(token),
    )

    assert response.status_code == 422


def test_application_event_route_rejects_invalid_event_uuid() -> None:
    user_id, token = create_authenticated_user()
    company_id = create_company_directly(user_id)
    application_id = create_application_directly(
        user_id,
        company_id,
    )

    response = client.get(
        f"/api/v1/applications/{application_id}/events/not-a-uuid",
        headers=auth_headers(token),
    )

    assert response.status_code == 422
