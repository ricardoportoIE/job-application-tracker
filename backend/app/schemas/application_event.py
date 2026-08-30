import uuid
from datetime import UTC, datetime
from typing import Self

from pydantic import BaseModel, ConfigDict, Field, model_validator

from app.models.enums import ApplicationEventType, ApplicationStatus


class ApplicationEventCreate(BaseModel):
    model_config = ConfigDict(str_strip_whitespace=True, extra="forbid")

    event_type: ApplicationEventType
    from_status: ApplicationStatus | None = None
    to_status: ApplicationStatus | None = None
    occurred_at: datetime = Field(
        default_factory=lambda: datetime.now(UTC),
    )
    notes: str | None = None


class ApplicationEventUpdate(BaseModel):
    model_config = ConfigDict(
        str_strip_whitespace=True,
        extra="forbid",
    )

    occurred_at: datetime | None = None
    notes: str | None = None

    @model_validator(mode="after")
    def reject_null_occurred_at(self) -> Self:
        if "occurred_at" in self.model_fields_set and self.occurred_at is None:
            raise ValueError("occurred_at cannot be null")

        return self


class ApplicationEventRead(BaseModel):
    id: uuid.UUID
    application_id: uuid.UUID
    event_type: ApplicationEventType
    from_status: ApplicationStatus | None
    to_status: ApplicationStatus | None
    occurred_at: datetime
    notes: str | None
    created_at: datetime

    model_config = ConfigDict(from_attributes=True)
