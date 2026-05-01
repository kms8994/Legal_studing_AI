from fastapi import APIRouter

from app.modules.input.schemas import (
    CaseNumberInputRequest,
    ImageInputRequest,
    NormalizedInput,
    OcrResult,
    PdfInputRequest,
    TextInputRequest,
)
from app.modules.input.service import InputService
from app.modules.shared import ApiResponse, StatusResponse


router = APIRouter(prefix="/input", tags=["input"])


@router.get("/health", response_model=ApiResponse[StatusResponse])
async def health() -> ApiResponse[StatusResponse]:
    return ApiResponse(data=InputService().health())


@router.post("/text", response_model=ApiResponse[NormalizedInput])
async def normalize_text(request: TextInputRequest) -> ApiResponse[NormalizedInput]:
    return ApiResponse(data=InputService().normalize_text(request.text))


@router.post("/case-number", response_model=ApiResponse[NormalizedInput])
async def normalize_case_number(
    request: CaseNumberInputRequest,
) -> ApiResponse[NormalizedInput]:
    return ApiResponse(data=InputService().normalize_case_number(request.case_number))


@router.post("/pdf", response_model=ApiResponse[NormalizedInput])
async def normalize_pdf(request: PdfInputRequest) -> ApiResponse[NormalizedInput]:
    return ApiResponse(data=InputService().normalize_pdf_base64(request.file_base64))


@router.post("/image", response_model=ApiResponse[OcrResult])
async def extract_image_text(request: ImageInputRequest) -> ApiResponse[OcrResult]:
    return ApiResponse(
        data=await InputService().extract_image_text(
            request.image_base64,
            mime_type=request.mime_type,
        )
    )
