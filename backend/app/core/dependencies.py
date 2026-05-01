from dataclasses import dataclass


@dataclass(frozen=True)
class RequestUser:
    id: str | None = None
    email: str | None = None
    plan: str = "free"


async def get_optional_user() -> RequestUser:
    return RequestUser()

