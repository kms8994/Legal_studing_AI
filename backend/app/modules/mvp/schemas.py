from pydantic import BaseModel

from app.modules.diagram.schemas import ExpertDiagramSet, MermaidDiagram
from app.modules.irac.schemas import IracAnalysis
from app.modules.retrieval.schemas import EvidenceChunk, RetrievalEntityHints


class MvpAnalyzeRequest(BaseModel):
    text: str
    persona_mode: str = "expert"


class MvpAnalyzeResponse(BaseModel):
    mode: str
    input_hash: str
    hints: RetrievalEntityHints
    evidence_chunks: list[EvidenceChunk]
    irac: IracAnalysis
    diagram: MermaidDiagram
    diagrams: ExpertDiagramSet
    disclaimer: str
