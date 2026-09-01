import uuid
from typing import Literal

from pydantic import BaseModel, ConfigDict, Field

from app.models.enums import (
    ApplicationStatus,
    JobSource,
    WorkModel,
)
from app.schemas.application import ApplicationRead

ApplicationSortBy = Literal[
    "created_at",
    "updated_at",
    "position",
    "applied_at",
]

SortOrder = Literal[
    "asc",
    "desc",
]


class ApplicationListParams(BaseModel):
    model_config = ConfigDict(
        str_strip_whitespace=True,
        extra="forbid",
    )

    status: ApplicationStatus | None = None
    company_id: uuid.UUID | None = None
    work_model: WorkModel | None = None
    source: JobSource | None = None

    search: str | None = Field(
        default=None,
        min_length=1,
        max_length=200,
    )

    limit: int = Field(
        default=20,
        ge=1,
        le=100,
    )

    offset: int = Field(
        default=0,
        ge=0,
    )

    sort_by: ApplicationSortBy = "created_at"
    sort_order: SortOrder = "desc"


class ApplicationListResponse(BaseModel):
    items: list[ApplicationRead]
    total: int = Field(
        ge=0,
    )
    limit: int = Field(
        ge=1,
    )
    offset: int = Field(
        ge=0,
    )
