from datetime import UTC, datetime
from decimal import Decimal
from uuid import uuid4

from sqlalchemy import select

from app.db.session import SessionLocal
from app.models.application import Application
from app.models.company import Company
from app.models.enums import ApplicationStatus, JobSource, WorkModel
from app.models.user import User


def main() -> None:
    email = f"application-test-{uuid4()}@example.com"

    with SessionLocal() as session:
        user = User(
            email=email,
            password_hash="test-password-hash",
        )

        company = Company(
            user=user,
            name="Example Tech",
            website="https://example.com",
            industry="Technology",
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
            job_url="https://example.com/jobs/backend-engineer",
            salary_min=Decimal("55000.00"),
            salary_max=Decimal("65000.00"),
            currency="EUR",
            applied_at=datetime.now(UTC),
            notes="Application model verification.",
        )

        session.add_all([user, company, application])
        session.commit()

        application_id = application.id
        user_id = user.id
        company_id = company.id

        print(f"Created user: {user.email}")
        print(f"Created company: {company.name}")
        print(f"Created application: {application.position}")
        print(f"Application status: {application.status}")
        print(
            f"Application salary: "
            f"{application.salary_min} - "
            f"{application.salary_max} "
            f"{application.currency}"
        )

    with SessionLocal() as session:
        reloaded_application = session.scalar(
            select(Application).where(Application.id == application_id)
        )

        if reloaded_application is None:
            raise RuntimeError("Application was not persisted")

        print()
        print("Reloaded from database:")
        print(f"Position: {reloaded_application.position}")
        print(f"Status: {reloaded_application.status}")
        print(f"Source: {reloaded_application.source}")
        print(f"Work model: {reloaded_application.work_model}")
        print(f"User: {reloaded_application.user.email}")
        print(f"Company: {reloaded_application.company.name}")
        print(f"Salary min type: {type(reloaded_application.salary_min).__name__}")
        print(f"Salary max type: {type(reloaded_application.salary_max).__name__}")

        assert reloaded_application.status is ApplicationStatus.APPLIED
        assert reloaded_application.source is JobSource.LINKEDIN
        assert reloaded_application.work_model is WorkModel.HYBRID
        assert reloaded_application.salary_min == Decimal("55000.00")
        assert reloaded_application.salary_max == Decimal("65000.00")
        assert reloaded_application.user.id == user_id
        assert reloaded_application.company.id == company_id

        session.delete(reloaded_application)
        session.commit()

        loaded_company = session.get(Company, company_id)
        loaded_user = session.get(User, user_id)

        if loaded_company is not None:
            session.delete(loaded_company)

        if loaded_user is not None:
            session.delete(loaded_user)

        session.commit()
        assert session.get(Application, application_id) is None
        assert session.get(Company, company_id) is None
        assert session.get(User, user_id) is None

    print()
    print("Application model verification and cleanup passed.")


if __name__ == "__main__":
    main()
