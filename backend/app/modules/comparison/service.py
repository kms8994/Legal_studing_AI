from app.modules.shared import StatusResponse


class ComparisonService:
    def health(self) -> StatusResponse:
        return StatusResponse(status="ready", module="comparison")

