import re

from app.infrastructure.lawinfo_client import LawInfoClient, LawInfoError
from app.infrastructure.lawinfo_urls import case_url
from app.modules.general.schemas import (
    GeneralSituationResponse,
    SimilarCaseCandidate,
)
from app.modules.retrieval.service import RetrievalService


LIMITATION = (
    "AI는 의견이나 법률 조언을 제시하지 않습니다. "
    "결과는 공식 API 또는 사용자가 제공한 근거에 명시된 판례 내용만 요약합니다."
)


class GeneralService:
    def __init__(self) -> None:
        self.retrieval_service = RetrievalService()

    async def analyze_situation(self, situation: str) -> GeneralSituationResponse:
        official = await self._try_official_similar_cases(situation)
        if official.candidates:
            return official
        return self._pending_response(situation)

    def _pending_response(self, situation: str) -> GeneralSituationResponse:
        hints = self.retrieval_service.extract_hints(situation)
        keywords = hints.keywords[:8]
        return GeneralSituationResponse(
            query_keywords=keywords,
            candidates=[
                SimilarCaseCandidate(
                    title="공식 판례 API 연결 대기",
                    case_number=hints.case_number,
                    court="대법원",
                    decision_date=None,
                    similarity_reason=(
                        "입력 상황에서 추출된 키워드를 기준으로 유사 판례를 검색할 예정입니다: "
                        + ", ".join(keywords)
                    ),
                    supreme_court_holding=(
                        "아직 공식 판례 원문이 연결되지 않았습니다. "
                        "법령 API 사용법 파일이 추가되면 API에 명시된 대법원 판단 내용만 표시합니다."
                    ),
                    source_url="pending://law-api-guide",
                    evidence_text=self._clip(situation),
                )
            ],
            limitation=LIMITATION,
        )

    async def _try_official_similar_cases(self, situation: str) -> GeneralSituationResponse:
        hints = self.retrieval_service.extract_hints(situation)
        keywords = hints.keywords[:8]
        query = " ".join(keywords[:5]) or situation
        try:
            summaries = await LawInfoClient().search_cases(
                query,
                search_scope=2,
                display=5,
            )
        except LawInfoError:
            return GeneralSituationResponse(
                query_keywords=keywords,
                candidates=[],
                limitation=LIMITATION,
            )

        candidates: list[SimilarCaseCandidate] = []
        for summary in summaries[:5]:
            source_url = case_url(summary.case_number) if summary.case_number else summary.source_url
            holding = "공식 판례 목록에서 후보를 찾았습니다. 판례 본문 조회 결과에 명시된 대법원 판단만 표시해야 합니다."
            evidence_text = ""
            try:
                document = await LawInfoClient().get_case_by_id(summary.id, title=summary.title)
                evidence_text = document.body_text[:500]
                holding = self._extract_holding(document.body_text)
            except LawInfoError:
                evidence_text = ""

            candidates.append(
                SimilarCaseCandidate(
                    title=summary.title or "공식 판례",
                    case_number=summary.case_number,
                    court=summary.court or "대법원",
                    decision_date=summary.decision_date,
                    similarity_reason=(
                        "입력 상황의 키워드와 공식 판례 검색 결과가 일부 일치합니다: "
                        + ", ".join(keywords[:5])
                    ),
                    supreme_court_holding=holding,
                    source_url=source_url,
                    evidence_text=evidence_text,
                )
            )

        return GeneralSituationResponse(
            query_keywords=keywords,
            candidates=candidates,
            limitation=LIMITATION,
        )

    def build_response_from_official_cases(
        self,
        *,
        situation: str,
        official_cases: list[dict[str, str | None]],
    ) -> GeneralSituationResponse:
        keywords = self.retrieval_service.extract_hints(situation).keywords[:8]
        candidates = [
            SimilarCaseCandidate(
                title=case.get("title") or "제목 없음",
                case_number=case.get("case_number"),
                court=case.get("court") or "대법원",
                decision_date=case.get("decision_date"),
                similarity_reason=case.get("similarity_reason")
                or "입력 상황과 공식 판례의 사실관계 키워드가 일부 유사합니다.",
                supreme_court_holding=case.get("supreme_court_holding")
                or case.get("holding")
                or "공식 API 응답에서 대법원 판단 요지를 확인할 수 없습니다.",
                source_url=case.get("source_url") or "",
                evidence_text=case.get("evidence_text") or "",
            )
            for case in official_cases
        ]
        return GeneralSituationResponse(
            query_keywords=keywords,
            candidates=candidates,
            limitation=LIMITATION,
        )

    def _clip(self, text: str, limit: int = 220) -> str:
        cleaned = re.sub(r"\s+", " ", text).strip()
        return cleaned if len(cleaned) <= limit else cleaned[: limit - 1] + "…"

    def _extract_holding(self, body_text: str) -> str:
        cleaned = re.sub(r"\s+", " ", body_text).strip()
        if not cleaned:
            return "공식 판례 본문에서 대법원 판단 요지를 확인할 수 없습니다."
        markers = ("판시사항", "판결요지", "이유", "주문")
        for marker in markers:
            index = cleaned.find(marker)
            if index >= 0:
                return self._clip(cleaned[index : index + 600], 320)
        return self._clip(cleaned, 320)
