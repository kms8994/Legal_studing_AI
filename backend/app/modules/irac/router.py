from fastapi import APIRouter

from app.modules.irac.schemas import IracAnalyzeRequest, IracAnalyzeResult
from app.modules.irac.service import IracService
from app.modules.shared import ApiResponse, StatusResponse


router = APIRouter(prefix="/irac", tags=["irac"])


@router.get("/health", response_model=ApiResponse[StatusResponse])
async def health() -> ApiResponse[StatusResponse]:
    return ApiResponse(data=IracService().health())


@router.post("/prepare", response_model=ApiResponse[IracAnalyzeResult])
async def prepare_analysis(request: IracAnalyzeRequest) -> ApiResponse[IracAnalyzeResult]:
    service = IracService()
    if not request.evidence_chunks:
        return ApiResponse(data=service.insufficient_evidence())
    return ApiResponse(
        data=IracAnalyzeResult(
            status="ready",
            analysis=service.placeholder_from_evidence(request.evidence_chunks),
        )
    )
