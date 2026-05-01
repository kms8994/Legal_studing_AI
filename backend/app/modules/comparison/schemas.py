from pydantic import BaseModel, Field


class ComparisonResult(BaseModel):
    factual_comparison: str
    legal_basis_comparison: str
    judgment_comparison: str
    decisive_difference: str
    similarity_score: int = Field(ge=0, le=100)

