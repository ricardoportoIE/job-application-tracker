import uuid
from typing import Annotated

from fastapi import APIRouter, Depends, HTTPException, status
from sqlalchemy.orm import Session

from app.api.dependencies import get_current_user
from app.db.session import get_db
from app.models.company import Company
from app.models.user import User
from app.schemas.company import CompanyCreate, CompanyRead, CompanyUpdate
from app.services.company import (
    CompanyInUseError,
    CompanyNotFoundError,
    CompanyService,
)

router = APIRouter(
    prefix="/companies",
    tags=["companies"],
)


@router.post(
    "",
    response_model=CompanyRead,
    status_code=status.HTTP_201_CREATED,
)
def create_company(
    data: CompanyCreate,
    current_user: Annotated[User, Depends(get_current_user)],
    session: Annotated[Session, Depends(get_db)],
) -> Company:
    return CompanyService.create(
        session,
        current_user.id,
        data,
    )


@router.get(
    "",
    response_model=list[CompanyRead],
    status_code=status.HTTP_200_OK,
)
def list_companies(
    current_user: Annotated[User, Depends(get_current_user)],
    session: Annotated[Session, Depends(get_db)],
) -> list[Company]:
    return CompanyService.list_for_user(
        session,
        current_user.id,
    )


@router.get(
    "/{company_id}",
    response_model=CompanyRead,
    status_code=status.HTTP_200_OK,
)
def get_company(
    company_id: uuid.UUID,
    current_user: Annotated[User, Depends(get_current_user)],
    session: Annotated[Session, Depends(get_db)],
) -> Company:
    try:
        return CompanyService.get(
            session,
            current_user.id,
            company_id,
        )
    except CompanyNotFoundError as exc:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Company not found",
        ) from exc


@router.patch(
    "/{company_id}",
    response_model=CompanyRead,
    status_code=status.HTTP_200_OK,
)
def update_company(
    company_id: uuid.UUID,
    data: CompanyUpdate,
    current_user: Annotated[User, Depends(get_current_user)],
    session: Annotated[Session, Depends(get_db)],
) -> Company:
    try:
        return CompanyService.update(
            session,
            current_user.id,
            company_id,
            data,
        )
    except CompanyNotFoundError as exc:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Company not found",
        ) from exc


@router.delete(
    "/{company_id}",
    status_code=status.HTTP_204_NO_CONTENT,
)
def delete_company(
    company_id: uuid.UUID,
    current_user: Annotated[User, Depends(get_current_user)],
    session: Annotated[Session, Depends(get_db)],
) -> None:
    try:
        CompanyService.delete(
            session,
            current_user.id,
            company_id,
        )
    except CompanyNotFoundError as exc:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Company not found",
        ) from exc
    except CompanyInUseError as exc:
        raise HTTPException(
            status_code=status.HTTP_409_CONFLICT,
            detail="Company has applications and cannot be deleted",
        ) from exc
