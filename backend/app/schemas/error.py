from typing import Any

from pydantic import BaseModel, ConfigDict


class ErrorResponse(BaseModel):
    model_config = ConfigDict(
        extra="forbid",
    )

    detail: str
    request_id: str


class ValidationErrorDetail(BaseModel):
    model_config = ConfigDict(
        extra="allow",
    )

    type: str
    loc: list[str | int]
    msg: str
    input: Any = None
    ctx: dict[str, Any] | None = None


class ValidationErrorResponse(BaseModel):
    model_config = ConfigDict(
        extra="forbid",
    )

    detail: list[ValidationErrorDetail]
    request_id: str
