from sqlalchemy import select
from sqlalchemy.exc import IntegrityError
from sqlalchemy.orm import Session

from app.core.security import hash_password
from app.models.user import User
from app.schemas.user import UserCreate


class UserAlreadyExistsError(Exception):
    pass


class UserService:
    @staticmethod
    def get_by_email(
        session: Session,
        email: str,
    ) -> User | None:
        normalized_email = email.strip().lower()

        return session.scalar(select(User).where(User.email == normalized_email))

    @classmethod
    def create(
        cls,
        session: Session,
        data: UserCreate,
    ) -> User:
        normalized_email = str(data.email).lower()

        existing_user = cls.get_by_email(
            session,
            normalized_email,
        )

        if existing_user is not None:
            raise UserAlreadyExistsError

        user = User(
            email=normalized_email,
            password_hash=hash_password(data.password),
        )

        session.add(user)

        try:
            session.commit()
        except IntegrityError as exc:
            session.rollback()
            raise UserAlreadyExistsError from exc

        session.refresh(user)

        return user
