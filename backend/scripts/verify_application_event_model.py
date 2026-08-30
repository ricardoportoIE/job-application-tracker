from datetime import UTC, datetime
from uuid import uuid4

from sqlalchemy import select

from app.db.session import SessionLocal
from app.models.application import Application
from app.models.application_event import ApplicationEvent
from app.models.company import Company
from app.models.enums import (
    ApplicationEventType,
    ApplicationStatus,
    JobSource,
    WorkModel,
)
from app.models.user import User


def main() -> None:
    email = f"application-event-test-{uuid4()}@example.com"

    with SessionLocal() as session:
        user = User(
            email=email,
            password_hash="test-password-hash",
        )

        company = Company(
            user=user,
            name="Example Tech",
            location="Dublin, Ireland",
        )

        application = Application(
            user=user,
            company=company,
            position="Backend Engineer",
            status=ApplicationStatus.APPLIED,
            source=JobSource.LINKEDIN,
            work_model=WorkModel.HYBRID,
            location="Dublin, Ireland",
            applied_at=datetime.now(UTC),
        )

        event = ApplicationEvent(
            application=application,
            event_type=ApplicationEventType.STATUS_CHANGED,
            from_status=ApplicationStatus.SAVED,
            to_status=ApplicationStatus.APPLIED,
            occurred_at=datetime.now(UTC),
            notes="Application submitted.",
        )

        session.add_all([user, company, application, event])
        session.commit()

        user_id = user.id
        company_id = company.id
        application_id = application.id
        event_id = event.id

        print(f"Created application: {application.position}")
        print(f"Created event: {event.event_type}")
        print(f"From status: {event.from_status}")
        print(f"To status: {event.to_status}")

    with SessionLocal() as session:
        reloaded_event = session.scalar(
            select(ApplicationEvent).where(ApplicationEvent.id == event_id)
        )

        if reloaded_event is None:
            raise RuntimeError("Application event was not persisted")

        print()
        print("Reloaded from database:")
        print(f"Event type: {reloaded_event.event_type}")
        print(f"From status: {reloaded_event.from_status}")
        print(f"To status: {reloaded_event.to_status}")
        print(f"Application: {reloaded_event.application.position}")
        print(f"Notes: {reloaded_event.notes}")
        print(f"Occurred at: {reloaded_event.occurred_at}")
        print(f"Created at: {reloaded_event.created_at}")

        assert reloaded_event.event_type is ApplicationEventType.STATUS_CHANGED
        assert reloaded_event.from_status is ApplicationStatus.SAVED
        assert reloaded_event.to_status is ApplicationStatus.APPLIED
        assert reloaded_event.application.id == application_id

        reloaded_application = session.get(Application, application_id)

        if reloaded_application is None:
            raise RuntimeError("Application was not persisted")

        assert any(
            application_event.id == event_id
            for application_event in reloaded_application.events
        )

        print(f"Application events: {len(reloaded_application.events)}")

        session.delete(reloaded_application)
        session.commit()

        assert session.get(ApplicationEvent, event_id) is None
        assert session.get(Application, application_id) is None

        loaded_company = session.get(Company, company_id)
        loaded_user = session.get(User, user_id)

        if loaded_company is not None:
            session.delete(loaded_company)

        if loaded_user is not None:
            session.delete(loaded_user)

        session.commit()

        assert session.get(Company, company_id) is None
        assert session.get(User, user_id) is None

    print()
    print("Application event model verification and cleanup passed.")


if __name__ == "__main__":
    main()
