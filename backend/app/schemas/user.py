import uuid
from datetime import datetime
from typing import Self

from pydantic import BaseModel, ConfigDict, EmailStr, Field, model_validator


class UserCreate(BaseModel):
    model_config = ConfigDict(
        extra="forbid",
    )

    email: EmailStr = Field(max_length=320)
    password: str = Field(min_length=8, max_length=128)


class UserUpdate(BaseModel):
    model_config = ConfigDict(
        extra="forbid",
    )

    email: EmailStr | None = Field(default=None, max_length=320)
    password: str | None = Field(default=None, min_length=8, max_length=128)

    @model_validator(mode="after")
    def reject_null_fields(self) -> Self:
        if "email" in self.model_fields_set and self.email is None:
            raise ValueError("email cannot be null")

        if "password" in self.model_fields_set and self.password is None:
            raise ValueError("password cannot be null")

        return self


class UserRead(BaseModel):
    id: uuid.UUID
    email: EmailStr
    is_active: bool
    created_at: datetime
    updated_at: datetime

    model_config = ConfigDict(
        from_attributes=True,
    )
