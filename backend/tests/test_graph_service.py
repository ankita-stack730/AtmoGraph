import sys
from pathlib import Path
from unittest.mock import patch

sys.path.insert(0, str(Path(__file__).resolve().parent.parent))

from app.graph import graph_service


def test_propagate_risk_with_no_sources_returns_empty():
    assert graph_service.propagate_risk([]) == []


def test_propagate_risk_source_node_has_hop_zero_and_max_risk():
    with patch("app.graph.graph_service.neo4j_client.run_query", return_value=[]):
        results = graph_service.propagate_risk(["port_rotterdam"])
    assert len(results) == 1
    assert results[0].hop_distance == 0
    assert results[0].is_source is True
    assert results[0].risk_score == 1.0


def test_propagate_risk_decays_with_hop_distance():
    fake_rows = [
        {"node_id": "warehouse_rotterdam_dc", "name": "Rotterdam DC", "labels": ["Warehouse"], "hop_distance": 1},
        {"node_id": "company_fashion_forward", "name": "Fashion Forward", "labels": ["Company"], "hop_distance": 2},
    ]
    with patch("app.graph.graph_service.neo4j_client.run_query", return_value=fake_rows):
        results = graph_service.propagate_risk(["port_rotterdam"])

    by_id = {r.node_id: r for r in results}
    assert by_id["warehouse_rotterdam_dc"].risk_score > by_id["company_fashion_forward"].risk_score
    assert by_id["warehouse_rotterdam_dc"].hop_distance == 1
    assert by_id["company_fashion_forward"].hop_distance == 2


def test_find_nodes_by_name_delegates_to_neo4j():
    fake_node = {"n": _FakeNeo4jNode(id_="port_rotterdam", name="Port of Rotterdam", labels=["Port"])}
    with patch("app.graph.graph_service.neo4j_client.run_query", return_value=[fake_node]):
        results = graph_service.find_nodes_by_name("Rotterdam")
    assert len(results) == 1
    assert results[0].node_id == "port_rotterdam"
    assert results[0].name == "Port of Rotterdam"


class _FakeNeo4jNode(dict):
    """Minimal stand-in for neo4j.graph.Node used in unit tests."""

    def __init__(self, id_: str, name: str, labels):
        super().__init__(id=id_, name=name)
        self.labels = labels
        self.element_id = id_
