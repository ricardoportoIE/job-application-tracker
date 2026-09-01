"""add application query indexes

Revision ID: d4a3a7cc59ce
Revises: dff581848917
"""

from collections.abc import Sequence

from alembic import op

revision: str = "d4a3a7cc59ce"
down_revision: str | None = "dff581848917"
branch_labels: str | Sequence[str] | None = None
depends_on: str | Sequence[str] | None = None


def upgrade() -> None:
    op.create_index(
        "ix_applications_user_created_at",
        "applications",
        ["user_id", "created_at"],
        unique=False,
    )

    op.create_index(
        "ix_applications_user_status_created_at",
        "applications",
        ["user_id", "status", "created_at"],
        unique=False,
    )

    op.create_index(
        "ix_applications_user_company_created_at",
        "applications",
        ["user_id", "company_id", "created_at"],
        unique=False,
    )


def downgrade() -> None:
    op.drop_index(
        "ix_applications_user_company_created_at",
        table_name="applications",
    )

    op.drop_index(
        "ix_applications_user_status_created_at",
        table_name="applications",
    )

    op.drop_index(
        "ix_applications_user_created_at",
        table_name="applications",
    )
