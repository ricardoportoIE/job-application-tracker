import uuid
from typing import Annotated

from fastapi import APIRouter, Depends, HTTPException, status
from sqlalchemy.orm import Session

from app.api.dependencies import get_current_user
from app.db.session import get_db
from app.models.application import Application
from app.models.user import User
from app.schemas.application import (
    ApplicationCreate,
    ApplicationRead,
    ApplicationUpdate,
)
from app.services.application import (
    ApplicationNotFoundError,
    ApplicationService,
    InvalidSalaryRangeError,
)
from app.services.company import CompanyNotFoundError

router = APIRouter(
    prefix="/applications",
    tags=["applications"],
)


@router.post(
    "",
    response_model=ApplicationRead,
    status_code=status.HTTP_201_CREATED,
)
def create_application(
    data: ApplicationCreate,
    current_user: Annotated[User, Depends(get_current_user)],
    session: Annotated[Session, Depends(get_db)],
) -> Application:
    try:
        return ApplicationService.create(
            session,
            current_user.id,
            data,
        )
    except CompanyNotFoundError as exc:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Company not found",
        ) from exc
    except InvalidSalaryRangeError as exc:
        raise HTTPException(
            status_code=status.HTTP_422_UNPROCESSABLE_CONTENT,
            detail="salary_min cannot be greater than salary_max",
        ) from exc


@router.get(
    "",
    response_model=list[ApplicationRead],
    status_code=status.HTTP_200_OK,
)
def list_applications(
    current_user: Annotated[User, Depends(get_current_user)],
    session: Annotated[Session, Depends(get_db)],
) -> list[Application]:
    return ApplicationService.list_for_user(
        session,
        current_user.id,
    )


@router.get(
    "/{application_id}",
    response_model=ApplicationRead,
    status_code=status.HTTP_200_OK,
)
def get_application(
    application_id: uuid.UUID,
    current_user: Annotated[User, Depends(get_current_user)],
    session: Annotated[Session, Depends(get_db)],
) -> Application:
    try:
        return ApplicationService.get(
            session,
            current_user.id,
            application_id,
        )
    except ApplicationNotFoundError as exc:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Application not found",
        ) from exc


@router.patch(
    "/{application_id}",
    response_model=ApplicationRead,
    status_code=status.HTTP_200_OK,
)
def update_application(
    application_id: uuid.UUID,
    data: ApplicationUpdate,
    current_user: Annotated[User, Depends(get_current_user)],
    session: Annotated[Session, Depends(get_db)],
) -> Application:
    try:
        return ApplicationService.update(
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
    except CompanyNotFoundError as exc:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Company not found",
        ) from exc
    except InvalidSalaryRangeError as exc:
        raise HTTPException(
            status_code=status.HTTP_422_UNPROCESSABLE_CONTENT,
            detail="salary_min cannot be greater than salary_max",
        ) from exc


@router.delete(
    "/{application_id}",
    status_code=status.HTTP_204_NO_CONTENT,
)
def delete_application(
    application_id: uuid.UUID,
    current_user: Annotated[User, Depends(get_current_user)],
    session: Annotated[Session, Depends(get_db)],
) -> None:
    try:
        ApplicationService.delete(
            session,
            current_user.id,
            application_id,
        )
    except ApplicationNotFoundError as exc:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Application not found",
        ) from exc
