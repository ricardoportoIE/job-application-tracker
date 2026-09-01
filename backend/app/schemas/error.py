from typing import Any

from pydantic import BaseModel, ConfigDict


class ErrorResponse(BaseModel):
    model_config = ConfigDict(
        extra="forbid",
    )

    detail: str | list[dict[str, Any]]
    request_id: str
