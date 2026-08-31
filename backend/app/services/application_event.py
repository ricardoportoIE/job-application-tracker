import uuid

from sqlalchemy import select
from sqlalchemy.exc import SQLAlchemyError
from sqlalchemy.orm import Session

from app.models.application_event import ApplicationEvent
from app.models.enums import ApplicationEventType
from app.schemas.application_event import (
    ApplicationEventCreate,
    ApplicationEventUpdate,
)
from app.services.application import ApplicationService

AUTOMATIC_EVENT_TYPES: frozenset[ApplicationEventType] = frozenset(
    {
        ApplicationEventType.CREATED,
        ApplicationEventType.STATUS_CHANGED,
    }
)

MANUAL_EVENT_TYPES: frozenset[ApplicationEventType] = frozenset(
    {
        ApplicationEventType.INTERVIEW_SCHEDULED,
        ApplicationEventType.INTERVIEW_COMPLETED,
        ApplicationEventType.OFFER_RECEIVED,
        ApplicationEventType.NOTE_ADDED,
    }
)


class ApplicationEventNotFoundError(Exception):
    pass


class ApplicationEventTypeNotAllowedError(Exception):
    pass


class ApplicationEventStatusFieldsNotAllowedError(Exception):
    pass


class ApplicationEventImmutableError(Exception):
    pass


class ApplicationEventService:
    @staticmethod
    def _validate_manual_event(
        data: ApplicationEventCreate,
    ) -> None:
        if data.event_type not in MANUAL_EVENT_TYPES:
            raise ApplicationEventTypeNotAllowedError

        if data.from_status is not None or data.to_status is not None:
            raise ApplicationEventStatusFieldsNotAllowedError

    @staticmethod
    def _is_automatic_event(
        event: ApplicationEvent,
    ) -> bool:
        return event.event_type in AUTOMATIC_EVENT_TYPES

    @classmethod
    def create(
        cls,
        session: Session,
        user_id: uuid.UUID,
        application_id: uuid.UUID,
        data: ApplicationEventCreate,
    ) -> ApplicationEvent:
        application = ApplicationService.get(
            session,
            user_id,
            application_id,
        )

        cls._validate_manual_event(data)

        event = ApplicationEvent(
            application_id=application.id,
            event_type=data.event_type,
            from_status=None,
            to_status=None,
            occurred_at=data.occurred_at,
            notes=data.notes,
        )

        session.add(event)

        try:
            session.commit()
        except SQLAlchemyError:
            session.rollback()
            raise

        session.refresh(event)

        return event

    @staticmethod
    def list_for_application(
        session: Session,
        user_id: uuid.UUID,
        application_id: uuid.UUID,
    ) -> list[ApplicationEvent]:
        ApplicationService.get(
            session,
            user_id,
            application_id,
        )

        events = session.scalars(
            select(ApplicationEvent)
            .where(
                ApplicationEvent.application_id == application_id,
            )
            .order_by(
                ApplicationEvent.occurred_at.desc(),
                ApplicationEvent.created_at.desc(),
            )
        )

        return list(events.all())

    @staticmethod
    def get_by_id(
        session: Session,
        application_id: uuid.UUID,
        event_id: uuid.UUID,
    ) -> ApplicationEvent | None:
        return session.scalar(
            select(ApplicationEvent).where(
                ApplicationEvent.id == event_id,
                ApplicationEvent.application_id == application_id,
            )
        )

    @classmethod
    def get(
        cls,
        session: Session,
        user_id: uuid.UUID,
        application_id: uuid.UUID,
        event_id: uuid.UUID,
    ) -> ApplicationEvent:
        ApplicationService.get(
            session,
            user_id,
            application_id,
        )

        event = cls.get_by_id(
            session,
            application_id,
            event_id,
        )

        if event is None:
            raise ApplicationEventNotFoundError

        return event

    @classmethod
    def update(
        cls,
        session: Session,
        user_id: uuid.UUID,
        application_id: uuid.UUID,
        event_id: uuid.UUID,
        data: ApplicationEventUpdate,
    ) -> ApplicationEvent:
        event = cls.get(
            session,
            user_id,
            application_id,
            event_id,
        )

        changes = data.model_dump(
            exclude_unset=True,
        )

        if not changes:
            return event

        if cls._is_automatic_event(event):
            raise ApplicationEventImmutableError

        for field, value in changes.items():
            setattr(
                event,
                field,
                value,
            )

        try:
            session.commit()
        except SQLAlchemyError:
            session.rollback()
            raise

        session.refresh(event)

        return event

    @classmethod
    def delete(
        cls,
        session: Session,
        user_id: uuid.UUID,
        application_id: uuid.UUID,
        event_id: uuid.UUID,
    ) -> None:
        event = cls.get(
            session,
            user_id,
            application_id,
            event_id,
        )

        if cls._is_automatic_event(event):
            raise ApplicationEventImmutableError

        session.delete(event)

        try:
            session.commit()
        except SQLAlchemyError:
            session.rollback()
            raise
