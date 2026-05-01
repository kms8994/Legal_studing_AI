from fastapi import APIRouter

from app.modules.shared import ApiResponse, StatusResponse
from app.modules.usage.service import UsageService


router = APIRouter(prefix="/usage", tags=["usage"])


@router.get("/health", response_model=ApiResponse[StatusResponse])
async def health() -> ApiResponse[StatusResponse]:
    return ApiResponse(data=UsageService().health())

