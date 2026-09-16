from unittest.mock import MagicMock, patch

import pytest

from app.db.migrations import DatabaseSchemaError, verify_database_schema


def test_verify_database_schema_accepts_current_head() -> None:
    connection = MagicMock()

    with (
        patch("app.db.migrations.ScriptDirectory.from_config") as script_directory,
        patch("app.db.migrations.MigrationContext.configure") as migration_context,
    ):
        script_directory.return_value.get_heads.return_value = ["current-head"]
        migration_context.return_value.get_current_heads.return_value = (
            "current-head",
        )

        verify_database_schema(connection)


def test_verify_database_schema_rejects_outdated_database() -> None:
    connection = MagicMock()

    with (
        patch("app.db.migrations.ScriptDirectory.from_config") as script_directory,
        patch("app.db.migrations.MigrationContext.configure") as migration_context,
    ):
        script_directory.return_value.get_heads.return_value = ["expected-head"]
        migration_context.return_value.get_current_heads.return_value = ("old-head",)

        with pytest.raises(DatabaseSchemaError, match="not at the expected"):
            verify_database_schema(connection)
