from fastapi import APIRouter

from app.modules.retrieval.schemas import (
    LawInfoDiagnosticResponse,
    RetrievalRequest,
    RetrievalResult,
    StatuteLinkRequest,
    StatuteLinkResponse,
)
from app.modules.retrieval.service import RetrievalService
from app.modules.shared import ApiResponse, StatusResponse


router = APIRouter(prefix="/retrieval", tags=["retrieval"])


@router.get("/health", response_model=ApiResponse[StatusResponse])
async def health() -> ApiResponse[StatusResponse]:
    return ApiResponse(data=RetrievalService().health())


@router.post("/analyze-query", response_model=ApiResponse[RetrievalResult])
async def analyze_query(request: RetrievalRequest) -> ApiResponse[RetrievalResult]:
    result = await RetrievalService().retrieve_official_case_evidence(
        query=request.query,
        top_k=request.top_k,
        score_threshold=request.score_threshold,
    )
    return ApiResponse(data=result)


@router.post("/statute-links", response_model=ApiResponse[StatuteLinkResponse])
async def statute_links(request: StatuteLinkRequest) -> ApiResponse[StatuteLinkResponse]:
    result = await RetrievalService().build_statute_links(request.text)
    return ApiResponse(data=result)


@router.get("/lawinfo-diagnostics", response_model=ApiResponse[LawInfoDiagnosticResponse])
async def lawinfo_diagnostics(query: str = "자동차") -> ApiResponse[LawInfoDiagnosticResponse]:
    result = await RetrievalService().diagnose_lawinfo(query=query)
    return ApiResponse(data=result)
