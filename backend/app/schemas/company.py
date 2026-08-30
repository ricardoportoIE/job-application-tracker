import uuid
from datetime import datetime

from pydantic import BaseModel, ConfigDict, Field


class CompanyCreate(BaseModel):
    model_config = ConfigDict(str_strip_whitespace=True)

    name: str = Field(min_length=1, max_length=200)
    website: str | None = Field(default=None, max_length=2048)
    industry: str | None = Field(default=None, max_length=120)
    location: str | None = Field(default=None, max_length=255)


class CompanyUpdate(BaseModel):
    model_config = ConfigDict(str_strip_whitespace=True)

    name: str | None = Field(default=None, min_length=1, max_length=200)
    website: str | None = Field(default=None, max_length=2048)
    industry: str | None = Field(default=None, max_length=120)
    location: str | None = Field(default=None, max_length=255)


class CompanyRead(BaseModel):
    id: uuid.UUID
    user_id: uuid.UUID
    name: str
    website: str | None
    industry: str | None
    location: str | None
    created_at: datetime
    updated_at: datetime

    model_config = ConfigDict(from_attributes=True)
