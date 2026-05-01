from fastapi import APIRouter

from app.modules.shared import ApiResponse, StatusResponse
from app.modules.user.service import UserService


router = APIRouter(prefix="/user", tags=["user"])


@router.get("/health", response_model=ApiResponse[StatusResponse])
async def health() -> ApiResponse[StatusResponse]:
    return ApiResponse(data=UserService().health())

