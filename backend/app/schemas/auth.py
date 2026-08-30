from typing import Literal

from pydantic import BaseModel, ConfigDict, EmailStr, Field


class LoginRequest(BaseModel):
    model_config = ConfigDict(
        extra="forbid",
    )

    email: EmailStr
    password: str = Field(min_length=1, max_length=128)


class TokenResponse(BaseModel):
    model_config = ConfigDict(
        extra="forbid",
    )

    access_token: str = Field(min_length=1)
    token_type: Literal["bearer"] = "bearer"
