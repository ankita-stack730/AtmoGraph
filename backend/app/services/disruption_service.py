"""
Orchestrates the end-to-end disruption analysis flow:

    text
      -> NLP
      -> entity resolution
      -> Neo4j graph traversal
      -> GraphSAGE prediction
      -> response
"""

from __future__ import annotations

import logging
from typing import List, Optional

from app.graph import graph_service
from app.ml.inference import graphsage_inference
from app.models.schemas import (
    AffectedNode,
    DisruptionAnalyzeResponse,
    DisruptionEvent,
    ExtractedEntity,
)
from app.nlp import pipeline as nlp_pipeline

logger = logging.getLogger("atmograph.services.disruption")

RESOLVABLE_ENTITY_TYPES = {
    "LOCATION",
    "ORGANIZATION",
    "FACILITY",
    "PORT",
    "WAREHOUSE",
    "SUPPLIER",
    "MANUFACTURER",
}

HIGH_RISK_THRESHOLD = 0.6


def _resolve_entities_to_nodes(
    entities: List[ExtractedEntity],
) -> List[ExtractedEntity]:
    """Mutates a copy of entities, filling matched_node_id where possible."""

    resolved: List[ExtractedEntity] = []

    for entity in entities:
        entity = entity.model_copy()

        if entity.type in RESOLVABLE_ENTITY_TYPES:
            matches = graph_service.find_nodes_by_name(
                entity.text,
                limit=1,
            )

            if matches:
                entity.matched_node_id = matches[0].node_id

        resolved.append(entity)

    return resolved


def analyze_disruption(
    text: str,
    max_hops: Optional[int] = None,
) -> DisruptionAnalyzeResponse:

    # ---------------------------------------------------------------
    # 1. NLP analysis
    # ---------------------------------------------------------------

    nlp_result = nlp_pipeline.analyze_text(text)

    # ---------------------------------------------------------------
    # 2. Resolve extracted entities to Neo4j nodes
    # ---------------------------------------------------------------

    resolved_entities = _resolve_entities_to_nodes(
        nlp_result.entities
    )

    source_node_ids = sorted(
        {
            entity.matched_node_id
            for entity in resolved_entities
            if entity.matched_node_id
        }
    )

    # ---------------------------------------------------------------
    # 3. Existing graph-baseline propagation
    # ---------------------------------------------------------------

    affected: List[AffectedNode] = graph_service.propagate_risk(
        source_node_ids,
        max_hops=max_hops,
    )

    high_risk_count = sum(
        1
        for node in affected
        if node.risk_score >= HIGH_RISK_THRESHOLD
    )

    # ---------------------------------------------------------------
    # 4. GraphSAGE prediction
    # ---------------------------------------------------------------

    predictions: List[dict] = []

    if graphsage_inference.is_available():
        try:
            snapshot = graph_service.get_full_graph()

            baseline_risk = {
                node.node_id: node.risk_score
                for node in affected
            }

            gnn_scores = graphsage_inference.predict(
                snapshot=snapshot,
                source_node_ids=source_node_ids,
                baseline_risk=baseline_risk,
                disruption_severity=nlp_result.severity,
            )

            predictions = [
                {
                    "node_id": node_id,
                    "risk_score": risk_score,
                }
                for node_id, risk_score in gnn_scores.items()
            ]

        except Exception:
            logger.exception(
                "GraphSAGE inference failed; "
                "returning graph-baseline response."
            )

    # ---------------------------------------------------------------
    # 5. Build response
    # ---------------------------------------------------------------

    method = (
        "GRAPHSAGE"
        if predictions
        else "GRAPH_BASELINE"
    )

    return DisruptionAnalyzeResponse(
        event=DisruptionEvent(
            type=nlp_result.disruption_type,
            severity=nlp_result.severity,
        ),
        entities=resolved_entities,
        matched_source_nodes=source_node_ids,
        affected_nodes=len(affected),
        high_risk_nodes=high_risk_count,
        nodes=affected,
        predictions=predictions,
        method=method,
    )