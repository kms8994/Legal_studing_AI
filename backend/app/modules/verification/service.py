import difflib
import re

from app.infrastructure.lawinfo_client import LawInfoClient, LawInfoError
from app.infrastructure.lawinfo_urls import case_url
from app.modules.shared import StatusResponse
from app.modules.verification.schemas import VerificationRequest, VerificationResult


class VerificationService:
    def health(self) -> StatusResponse:
        return StatusResponse(status="ready", module="verification")

    async def check(self, request: VerificationRequest) -> VerificationResult:
        request = await self._with_official_text(request)
        if not request.official_text:
            return VerificationResult(
                status="unknown",
                source_url=request.source_url,
                message=(
                    "공식 판례 원문이 아직 연결되지 않았습니다. "
                    "법령 API 사용법 파일이 추가되면 case_number 기반 조회와 연결됩니다."
                ),
            )

        input_text = self._normalize(request.input_text)
        official_text = self._normalize(request.official_text)
        if input_text == official_text:
            return VerificationResult(
                status="valid",
                source_url=request.source_url,
                message="입력 원문과 공식 원문이 일치합니다.",
            )

        ratio = difflib.SequenceMatcher(None, input_text, official_text).ratio()
        return VerificationResult(
            status="modified" if ratio >= 0.6 else "unknown",
            diff=self._build_diff(input_text, official_text),
            source_url=request.source_url,
            message=f"원문 유사도 {ratio:.2f} 기준으로 차이를 감지했습니다.",
        )

    def _build_diff(self, input_text: str, official_text: str) -> list[dict[str, object]]:
        input_tokens = input_text.split()
        official_tokens = official_text.split()
        matcher = difflib.SequenceMatcher(None, input_tokens, official_tokens)
        changes: list[dict[str, object]] = []
        for tag, i1, i2, j1, j2 in matcher.get_opcodes():
            if tag == "equal":
                continue
            changes.append(
                {
                    "type": tag,
                    "input": " ".join(input_tokens[i1:i2]),
                    "official": " ".join(official_tokens[j1:j2]),
                }
            )
        return changes[:20]

    def _normalize(self, text: str) -> str:
        return re.sub(r"\s+", " ", text).strip()

    async def _with_official_text(self, request: VerificationRequest) -> VerificationRequest:
        if request.official_text or not request.case_number:
            return request
        try:
            document = await LawInfoClient().get_case_by_number(request.case_number)
        except LawInfoError:
            return request

        return VerificationRequest(
            input_text=request.input_text,
            official_text=str(document.get("body_text") or ""),
            case_number=request.case_number,
            source_url=request.source_url or case_url(request.case_number),
        )
