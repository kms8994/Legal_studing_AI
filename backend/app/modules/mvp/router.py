from fastapi import APIRouter

from app.modules.mvp.schemas import MvpAnalyzeRequest, MvpAnalyzeResponse
from app.modules.mvp.service import MvpService
from app.modules.shared import ApiResponse


router = APIRouter(prefix="/mvp", tags=["mvp"])


@router.post("/analyze", response_model=ApiResponse[MvpAnalyzeResponse])
async def analyze(request: MvpAnalyzeRequest) -> ApiResponse[MvpAnalyzeResponse]:
    return ApiResponse(
        data=await MvpService().analyze(request.text, persona_mode=request.persona_mode)
    )
