import logging
from typing import Annotated

from fastapi import APIRouter, Depends, HTTPException, status
from sqlalchemy.orm import Session

from app.api.dependencies import get_current_user
from app.api.openapi import error_responses
from app.db.session import get_db
from app.models.user import User
from app.schemas.auth import LoginRequest, TokenResponse
from app.schemas.user import UserCreate, UserRead
from app.services.auth import (
    AuthService,
    InactiveUserError,
    InvalidCredentialsError,
)
from app.services.user import UserAlreadyExistsError, UserService

logger = logging.getLogger(__name__)

router = APIRouter(
    prefix="/auth",
    tags=["auth"],
)


@router.post(
    "/register",
    response_model=UserRead,
    status_code=status.HTTP_201_CREATED,
    responses=error_responses(
        409,
        422,
        500,
    ),
)
def register_user(
    data: UserCreate,
    session: Annotated[Session, Depends(get_db)],
) -> User:
    try:
        return UserService.create(
            session,
            data,
        )
    except UserAlreadyExistsError as exc:
        raise HTTPException(
            status_code=status.HTTP_409_CONFLICT,
            detail="Email already registered",
        ) from exc


@router.post(
    "/login",
    response_model=TokenResponse,
    status_code=status.HTTP_200_OK,
    responses=error_responses(
        401,
        403,
        422,
        500,
    ),
)
def login(
    data: LoginRequest,
    session: Annotated[Session, Depends(get_db)],
) -> TokenResponse:
    try:
        token = AuthService.login(
            session,
            str(data.email),
            data.password,
        )
    except InvalidCredentialsError as exc:
        logger.warning(
            "Authentication failed",
            extra={
                "event": "auth.login.failed",
            },
        )

        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Invalid credentials",
            headers={"WWW-Authenticate": "Bearer"},
        ) from exc
    except InactiveUserError as exc:
        logger.warning(
            "Authentication rejected for inactive user",
            extra={
                "event": "auth.login.inactive",
            },
        )

        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="Inactive user",
        ) from exc

    logger.info(
        "Authentication succeeded",
        extra={
            "event": "auth.login.succeeded",
        },
    )

    return token


@router.get(
    "/me",
    response_model=UserRead,
    status_code=status.HTTP_200_OK,
    responses=error_responses(
        401,
        403,
        500,
    ),
)
def get_me(
    current_user: Annotated[User, Depends(get_current_user)],
) -> User:
    return current_user
