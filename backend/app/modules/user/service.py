from app.modules.shared import StatusResponse


class UserService:
    def health(self) -> StatusResponse:
        return StatusResponse(status="ready", module="user")

