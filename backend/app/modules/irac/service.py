from app.modules.irac.prompts import COMMON_PERSONA, EXPERT_PERSONA, GENERAL_PERSONA
from app.modules.irac.schemas import EvidenceBackedText, IracAnalysis, IracAnalyzeResult
from app.modules.retrieval.schemas import EvidenceChunk
from app.modules.analysis_guard.policy import contains_prohibited_legal_advice
from app.modules.shared import StatusResponse


class IracService:
    def health(self) -> StatusResponse:
        return StatusResponse(status="ready", module="irac")

    def build_grounded_prompt(
        self,
        *,
        case_text: str,
        evidence_chunks: list[EvidenceChunk],
        persona_mode: str,
    ) -> str:
        persona = GENERAL_PERSONA if persona_mode == "general" else EXPERT_PERSONA
        evidence_text = "\n\n".join(
            f"[{chunk.id}]\n출처: {chunk.source_name}\nURL: {chunk.source_url}\n{chunk.chunk_text}"
            for chunk in evidence_chunks
        )
        return f"""{COMMON_PERSONA}
{persona}

다음 판례 입력을 IRAC JSON으로만 분석하세요.
모든 주요 설명에는 반드시 evidence_ids를 포함하세요.

[사용자 입력]
{case_text}

[공식 근거 문서]
{evidence_text}
"""

    def validate_evidence_support(
        self,
        analysis: IracAnalysis,
        evidence_chunks: list[EvidenceChunk],
    ) -> bool:
        allowed_ids = {chunk.id for chunk in evidence_chunks}
        evidence_groups = [
            analysis.issue.evidence_ids,
            analysis.rule.evidence_ids,
            analysis.application.evidence_ids,
            analysis.conclusion.evidence_ids,
        ]
        return all(
            ids and all(evidence_id in allowed_ids for evidence_id in ids)
            for ids in evidence_groups
        )

    def validate_legal_advice_policy(self, analysis: IracAnalysis) -> bool:
        text = "\n".join(
            (
                analysis.issue.text,
                analysis.rule.text,
                analysis.application.text,
                analysis.conclusion.text,
            )
        )
        return not contains_prohibited_legal_advice(text)

    def insufficient_evidence(self) -> IracAnalyzeResult:
        return IracAnalyzeResult(
            status="insufficient_evidence",
            reason="RAG 근거가 없어 Gemini 분석을 실행하지 않습니다.",
        )

    def placeholder_from_evidence(self, evidence_chunks: list[EvidenceChunk]) -> IracAnalysis:
        first_id = evidence_chunks[0].id
        unsupported = "AI 분석 호출 전입니다. 공식 근거 확보 후 Gemini 분석 단계에서 생성됩니다."
        return IracAnalysis(
            issue=EvidenceBackedText(text=unsupported, evidence_ids=[first_id]),
            rule=EvidenceBackedText(text=unsupported, evidence_ids=[first_id]),
            application=EvidenceBackedText(text=unsupported, evidence_ids=[first_id]),
            conclusion=EvidenceBackedText(text=unsupported, evidence_ids=[first_id]),
        )
