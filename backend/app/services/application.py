import uuid
from datetime import UTC, datetime
from decimal import Decimal
from typing import Any

from sqlalchemy import func, or_, select
from sqlalchemy.exc import SQLAlchemyError
from sqlalchemy.orm import Session

from app.models.application import Application
from app.models.application_event import ApplicationEvent
from app.models.company import Company
from app.models.enums import ApplicationEventType, ApplicationStatus
from app.schemas.application import ApplicationCreate, ApplicationUpdate
from app.schemas.application_query import ApplicationListParams
from app.services.company import CompanyService


class ApplicationNotFoundError(Exception):
    pass


class InvalidSalaryRangeError(Exception):
    pass


class ApplicationService:
    @staticmethod
    def _validate_salary_range(
        salary_min: Decimal | None,
        salary_max: Decimal | None,
    ) -> None:
        if (
            salary_min is not None
            and salary_max is not None
            and salary_min > salary_max
        ):
            raise InvalidSalaryRangeError

    @staticmethod
    def _normalize_currency(
        currency: str | None,
    ) -> str | None:
        if currency is None:
            return None

        return currency.upper()

    @staticmethod
    def _status_implies_application(
        status: ApplicationStatus,
    ) -> bool:
        return status is not ApplicationStatus.SAVED

    @staticmethod
    def _escape_like_pattern(value: str) -> str:
        return value.replace("\\", "\\\\").replace("%", "\\%").replace("_", "\\_")

    @classmethod
    def list_page_for_user(
        cls,
        session: Session,
        user_id: uuid.UUID,
        params: ApplicationListParams,
    ) -> tuple[list[Application], int]:
        conditions = [
            Application.user_id == user_id,
        ]

        if params.status is not None:
            conditions.append(
                Application.status == params.status,
            )

        if params.company_id is not None:
            conditions.append(
                Application.company_id == params.company_id,
            )

        if params.work_model is not None:
            conditions.append(
                Application.work_model == params.work_model,
            )

        if params.source is not None:
            conditions.append(
                Application.source == params.source,
            )

        if params.search is not None:
            escaped_search = cls._escape_like_pattern(
                params.search,
            )
            search_pattern = f"%{escaped_search}%"

            conditions.append(
                or_(
                    Application.position.ilike(
                        search_pattern,
                        escape="\\",
                    ),
                    Company.name.ilike(
                        search_pattern,
                        escape="\\",
                    ),
                    Application.location.ilike(
                        search_pattern,
                        escape="\\",
                    ),
                )
            )

        total_statement = (
            select(
                func.count(Application.id),
            )
            .select_from(Application)
            .join(
                Company,
                Application.company_id == Company.id,
            )
            .where(*conditions)
        )

        total = session.scalar(
            total_statement,
        )
        order_expression: Any

        if params.sort_by == "created_at":
            if params.sort_order == "asc":
                order_expression = Application.created_at.asc()
            else:
                order_expression = Application.created_at.desc()

        elif params.sort_by == "updated_at":
            if params.sort_order == "asc":
                order_expression = Application.updated_at.asc()
            else:
                order_expression = Application.updated_at.desc()

        elif params.sort_by == "position":
            if params.sort_order == "asc":
                order_expression = func.lower(
                    Application.position,
                ).asc()
            else:
                order_expression = func.lower(
                    Application.position,
                ).desc()

        else:
            if params.sort_order == "asc":
                order_expression = Application.applied_at.asc().nulls_last()
            else:
                order_expression = Application.applied_at.desc().nulls_last()

        if params.sort_order == "asc":
            id_order_expression = Application.id.asc()
        else:
            id_order_expression = Application.id.desc()

        statement = (
            select(Application)
            .join(
                Company,
                Application.company_id == Company.id,
            )
            .where(*conditions)
            .order_by(
                order_expression,
                id_order_expression,
            )
            .limit(params.limit)
            .offset(params.offset)
        )

        applications = session.scalars(
            statement,
        )

        return (
            list(applications.all()),
            int(total or 0),
        )

    @staticmethod
    def get_by_id(
        session: Session,
        user_id: uuid.UUID,
        application_id: uuid.UUID,
    ) -> Application | None:
        return session.scalar(
            select(Application).where(
                Application.id == application_id,
                Application.user_id == user_id,
            )
        )

    @classmethod
    def get(
        cls,
        session: Session,
        user_id: uuid.UUID,
        application_id: uuid.UUID,
    ) -> Application:
        application = cls.get_by_id(
            session,
            user_id,
            application_id,
        )

        if application is None:
            raise ApplicationNotFoundError

        return application

    @classmethod
    def create(
        cls,
        session: Session,
        user_id: uuid.UUID,
        data: ApplicationCreate,
    ) -> Application:
        CompanyService.get(
            session,
            user_id,
            data.company_id,
        )

        cls._validate_salary_range(
            data.salary_min,
            data.salary_max,
        )

        values = data.model_dump()

        values["currency"] = cls._normalize_currency(
            data.currency,
        )

        if data.applied_at is None and cls._status_implies_application(data.status):
            values["applied_at"] = datetime.now(UTC)

        application = Application(
            user_id=user_id,
            **values,
        )

        event = ApplicationEvent(
            application=application,
            event_type=ApplicationEventType.CREATED,
            from_status=None,
            to_status=application.status,
        )

        session.add_all(
            [
                application,
                event,
            ]
        )

        try:
            session.commit()
        except SQLAlchemyError:
            session.rollback()
            raise

        session.refresh(application)

        return application

    @classmethod
    def update(
        cls,
        session: Session,
        user_id: uuid.UUID,
        application_id: uuid.UUID,
        data: ApplicationUpdate,
    ) -> Application:
        application = cls.get(
            session,
            user_id,
            application_id,
        )

        changes = data.model_dump(
            exclude_unset=True,
        )

        if not changes:
            return application

        new_company_id = changes.get(
            "company_id",
            application.company_id,
        )

        if new_company_id != application.company_id:
            CompanyService.get(
                session,
                user_id,
                new_company_id,
            )

        salary_min = changes.get(
            "salary_min",
            application.salary_min,
        )

        salary_max = changes.get(
            "salary_max",
            application.salary_max,
        )

        cls._validate_salary_range(
            salary_min,
            salary_max,
        )

        if "currency" in changes:
            changes["currency"] = cls._normalize_currency(
                changes["currency"],
            )

        old_status = application.status

        new_status = changes.get(
            "status",
            old_status,
        )

        resulting_applied_at = changes.get(
            "applied_at",
            application.applied_at,
        )

        if resulting_applied_at is None and cls._status_implies_application(new_status):
            changes["applied_at"] = datetime.now(UTC)

        for field, value in changes.items():
            setattr(
                application,
                field,
                value,
            )

        if new_status is not old_status:
            event = ApplicationEvent(
                application=application,
                event_type=ApplicationEventType.STATUS_CHANGED,
                from_status=old_status,
                to_status=new_status,
            )

            session.add(event)

        try:
            session.commit()
        except SQLAlchemyError:
            session.rollback()
            raise

        session.refresh(application)

        return application

    @classmethod
    def delete(
        cls,
        session: Session,
        user_id: uuid.UUID,
        application_id: uuid.UUID,
    ) -> None:
        application = cls.get(
            session,
            user_id,
            application_id,
        )

        session.delete(application)

        try:
            session.commit()
        except SQLAlchemyError:
            session.rollback()
            raise
