from fastapi import APIRouter

from app.modules.retrieval.schemas import RetrievalRequest, RetrievalResult
from app.modules.retrieval.service import RetrievalService
from app.modules.shared import ApiResponse, StatusResponse


router = APIRouter(prefix="/retrieval", tags=["retrieval"])


@router.get("/health", response_model=ApiResponse[StatusResponse])
async def health() -> ApiResponse[StatusResponse]:
    return ApiResponse(data=RetrievalService().health())


@router.post("/analyze-query", response_model=ApiResponse[RetrievalResult])
async def analyze_query(request: RetrievalRequest) -> ApiResponse[RetrievalResult]:
    result = RetrievalService().build_result(
        query=request.query,
        chunks=[],
        top_k=request.top_k,
        score_threshold=request.score_threshold,
    )
    return ApiResponse(data=result)
