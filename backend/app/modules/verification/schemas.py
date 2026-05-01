from typing import Literal

from pydantic import BaseModel


VerificationStatus = Literal["valid", "modified", "overruled", "unknown"]


class VerificationResult(BaseModel):
    status: VerificationStatus
    diff: list[dict[str, object]] = []
    source_url: str | None = None
    message: str | None = None


class VerificationRequest(BaseModel):
    input_text: str
    official_text: str | None = None
    case_number: str | None = None
    source_url: str | None = None
