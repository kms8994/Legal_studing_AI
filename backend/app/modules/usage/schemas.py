from pydantic import BaseModel


class UsageLimit(BaseModel):
    plan: str
    monthly_count: int
    monthly_limit: int | None


class UsageDecision(BaseModel):
    allowed: bool
    remaining: int | None
    reason: str
