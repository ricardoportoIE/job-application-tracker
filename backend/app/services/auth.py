from sqlalchemy.orm import Session

from app.core.security import create_access_token, verify_password
from app.models.user import User
from app.schemas.auth import TokenResponse
from app.services.user import UserService


class InvalidCredentialsError(Exception):
    pass


class InactiveUserError(Exception):
    pass


class AuthService:
    @staticmethod
    def authenticate(
        session: Session,
        email: str,
        password: str,
    ) -> User:
        user = UserService.get_by_email(
            session,
            email,
        )

        if user is None:
            raise InvalidCredentialsError

        if not verify_password(
            password,
            user.password_hash,
        ):
            raise InvalidCredentialsError

        if not user.is_active:
            raise InactiveUserError

        return user

    @classmethod
    def login(
        cls,
        session: Session,
        email: str,
        password: str,
    ) -> TokenResponse:
        user = cls.authenticate(
            session,
            email,
            password,
        )

        access_token = create_access_token(
            subject=str(user.id),
        )

        return TokenResponse(
            access_token=access_token,
        )
