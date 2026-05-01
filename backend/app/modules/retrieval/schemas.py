from typing import Literal

from pydantic import BaseModel, Field


class EvidenceChunk(BaseModel):
    id: str
    source_type: str
    source_name: str
    source_url: str
    chunk_text: str
    chunk_index: int
    retrieval_score: float = Field(ge=0.0, le=1.0)
    case_number: str | None = None
    law_article: str | None = None
    published_at: str | None = None


class RetrievalEntityHints(BaseModel):
    case_number: str | None = None
    case_title: str | None = None
    law_names: list[str] = []
    articles: list[str] = []
    keywords: list[str] = []


class RetrievalRequest(BaseModel):
    query: str
    top_k: int = Field(default=5, ge=1, le=20)
    score_threshold: float = Field(default=0.72, ge=0.0, le=1.0)


class RetrievalResult(BaseModel):
    status: Literal["ok", "insufficient_evidence", "api_error"]
    query_hash: str
    hints: RetrievalEntityHints
    evidence_chunks: list[EvidenceChunk]
    source: Literal["official_api", "local_fallback"]
    message: str | None = None
    attempted_query: str | None = None


class LawInfoDiagnosticResponse(BaseModel):
    has_api_key: bool
    base_url: str
    status: Literal["ok", "missing_key", "api_error"]
    message: str
    sample_count: int = 0
