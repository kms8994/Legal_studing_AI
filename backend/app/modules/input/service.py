import base64
import io
import re

from app.infrastructure.gemini_client import GeminiClient, GeminiError
from app.infrastructure.cache import build_cache_key
from app.modules.input.schemas import NormalizedInput, OcrResult
from app.modules.shared import StatusResponse


class InputService:
    def health(self) -> StatusResponse:
        return StatusResponse(status="ready", module="input")

    def normalize_text(self, text: str) -> NormalizedInput:
        normalized = self._normalize_whitespace(text)
        return NormalizedInput(
            input_type="text",
            text=normalized,
            text_hash=self.hash_text(normalized),
        )

    def normalize_case_number(self, case_number: str) -> NormalizedInput:
        normalized = re.sub(r"\s+", "", case_number)
        return NormalizedInput(
            input_type="case_number",
            text=normalized,
            text_hash=self.hash_text(normalized),
        )

    def normalize_pdf_base64(self, file_base64: str) -> NormalizedInput:
        data = base64.b64decode(file_base64)
        text = self._extract_pdf_text(data)
        return self.normalize_text(text)

    async def extract_image_text(self, image_base64: str, *, mime_type: str) -> OcrResult:
        try:
            text = await GeminiClient().extract_text_from_image(
                image_base64,
                mime_type=mime_type,
            )
        except GeminiError as exc:
            return OcrResult(
                status="not_configured",
                message=exc.message,
            )
        return OcrResult(status="requires_user_confirmation", extracted_text=text)

    def hash_text(self, text: str) -> str:
        return build_cache_key(("input", text))

    def _normalize_whitespace(self, text: str) -> str:
        return re.sub(r"\s+", " ", text).strip()

    def _extract_pdf_text(self, data: bytes) -> str:
        try:
            from pypdf import PdfReader
        except ImportError:
            return data.decode("utf-8", errors="ignore")

        try:
            reader = PdfReader(io.BytesIO(data))
            pages = [page.extract_text() or "" for page in reader.pages]
        except Exception as exc:
            fallback = data.decode("utf-8", errors="ignore").strip()
            if fallback:
                return fallback
            raise ValueError("PDF 텍스트 추출에 실패했습니다.") from exc

        text = "\n".join(page for page in pages if page.strip())
        if not text.strip():
            raise ValueError("PDF에서 텍스트 레이어를 찾을 수 없습니다.")
        return text
