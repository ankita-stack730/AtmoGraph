"""
Tests for app/ml/train.py.

Fully offline: builds an in-memory GraphSnapshot directly (via the real
Pydantic schemas) and calls build_datasets()/run_training()/evaluate()
straight -- load_graph_snapshot() (the only function that touches Neo4j) is
never exercised here.

Skips cleanly via pytest.importorskip if torch/torch_geometric are not
installed, so `pytest` still passes on a fresh checkout before
`pip install -r requirements.txt`.
"""
import json
import sys
from pathlib import Path

import pytest

sys.path.insert(0, str(Path(__file__).resolve().parent.parent))

torch = pytest.importorskip("torch")
pytest.importorskip("torch_geometric")

from app.models.schemas import GraphNode, GraphRelationship, GraphSnapshot  # noqa: E402
from app.ml import train as train_module  # noqa: E402


def _demo_snapshot() -> GraphSnapshot:
    """A slightly bigger graph than the tiny scenarios.py fixtures, so
    train/val/test all end up non-empty at the default 70/15/15 split."""
    nodes = [
        GraphNode(node_id="port_a", labels=["Port"], name="Port A", properties={}),
        GraphNode(node_id="port_b", labels=["Port"], name="Port B", properties={}),
        GraphNode(node_id="route_ab", labels=["ShippingRoute"], name="Route AB", properties={}),
        GraphNode(node_id="route_cd", labels=["ShippingRoute"], name="Route CD", properties={}),
        GraphNode(node_id="wh_a", labels=["Warehouse"], name="Warehouse A", properties={}),
        GraphNode(node_id="wh_b", labels=["Warehouse"], name="Warehouse B", properties={}),
        GraphNode(node_id="sup_a", labels=["Supplier"], name="Supplier A", properties={}),
        GraphNode(node_id="sup_b", labels=["Supplier"], name="Supplier B", properties={}),
        GraphNode(node_id="mfg_a", labels=["Manufacturer"], name="Manufacturer A", properties={}),
        GraphNode(node_id="mfg_b", labels=["Manufacturer"], name="Manufacturer B", properties={}),
        GraphNode(node_id="prod_a", labels=["Product"], name="Product A", properties={}),
        GraphNode(node_id="co_a", labels=["Company"], name="Company A", properties={}),
        GraphNode(node_id="ctry_a", labels=["Country"], name="Country A", properties={}),
    ]
    rels = [
        GraphRelationship(source="port_a", target="route_ab", type="SHIPS_THROUGH", properties={}),
        GraphRelationship(source="route_ab", target="port_b", type="SHIPS_THROUGH", properties={}),
        GraphRelationship(source="port_a", target="wh_a", type="CONNECTED_TO", properties={}),
        GraphRelationship(source="port_b", target="wh_b", type="CONNECTED_TO", properties={}),
        GraphRelationship(source="route_cd", target="port_b", type="SHIPS_THROUGH", properties={}),
        GraphRelationship(source="sup_a", target="mfg_a", type="SUPPLIES_TO", properties={}),
        GraphRelationship(source="sup_b", target="mfg_b", type="SUPPLIES_TO", properties={}),
        GraphRelationship(source="mfg_a", target="prod_a", type="MANUFACTURES", properties={}),
        GraphRelationship(source="prod_a", target="co_a", type="DEPENDS_ON", properties={}),
        GraphRelationship(source="mfg_a", target="wh_a", type="DEPENDS_ON", properties={}),
        GraphRelationship(source="port_a", target="ctry_a", type="LOCATED_IN", properties={}),
    ]
    return GraphSnapshot(nodes=nodes, relationships=rels)


def _quick_args(**overrides):
    args = train_module.parse_args(["--quick"])
    for key, value in overrides.items():
        setattr(args, key, value)
    return args


# ---------------------------------------------------------------------------
# Dataset assembly / split wiring
# ---------------------------------------------------------------------------

def test_build_datasets_produces_nonempty_disjoint_splits():
    snapshot = _demo_snapshot()
    datasets = train_module.build_datasets(snapshot, seed=42)

    assert datasets.scenario_counts["train"] > 0
    assert datasets.scenario_counts["validation"] > 0
    assert datasets.scenario_counts["test"] > 0
    total = datasets.scenario_counts["train"] + datasets.scenario_counts["validation"] + datasets.scenario_counts["test"]
    assert total == datasets.scenario_counts["total"]

    train_ids = {d.scenario_id for d in datasets.train}
    val_ids = {d.scenario_id for d in datasets.validation}
    test_ids = {d.scenario_id for d in datasets.test}
    assert train_ids.isdisjoint(val_ids)
    assert train_ids.isdisjoint(test_ids)
    assert val_ids.isdisjoint(test_ids)


