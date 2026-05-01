import re

from pydantic import ValidationError

from app.core.config import settings
from app.infrastructure.cache import MemoryTTLCache, build_cache_key
from app.infrastructure.gemini_client import GeminiClient, GeminiError
from app.infrastructure.inflight import InFlightRegistry
from app.modules.diagram.schemas import (
    DiagramEdge,
    DiagramNode,
    DiagramSpec,
    ExpertDiagramSet,
    ExpertDiagramSpecSet,
    MermaidDiagram,
)
from app.modules.irac.schemas import IracAnalysis
from app.modules.retrieval.schemas import EvidenceChunk
from app.modules.shared import StatusResponse


DIAGRAM_VERSION = "expert-diagram-gemini-json-v1"
_diagram_cache: MemoryTTLCache[ExpertDiagramSet] = MemoryTTLCache(ttl_seconds=1800)
_diagram_inflight = InFlightRegistry()


class DiagramService:
    def __init__(self) -> None:
        self.gemini = GeminiClient()

    def health(self) -> StatusResponse:
        return StatusResponse(status="ready", module="diagram")

    async def generate_from_irac(self, analysis: IracAnalysis) -> MermaidDiagram:
        return (await self.generate_expert_diagrams(analysis)).legal_reasoning

    async def generate_expert_diagrams(
        self,
        analysis: IracAnalysis,
        *,
        case_text: str = "",
        evidence_chunks: list[EvidenceChunk] | None = None,
    ) -> ExpertDiagramSet:
        source_text = self._source_text(case_text, evidence_chunks)
        if not settings.gemini_api_key:
            return self._generate_local_diagrams(analysis, source_text)

        cache_key = build_cache_key(
            [
                DIAGRAM_VERSION,
                settings.gemini_model,
                source_text,
                self._analysis_json(analysis),
            ]
        )
        cached = _diagram_cache.get(cache_key)
        if cached is not None:
            return cached

        async def factory() -> ExpertDiagramSet:
            try:
                result = await self._generate_gemini_diagrams(analysis, source_text)
            except (GeminiError, ValidationError, KeyError, TypeError, ValueError):
                result = self._generate_local_diagrams(analysis, source_text)
            _diagram_cache.set(cache_key, result)
            return result

        return await _diagram_inflight.run_once(cache_key, factory)

    async def _generate_gemini_diagrams(
        self,
        analysis: IracAnalysis,
        source_text: str,
    ) -> ExpertDiagramSet:
        payload = await self.gemini.generate_json(self._build_prompt(analysis, source_text))
        specs = ExpertDiagramSpecSet.model_validate(payload)
        return ExpertDiagramSet(
            party_relation=self._spec_to_mermaid(specs.party_relation, direction="LR"),
            event_timeline=self._spec_to_mermaid(specs.event_timeline, direction="LR"),
            legal_reasoning=self._spec_to_mermaid(specs.legal_reasoning, direction="LR"),
        )

    def _generate_local_diagrams(self, analysis: IracAnalysis, source_text: str) -> ExpertDiagramSet:
        return ExpertDiagramSet(
            party_relation=self._spec_to_mermaid(self._local_party_spec(source_text, analysis), direction="LR"),
            event_timeline=self._spec_to_mermaid(self._local_timeline_spec(source_text), direction="LR"),
            legal_reasoning=self._spec_to_mermaid(self._local_reasoning_spec(analysis), direction="LR"),
        )

    def _build_prompt(self, analysis: IracAnalysis, source_text: str) -> str:
        return f"""
당신은 StackSync AI의 한국어 판례 다이어그램 구조 분석기입니다.
주어진 판례 원문과 IRAC 필드에 근거해서만 답하세요.
법률 조언, 승소 가능성, 새로운 사실 추정은 금지합니다.

반드시 JSON object만 반환하세요. Markdown, 설명문, Mermaid 코드는 출력하지 마세요.

출력 형식:
{{
  "party_relation": {{
    "title": "당사자 관계도",
    "nodes": [{{"id": "P1", "label": "원고", "detail": "손해배상 청구", "type": "partyA"}}],
    "edges": [{{"source": "P1", "target": "ISSUE", "label": "주장"}}]
  }},
  "event_timeline": {{
    "title": "사건 흐름",
    "nodes": [{{"id": "E1", "label": "계약 체결", "detail": "핵심 사실", "type": "event"}}],
    "edges": [{{"source": "E1", "target": "E2", "label": ""}}]
  }},
  "legal_reasoning": {{
    "title": "법리 판단 분기",
    "nodes": [{{"id": "R1", "label": "쟁점", "detail": "계약 해제 요건", "type": "issue"}}],
    "edges": [{{"source": "R1", "target": "R2", "label": "기준 확인"}}]
  }}
}}

규칙:
- 세 다이어그램을 한 번의 JSON 응답에 모두 포함하세요.
- 각 다이어그램은 3~6개 노드만 사용하세요.
- label은 18자 이하, detail은 28자 이하의 짧은 한국어로 작성하세요.
- 마름모/조건 노드 개념을 쓰지 마세요. 모든 노드는 직사각형으로 렌더링됩니다.
- type은 partyA, partyB, issue, rule, apply, event, decision 중 하나만 사용하세요.
- party_relation은 누가 누구에게 무엇을 주장/다투는지에 집중하세요.
- event_timeline은 IRAC 표현이 아니라 사건 사실의 시간 순서에 집중하세요.
- legal_reasoning만 IRAC를 사용해 쟁점, 판단 기준, 사실 적용, 결론을 분리하세요.
- 불명확한 내용은 "확인 필요"라고 쓰고 지어내지 마세요.

판례 원문:
{self._clip_for_prompt(source_text, 5000)}

IRAC:
{self._analysis_json(analysis)}
""".strip()

    def _spec_to_mermaid(self, spec: DiagramSpec, *, direction: str) -> MermaidDiagram:
        nodes = spec.nodes[:6] or [DiagramNode(id="N1", label="확인 필요", detail="", type="event")]
        node_ids = {self._node_id(node.id) for node in nodes}
        lines = self._style_header(direction)
        for node in nodes:
            node_id = self._node_id(node.id)
            label = self._node_label(node.label, node.detail)
            node_class = self._node_class(node.type)
            lines.append(f"    {node_id}[\"{label}\"]:::{node_class}")

        valid_edges = [
            edge
            for edge in spec.edges[:8]
            if self._node_id(edge.source) in node_ids and self._node_id(edge.target) in node_ids
        ]
        if not valid_edges and len(nodes) > 1:
            valid_edges = [
                DiagramEdge(source=nodes[index].id, target=nodes[index + 1].id)
                for index in range(len(nodes) - 1)
            ]
        for edge in valid_edges:
            source = self._node_id(edge.source)
            target = self._node_id(edge.target)
            label = self._clean(edge.label)
            if label:
                lines.append(f"    {source} -->|{self._escape_label(label)}| {target}")
            else:
                lines.append(f"    {source} --> {target}")
        return MermaidDiagram(title=spec.title, code="\n".join(lines))

    def _local_party_spec(self, text: str, analysis: IracAnalysis) -> DiagramSpec:
        issue = self._extract_issue_label(text, analysis)
        claim = self._extract_claim(text)
        parties = self._extract_parties(text, analysis.key_terms)
        return DiagramSpec(
            title="당사자 관계도",
            nodes=[
                DiagramNode(id="P1", label=parties["left"], detail=claim["left"], type="partyA"),
                DiagramNode(id="ISSUE", label="분쟁 쟁점", detail=issue, type="issue"),
                DiagramNode(id="P2", label=parties["right"], detail=claim["right"], type="partyB"),
            ],
            edges=[
                DiagramEdge(source="P1", target="ISSUE", label="주장"),
                DiagramEdge(source="P2", target="ISSUE", label="다툼"),
            ],
        )

    def _local_timeline_spec(self, text: str) -> DiagramSpec:
        events = self._extract_events(text)
        nodes = [
            DiagramNode(
                id=f"E{index}",
                label=f"{index + 1}단계",
                detail=event,
                type="decision" if index == len(events) - 1 else "event",
            )
            for index, event in enumerate(events)
        ]
        return DiagramSpec(
            title="사건 흐름",
            nodes=nodes,
            edges=[
                DiagramEdge(source=f"E{index}", target=f"E{index + 1}")
                for index in range(len(nodes) - 1)
            ],
        )

    def _local_reasoning_spec(self, analysis: IracAnalysis) -> DiagramSpec:
        laws = self._shorten(", ".join(analysis.referenced_laws) or "명시 조문 없음", 28)
        return DiagramSpec(
            title="법리 판단 분기",
            nodes=[
                DiagramNode(id="I", label="쟁점", detail=self._shorten(analysis.issue.text, 34), type="issue"),
                DiagramNode(id="R", label="판단 기준", detail=f"{self._shorten(analysis.rule.text, 26)} / {laws}", type="rule"),
                DiagramNode(id="A", label="사실 적용", detail=self._shorten(analysis.application.text, 34), type="apply"),
                DiagramNode(id="C", label="판결 요지", detail=self._shorten(analysis.conclusion.text, 34), type="decision"),
            ],
            edges=[
                DiagramEdge(source="I", target="R", label="기준 확인"),
                DiagramEdge(source="R", target="A", label="사안 적용"),
                DiagramEdge(source="A", target="C", label="결론"),
            ],
        )

    def is_valid_mermaid_flowchart(self, code: str) -> bool:
        stripped = code.strip()
        return stripped.startswith("flowchart ") and "-->" in stripped and "{" not in stripped

    def _style_header(self, direction: str) -> list[str]:
        return [
            f"flowchart {direction}",
            "    classDef issue fill:#1d4ed8,stroke:#bfdbfe,color:#ffffff,stroke-width:1px",
            "    classDef rule fill:#047857,stroke:#a7f3d0,color:#ffffff,stroke-width:1px",
            "    classDef apply fill:#92400e,stroke:#fde68a,color:#ffffff,stroke-width:1px",
            "    classDef event fill:#374151,stroke:#d1d5db,color:#ffffff,stroke-width:1px",
            "    classDef partyA fill:#6d28d9,stroke:#ddd6fe,color:#ffffff,stroke-width:1px",
            "    classDef partyB fill:#b91c1c,stroke:#fecaca,color:#ffffff,stroke-width:1px",
            "    classDef decision fill:#15803d,stroke:#bbf7d0,color:#ffffff,stroke-width:1px",
        ]

    def _source_text(self, case_text: str, evidence_chunks: list[EvidenceChunk] | None) -> str:
        if case_text.strip():
            return case_text.strip()
        chunks = evidence_chunks or []
        return " ".join(chunk.chunk_text for chunk in chunks).strip()

    def _analysis_json(self, analysis: IracAnalysis) -> str:
        if hasattr(analysis, "model_dump_json"):
            return analysis.model_dump_json()
        return analysis.json(ensure_ascii=False)

    def _extract_parties(self, text: str, key_terms: list[str]) -> dict[str, str]:
        left = self._find_party(text, ("원고", "청구인", "신청인", "피해자"))
        right = self._find_party(text, ("피고", "피청구인", "상대방", "가해자"))
        if not left:
            left = self._pick_first(key_terms, ("원고", "청구인", "신청인", "피해자"), "원고 측")
        if not right:
            right = self._pick_first(key_terms, ("피고", "피청구인", "상대방", "가해자"), "피고 측")
        return {"left": left, "right": right}

    def _find_party(self, text: str, labels: tuple[str, ...]) -> str | None:
        for label in labels:
            if label in text:
                return label
        return None

    def _extract_claim(self, text: str) -> dict[str, str]:
        left = "청구 또는 주장"
        right = "항변 또는 다툼"
        if "손해배상" in text:
            left = "손해배상 청구"
        elif "해제" in text or "취소" in text:
            left = "계약 효력 다툼"
        if "항변" in text:
            right = "항변"
        elif "다투" in text or "부인" in text:
            right = "청구 원인 다툼"
        return {"left": left, "right": right}

    def _extract_issue_label(self, text: str, analysis: IracAnalysis) -> str:
        labels: list[str] = []
        if "계약" in text and ("해제" in text or "취소" in text):
            labels.append("계약 효력")
        if "손해배상" in text or "손해" in text:
            labels.append("손해배상 책임")
        if "부당이득" in text:
            labels.append("부당이득 반환")
        if "소유권" in text:
            labels.append("소유권 귀속")
        if "보증금" in text:
            labels.append("보증금 반환")
        if labels:
            return " / ".join(labels[:2])
        return self._shorten(analysis.issue.text, 34)

    def _extract_events(self, text: str) -> list[str]:
        sentences = self._sentence_fragments(text)
        candidates = [self._shorten(sentence, 34) for sentence in sentences[:5]]
        if len(candidates) >= 3:
            return candidates
        if text.strip():
            return [self._shorten(text, 34), "당사자 주장 대립", "법원 판단"]
        return ["사실관계 확인", "당사자 주장 대립", "법원 판단"]

    def _node_id(self, value: str) -> str:
        cleaned = re.sub(r"[^A-Za-z0-9_]", "_", value.strip() or "N")
        if cleaned[0].isdigit():
            cleaned = f"N_{cleaned}"
        return cleaned[:24]

    def _node_label(self, label: str, detail: str) -> str:
        head = self._escape_label(self._shorten(label, 20))
        body = self._escape_label(self._shorten(detail, 34))
        return f"{head}<br/>{body}" if body else head

    def _node_class(self, value: str) -> str:
        allowed = {"partyA", "partyB", "issue", "rule", "apply", "event", "decision"}
        return value if value in allowed else "event"

    def _escape_label(self, text: str) -> str:
        return self._clean(text).replace('"', "'").replace("|", "/")

    def _shorten(self, text: str, limit: int = 40) -> str:
        cleaned = self._clean(text)
        return cleaned if len(cleaned) <= limit else cleaned[: limit - 1] + "..."

    def _clean(self, text: str) -> str:
        cleaned = re.sub(r'["\n\r]+', " ", str(text)).strip()
        return re.sub(r"\s+", " ", cleaned)

    def _clip_for_prompt(self, text: str, limit: int) -> str:
        cleaned = self._clean(text)
        return cleaned if len(cleaned) <= limit else cleaned[:limit]

    def _sentence_fragments(self, text: str) -> list[str]:
        parts = re.split(r"(?<=[.!?。])\s+|(?<=다\.)\s*", text)
        return [part.strip() for part in parts if part.strip()]

    def _pick_first(self, values: list[str], candidates: tuple[str, ...], fallback: str) -> str:
        for candidate in candidates:
            if candidate in values:
                return candidate
        return fallback
