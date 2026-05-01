import asyncio
import json
import re
import urllib.error
import urllib.parse
import urllib.request
import xml.etree.ElementTree as ET
from dataclasses import asdict
from typing import Any

from app.core.config import settings
from app.core.exceptions import AppError
from app.infrastructure.cache import build_cache_key
from app.infrastructure.lawinfo_schemas import CaseDocument, CaseSummary, StatuteArticle


class LawInfoError(AppError):
    def __init__(self, message: str, *, status_code: int = 502) -> None:
        super().__init__(message, status_code=status_code, code="lawinfo_error")


class LawInfoClient:
    def __init__(
        self,
        *,
        api_key: str | None = None,
        base_url: str | None = None,
        timeout_seconds: float = 10.0,
        max_retries: int = 2,
    ) -> None:
        self.api_key = api_key or settings.lawinfo_api_key
        self.base_url = (base_url or settings.lawinfo_base_url).rstrip("/")
        self.timeout_seconds = timeout_seconds
        self.max_retries = max_retries

    async def get_case_by_number(self, case_number: str) -> dict[str, object]:
        matches = await self.search_cases_by_number(case_number, display=5)
        exact = self._select_case_match(matches, case_number)
        if exact is None:
            raise LawInfoError(f"판례 번호로 공식 판례를 찾을 수 없습니다: {case_number}", status_code=404)

        document = await self.get_case_by_id(exact.id, title=exact.title)
        return asdict(document)

    async def get_case_by_id(self, case_id: str, *, title: str | None = None) -> CaseDocument:
        params = {
            "target": "prec",
            "ID": case_id,
            "type": "HTML",
            "mobileYn": "Y",
        }
        raw, source_url = await self._request("lawService.do", params=params, expect_json=False)
        body_text = self._html_to_text(str(raw))
        return CaseDocument(
            id=case_id,
            title=title or "",
            case_number=None,
            body_text=body_text,
            source_url=source_url,
            raw={"html": raw},
        )

    async def search_cases(
        self,
        query: str,
        *,
        search_scope: int = 1,
        display: int = 20,
        page: int = 1,
    ) -> list[CaseSummary]:
        params = {
            "target": "prec",
            "type": "JSON",
            "search": str(search_scope),
            "query": query,
            "display": str(display),
            "page": str(page),
        }
        raw, source_url = await self._request("lawSearch.do", params=params)
        items = self._extract_items(raw, preferred_keys=("prec", "Prec", "판례"))
        return [self._normalize_case_summary(item, source_url) for item in items]

    async def search_cases_by_number(
        self,
        case_number: str,
        *,
        display: int = 20,
        page: int = 1,
    ) -> list[CaseSummary]:
        attempts = (
            {
                "target": "prec",
                "type": "JSON",
                "nb": case_number,
                "display": str(display),
                "page": str(page),
            },
            {
                "target": "prec",
                "type": "JSON",
                "search": "2",
                "query": case_number,
                "display": str(display),
                "page": str(page),
            },
        )
        last_error: LawInfoError | None = None
        for params in attempts:
            try:
                raw, source_url = await self._request("lawSearch.do", params=params)
                items = self._extract_items(raw, preferred_keys=("prec", "Prec", "판례"))
                summaries = [self._normalize_case_summary(item, source_url) for item in items]
                if summaries:
                    return summaries
            except LawInfoError as exc:
                last_error = exc

        if last_error:
            raise last_error
        return []

    async def get_statute_article(self, law_name: str, article: str) -> dict[str, object]:
        law = await self._find_law(law_name)
        law_id = self._first_present(law, ("법령ID", "법령ID값", "ID", "id"))
        mst = self._first_present(law, ("법령일련번호", "MST", "mst", "lsi_seq"))
        if not law_id and not mst:
            raise LawInfoError(f"법령 ID를 찾을 수 없습니다: {law_name}", status_code=404)

        params = {
            "target": "lawjosub",
            "type": "JSON",
            "JO": self._normalize_article_number(article),
        }
        if law_id:
            params["ID"] = str(law_id)
        else:
            params["MST"] = str(mst)

        raw, source_url = await self._request("lawService.do", params=params)
        body_text = self._collect_text(raw)
        result = StatuteArticle(
            law_id=str(law_id or mst),
            law_name=law_name,
            article=article,
            body_text=body_text,
            source_url=source_url,
            raw=raw if isinstance(raw, dict) else {"response": raw},
        )
        return asdict(result)

    async def _find_law(self, law_name: str) -> dict[str, Any]:
        params = {
            "target": "law",
            "type": "JSON",
            "search": "1",
            "query": law_name,
            "display": "5",
            "page": "1",
        }
        raw, _ = await self._request("lawSearch.do", params=params)
        items = self._extract_items(raw, preferred_keys=("law", "Law", "법령"))
        if not items:
            raise LawInfoError(f"공식 법령 검색 결과가 없습니다: {law_name}", status_code=404)
        return items[0]

    async def _request(
        self,
        path: str,
        *,
        params: dict[str, str],
        expect_json: bool = True,
    ) -> tuple[Any, str]:
        if not self.api_key:
            raise LawInfoError("LAWINFO_API_KEY가 설정되어 있지 않습니다.", status_code=500)

        request_url = self._build_url(path, {"OC": self.api_key, **params})
        source_url = self._build_url(path, params)

        last_error: Exception | None = None
        for attempt in range(self.max_retries + 1):
            try:
                text = await asyncio.to_thread(self._fetch_text, request_url)
                if expect_json:
                    parsed = self._parse_json_or_xml(text)
                    self._raise_if_api_error(parsed)
                    return parsed, source_url
                return text, source_url
            except (OSError, urllib.error.URLError, TimeoutError, json.JSONDecodeError, ET.ParseError) as exc:
                last_error = exc
                if attempt < self.max_retries:
                    await asyncio.sleep(0.25 * (attempt + 1))

        raise LawInfoError(f"공식 법률 API 호출에 실패했습니다: {last_error}")

    def _raise_if_api_error(self, payload: dict[str, Any]) -> None:
        result, message = self._find_api_error(payload)
        if result and ("실패" in result or "오류" in result):
            raise LawInfoError(message or result, status_code=502)

    def _find_api_error(self, value: Any) -> tuple[str, str]:
        if isinstance(value, dict):
            result = str(value.get("result", "")).strip()
            message = str(value.get("msg", "")).strip()
            if result or message:
                return result, message
            for child in value.values():
                nested_result, nested_message = self._find_api_error(child)
                if nested_result or nested_message:
                    return nested_result, nested_message
        elif isinstance(value, list):
            for child in value:
                nested_result, nested_message = self._find_api_error(child)
                if nested_result or nested_message:
                    return nested_result, nested_message
        return "", ""

    def build_request_cache_key(self, path: str, params: dict[str, str]) -> str:
        encoded = urllib.parse.urlencode(sorted(params.items()))
        return build_cache_key(("lawinfo", path, encoded))

    def _build_url(self, path: str, params: dict[str, str]) -> str:
        return f"{self.base_url}/{path}?{urllib.parse.urlencode(params)}"

    def _fetch_text(self, url: str) -> str:
        request = urllib.request.Request(
            url,
            headers={"User-Agent": "case-ai-learning-service/0.1"},
        )
        with urllib.request.urlopen(request, timeout=self.timeout_seconds) as response:
            charset = response.headers.get_content_charset() or "utf-8"
            return response.read().decode(charset, errors="replace")

    def _parse_json_or_xml(self, text: str) -> dict[str, Any]:
        stripped = text.strip()
        if stripped.startswith("{") or stripped.startswith("["):
            parsed = json.loads(stripped)
            return parsed if isinstance(parsed, dict) else {"items": parsed}
        return self._xml_to_dict(ET.fromstring(stripped))

    def _xml_to_dict(self, element: ET.Element) -> dict[str, Any]:
        children = list(element)
        if not children:
            return {element.tag: (element.text or "").strip()}

        result: dict[str, Any] = {}
        for child in children:
            child_dict = self._xml_to_dict(child)
            key, value = next(iter(child_dict.items()))
            if key in result:
                if not isinstance(result[key], list):
                    result[key] = [result[key]]
                result[key].append(value)
            else:
                result[key] = value
        return {element.tag: result}

    def _extract_items(self, raw: dict[str, Any], *, preferred_keys: tuple[str, ...]) -> list[dict[str, Any]]:
        candidates: list[Any] = []

        def walk(value: Any) -> None:
            if isinstance(value, dict):
                for key, child in value.items():
                    if key in preferred_keys:
                        candidates.append(child)
                    walk(child)
            elif isinstance(value, list):
                for child in value:
                    walk(child)

        walk(raw)
        flattened: list[dict[str, Any]] = []
        for candidate in candidates:
            if isinstance(candidate, list):
                flattened.extend(item for item in candidate if isinstance(item, dict))
            elif isinstance(candidate, dict):
                flattened.append(candidate)

        if flattened:
            return flattened

        if isinstance(raw, dict):
            return [raw]
        return []

    def _normalize_case_summary(self, item: dict[str, Any], source_url: str) -> CaseSummary:
        case_id = self._first_present(item, ("판례일련번호", "판례정보일련번호", "ID", "id")) or ""
        title = self._first_present(item, ("사건명", "판례명", "title")) or ""
        case_number = self._first_present(item, ("사건번호", "case_number"))
        court = self._first_present(item, ("법원명", "선고법원", "court"))
        decision_date = self._first_present(item, ("선고일자", "decision_date"))
        detail_link = self._first_present(item, ("판례상세링크", "상세링크", "detail_link"))
        return CaseSummary(
            id=str(case_id),
            title=str(title),
            case_number=str(case_number) if case_number else None,
            court=str(court) if court else None,
            decision_date=str(decision_date) if decision_date else None,
            source_url=self._absolute_law_url(str(detail_link)) if detail_link else source_url,
            raw=item,
        )

    def _select_case_match(self, cases: list[CaseSummary], case_number: str) -> CaseSummary | None:
        normalized = self._compact(case_number)
        for case in cases:
            if case.case_number and self._compact(case.case_number) == normalized:
                return case
        return cases[0] if cases else None

    def _normalize_article_number(self, article: str) -> str:
        numbers = re.findall(r"\d+", article)
        if not numbers:
            raise LawInfoError(f"조문 번호를 해석할 수 없습니다: {article}", status_code=400)
        main = int(numbers[0])
        branch = int(numbers[1]) if len(numbers) > 1 else 0
        return f"{main:04d}{branch:02d}"

    def _collect_text(self, value: Any) -> str:
        parts: list[str] = []

        def walk(node: Any) -> None:
            if isinstance(node, dict):
                for child in node.values():
                    walk(child)
            elif isinstance(node, list):
                for child in node:
                    walk(child)
            elif node is not None:
                text = str(node).strip()
                if text:
                    parts.append(text)

        walk(value)
        return "\n".join(dict.fromkeys(parts))

    def _html_to_text(self, html: str) -> str:
        without_script = re.sub(r"(?is)<(script|style).*?>.*?</\1>", " ", html)
        without_tags = re.sub(r"(?s)<[^>]+>", " ", without_script)
        unescaped = (
            without_tags.replace("&nbsp;", " ")
            .replace("&lt;", "<")
            .replace("&gt;", ">")
            .replace("&amp;", "&")
        )
        return re.sub(r"\s+", " ", unescaped).strip()

    def _first_present(self, item: dict[str, Any], keys: tuple[str, ...]) -> Any:
        for key in keys:
            value = item.get(key)
            if value not in (None, ""):
                return value
        return None

    def _absolute_law_url(self, link: str) -> str:
        if link.startswith("http://") or link.startswith("https://"):
            return link
        return f"https://www.law.go.kr{link if link.startswith('/') else '/' + link}"

    def _compact(self, value: str) -> str:
        return re.sub(r"\s+", "", value)
