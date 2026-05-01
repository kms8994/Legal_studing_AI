from fastapi import APIRouter

from app.modules.diagram.schemas import DiagramGenerateRequest, ExpertDiagramSet, MermaidDiagram
from app.modules.diagram.service import DiagramService
from app.modules.shared import ApiResponse, StatusResponse


router = APIRouter(prefix="/diagram", tags=["diagram"])


@router.get("/health", response_model=ApiResponse[StatusResponse])
async def health() -> ApiResponse[StatusResponse]:
    return ApiResponse(data=DiagramService().health())


@router.post("/generate", response_model=ApiResponse[MermaidDiagram])
async def generate_diagram(
    request: DiagramGenerateRequest,
) -> ApiResponse[MermaidDiagram]:
    return ApiResponse(data=await DiagramService().generate_from_irac(request.analysis))


@router.post("/generate-expert", response_model=ApiResponse[ExpertDiagramSet])
async def generate_expert_diagrams(
    request: DiagramGenerateRequest,
) -> ApiResponse[ExpertDiagramSet]:
    return ApiResponse(data=await DiagramService().generate_expert_diagrams(request.analysis))