def test_build_datasets_raises_clearly_when_graph_has_no_eligible_sources():
    empty_ish = GraphSnapshot(
        nodes=[GraphNode(node_id="prod_only", labels=["Product"], name="P", properties={})],
        relationships=[],
    )
    with pytest.raises(RuntimeError, match="eligible disruption-source"):
        train_module.build_datasets(empty_ish, seed=42)


def test_load_graph_snapshot_rejects_empty_graph(monkeypatch):
    import app.graph.graph_service as gs
    import app.graph.neo4j_client as nc

    monkeypatch.setattr(gs, "get_full_graph", lambda: GraphSnapshot(nodes=[], relationships=[]))
    monkeypatch.setattr(nc.neo4j_client, "connect", lambda: None)
    monkeypatch.setattr(nc.neo4j_client, "close", lambda: None)

    with pytest.raises(RuntimeError, match="0 nodes"):
        train_module.load_graph_snapshot()


# ---------------------------------------------------------------------------
# Training output shape / behaviour
# ---------------------------------------------------------------------------

def test_training_output_shapes_and_finite_range():
    snapshot = _demo_snapshot()
    datasets = train_module.build_datasets(snapshot, seed=42)
    in_channels = datasets.train[0].x.shape[1]
    assert in_channels == 14  # app/ml/graph_data.py's declared feature width

    args = _quick_args()
    model, _state, best_epoch, _early, train_loss, val_loss = train_module.run_training(datasets, in_channels, args)

    assert best_epoch >= 1
    assert train_loss == train_loss  # not NaN
    assert val_loss == val_loss

    sample = datasets.train[0]
    model.eval()
    with torch.no_grad():
        risk = model.predict_risk(sample.x, sample.edge_index)
    assert risk.shape == (sample.x.shape[0],)
    assert torch.isfinite(risk).all()
    assert bool((risk >= 0).all()) and bool((risk <= 1).all())


def test_evaluate_returns_finite_metrics_in_range():
    snapshot = _demo_snapshot()
    datasets = train_module.build_datasets(snapshot, seed=42)
    in_channels = datasets.train[0].x.shape[1]
    args = _quick_args()
    model, *_ = train_module.run_training(datasets, in_channels, args)

    metrics = train_module.evaluate(model, datasets.test)
    assert metrics["n_predictions"] > 0
    assert metrics["mae"] == metrics["mae"]  # not NaN
    assert metrics["rmse"] >= 0
    assert metrics["mae"] >= 0


def test_evaluate_handles_empty_dataset_without_crashing():
    metrics = train_module.evaluate(model=None, dataset=[])
    assert metrics["n_predictions"] == 0
    assert metrics["mae"] != metrics["mae"]  # NaN by design when there's nothing to evaluate


# ---------------------------------------------------------------------------
# Reproducibility
# ---------------------------------------------------------------------------

def test_training_is_reproducible_for_the_same_seed():
    snapshot = _demo_snapshot()

    def run_once():
        train_module.set_seeds(42)
        datasets = train_module.build_datasets(snapshot, seed=42)
        in_channels = datasets.train[0].x.shape[1]
        args = _quick_args(epochs=5, hidden_dim=8)
        model, _state, best_epoch, _early, train_loss, val_loss = train_module.run_training(datasets, in_channels, args)
        return best_epoch, round(train_loss, 6), round(val_loss, 6)

    result_a = run_once()
    result_b = run_once()
    assert result_a == result_b


def test_scenario_generation_within_build_datasets_is_deterministic():
    snapshot = _demo_snapshot()
    a = train_module.build_datasets(snapshot, seed=42)
    b = train_module.build_datasets(snapshot, seed=42)
    assert [d.scenario_id for d in a.train] == [d.scenario_id for d in b.train]
    assert [d.scenario_id for d in a.test] == [d.scenario_id for d in b.test]


# ---------------------------------------------------------------------------
# Target-leakage guard (end-to-end through the real graph_data feature builder)
# ---------------------------------------------------------------------------

