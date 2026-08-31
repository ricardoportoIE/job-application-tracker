import uuid

from sqlalchemy import select
from sqlalchemy.exc import IntegrityError
from sqlalchemy.orm import Session

from app.models.company import Company
from app.schemas.company import CompanyCreate, CompanyUpdate


class CompanyNotFoundError(Exception):
    pass


class CompanyInUseError(Exception):
    pass


class CompanyService:
    @staticmethod
    def create(
        session: Session,
        user_id: uuid.UUID,
        data: CompanyCreate,
    ) -> Company:
        company = Company(
            user_id=user_id,
            **data.model_dump(),
        )

        session.add(company)
        session.commit()
        session.refresh(company)

        return company

    @staticmethod
    def list_for_user(
        session: Session,
        user_id: uuid.UUID,
    ) -> list[Company]:
        result = session.scalars(
            select(Company)
            .where(Company.user_id == user_id)
            .order_by(
                Company.created_at.desc(),
                Company.name.asc(),
            )
        )

        return list(result.all())

    @staticmethod
    def get_by_id(
        session: Session,
        user_id: uuid.UUID,
        company_id: uuid.UUID,
    ) -> Company | None:
        return session.scalar(
            select(Company).where(
                Company.id == company_id,
                Company.user_id == user_id,
            )
        )

    @classmethod
    def get(
        cls,
        session: Session,
        user_id: uuid.UUID,
        company_id: uuid.UUID,
    ) -> Company:
        company = cls.get_by_id(
            session,
            user_id,
            company_id,
        )

        if company is None:
            raise CompanyNotFoundError

        return company

    @classmethod
    def update(
        cls,
        session: Session,
        user_id: uuid.UUID,
        company_id: uuid.UUID,
        data: CompanyUpdate,
    ) -> Company:
        company = cls.get(
            session,
            user_id,
            company_id,
        )

        changes = data.model_dump(
            exclude_unset=True,
        )

        if not changes:
            return company

        for field, value in changes.items():
            setattr(
                company,
                field,
                value,
            )

        session.commit()
        session.refresh(company)

        return company

    @classmethod
    def delete(
        cls,
        session: Session,
        user_id: uuid.UUID,
        company_id: uuid.UUID,
    ) -> None:
        company = cls.get(
            session,
            user_id,
            company_id,
        )

        session.delete(company)

        try:
            session.commit()
        except IntegrityError as exc:
            session.rollback()
            raise CompanyInUseError from exc
