from pydantic import BaseModel


class AnalysisCacheIdentity(BaseModel):
    normalized_input_text: str
    analysis_type: str
    persona_mode: str
    evidence_chunk_ids: list[str]
    prompt_version: str
    model_version: str


class GeminiCallDecision(BaseModel):
    allowed: bool
    reason: str
    cache_key: str
