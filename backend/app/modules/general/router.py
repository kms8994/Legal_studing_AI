from fastapi import APIRouter

from app.modules.general.schemas import GeneralSituationRequest, GeneralSituationResponse
from app.modules.general.service import GeneralService
from app.modules.shared import ApiResponse


router = APIRouter(prefix="/general", tags=["general"])


@router.post("/similar-cases", response_model=ApiResponse[GeneralSituationResponse])
async def similar_cases(
    request: GeneralSituationRequest,
) -> ApiResponse[GeneralSituationResponse]:
    return ApiResponse(data=await GeneralService().analyze_situation(request.situation))
