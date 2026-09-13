from collections.abc import Generator

from sqlalchemy import create_engine
from sqlalchemy.orm import Session, sessionmaker

from app.core.config import settings

database_url = settings.database_url

if database_url is None:
    raise RuntimeError("Database URL was not resolved from application settings")

engine = create_engine(
    database_url,
    pool_pre_ping=True,
)

SessionLocal = sessionmaker(
    bind=engine,
    autoflush=False,
    expire_on_commit=False,
)


def get_db() -> Generator[Session]:
    session = SessionLocal()

    try:
        yield session
    finally:
        session.close()
