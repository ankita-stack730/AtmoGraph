"""
Complete end-to-end test for the primary demo flow:

    text -> NLP -> Neo4j entity resolution -> graph risk propagation -> API response

spaCy and Neo4j are mocked so this test runs fast and without external
services, while still exercising the full request/response path required by
Section 18 ("at least one complete end-to-end test").
"""
import sys
from pathlib import Path
from unittest.mock import patch

sys.path.insert(0, str(Path(__file__).resolve().parent.parent))

from app.models.schemas import AffectedNode, ExtractedEntity, GraphNode


def test_disruption_analyze_end_to_end(client):
    fake_entities = [ExtractedEntity(text="Rotterdam", type="LOCATION", start_char=0, end_char=9)]
    fake_graph_match = [GraphNode(id="port_rotterdam", labels=["Port"], name="Port of Rotterdam", properties={})]
    fake_affected = [
        AffectedNode(node_id="port_rotterdam", name="Port of Rotterdam", labels=["Port"],
                     hop_distance=0, risk_score=1.0, is_source=True),
        AffectedNode(node_id="warehouse_rotterdam_dc", name="Rotterdam DC", labels=["Warehouse"],
                     hop_distance=1, risk_score=0.8, is_source=False),
    ]

    with patch("app.nlp.entity_extractor.extract_entities", return_value=fake_entities), \
         patch("app.graph.graph_service.find_nodes_by_name", return_value=fake_graph_match), \
         patch("app.graph.graph_service.propagate_risk", return_value=fake_affected):

        response = client.post(
            "/disruption/analyze",
            json={"text": "Rotterdam port strike causes major shipping delays."},
        )

    assert response.status_code == 200
    body = response.json()

    assert body["event"]["type"] == "PORT_STRIKE"
    assert body["event"]["severity"] > 0
    assert body["matched_source_nodes"] == ["port_rotterdam"]
    assert body["affected_nodes"] == 2
    assert body["high_risk_nodes"] == 2  # both >= 0.6 threshold
    assert body["method"] == "GRAPH_BASELINE"
    assert body["predictions"] == []  # honest: no GNN yet (Phase 6)
