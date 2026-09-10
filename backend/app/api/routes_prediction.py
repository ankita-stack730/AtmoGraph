"""
GNN prediction endpoints.

PHASE 1 STATUS: stubs only. The GNN does not exist yet (that's Phase 6).
These return HTTP 501 with a clear explanation rather than fake numbers,
per Section 17 ("do not generate fake implementation claims").
"""
from fastapi import APIRouter, HTTPException

router = APIRouter(tags=["prediction"])

_NOT_YET_IMPLEMENTED = (
    "The GNN model has not been trained yet (Phase 6 of the roadmap). "
    "Use POST /disruption/analyze for the current graph-baseline risk propagation."
)


@router.post("/predict")
def predict():
    raise HTTPException(status_code=501, detail=_NOT_YET_IMPLEMENTED)


@router.get("/risk/nodes")
def risk_nodes():
    raise HTTPException(status_code=501, detail=_NOT_YET_IMPLEMENTED)


@router.get("/risk/timeline")
def risk_timeline():
    raise HTTPException(status_code=501, detail=_NOT_YET_IMPLEMENTED)
