from fastapi import APIRouter

from app.modules.comparison.service import ComparisonService
from app.modules.shared import ApiResponse, StatusResponse


router = APIRouter(prefix="/comparison", tags=["comparison"])


@router.get("/health", response_model=ApiResponse[StatusResponse])
async def health() -> ApiResponse[StatusResponse]:
    return ApiResponse(data=ComparisonService().health())

