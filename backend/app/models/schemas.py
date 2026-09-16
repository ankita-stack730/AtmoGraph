"""
Shared Pydantic request/response schemas.
"""
from __future__ import annotations

from typing import List, Optional

from pydantic import BaseModel, Field


# ---------------------------------------------------------------------------
# Graph primitives
# ---------------------------------------------------------------------------

class GraphNode(BaseModel):
    node_id: str
    labels: List[str] = Field(default_factory=list)
    name: Optional[str] = None
    properties: dict = Field(default_factory=dict)


class GraphRelationship(BaseModel):
    source: str
    target: str
    type: str
    properties: dict = Field(default_factory=dict)


class GraphSnapshot(BaseModel):
    nodes: List[GraphNode]
    relationships: List[GraphRelationship]


# ---------------------------------------------------------------------------
# NLP
# ---------------------------------------------------------------------------

class ExtractedEntity(BaseModel):
    text: str
    type: str
    start_char: Optional[int] = None
    end_char: Optional[int] = None
    matched_node_id: Optional[str] = None  # filled in once matched against Neo4j


class NLPAnalysisRequest(BaseModel):
    text: str = Field(..., min_length=3, examples=["Rotterdam port strike causes major shipping delays."])


class NLPAnalysisResult(BaseModel):
    text: str
    entities: List[ExtractedEntity]
    disruption_type: str
    severity: float = Field(..., ge=0.0, le=1.0)
    confidence: float = Field(..., ge=0.0, le=1.0)
    method: str = "BASELINE_RULE_BASED"  # honestly labeled per project rules


# ---------------------------------------------------------------------------
# Disruption / risk propagation
# ---------------------------------------------------------------------------

class AffectedNode(BaseModel):
    node_id: str
    name: str
    labels: List[str]
    hop_distance: int
    risk_score: float = Field(..., ge=0.0, le=1.0)
    is_source: bool = False


class DisruptionAnalyzeRequest(BaseModel):
    text: str = Field(..., min_length=3, examples=["Rotterdam port strike causes major shipping delays."])
    max_hops: Optional[int] = Field(default=None, ge=1, le=10)


class DisruptionEvent(BaseModel):
    type: str
    severity: float


class DisruptionAnalyzeResponse(BaseModel):
    event: DisruptionEvent
    entities: List[ExtractedEntity]
    matched_source_nodes: List[str]
    affected_nodes: int
    high_risk_nodes: int
    nodes: List[AffectedNode]
    predictions: List[dict] = Field(
        default_factory=list,
        description="Populated once the GNN (Phase 6) is available. Empty list = baseline-only response.",
    )
    method: str = "GRAPH_BASELINE"  # will become "GNN" once Phase 6 lands


class ErrorResponse(BaseModel):
    detail: str
