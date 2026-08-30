from __future__ import annotations

import uuid
from datetime import datetime
from decimal import Decimal
from typing import TYPE_CHECKING

from sqlalchemy import (
    CheckConstraint,
    DateTime,
    Enum,
    ForeignKey,
    Numeric,
    String,
    Text,
    Uuid,
)
from sqlalchemy.orm import Mapped, mapped_column, relationship

from app.db.base import Base
from app.models.enums import ApplicationStatus, JobSource, WorkModel
from app.models.mixins import TimestampMixin, UUIDPrimaryKeyMixin

if TYPE_CHECKING:
    from app.models.company import Company
    from app.models.user import User


class Application(UUIDPrimaryKeyMixin, TimestampMixin, Base):
    __tablename__ = "applications"

    __table_args__ = (
        CheckConstraint(
            "status IN ("
            "'saved', "
            "'applied', "
            "'screening', "
            "'interview', "
            "'technical_interview', "
            "'final_interview', "
            "'offer', "
            "'accepted', "
            "'rejected', "
            "'withdrawn'"
            ")",
            name="application_status",
        ),
        CheckConstraint(
            "source IN ("
            "'linkedin', "
            "'indeed', "
            "'company_website', "
            "'recruiter', "
            "'referral', "
            "'other'"
            ")",
            name="job_source",
        ),
        CheckConstraint(
            "work_model IN ('onsite', 'hybrid', 'remote')",
            name="work_model",
        ),
    )

    user_id: Mapped[uuid.UUID] = mapped_column(
        Uuid,
        ForeignKey("users.id", ondelete="CASCADE"),
        nullable=False,
        index=True,
    )

    company_id: Mapped[uuid.UUID] = mapped_column(
        Uuid,
        ForeignKey("companies.id", ondelete="RESTRICT"),
        nullable=False,
        index=True,
    )

    position: Mapped[str] = mapped_column(
        String(200),
        nullable=False,
    )

    status: Mapped[ApplicationStatus] = mapped_column(
        Enum(
            ApplicationStatus,
            name="application_status",
            native_enum=False,
            create_constraint=False,
            values_callable=lambda enum: [item.value for item in enum],
        ),
        nullable=False,
        default=ApplicationStatus.SAVED,
        server_default=ApplicationStatus.SAVED.value,
    )

    source: Mapped[JobSource | None] = mapped_column(
        Enum(
            JobSource,
            name="job_source",
            native_enum=False,
            create_constraint=False,
            values_callable=lambda enum: [item.value for item in enum],
        ),
        nullable=True,
    )

    work_model: Mapped[WorkModel | None] = mapped_column(
        Enum(
            WorkModel,
            name="work_model",
            native_enum=False,
            create_constraint=False,
            values_callable=lambda enum: [item.value for item in enum],
        ),
        nullable=True,
    )

    location: Mapped[str | None] = mapped_column(
        String(255),
        nullable=True,
    )

    job_url: Mapped[str | None] = mapped_column(
        String(2048),
        nullable=True,
    )

    salary_min: Mapped[Decimal | None] = mapped_column(
        Numeric(12, 2),
        nullable=True,
    )

    salary_max: Mapped[Decimal | None] = mapped_column(
        Numeric(12, 2),
        nullable=True,
    )

    currency: Mapped[str | None] = mapped_column(
        String(3),
        nullable=True,
    )

    applied_at: Mapped[datetime | None] = mapped_column(
        DateTime(timezone=True),
        nullable=True,
    )

    notes: Mapped[str | None] = mapped_column(
        Text,
        nullable=True,
    )
    user: Mapped[User] = relationship(
        back_populates="applications",
    )

    company: Mapped[Company] = relationship(
        back_populates="applications",
    )
