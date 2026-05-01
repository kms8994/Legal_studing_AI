from pydantic import BaseModel

from app.modules.irac.schemas import IracAnalysis


class MermaidDiagram(BaseModel):
    title: str = "Diagram"
    code: str


class ExpertDiagramSet(BaseModel):
    party_relation: MermaidDiagram
    event_timeline: MermaidDiagram
    legal_reasoning: MermaidDiagram


class DiagramNode(BaseModel):
    id: str
    label: str
    detail: str = ""
    type: str = "event"


class DiagramEdge(BaseModel):
    source: str
    target: str
    label: str = ""


class DiagramSpec(BaseModel):
    title: str
    nodes: list[DiagramNode]
    edges: list[DiagramEdge]


class ExpertDiagramSpecSet(BaseModel):
    party_relation: DiagramSpec
    event_timeline: DiagramSpec
    legal_reasoning: DiagramSpec


class DiagramGenerateRequest(BaseModel):
    analysis: IracAnalysis
