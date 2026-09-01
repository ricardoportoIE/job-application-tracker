import re
import uuid
from contextvars import ContextVar, Token

_REQUEST_ID_PATTERN = re.compile(r"^[A-Za-z0-9._-]{1,128}$")

_request_id: ContextVar[str | None] = ContextVar(
    "request_id",
    default=None,
)


def generate_request_id() -> str:
    return str(uuid.uuid4())


def is_valid_request_id(value: str) -> bool:
    return _REQUEST_ID_PATTERN.fullmatch(value) is not None


def get_request_id() -> str | None:
    return _request_id.get()


def set_request_id(
    value: str,
) -> Token[str | None]:
    return _request_id.set(value)


def reset_request_id(
    token: Token[str | None],
) -> None:
    _request_id.reset(token)
