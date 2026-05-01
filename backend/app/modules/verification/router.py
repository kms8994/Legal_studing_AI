from fastapi import APIRouter

from app.modules.shared import ApiResponse, StatusResponse
from app.modules.verification.schemas import VerificationRequest, VerificationResult
from app.modules.verification.service import VerificationService


router = APIRouter(prefix="/verification", tags=["verification"])


@router.get("/health", response_model=ApiResponse[StatusResponse])
async def health() -> ApiResponse[StatusResponse]:
    return ApiResponse(data=VerificationService().health())


@router.post("/check", response_model=ApiResponse[VerificationResult])
async def check(request: VerificationRequest) -> ApiResponse[VerificationResult]:
    return ApiResponse(data=await VerificationService().check(request))
