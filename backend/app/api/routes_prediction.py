"""
GNN prediction endpoints.

Provides node-level ripple-risk predictions from the trained
AtmoGraph GraphSAGE model.
"""

from fastapi import APIRouter, HTTPException

from app.graph import graph_service
from app.ml.inference import graphsage_inference

router = APIRouter(tags=["prediction"])


@router.post("/predict")
def predict():
    """Run GraphSAGE inference on the current supply-chain graph."""

    if not graphsage_inference.is_available():
        raise HTTPException(
            status_code=503,
            detail="Trained GraphSAGE model is not available.",
        )

    try:
        snapshot = graph_service.get_full_graph()

        predictions = graphsage_inference.predict(
            snapshot=snapshot,
        )

        return {
            "predictions": predictions,
            "node_count": len(predictions),
            "method": "GRAPHSAGE",
        }

    except Exception as exc:
        raise HTTPException(
            status_code=500,
            detail=f"GNN prediction failed: {exc}",
        ) from exc


@router.get("/risk/nodes")
def risk_nodes():
    """Return GraphSAGE risk scores for all graph nodes."""

    return predict()


@router.get("/risk/timeline")
def risk_timeline():
    """
    Timeline endpoint placeholder.

    A true temporal prediction requires timestamped disruption
    scenarios, which are not currently part of the trained model.
    """

    raise HTTPException(
        status_code=501,
        detail=(
            "Risk timeline is not implemented because the current "
            "GraphSAGE model performs node-level risk prediction "
            "without temporal forecasting."
        ),
    )