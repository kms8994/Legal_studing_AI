import re

from app.core.config import settings
from app.infrastructure.cache import build_cache_key
from app.infrastructure.lawinfo_client import LawInfoClient, LawInfoError
from app.infrastructure.lawinfo_urls import case_url
from app.modules.retrieval.ranker import filter_ranked_chunks
from app.modules.retrieval.schemas import (
    EvidenceChunk,
    LawInfoDiagnosticResponse,
    RetrievalEntityHints,
    RetrievalResult,
)
from app.modules.shared import StatusResponse


CASE_NUMBER_PATTERN = re.compile(
    r"\d{2,4}\s*[-–]?\s*[가-힣]{1,4}\s*[-–]?\s*\d+",
)
LAW_NAME_PATTERN = re.compile(r"[가-힣A-Za-z0-9·\s]+(?:법|규칙)")
ARTICLE_PATTERN = re.compile(r"제\s*\d+\s*조(?:의\s*\d+)?")
KEYWORD_PATTERN = re.compile(r"[가-힣A-Za-z0-9]{2,}")


class RetrievalService:
    def health(self) -> StatusResponse:
        return StatusResponse(status="ready", module="retrieval")

    def extract_hints(self, query: str) -> RetrievalEntityHints:
        normalized_query = self.normalize_query(query)
        case_numbers = [self._compact(match.group(0)) for match in CASE_NUMBER_PATTERN.finditer(normalized_query)]
        law_names = self._unique(
            self._clean_text(match.group(0))
            for match in LAW_NAME_PATTERN.finditer(normalized_query)
        )
        articles = self._unique(
            self._clean_text(match.group(0).replace(" ", ""))
            for match in ARTICLE_PATTERN.finditer(normalized_query)
        )
        keywords = [
            keyword
            for keyword in self._unique(KEYWORD_PATTERN.findall(normalized_query))
            if keyword not in law_names and keyword not in articles
        ][:12]

        return RetrievalEntityHints(
            case_number=case_numbers[0] if case_numbers else None,
            law_names=law_names[:5],
            articles=articles[:8],
            keywords=keywords,
        )

    def build_query_hash(self, query: str) -> str:
        return build_cache_key(("retrieval", self.normalize_query(query)))

    def normalize_query(self, query: str) -> str:
        return re.sub(r"\s+", " ", query).strip()

    def build_result(
        self,
        *,
        query: str,
        chunks: list[EvidenceChunk],
        top_k: int,
        score_threshold: float,
        source: str = "local_fallback",
        message: str | None = None,
        attempted_query: str | None = None,
        forced_status: str | None = None,
    ) -> RetrievalResult:
        evidence = filter_ranked_chunks(
            chunks,
            top_k=top_k,
            score_threshold=score_threshold,
        )
        return RetrievalResult(
            status=forced_status or ("ok" if evidence else "insufficient_evidence"),
            query_hash=self.build_query_hash(query),
            hints=self.extract_hints(query),
            evidence_chunks=evidence,
            source=source,
            message=message,
            attempted_query=attempted_query,
        )

    async def retrieve_official_case_evidence(
        self,
        query: str,
        *,
        top_k: int,
        score_threshold: float,
    ) -> RetrievalResult:
        hints = self.extract_hints(query)
        chunks: list[EvidenceChunk] = []
        attempted_query = hints.case_number or " ".join(hints.keywords[:5]) or self.normalize_query(query)
        message: str | None = None
        forced_status: str | None = None
        try:
            if hints.case_number:
                document = await LawInfoClient().get_case_by_number(hints.case_number)
                chunks = self._case_document_to_chunks(document, fallback_case_number=hints.case_number)
            else:
                summaries = await LawInfoClient().search_cases(
                    attempted_query,
                    search_scope=2,
                    display=min(top_k, 10),
                )
                for summary in summaries[:top_k]:
                    if not summary.id:
                        continue
                    document = await LawInfoClient().get_case_by_id(summary.id, title=summary.title)
                    chunks.extend(
                        self._case_document_to_chunks(
                            {
                                "id": document.id,
                                "title": document.title or summary.title,
                                "case_number": summary.case_number,
                                "body_text": document.body_text,
                                "source_url": summary.source_url,
                                "raw": summary.raw,
                            },
                            fallback_case_number=summary.case_number,
                        )
                    )
        except LawInfoError as exc:
            chunks = []
            forced_status = "api_error"
            message = str(exc)

        return self.build_result(
            query=query,
            chunks=chunks,
            top_k=top_k,
            score_threshold=score_threshold,
            source="official_api" if chunks else "local_fallback",
            message=message,
            attempted_query=attempted_query,
            forced_status=forced_status,
        )

    async def diagnose_lawinfo(self, query: str = "자동차") -> LawInfoDiagnosticResponse:
        if not settings.lawinfo_api_key:
            return LawInfoDiagnosticResponse(
                has_api_key=False,
                base_url=settings.lawinfo_base_url,
                status="missing_key",
                message="LAWINFO_API_KEY가 설정되어 있지 않습니다.",
            )

        try:
            samples = await LawInfoClient().search_cases(query, search_scope=1, display=1)
            return LawInfoDiagnosticResponse(
                has_api_key=True,
                base_url=settings.lawinfo_base_url,
                status="ok",
                message="국가법령정보 API 검색 호출에 성공했습니다.",
                sample_count=len(samples),
            )
        except LawInfoError as exc:
            return LawInfoDiagnosticResponse(
                has_api_key=True,
                base_url=settings.lawinfo_base_url,
                status="api_error",
                message=str(exc),
            )

    def _case_document_to_chunks(
        self,
        document: dict[str, object],
        *,
        fallback_case_number: str | None,
    ) -> list[EvidenceChunk]:
        body_text = str(document.get("body_text") or "")
        if not body_text.strip():
            return []

        source_name = str(document.get("title") or fallback_case_number or "공식 판례")
        case_number = str(document.get("case_number") or fallback_case_number or "")
        source_url = case_url(case_number) if case_number else str(document.get("source_url") or "")

        from app.modules.retrieval.chunking import chunk_document

        raw_chunks = chunk_document(
            body_text,
            source_type="case",
            source_name=source_name,
            source_url=source_url,
            case_number=case_number or None,
            chunk_size=1200,
            overlap=150,
        )
        return [EvidenceChunk(**chunk) for chunk in raw_chunks]

    def _compact(self, value: str) -> str:
        return re.sub(r"[\s\-–]+", "", value)

    def _clean_text(self, value: str) -> str:
        return re.sub(r"\s+", " ", value).strip()

    def _unique(self, values) -> list[str]:
        seen: set[str] = set()
        result: list[str] = []
        for value in values:
            if value and value not in seen:
                seen.add(value)
                result.append(value)
        return result
