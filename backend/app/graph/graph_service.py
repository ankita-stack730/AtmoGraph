"""
Graph service layer.

Sits between the API routes and the raw Neo4j client. Responsible for:
  - fetching graph snapshots / single nodes
  - fuzzy-matching NLP entity text to graph nodes
  - baseline (non-ML) risk propagation described in Section 8 of the spec
"""
from __future__ import annotations

import logging
from typing import Dict, List, Optional

from neo4j.graph import Node as Neo4jNode

from app.config import get_settings
from app.graph import queries
from app.graph.neo4j_client import neo4j_client
from app.models.schemas import AffectedNode, GraphNode, GraphRelationship, GraphSnapshot

logger = logging.getLogger("atmograph.graph_service")


def _neo4j_node_to_schema(node: Neo4jNode) -> GraphNode:
    props = dict(node)
    return GraphNode(
        id=props.get("id", str(node.element_id)),
        labels=list(node.labels),
        name=props.get("name"),
        properties=props,
    )


def get_full_graph() -> GraphSnapshot:
    """Fetch the entire graph. Fine for MVP-sized demo data; would need
    pagination/limits for a graph with thousands of nodes (see Section 13)."""
    rows = neo4j_client.run_query(queries.GET_FULL_GRAPH)

    nodes_by_id: Dict[str, GraphNode] = {}
    relationships: List[GraphRelationship] = []

    for row in rows:
        n = row.get("n")
        m = row.get("m")
        r = row.get("r")

        if n is not None:
            node_schema = _neo4j_node_to_schema(n)
            nodes_by_id[node_schema.id] = node_schema
        if m is not None:
            node_schema = _neo4j_node_to_schema(m)
            nodes_by_id[node_schema.id] = node_schema
        if r is not None and n is not None and m is not None:
            relationships.append(
                GraphRelationship(
                    source=dict(n).get("id"),
                    target=dict(m).get("id"),
                    type=r.type,
                    properties=dict(r),
                )
            )

    return GraphSnapshot(nodes=list(nodes_by_id.values()), relationships=relationships)


def get_node_by_id(node_id: str) -> Optional[GraphNode]:
    rows = neo4j_client.run_query(queries.GET_NODE_BY_ID, {"node_id": node_id})
    if not rows:
        return None
    return _neo4j_node_to_schema(rows[0]["n"])


def find_nodes_by_name(name: str, limit: int = 5) -> List[GraphNode]:
    """Fuzzy (substring, case-insensitive) match — used to resolve NLP
    entities like 'Rotterdam' to actual graph nodes such as 'Port of Rotterdam'."""
    rows = neo4j_client.run_query(queries.FIND_NODES_BY_NAME, {"name": name, "limit": limit})
    return [_neo4j_node_to_schema(row["n"]) for row in rows]


def propagate_risk(source_node_ids: List[str], max_hops: Optional[int] = None) -> List[AffectedNode]:
    """BASELINE (non-ML) ripple-risk propagation.

    Risk decays with hop distance according to RISK_HOP_DECAY in .env.
    This is intentionally simple so it works before the GNN (Phase 6) exists;
    it is NOT a learned model.
    """
    settings = get_settings()
    hops = max_hops or settings.risk_max_hops
    decay = settings.risk_hop_decay_list

    results: List[AffectedNode] = [
        AffectedNode(node_id=nid, name=nid, labels=[], hop_distance=0, risk_score=decay[0], is_source=True)
        for nid in source_node_ids
    ]

    if not source_node_ids:
        return results

    cypher = queries.propagate_query(hops)
    rows = neo4j_client.run_query(cypher, {"source_ids": source_node_ids})

    for row in rows:
        hop = int(row["hop_distance"])
        risk = decay[hop] if hop < len(decay) else decay[-1]
        results.append(
            AffectedNode(
                node_id=row["node_id"],
                name=row["name"] or row["node_id"],
                labels=row["labels"] or [],
                hop_distance=hop,
                risk_score=round(risk, 4),
                is_source=False,
            )
        )

    return results