def test_no_target_leakage_between_features_and_labels():
    """The baseline_risk feature column (index 11: 8 one-hot + 3 degree
    features) must not equal the label it's paired with -- if it did, the
    model could read its answer straight off an input feature."""
    snapshot = _demo_snapshot()
    datasets = train_module.build_datasets(snapshot, seed=42)

    baseline_risk_column_index = 11  # 8 (node type) + 3 (degree/in/out)
    mismatches = 0
    total = 0
    for data in datasets.train:
        baseline_col = data.x[:, baseline_risk_column_index]
        for i in range(data.y.shape[0]):
            total += 1
            if abs(float(baseline_col[i]) - float(data.y[i])) > 1e-6:
                mismatches += 1

    # Virtually all non-source nodes should differ from their baseline_risk
    # feature (labels depend on disruption-type susceptibility + degree hub
    # bonus; baseline_risk depends on hop distance alone).
    assert mismatches / total > 0.8


def test_feature_dimension_has_no_extra_leaked_column():
    """The model's declared input width must exactly match graph_data's
    documented feature count -- not one column wider (which would suggest
    an accidental label column got appended)."""
    snapshot = _demo_snapshot()
    datasets = train_module.build_datasets(snapshot, seed=42)
    assert datasets.train[0].x.shape[1] == 14


# ---------------------------------------------------------------------------
# Save / metadata / state_dict reload
# ---------------------------------------------------------------------------

def test_save_model_and_metadata_writes_loadable_files(tmp_path):
    from app.ml.graphsage_model import AtmoGraphGraphSAGE

    snapshot = _demo_snapshot()
    datasets = train_module.build_datasets(snapshot, seed=42)
    in_channels = datasets.train[0].x.shape[1]
    args = _quick_args(
        model_path=str(tmp_path / "sub" / "model.pt"),
        metadata_path=str(tmp_path / "sub" / "metadata.json"),
    )
    model, _state, best_epoch, early_stopped, train_loss, val_loss = train_module.run_training(datasets, in_channels, args)
    test_metrics = train_module.evaluate(model, datasets.test)

    # save_model_and_metadata resolves paths as BACKEND_ROOT / args.*_path;
    # point it at an absolute tmp_path by monkeypatching BACKEND_ROOT-relative
    # join via an absolute path (Path(abs) / anything discards the base).
    model_path, metadata_path = train_module.save_model_and_metadata(
        model, args, in_channels, datasets.scenario_counts, best_epoch, early_stopped, train_loss, val_loss, test_metrics,
    )

    assert model_path.exists()
    assert metadata_path.exists()

    metadata = json.loads(metadata_path.read_text())
    assert metadata["model_architecture"] == "AtmoGraphGraphSAGE"
    assert metadata["in_channels"] == 14
    assert metadata["hidden_channels"] == args.hidden_dim
    assert metadata["num_layers"] == args.num_layers
    assert metadata["seed"] == 42
    assert metadata["scenario_counts"] == datasets.scenario_counts
    assert metadata["train_val_test_split"] == [0.70, 0.15, 0.15]
    assert metadata["synthetic_training_data"] is True
    assert "disclaimer" in metadata and "synthetic" in metadata["disclaimer"].lower()
    assert set(metadata["metrics"]["test"]) == {"mae", "rmse", "r2", "n_predictions"}
    # metadata metrics must be the ACTUAL computed values, not placeholders
    assert metadata["metrics"]["test"]["mae"] == test_metrics["mae"]

    # Reconstruct the architecture from metadata and load the saved
    # state_dict -- this is the literal "inference using the saved
    # state_dict" requirement.
    reloaded = AtmoGraphGraphSAGE(
        in_channels=metadata["in_channels"],
        hidden_channels=metadata["hidden_channels"],
        num_layers=metadata["num_layers"],
        dropout=metadata["dropout"],
    )
    state_dict = torch.load(model_path, map_location="cpu", weights_only=True)
    reloaded.load_state_dict(state_dict)
    reloaded.eval()

    sample = datasets.test[0] if datasets.test else datasets.train[0]
    with torch.no_grad():
        original_out = model.predict_risk(sample.x, sample.edge_index)
        reloaded_out = reloaded.predict_risk(sample.x, sample.edge_index)
    assert torch.allclose(original_out, reloaded_out)
    assert torch.isfinite(reloaded_out).all()
    assert bool((reloaded_out >= 0).all()) and bool((reloaded_out <= 1).all())
