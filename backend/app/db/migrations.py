import os
from pathlib import Path

from alembic import command
from alembic.config import Config
from alembic.migration import MigrationContext
from alembic.script import ScriptDirectory
from psycopg import sql
from sqlalchemy import Connection, create_engine, text
from sqlalchemy.engine import URL, Engine

from app.core.config import BACKEND_DIR, settings
from app.db.session import engine as application_engine

MIGRATION_LOCK_ID = 726_381_941


class DatabaseSchemaError(RuntimeError):
    pass


def _alembic_config() -> Config:
    config = Config(str(BACKEND_DIR / "alembic.ini"))
    config.set_main_option(
        "script_location",
        str(BACKEND_DIR / "migrations"),
    )
    return config


def verify_database_schema(connection: Connection) -> None:
    config = _alembic_config()
    expected_heads = set(ScriptDirectory.from_config(config).get_heads())
    current_heads = set(MigrationContext.configure(connection).get_current_heads())

    if current_heads != expected_heads:
        raise DatabaseSchemaError(
            "Database schema is not at the expected Alembic head: "
            f"expected={sorted(expected_heads)}, current={sorted(current_heads)}"
        )


def _admin_engine() -> Engine:
    if settings.db_admin_user is None or settings.db_admin_password is None:
        return application_engine

    if settings.db_host is None or settings.db_name is None:
        raise DatabaseSchemaError("Administrative database settings are incomplete")

    url = URL.create(
        drivername="postgresql+psycopg",
        username=settings.db_admin_user,
        password=settings.db_admin_password.get_secret_value(),
        host=settings.db_host,
        port=settings.db_port,
        database=settings.db_name,
    )
    return create_engine(url, pool_pre_ping=True)


def _provision_application_role(connection: Connection) -> None:
    if settings.db_admin_user is None or settings.db_admin_password is None:
        return

    if settings.db_user is None or settings.db_password is None:
        raise DatabaseSchemaError("Application database credentials are incomplete")

    raw_connection = connection.connection.driver_connection
    assert raw_connection is not None
    role_name = settings.db_user
    role_password = settings.db_password.get_secret_value()

    with raw_connection.cursor() as cursor:
        cursor.execute(
            "SELECT 1 FROM pg_roles WHERE rolname = %s",
            (role_name,),
        )

        statement = "ALTER ROLE {} WITH LOGIN PASSWORD {}"
        if cursor.fetchone() is None:
            statement = "CREATE ROLE {} LOGIN PASSWORD {}"

        cursor.execute(
            sql.SQL(statement).format(
                sql.Identifier(role_name),
                sql.Literal(role_password),
            ),
        )


def _grant_application_privileges(connection: Connection) -> None:
    if settings.db_admin_user is None or settings.db_user is None:
        return

    raw_connection = connection.connection.driver_connection
    assert raw_connection is not None
    role = sql.Identifier(settings.db_user)
    owner = sql.Identifier(settings.db_admin_user)

    with raw_connection.cursor() as cursor:
        cursor.execute(
            sql.SQL("GRANT CONNECT ON DATABASE {} TO {}").format(
                sql.Identifier(settings.db_name or ""),
                role,
            )
        )
        cursor.execute(sql.SQL("GRANT USAGE ON SCHEMA public TO {}").format(role))
        cursor.execute(
            sql.SQL(
                "GRANT SELECT, INSERT, UPDATE, DELETE ON ALL TABLES "
                "IN SCHEMA public TO {}"
            ).format(role)
        )
        cursor.execute(
            sql.SQL(
                "GRANT USAGE, SELECT ON ALL SEQUENCES IN SCHEMA public TO {}"
            ).format(role)
        )
        cursor.execute(
            sql.SQL(
                "ALTER DEFAULT PRIVILEGES FOR ROLE {} IN SCHEMA public "
                "GRANT SELECT, INSERT, UPDATE, DELETE ON TABLES TO {}"
            ).format(owner, role)
        )
        cursor.execute(
            sql.SQL(
                "ALTER DEFAULT PRIVILEGES FOR ROLE {} IN SCHEMA public "
                "GRANT USAGE, SELECT ON SEQUENCES TO {}"
            ).format(owner, role)
        )


def migrate_and_verify() -> None:
    migration_engine = _admin_engine()
    config = _alembic_config()

    with migration_engine.begin() as connection:
        connection.execute(
            text("SELECT pg_advisory_xact_lock(:lock_id)"),
            {"lock_id": MIGRATION_LOCK_ID},
        )
        _provision_application_role(connection)
        config.attributes["connection"] = connection
        command.upgrade(config, "head")
        verify_database_schema(connection)
        _grant_application_privileges(connection)

    if migration_engine is not application_engine:
        migration_engine.dispose()


def main() -> None:
    os.chdir(Path(BACKEND_DIR))
    migrate_and_verify()


if __name__ == "__main__":
    main()
