from unittest.mock import MagicMock, patch

import pytest
from sqlalchemy import text
from sqlalchemy.orm import Session

from app.db.session import get_db


def test_get_db_provides_working_database_session() -> None:
    dependency = get_db()
    session = next(dependency)

    try:
        result = session.scalar(text("SELECT 1"))

        assert result == 1
    finally:
        dependency.close()


def test_get_db_closes_session_after_use() -> None:
    mock_session = MagicMock(spec=Session)

    with patch(
        "app.db.session.SessionLocal",
        return_value=mock_session,
    ):
        dependency = get_db()

        yielded_session = next(dependency)

        assert yielded_session is mock_session

        with pytest.raises(StopIteration):
            next(dependency)

        mock_session.close.assert_called_once_with()
