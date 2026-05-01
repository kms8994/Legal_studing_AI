from app.modules.shared import StatusResponse
from app.modules.usage.schemas import UsageDecision, UsageLimit


class UsageService:
    def health(self) -> StatusResponse:
        return StatusResponse(status="ready", module="usage")

    def decide(self, usage: UsageLimit) -> UsageDecision:
        if usage.monthly_limit is None:
            return UsageDecision(allowed=True, remaining=None, reason="unlimited")

        remaining = max(usage.monthly_limit - usage.monthly_count, 0)
        return UsageDecision(
            allowed=remaining > 0,
            remaining=remaining,
            reason="allowed" if remaining > 0 else "usage_limit_exceeded",
        )
