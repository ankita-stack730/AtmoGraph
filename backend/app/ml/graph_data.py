"""
AtmoGraph graph-to-PyTorch-Geometric conversion.

Converts the existing Neo4j-backed GraphSnapshot into a PyG Data object
without modifying the Neo4j database or existing graph service.

Node features:
    - one-hot node type
    - normalized total degree
    - normalized in-degree
    - normalized out-degree
    - baseline risk
    - source-node indicator
    - disruption severity

The converter keeps a stable mapping between AtmoGraph node_id values
and PyG integer node indices.
"""

from __future__ import annotations

from typing import Dict, List, Optional, Tuple

import torch
from torch_geometric.data import Data

from app.models.schemas import GraphSnapshot


NODE_TYPES = [
    "Supplier",
    "Manufacturer",
    "Warehouse",
    "Port",
    "ShippingRoute",
    "Product",
    "Company",
    "Country",
]


def _node_type(node_labels: List[str]) -> str:
    """Return the first supported AtmoGraph node type."""

    for node_type in NODE_TYPES:
        if node_type in node_labels:
            return node_type

    return "Unknown"


def _normalize(value: float, maximum: float) -> float:
    """Normalize a value to [0, 1]."""

    if maximum <= 0:
        return 0.0

    return float(value) / float(maximum)


def build_graph_data(
    snapshot: GraphSnapshot,
    source_node_ids: Optional[List[str]] = None,
    baseline_risk: Optional[Dict[str, float]] = None,
    disruption_severity: float = 0.0,
) -> Tuple[Data, Dict[str, int], Dict[int, str]]:
    """
    Convert an AtmoGraph GraphSnapshot into a PyTorch Geometric Data object.

    Args:
        snapshot:
            Existing graph returned by graph_service.get_full_graph().

        source_node_ids:
            Node IDs directly affected by the disruption.

        baseline_risk:
            Optional mapping of node_id -> baseline risk score.

        disruption_severity:
            Disruption severity in the range [0, 1].

    Returns:
        data:
            PyTorch Geometric Data object.

        node_id_to_index:
            Mapping from AtmoGraph node_id -> PyG integer index.

        index_to_node_id:
            Reverse mapping from PyG integer index -> AtmoGraph node_id.
    """

    source_node_ids = set(source_node_ids or [])
    baseline_risk = baseline_risk or {}

    nodes = snapshot.nodes

    if not nodes:
        raise ValueError("Cannot build PyG graph from an empty graph.")

    # ------------------------------------------------------------------
    # Stable node mapping
    # ------------------------------------------------------------------

    node_id_to_index: Dict[str, int] = {
        node.node_id: index
        for index, node in enumerate(nodes)
    }

    index_to_node_id: Dict[int, str] = {
        index: node_id
        for node_id, index in node_id_to_index.items()
    }

    # ------------------------------------------------------------------
    # Calculate graph degrees
    # ------------------------------------------------------------------

    in_degree = {node.node_id: 0 for node in nodes}
    out_degree = {node.node_id: 0 for node in nodes}

    valid_edges: List[Tuple[int, int]] = []

    for relationship in snapshot.relationships:
        source = relationship.source
        target = relationship.target

        if source not in node_id_to_index:
            continue

        if target not in node_id_to_index:
            continue

        source_index = node_id_to_index[source]
        target_index = node_id_to_index[target]

        valid_edges.append((source_index, target_index))

        out_degree[source] += 1
        in_degree[target] += 1

    total_degree = {
        node_id: in_degree[node_id] + out_degree[node_id]
        for node_id in node_id_to_index
    }

    max_total_degree = max(total_degree.values(), default=0)
    max_in_degree = max(in_degree.values(), default=0)
    max_out_degree = max(out_degree.values(), default=0)

    # ------------------------------------------------------------------
    # Build node feature matrix
    # ------------------------------------------------------------------

    features: List[List[float]] = []

    severity = max(0.0, min(float(disruption_severity), 1.0))

    for node in nodes:
        node_id = node.node_id
        node_type = _node_type(node.labels)

        # One-hot node type
        type_features = [
            1.0 if node_type == supported_type else 0.0
            for supported_type in NODE_TYPES
        ]

        degree_features = [
            _normalize(total_degree[node_id], max_total_degree),
            _normalize(in_degree[node_id], max_in_degree),
            _normalize(out_degree[node_id], max_out_degree),
        ]

        risk = float(baseline_risk.get(node_id, 0.0))
        risk = max(0.0, min(risk, 1.0))

        source_indicator = (
            1.0 if node_id in source_node_ids else 0.0
        )

        features.append(
            type_features
            + degree_features
            + [
                risk,
                source_indicator,
                severity,
            ]
        )

    x = torch.tensor(features, dtype=torch.float32)

    # ------------------------------------------------------------------
    # Build edge_index
    # ------------------------------------------------------------------

    if valid_edges:
        edge_index = torch.tensor(
            valid_edges,
            dtype=torch.long,
        ).t().contiguous()
    else:
        edge_index = torch.empty(
            (2, 0),
            dtype=torch.long,
        )

    data = Data(
        x=x,
        edge_index=edge_index,
    )

    # Useful metadata for downstream training/inference.
    data.node_ids = list(node_id_to_index.keys())

    return data, node_id_to_index, index_to_node_id