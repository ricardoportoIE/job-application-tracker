import uuid
from datetime import datetime
from decimal import Decimal
from typing import Self

from pydantic import BaseModel, ConfigDict, Field, model_validator

from app.models.enums import ApplicationStatus, JobSource, WorkModel


class ApplicationCreate(BaseModel):
    model_config = ConfigDict(str_strip_whitespace=True)

    company_id: uuid.UUID
    position: str = Field(min_length=1, max_length=200)
    status: ApplicationStatus = ApplicationStatus.SAVED
    source: JobSource | None = None
    work_model: WorkModel | None = None
    location: str | None = Field(default=None, max_length=255)
    job_url: str | None = Field(default=None, max_length=2048)
    salary_min: Decimal | None = Field(default=None, ge=0)
    salary_max: Decimal | None = Field(default=None, ge=0)
    currency: str | None = Field(default=None, min_length=3, max_length=3)
    applied_at: datetime | None = None
    notes: str | None = None


class ApplicationUpdate(BaseModel):
    model_config = ConfigDict(str_strip_whitespace=True)

    company_id: uuid.UUID | None = None
    position: str | None = Field(default=None, min_length=1, max_length=200)
    status: ApplicationStatus | None = None
    source: JobSource | None = None
    work_model: WorkModel | None = None
    location: str | None = Field(default=None, max_length=255)
    job_url: str | None = Field(default=None, max_length=2048)
    salary_min: Decimal | None = Field(default=None, ge=0)
    salary_max: Decimal | None = Field(default=None, ge=0)
    currency: str | None = Field(default=None, min_length=3, max_length=3)
    applied_at: datetime | None = None
    notes: str | None = None

    @model_validator(mode="after")
    def reject_null_required_fields(self) -> Self:
        if "company_id" in self.model_fields_set and self.company_id is None:
            raise ValueError("company_id cannot be null")

        if "position" in self.model_fields_set and self.position is None:
            raise ValueError("position cannot be null")

        if "status" in self.model_fields_set and self.status is None:
            raise ValueError("status cannot be null")

        return self


class ApplicationRead(BaseModel):
    id: uuid.UUID
    user_id: uuid.UUID
    company_id: uuid.UUID
    position: str
    status: ApplicationStatus
    source: JobSource | None
    work_model: WorkModel | None
    location: str | None
    job_url: str | None
    salary_min: Decimal | None
    salary_max: Decimal | None
    currency: str | None
    applied_at: datetime | None
    notes: str | None
    created_at: datetime
    updated_at: datetime

    model_config = ConfigDict(from_attributes=True)
