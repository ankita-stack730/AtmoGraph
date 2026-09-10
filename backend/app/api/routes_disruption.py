from fastapi import APIRouter, HTTPException

from app.models.schemas import DisruptionAnalyzeRequest, DisruptionAnalyzeResponse
from app.services import disruption_service

router = APIRouter(prefix="/disruption", tags=["disruption"])


@router.post("/analyze", response_model=DisruptionAnalyzeResponse)
def analyze_disruption(request: DisruptionAnalyzeRequest):
    """The primary demonstration endpoint (Section 11).

    text -> NLP -> entity resolution against Neo4j -> baseline risk
    propagation. GNN predictions (Phase 6) will populate `predictions` once
    trained; for now it is always an empty list and `method` is
    "GRAPH_BASELINE".
    """
    try:
        return disruption_service.analyze_disruption(request.text, max_hops=request.max_hops)
    except RuntimeError as exc:
        # e.g. spaCy model missing — surface a clear, actionable error
        raise HTTPException(status_code=503, detail=str(exc)) from exc
