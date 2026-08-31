from sqlalchemy import text

from app.db.session import SessionLocal


def test_tests_use_dedicated_database() -> None:
    with SessionLocal() as session:
        database_name = session.scalar(text("SELECT current_database()"))

    assert database_name == "jobtracker_test"
