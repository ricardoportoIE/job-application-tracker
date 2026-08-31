import uuid
from typing import Annotated

from fastapi import APIRouter, Depends, HTTPException, status
from sqlalchemy.orm import Session

from app.api.dependencies import get_current_user
from app.db.session import get_db
from app.models.application_event import ApplicationEvent
from app.models.user import User
from app.schemas.application_event import (
    ApplicationEventCreate,
    ApplicationEventRead,
    ApplicationEventUpdate,
)
from app.services.application import ApplicationNotFoundError
from app.services.application_event import (
    ApplicationEventImmutableError,
    ApplicationEventNotFoundError,
    ApplicationEventService,
    ApplicationEventStatusFieldsNotAllowedError,
    ApplicationEventTypeNotAllowedError,
)

router = APIRouter(
    prefix="/applications/{application_id}/events",
    tags=["application-events"],
)


@router.post(
    "",
    response_model=ApplicationEventRead,
    status_code=status.HTTP_201_CREATED,
)
def create_application_event(
    application_id: uuid.UUID,
    data: ApplicationEventCreate,
    current_user: Annotated[User, Depends(get_current_user)],
    session: Annotated[Session, Depends(get_db)],
) -> ApplicationEvent:
    try:
        return ApplicationEventService.create(
            session,
            current_user.id,
            application_id,
            data,
        )
    except ApplicationNotFoundError as exc:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Application not found",
        ) from exc
    except ApplicationEventTypeNotAllowedError as exc:
        raise HTTPException(
            status_code=status.HTTP_422_UNPROCESSABLE_CONTENT,
            detail="Event type cannot be created manually",
        ) from exc
    except ApplicationEventStatusFieldsNotAllowedError as exc:
        raise HTTPException(
            status_code=status.HTTP_422_UNPROCESSABLE_CONTENT,
            detail="from_status and to_status cannot be set manually",
        ) from exc


@router.get(
    "",
    response_model=list[ApplicationEventRead],
    status_code=status.HTTP_200_OK,
)
def list_application_events(
    application_id: uuid.UUID,
    current_user: Annotated[User, Depends(get_current_user)],
    session: Annotated[Session, Depends(get_db)],
) -> list[ApplicationEvent]:
    try:
        return ApplicationEventService.list_for_application(
            session,
            current_user.id,
            application_id,
        )
    except ApplicationNotFoundError as exc:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Application not found",
        ) from exc


@router.get(
    "/{event_id}",
    response_model=ApplicationEventRead,
    status_code=status.HTTP_200_OK,
)
def get_application_event(
    application_id: uuid.UUID,
    event_id: uuid.UUID,
    current_user: Annotated[User, Depends(get_current_user)],
    session: Annotated[Session, Depends(get_db)],
) -> ApplicationEvent:
    try:
        return ApplicationEventService.get(
            session,
            current_user.id,
            application_id,
            event_id,
        )
    except ApplicationNotFoundError as exc:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Application not found",
        ) from exc
    except ApplicationEventNotFoundError as exc:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Application event not found",
        ) from exc


@router.patch(
    "/{event_id}",
    response_model=ApplicationEventRead,
    status_code=status.HTTP_200_OK,
)
def update_application_event(
    application_id: uuid.UUID,
    event_id: uuid.UUID,
    data: ApplicationEventUpdate,
    current_user: Annotated[User, Depends(get_current_user)],
    session: Annotated[Session, Depends(get_db)],
) -> ApplicationEvent:
    try:
        return ApplicationEventService.update(
            session,
            current_user.id,
            application_id,
            event_id,
            data,
        )
    except ApplicationNotFoundError as exc:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Application not found",
        ) from exc
    except ApplicationEventNotFoundError as exc:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Application event not found",
        ) from exc
    except ApplicationEventImmutableError as exc:
        raise HTTPException(
            status_code=status.HTTP_409_CONFLICT,
            detail="Automatic application events cannot be modified",
        ) from exc


@router.delete(
    "/{event_id}",
    status_code=status.HTTP_204_NO_CONTENT,
)
def delete_application_event(
    application_id: uuid.UUID,
    event_id: uuid.UUID,
    current_user: Annotated[User, Depends(get_current_user)],
    session: Annotated[Session, Depends(get_db)],
) -> None:
    try:
        ApplicationEventService.delete(
            session,
            current_user.id,
            application_id,
            event_id,
        )
    except ApplicationNotFoundError as exc:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Application not found",
        ) from exc
    except ApplicationEventNotFoundError as exc:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Application event not found",
        ) from exc
    except ApplicationEventImmutableError as exc:
        raise HTTPException(
            status_code=status.HTTP_409_CONFLICT,
            detail="Automatic application events cannot be deleted",
        ) from exc
