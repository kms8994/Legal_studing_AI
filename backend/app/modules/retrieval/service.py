import re
from urllib.parse import quote

from app.core.config import settings
from app.infrastructure.cache import build_cache_key
from app.infrastructure.lawinfo_client import LawInfoClient, LawInfoError
from app.infrastructure.lawinfo_urls import case_url
from app.modules.retrieval.ranker import filter_ranked_chunks
from app.modules.retrieval.schemas import (
    EvidenceChunk,
    LawInfoDiagnosticResponse,
    LegalTerm,
    LegalTermResponse,
    RetrievalEntityHints,
    RetrievalResult,
    StatuteLink,
    StatuteLinkResponse,
)
from app.modules.shared import StatusResponse


CASE_NUMBER_PATTERN = re.compile(
    r"\d{2,4}\s*[-–]?\s*[가-힣]{1,4}\s*[-–]?\s*\d+",
)
LAW_NAME_PATTERN = re.compile(r"[가-힣A-Za-z0-9·\s]+(?:법|규칙)(?=\s|$|제)")
ARTICLE_PATTERN = re.compile(r"제\s*\d+\s*조(?:의\s*\d+)?")
KEYWORD_PATTERN = re.compile(r"[가-힣A-Za-z0-9]{2,}")

LEGAL_TERM_DICTIONARY: dict[str, tuple[str, str]] = {
    "과세처분": ("세무서 등 과세관청이 세금을 부과하거나 정정하는 행정처분입니다.", "조세"),
    "귀속": ("권리, 이익, 책임이 특정 사람이나 법률관계에 속하게 되는 것을 말합니다.", "민사/조세"),
    "기각": ("법원이 청구나 신청을 이유 없다고 보아 받아들이지 않는 결정입니다.", "소송"),
    "납세의무": ("법률상 세금을 납부해야 하는 의무입니다.", "조세"),
    "대금": ("매매 등 계약에서 물건이나 권리의 대가로 지급하는 돈입니다.", "민사"),
    "배당": ("회사 이익이나 잔여재산을 주주 등에게 나누어 주는 것을 말합니다.", "회사"),
    "부과처분": ("행정청이 세금이나 부담금을 납부하도록 정하는 처분입니다.", "행정/조세"),
    "상계": ("서로 같은 종류의 채권을 맞비겨 소멸시키는 의사표시입니다.", "민사"),
    "소각": ("주식이나 채권 등을 없애 법률상 효력을 소멸시키는 절차입니다.", "회사"),
    "수증자": ("증여를 받는 사람입니다.", "민사/세법"),
    "유류분": ("상속인이 최소한으로 보장받는 상속 재산 비율입니다.", "상속"),
    "의제": ("실제와 다르더라도 법률상 특정한 것으로 보아 취급하는 것입니다.", "공통"),
    "의제배당": ("실제 배당이 아니더라도 세법상 배당을 받은 것으로 보아 과세하는 금액입니다.", "조세"),
    "입증책임": ("어떤 사실을 증명하지 못했을 때 불이익을 부담하는 책임입니다.", "소송"),
    "증여": ("대가 없이 재산을 넘겨주는 계약입니다.", "민사/세법"),
    "증여이익": ("증여나 그와 유사한 거래로 얻은 경제적 이익입니다.", "조세"),
    "처분": ("행정청의 공권력 행사나 법률상 권리 변동 행위를 말합니다.", "행정"),
    "취소청구": ("행정처분이나 법률행위의 효력을 없애 달라고 구하는 청구입니다.", "행정/소송"),
    "항소": ("제1심 판결에 불복해 상급 법원에 다시 판단을 구하는 절차입니다.", "소송"),
}


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
                if not chunks:
                    message = self._empty_case_body_message(document)
            else:
                summaries = []
                for search_query in self._official_search_queries(query, hints):
                    attempted_query = search_query
                    summaries = await self._search_cases_with_fallback_scopes(search_query, top_k=top_k)
                    if summaries:
                        break
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
                if not summaries:
                    message = "공식 국가법령정보 API 검색 결과가 없습니다."
                elif not chunks:
                    message = "공식 API 목록 검색은 성공했지만 상세 판례 본문 API가 빈 응답을 반환했습니다."
        except LawInfoError as exc:
            chunks = []
            message = str(exc)
            forced_status = None if exc.status_code == 404 else "api_error"

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
            if not samples:
                return LawInfoDiagnosticResponse(
                    has_api_key=True,
                    base_url=settings.lawinfo_base_url,
                    status="ok",
                    message="국가법령정보 API 호출은 성공했지만 해당 검색어의 판례 결과가 없습니다.",
                    sample_count=0,
                )
            return LawInfoDiagnosticResponse(
                has_api_key=True,
                base_url=settings.lawinfo_base_url,
                status="ok",
                message="국가법령정보 API 검색 호출에 성공했고 판례 결과를 확인했습니다.",
                sample_count=len(samples),
            )
        except LawInfoError as exc:
            return LawInfoDiagnosticResponse(
                has_api_key=True,
                base_url=settings.lawinfo_base_url,
                status="api_error",
                message=str(exc),
            )

    async def build_statute_links(self, text: str) -> StatuteLinkResponse:
        pairs = self.extract_statute_references(text)
        links: list[StatuteLink] = []
        client = LawInfoClient()
        for law_name, article in pairs[:12]:
            fallback_url = self._fallback_statute_url(law_name, article)
            try:
                article_data = await client.get_statute_article(law_name, article)
                links.append(
                    StatuteLink(
                        law_name=law_name,
                        article=article,
                        title=f"{law_name} {article}",
                        url=str(article_data.get("source_url") or fallback_url),
                        status="official",
                        excerpt=self._trim_article_text(str(article_data.get("body_text") or "")),
                    )
                )
            except LawInfoError:
                links.append(
                    StatuteLink(
                        law_name=law_name,
                        article=article,
                        title=f"{law_name} {article}",
                        url=fallback_url,
                        status="fallback",
                        excerpt=None,
                    )
                )
        return StatuteLinkResponse(links=links)

    def build_legal_terms(self, text: str) -> LegalTermResponse:
        terms: list[LegalTerm] = []
        selected_terms: list[str] = []
        for term in sorted(LEGAL_TERM_DICTIONARY, key=len, reverse=True):
            if term in text and not any(term in selected for selected in selected_terms):
                definition, category = LEGAL_TERM_DICTIONARY[term]
                selected_terms.append(term)
                terms.append(
                    LegalTerm(
                        term=term,
                        definition=definition,
                        category=category,
                        source="dictionary",
                    )
                )
        return LegalTermResponse(terms=terms[:16])

    def extract_statute_references(self, text: str) -> list[tuple[str, str]]:
        pairs: list[tuple[str, str]] = []
        normalized = self.normalize_query(text)
        law_pattern = re.compile(r"([가-힣A-Za-z0-9·\s]{1,40}?(?:법|규칙|령))")
        article_pattern = re.compile(r"제\s*\d+\s*조(?:의\s*\d+)?")

        law_matches = list(law_pattern.finditer(normalized))
        for index, law_match in enumerate(law_matches):
            law_name = self._clean_law_name(law_match.group(1))
            if not law_name:
                continue
            next_law_start = law_matches[index + 1].start() if index + 1 < len(law_matches) else len(normalized)
            window = normalized[law_match.end() : min(next_law_start, law_match.end() + 90)]
            for article_match in article_pattern.finditer(window):
                article = self._clean_text(article_match.group(0).replace(" ", ""))
                pairs.append((law_name, article))

        direct_pattern = re.compile(
            r"([가-힣A-Za-z0-9·\s]{1,40}?(?:법|규칙|령))\s*(제\s*\d+\s*조(?:의\s*\d+)?)",
        )
        for match in direct_pattern.finditer(normalized):
            law_name = self._clean_law_name(match.group(1))
            article = self._clean_text(match.group(2).replace(" ", ""))
            pairs.append((law_name, article))
        return self._unique_pairs(pairs)

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

    def _empty_case_body_message(self, document: dict[str, object]) -> str:
        case_id = document.get("id")
        raw = document.get("raw")
        summary = raw.get("summary") if isinstance(raw, dict) else None
        source_name = ""
        if isinstance(summary, dict):
            summary_raw = summary.get("raw")
            if isinstance(summary_raw, dict):
                source_name = str(summary_raw.get("데이터출처명") or "")
        suffix = f" 데이터 출처: {source_name}." if source_name else ""
        return (
            "공식 API 목록 검색은 성공했지만 상세 판례 본문 API가 빈 응답을 반환했습니다."
            f" 판례 ID: {case_id}.{suffix}"
        )

    async def _search_cases_with_fallback_scopes(self, query: str, *, top_k: int):
        client = LawInfoClient()
        for search_scope in (2, 1):
            summaries = await client.search_cases(
                query,
                search_scope=search_scope,
                display=min(top_k, 10),
            )
            if summaries:
                return summaries
        return []

    def _official_search_queries(self, query: str, hints: RetrievalEntityHints) -> list[str]:
        candidates = [
            " ".join(hints.keywords[:5]),
            " ".join(hints.keywords[:3]),
            self.normalize_query(query),
        ]
        return [candidate for candidate in self._unique(candidates) if candidate]

    def _compact(self, value: str) -> str:
        return re.sub(r"[\s\-–]+", "", value)

    def _clean_text(self, value: str) -> str:
        return re.sub(r"\s+", " ", value).strip()

    def _clean_law_name(self, value: str) -> str:
        cleaned = self._clean_text(value).strip("「」 ,.")
        for separator in ("따른",):
            if separator in cleaned:
                candidate = cleaned.split(separator)[-1].strip("「」 ,.")
                if candidate.endswith(("법", "규칙", "령")):
                    return candidate
        return cleaned

    def _fallback_statute_url(self, law_name: str, article: str) -> str:
        return f"https://www.law.go.kr/법령/{quote(law_name)}/{quote(article)}"

    def _trim_article_text(self, text: str) -> str | None:
        cleaned = self._clean_text(text)
        if not cleaned:
            return None
        return cleaned[:260] + ("..." if len(cleaned) > 260 else "")

    def _unique_pairs(self, values: list[tuple[str, str]]) -> list[tuple[str, str]]:
        seen: set[tuple[str, str]] = set()
        result: list[tuple[str, str]] = []
        for value in values:
            if value not in seen:
                seen.add(value)
                result.append(value)
        return result

    def _unique(self, values) -> list[str]:
        seen: set[str] = set()
        result: list[str] = []
        for value in values:
            if value and value not in seen:
                seen.add(value)
                result.append(value)
        return result
