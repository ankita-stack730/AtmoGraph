"""
AtmoGraph GraphSAGE inference service.

Loads the trained GraphSAGE model and performs node-level
risk prediction using the same 14-feature graph representation
used during training.
"""

from __future__ import annotations

import json
from pathlib import Path
from typing import Dict, List, Optional

import torch

from app.ml.graph_data import build_graph_data
from app.ml.graphsage_model import AtmoGraphGraphSAGE
from app.models.schemas import GraphSnapshot


class GraphSAGEInference:
    """Cached GraphSAGE model loader and inference service."""

    def __init__(
        self,
        model_path: Optional[Path] = None,
        metadata_path: Optional[Path] = None,
    ) -> None:
        backend_root = Path(__file__).resolve().parents[2]

        self.model_path = model_path or (
            backend_root / "models" / "graphsage_model.pt"
        )

        self.metadata_path = metadata_path or (
            backend_root / "models" / "graphsage_metadata.json"
        )

        self.model: Optional[AtmoGraphGraphSAGE] = None
        self.metadata: Optional[Dict] = None

    def is_available(self) -> bool:
        """Return True when both model and metadata files exist."""

        return (
            self.model_path.exists()
            and self.metadata_path.exists()
        )

    def load(self) -> AtmoGraphGraphSAGE:
        """Load the trained model once and cache it."""

        if self.model is not None:
            return self.model

        if not self.is_available():
            raise FileNotFoundError(
                "Trained GraphSAGE model not found at "
                f"{self.model_path}"
            )

        with self.metadata_path.open(
            "r",
            encoding="utf-8",
        ) as file:
            self.metadata = json.load(file)

        in_channels = int(
            self.metadata["in_channels"]
        )
        hidden_channels = int(
            self.metadata["hidden_channels"]
        )
        num_layers = int(
            self.metadata["num_layers"]
        )
        dropout = float(
            self.metadata["dropout"]
        )

        self.model = AtmoGraphGraphSAGE(
            in_channels=in_channels,
            hidden_channels=hidden_channels,
            num_layers=num_layers,
            dropout=dropout,
        )

        state_dict = torch.load(
            self.model_path,
            map_location="cpu",
        )

        self.model.load_state_dict(state_dict)
        self.model.eval()

        return self.model

    def predict(
        self,
        snapshot: GraphSnapshot,
        source_node_ids: Optional[List[str]] = None,
        baseline_risk: Optional[Dict[str, float]] = None,
        disruption_severity: float = 0.0,
    ) -> Dict[str, float]:
        """
        Predict ripple-risk scores for every node in the graph.

        The feature construction is delegated to build_graph_data()
        so inference uses the exact same feature ordering as training.
        """

        model = self.load()

        data, _, index_to_node_id = build_graph_data(
            snapshot=snapshot,
            source_node_ids=source_node_ids,
            baseline_risk=baseline_risk,
            disruption_severity=disruption_severity,
        )

        with torch.no_grad():
            risk_scores = model.predict_risk(
                data.x,
                data.edge_index,
            )

        predictions: Dict[str, float] = {}

        for index, score in enumerate(risk_scores.tolist()):
            node_id = index_to_node_id[index]
            predictions[node_id] = round(
                float(score),
                4,
            )

        return predictions


# Shared application-level inference service.
graphsage_inference = GraphSAGEInference()