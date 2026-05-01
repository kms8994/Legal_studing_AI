from pydantic import BaseModel, Field


class GeneralSituationRequest(BaseModel):
    situation: str = Field(min_length=1)


class SimilarCaseCandidate(BaseModel):
    title: str
    case_number: str | None = None
    court: str | None = None
    decision_date: str | None = None
    similarity_reason: str
    supreme_court_holding: str
    source_url: str
    evidence_text: str


class GeneralSituationResponse(BaseModel):
    mode: str = "general-similar-case"
    query_keywords: list[str]
    candidates: list[SimilarCaseCandidate]
    limitation: str
