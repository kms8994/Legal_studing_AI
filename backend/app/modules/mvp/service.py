import re

from app.modules.diagram.service import DiagramService
from app.modules.input.service import InputService
from app.modules.irac.schemas import EvidenceBackedText, IracAnalysis
from app.modules.mvp.schemas import MvpAnalyzeResponse
from app.modules.retrieval.schemas import EvidenceChunk
from app.modules.retrieval.service import RetrievalService


DISCLAIMER = (
    "본 서비스는 법률 조언이 아닌 학습 및 정보 제공 서비스입니다. "
    "분석 결과는 입력된 판례와 확인 가능한 근거를 학습용으로 구조화한 것이며, "
    "개별 사건에 대한 법률 판단이나 대응 방안을 제시하지 않습니다."
)


class MvpService:
    def __init__(self) -> None:
        self.input_service = InputService()
        self.retrieval_service = RetrievalService()
        self.diagram_service = DiagramService()

    async def analyze(self, text: str, *, persona_mode: str = "expert") -> MvpAnalyzeResponse:
        normalized = self.input_service.normalize_text(text)
        hints = self.retrieval_service.extract_hints(normalized.text)
        official_result = await self.retrieval_service.retrieve_official_case_evidence(
            normalized.text,
            top_k=5,
            score_threshold=0.1,
        )
        evidence = official_result.evidence_chunks or self._build_demo_evidence(
            normalized.text,
            hints.case_number,
        )
        irac = self._build_heuristic_irac(normalized.text, evidence[0].id, persona_mode)
        diagrams = await self.diagram_service.generate_expert_diagrams(
            irac,
            case_text=normalized.text,
            evidence_chunks=evidence,
        )
        return MvpAnalyzeResponse(
            mode="official-rag" if official_result.evidence_chunks else "demo-local-rag",
            input_hash=normalized.text_hash,
            hints=hints,
            evidence_chunks=evidence,
            irac=irac,
            diagram=diagrams.legal_reasoning,
            diagrams=diagrams,
            disclaimer=DISCLAIMER,
        )

    def _build_demo_evidence(
        self,
        text: str,
        case_number: str | None,
    ) -> list[EvidenceChunk]:
        return [
            EvidenceChunk(
                id="input:case-text:0",
                source_type="metadata",
                source_name="사용자 입력 원문",
                source_url="local://user-input",
                case_number=case_number,
                law_article=None,
                chunk_text=text,
                chunk_index=0,
                retrieval_score=1.0,
            )
        ]

    def _build_heuristic_irac(
        self,
        text: str,
        evidence_id: str,
        persona_mode: str,
    ) -> IracAnalysis:
        sentences = self._split_sentences(text)
        laws = self._extract_laws(text)
        issue = self._make_issue(sentences)
        rule = self._make_rule(laws, persona_mode)
        application = self._make_application(sentences)
        conclusion = self._make_conclusion(sentences)
        return IracAnalysis(
            issue=EvidenceBackedText(text=issue, evidence_ids=[evidence_id]),
            rule=EvidenceBackedText(text=rule, evidence_ids=[evidence_id]),
            application=EvidenceBackedText(text=application, evidence_ids=[evidence_id]),
            conclusion=EvidenceBackedText(text=conclusion, evidence_ids=[evidence_id]),
            key_terms=self._extract_key_terms(text),
            referenced_laws=laws,
        )

    def _split_sentences(self, text: str) -> list[str]:
        parts = re.split(r"(?<=[.。!?])\s+|(?<=다\.)\s*", text)
        return [part.strip() for part in parts if part.strip()]

    def _extract_laws(self, text: str) -> list[str]:
        laws = re.findall(r"[가-힣A-Za-z0-9·ㆍ\s]*(?:법|령)\s*제\s*\d+\s*조(?:의\s*\d+)?", text)
        articles = re.findall(r"제\s*\d+\s*조(?:의\s*\d+)?", text)
        values = [self._clean(value) for value in laws + articles]
        return self._unique(values)[:8]

    def _extract_key_terms(self, text: str) -> list[str]:
        candidates = re.findall(r"[가-힣A-Za-z0-9]{2,}", text)
        stopwords = {"그리고", "그러나", "따라서", "판례", "법원", "원고", "피고"}
        return [
            word
            for word in self._unique(candidates)
            if word not in stopwords
        ][:10]

    def _make_issue(self, sentences: list[str]) -> str:
        if not sentences:
            return "입력된 판례에서 핵심 쟁점을 확인할 수 없습니다."
        return f"입력된 판례에서 문제되는 핵심 쟁점은 다음 사실관계의 법적 평가입니다: {self._clip(sentences[0])}"

    def _make_rule(self, laws: list[str], persona_mode: str) -> str:
        if laws:
            return "입력 원문에서 확인되는 관련 법령 또는 조문은 " + ", ".join(laws) + "입니다."
        if persona_mode == "general":
            return "입력 원문에서 명시적인 법령 조문은 확인되지 않습니다."
        return "입력 원문에서 명시적으로 특정된 적용 법령 조항은 확인되지 않습니다."

    def _make_application(self, sentences: list[str]) -> str:
        if len(sentences) >= 2:
            return "법원 판단 과정은 입력 원문의 사실관계와 판단 이유를 연결해 보아야 합니다: " + self._clip(" ".join(sentences[1:3]), 180)
        return "입력 원문만으로는 구체적인 적용 과정을 충분히 분리하기 어렵습니다."

    def _make_conclusion(self, sentences: list[str]) -> str:
        if not sentences:
            return "입력 원문에서 결론을 확인할 수 없습니다."
        return "입력 원문상 결론 또는 판단 요지는 다음 부분을 중심으로 정리할 수 있습니다: " + self._clip(sentences[-1], 160)

    def _clip(self, text: str, limit: int = 140) -> str:
        cleaned = self._clean(text)
        return cleaned if len(cleaned) <= limit else cleaned[: limit - 1] + "…"

    def _clean(self, text: str) -> str:
        return re.sub(r"\s+", " ", text).strip()

    def _unique(self, values: list[str]) -> list[str]:
        seen: set[str] = set()
        result: list[str] = []
        for value in values:
            if value and value not in seen:
                seen.add(value)
                result.append(value)
        return result
