from __future__ import annotations

import uuid
from datetime import datetime
from typing import TYPE_CHECKING

from sqlalchemy import (
    CheckConstraint,
    DateTime,
    Enum,
    ForeignKey,
    Text,
    Uuid,
    func,
)
from sqlalchemy.orm import Mapped, mapped_column, relationship

from app.db.base import Base
from app.models.enums import ApplicationEventType, ApplicationStatus
from app.models.mixins import UUIDPrimaryKeyMixin

if TYPE_CHECKING:
    from app.models.application import Application


class ApplicationEvent(UUIDPrimaryKeyMixin, Base):
    __tablename__ = "application_events"

    __table_args__ = (
        CheckConstraint(
            "event_type IN ("
            "'created', "
            "'status_changed', "
            "'interview_scheduled', "
            "'interview_completed', "
            "'offer_received', "
            "'note_added'"
            ")",
            name="application_event_type",
        ),
        CheckConstraint(
            "from_status IN ("
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
            name="application_event_from_status",
        ),
        CheckConstraint(
            "to_status IN ("
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
            name="application_event_to_status",
        ),
    )

    application_id: Mapped[uuid.UUID] = mapped_column(
        Uuid,
        ForeignKey("applications.id", ondelete="CASCADE"),
        nullable=False,
        index=True,
    )

    event_type: Mapped[ApplicationEventType] = mapped_column(
        Enum(
            ApplicationEventType,
            name="application_event_type",
            native_enum=False,
            create_constraint=False,
            values_callable=lambda enum: [item.value for item in enum],
        ),
        nullable=False,
    )

    from_status: Mapped[ApplicationStatus | None] = mapped_column(
        Enum(
            ApplicationStatus,
            name="application_status",
            native_enum=False,
            create_constraint=False,
            values_callable=lambda enum: [item.value for item in enum],
        ),
        nullable=True,
    )

    to_status: Mapped[ApplicationStatus | None] = mapped_column(
        Enum(
            ApplicationStatus,
            name="application_status",
            native_enum=False,
            create_constraint=False,
            values_callable=lambda enum: [item.value for item in enum],
        ),
        nullable=True,
    )

    occurred_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True),
        nullable=False,
        server_default=func.now(),
    )

    notes: Mapped[str | None] = mapped_column(
        Text,
        nullable=True,
    )

    created_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True),
        nullable=False,
        server_default=func.now(),
    )
    application: Mapped[Application] = relationship(
        back_populates="events",
    )
