"""
Orchestrates the end-to-end disruption analysis flow described in Section 8:

  text -> NLP -> match entities to Neo4j nodes -> propagate risk -> response

The GNN (Phase 6) will plug into `predictions` once it exists; until then
this returns the graph-baseline propagation only (method="GRAPH_BASELINE").
"""
from __future__ import annotations

import logging
from typing import List, Optional

from app.graph import graph_service
from app.models.schemas import (
    AffectedNode,
    DisruptionAnalyzeResponse,
    DisruptionEvent,
    ExtractedEntity,
)
from app.nlp import pipeline as nlp_pipeline

logger = logging.getLogger("atmograph.services.disruption")

# Entity types worth trying to resolve against the graph.
RESOLVABLE_ENTITY_TYPES = {"LOCATION", "ORGANIZATION", "FACILITY", "PORT", "WAREHOUSE", "SUPPLIER", "MANUFACTURER"}

HIGH_RISK_THRESHOLD = 0.6


def _resolve_entities_to_nodes(entities: List[ExtractedEntity]) -> List[ExtractedEntity]:
    """Mutates a copy of entities, filling matched_node_id where possible."""
    resolved: List[ExtractedEntity] = []
    for entity in entities:
        entity = entity.model_copy()
        if entity.type in RESOLVABLE_ENTITY_TYPES:
            matches = graph_service.find_nodes_by_name(entity.text, limit=1)
            if matches:
                entity.matched_node_id = matches[0].id
        resolved.append(entity)
    return resolved


def analyze_disruption(text: str, max_hops: Optional[int] = None) -> DisruptionAnalyzeResponse:
    nlp_result = nlp_pipeline.analyze_text(text)
    resolved_entities = _resolve_entities_to_nodes(nlp_result.entities)

    source_node_ids = sorted({e.matched_node_id for e in resolved_entities if e.matched_node_id})

    affected: List[AffectedNode] = graph_service.propagate_risk(source_node_ids, max_hops=max_hops)

    high_risk_count = sum(1 for n in affected if n.risk_score >= HIGH_RISK_THRESHOLD)

    return DisruptionAnalyzeResponse(
        event=DisruptionEvent(type=nlp_result.disruption_type, severity=nlp_result.severity),
        entities=resolved_entities,
        matched_source_nodes=source_node_ids,
        affected_nodes=len(affected),
        high_risk_nodes=high_risk_count,
        nodes=affected,
        predictions=[],  # populated once Phase 6 GNN inference is wired in
        method="GRAPH_BASELINE",
    )
