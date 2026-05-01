from pydantic import BaseModel

from app.modules.retrieval.schemas import EvidenceChunk


class EvidenceBackedText(BaseModel):
    text: str
    evidence_ids: list[str]


class IracAnalysis(BaseModel):
    issue: EvidenceBackedText
    rule: EvidenceBackedText
    application: EvidenceBackedText
    conclusion: EvidenceBackedText
    key_terms: list[str] = []
    referenced_laws: list[str] = []


class IracAnalyzeRequest(BaseModel):
    case_text: str
    evidence_chunks: list[EvidenceChunk]
    persona_mode: str = "expert"


class IracAnalyzeResult(BaseModel):
    status: str
    analysis: IracAnalysis | None = None
    reason: str | None = None
