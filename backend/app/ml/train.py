"""
GNN training entry point for AtmoGraph's GraphSAGE ripple-risk model.

    python -m app.ml.train
    python -m app.ml.train --epochs 200 --hidden-dim 64
    python -m app.ml.train --quick        # tiny smoke-test config, not real training

Run from backend/ with the project venv activated (Windows):

    cd E:\\AtmoGraph-Git\\backend
    .\\venv\\Scripts\\Activate.ps1
    python -m app.ml.train

Pipeline
--------
    Neo4j graph snapshot  (app.graph.graph_service.get_full_graph)
        -> deterministic synthetic disruption scenarios (app.ml.scenarios.generate_scenarios)
        -> scenario-level 70/15/15 split, seed=42 (app.ml.scenarios.split_scenarios)
        -> one PyG Data object per scenario, features from app.ml.graph_data,
           labels from app.ml.scenarios (app.ml.scenarios.build_scenario_example)
        -> AtmoGraphGraphSAGE training loop
        -> best-validation-loss checkpoint selection (with early stopping)
        -> held-out test evaluation: MAE, RMSE, R2
        -> save state_dict + metadata JSON

Loss / target framing
----------------------
The label is a continuous ripple-risk value in [0, 1] (app.ml.scenarios'
documented simulation rule), and AtmoGraphGraphSAGE.forward() returns raw
logits (pre-sigmoid), with predict_risk() applying sigmoid separately. We
train with BCEWithLogitsLoss directly against the continuous [0, 1] targets
-- BCE supports soft targets (not just hard 0/1 labels) and pairs naturally
with the model's existing sigmoid output head, so no architecture change is
needed. Evaluation metrics (MAE/RMSE/R2) are computed on predict_risk()'s
post-sigmoid output, since that's what a caller will actually consume.

Target-leakage note: features come entirely from app.ml.graph_data (node
type/degree/baseline_risk/source-indicator/severity) and never include the
label itself -- see app/ml/scenarios.py's "TARGET-LEAKAGE AVOIDANCE" section
for the full argument.

HONESTY (Section 3/40 of the project spec): the Neo4j graph here is a small
synthetic/demo supply-chain topology, and every training label comes from
app/ml/scenarios.py's documented, deterministic simulation -- not real-world
historical disruption data. The metrics printed and saved below describe
how well the model fits that synthetic simulation, not real-world
forecasting accuracy, and must never be presented as the latter.
"""
from __future__ import annotations

import argparse
import json
import logging
import random
import sys
from dataclasses import dataclass
from datetime import datetime, timezone
from pathlib import Path
from typing import List, Optional, Tuple

BACKEND_ROOT = Path(__file__).resolve().parents[2]
if str(BACKEND_ROOT) not in sys.path:
    sys.path.insert(0, str(BACKEND_ROOT))

logging.basicConfig(level="INFO", format="%(message)s")
logger = logging.getLogger("app.ml.train")

DEFAULT_MODEL_PATH = "models/graphsage_model.pt"
DEFAULT_METADATA_PATH = "models/graphsage_metadata.json"


# ---------------------------------------------------------------------------
# CLI
# ---------------------------------------------------------------------------

def parse_args(argv: Optional[List[str]] = None) -> argparse.Namespace:
    parser = argparse.ArgumentParser(description="Train the AtmoGraph GraphSAGE ripple-risk model.")
    parser.add_argument("--epochs", type=int, default=150)
    parser.add_argument("--hidden-dim", type=int, default=32)
    parser.add_argument("--num-layers", type=int, default=2)
    parser.add_argument("--dropout", type=float, default=0.2)
    parser.add_argument("--lr", type=float, default=0.01)
    parser.add_argument("--weight-decay", type=float, default=5e-4)
    parser.add_argument("--seed", type=int, default=42)
    parser.add_argument("--patience", type=int, default=25, help="Early-stopping patience on validation loss.")
    parser.add_argument("--model-path", type=str, default=DEFAULT_MODEL_PATH)
    parser.add_argument("--metadata-path", type=str, default=DEFAULT_METADATA_PATH)
    parser.add_argument(
        "--quick",
        action="store_true",
        help="Tiny config for fast smoke-testing (few epochs, small hidden dim). Not for real training.",
    )
    return parser.parse_args(argv)


def set_seeds(seed: int) -> None:
    random.seed(seed)
    try:
        import numpy as np

        np.random.seed(seed)
    except ImportError:
        pass
    import torch

    torch.manual_seed(seed)


# ---------------------------------------------------------------------------
# Data assembly
# ---------------------------------------------------------------------------

def load_graph_snapshot():
    """Fetch the live Neo4j graph. Raises RuntimeError with a clear message
    on any failure (Section 10: fail clearly, never continue silently)."""
    from app.graph import graph_service
    from app.graph.neo4j_client import neo4j_client

    try:
        neo4j_client.connect()
        snapshot = graph_service.get_full_graph()
    finally:
        neo4j_client.close()

    if not snapshot.nodes:
        raise RuntimeError(
            "Neo4j returned 0 nodes -- cannot train without a graph. "
            "Seed the demo graph first: python scripts/seed_neo4j.py"
        )
    return snapshot


@dataclass
class Datasets:
    train: List
    validation: List
    test: List
    scenario_counts: dict


def build_datasets(snapshot, seed: int) -> Datasets:
    from app.ml.scenarios import build_scenario_dataset, generate_scenarios, split_scenarios

    scenarios = generate_scenarios(snapshot, seed=seed)
    if not scenarios:
        raise RuntimeError(
            "No eligible disruption-source nodes (Port/Supplier/Manufacturer/ShippingRoute) "
            "were found in the graph -- cannot generate training scenarios."
        )

    split = split_scenarios(scenarios, seed=seed)
    if not split.train:
        raise RuntimeError("Scenario split produced an empty training set -- check the graph/scenario generator.")

    train_data = build_scenario_dataset(snapshot, split.train)
    val_data = build_scenario_dataset(snapshot, split.validation)
    test_data = build_scenario_dataset(snapshot, split.test)

    return Datasets(
        train=train_data,
        validation=val_data,
        test=test_data,
        scenario_counts={
            "total": len(scenarios),
            "train": len(split.train),
            "validation": len(split.validation),
            "test": len(split.test),
        },
    )


# ---------------------------------------------------------------------------
# Training
# ---------------------------------------------------------------------------

def run_training(datasets: Datasets, in_channels: int, args: argparse.Namespace):
    """Returns (best_state_dict, best_epoch, early_stopped, final_train_loss, best_val_loss)."""
    import torch
    from torch import nn

    from app.ml.graphsage_model import AtmoGraphGraphSAGE

    model = AtmoGraphGraphSAGE(
        in_channels=in_channels,
        hidden_channels=args.hidden_dim,
        num_layers=args.num_layers,
        dropout=args.dropout,
    )
    optimizer = torch.optim.Adam(model.parameters(), lr=args.lr, weight_decay=args.weight_decay)
    criterion = nn.BCEWithLogitsLoss()

    def run_epoch(dataset: List, train: bool) -> float:
        model.train(mode=train)
        if not dataset:
            return float("nan")
        total_loss = 0.0
        for data in dataset:
            if train:
                optimizer.zero_grad()
            logits = model(data.x, data.edge_index)
            loss = criterion(logits, data.y)
            if train:
                loss.backward()
                optimizer.step()
            total_loss += loss.item()
        return total_loss / len(dataset)

    logger.info("Training AtmoGraphGraphSAGE...")
    best_val_loss = float("inf")
    best_state = None
    best_epoch = 0
    final_train_loss = float("nan")
    epochs_without_improvement = 0
    early_stopped = False

    for epoch in range(1, args.epochs + 1):
        train_loss = run_epoch(datasets.train, train=True)
        val_loss = run_epoch(datasets.validation, train=False) if datasets.validation else train_loss
        final_train_loss = train_loss

        if epoch == 1 or epoch % max(1, args.epochs // 10) == 0 or epoch == args.epochs:
            logger.info("Epoch %d/%d — train loss: %.4f | validation loss: %.4f", epoch, args.epochs, train_loss, val_loss)

        if val_loss < best_val_loss - 1e-5:
            best_val_loss = val_loss
            best_epoch = epoch
            best_state = {k: v.clone() for k, v in model.state_dict().items()}
            epochs_without_improvement = 0
        else:
            epochs_without_improvement += 1
            if epochs_without_improvement >= args.patience:
                logger.info("Early stopping at epoch %d (no validation improvement for %d epochs).", epoch, args.patience)
                early_stopped = True
                break

    if best_state is None:
        # No validation set (or it never improved past inf) — fall back to
        # the final trained weights rather than fail.
        best_state = {k: v.clone() for k, v in model.state_dict().items()}
        best_epoch = args.epochs
        best_val_loss = final_train_loss

    model.load_state_dict(best_state)
    logger.info("Training complete.")
    return model, best_state, best_epoch, early_stopped, final_train_loss, best_val_loss


def evaluate(model, dataset: List) -> dict:
    """MAE / RMSE / R2 computed on predict_risk() (post-sigmoid) output vs
    the continuous [0,1] targets, over every node in every test scenario."""
    import numpy as np
    import torch

    if not dataset:
        return {"mae": float("nan"), "rmse": float("nan"), "r2": float("nan"), "n_predictions": 0}

    model.eval()
    all_true, all_pred = [], []
    with torch.no_grad():
        for data in dataset:
            pred = model.predict_risk(data.x, data.edge_index)
            all_true.append(data.y.numpy())
            all_pred.append(pred.numpy())

    y_true = np.concatenate(all_true).flatten()
    y_pred = np.concatenate(all_pred).flatten()

    mae = float(np.mean(np.abs(y_true - y_pred)))
    rmse = float(np.sqrt(np.mean((y_true - y_pred) ** 2)))
    ss_res = float(np.sum((y_true - y_pred) ** 2))
    ss_tot = float(np.sum((y_true - y_true.mean()) ** 2))
    r2 = float(1 - ss_res / ss_tot) if ss_tot > 1e-9 else float("nan")

    return {"mae": round(mae, 4), "rmse": round(rmse, 4), "r2": round(r2, 4), "n_predictions": int(y_true.size)}


# ---------------------------------------------------------------------------
# Save
# ---------------------------------------------------------------------------

def save_model_and_metadata(
    model,
    args: argparse.Namespace,
    in_channels: int,
    scenario_counts: dict,
    best_epoch: int,
    early_stopped: bool,
    train_loss: float,
    val_loss: float,
    test_metrics: dict,
) -> Tuple[Path, Path]:
    import torch

    model_path = BACKEND_ROOT / args.model_path
    metadata_path = BACKEND_ROOT / args.metadata_path
    model_path.parent.mkdir(parents=True, exist_ok=True)
    metadata_path.parent.mkdir(parents=True, exist_ok=True)

    # Save the raw state_dict (per spec item 8/11: "inference using the
    # saved state_dict") — architecture parameters needed to reconstruct
    # the model live in metadata.json alongside it.
    torch.save(model.state_dict(), model_path)

    try:
        import torch_geometric

        pyg_version = torch_geometric.__version__
    except Exception:  # noqa: BLE001
        pyg_version = "unknown"

    metadata = {
        "model_architecture": "AtmoGraphGraphSAGE",
        "in_channels": in_channels,
        "hidden_channels": args.hidden_dim,
        "num_layers": args.num_layers,
        "dropout": args.dropout,
        "seed": args.seed,
        "loss_function": "BCEWithLogitsLoss",
        "optimizer": "Adam",
        "learning_rate": args.lr,
        "weight_decay": args.weight_decay,
        "epochs_configured": args.epochs,
        "best_epoch": best_epoch,
        "early_stopped": early_stopped,
        "scenario_counts": scenario_counts,
        "train_val_test_split": [0.70, 0.15, 0.15],
        "metrics": {
            "train_loss": round(train_loss, 4) if train_loss == train_loss else None,
            "validation_loss": round(val_loss, 4) if val_loss == val_loss else None,
            "test": test_metrics,
        },
        "trained_at": datetime.now(timezone.utc).isoformat(),
        "torch_version": torch.__version__,
        "torch_geometric_version": pyg_version,
        "synthetic_training_data": True,
        "disclaimer": (
            "Trained on synthetic disruption scenarios generated from the demo AtmoGraph "
            "supply-chain topology (see app/ml/scenarios.py). Not real-world historical data; "
            "metrics reflect fit to the synthetic simulation, not production forecasting accuracy."
        ),
    }
    with open(metadata_path, "w", encoding="utf-8") as f:
        json.dump(metadata, f, indent=2)

    return model_path, metadata_path


# ---------------------------------------------------------------------------
# Entry point
# ---------------------------------------------------------------------------

def main(argv: Optional[List[str]] = None) -> int:
    args = parse_args(argv)
    if args.quick:
        args.epochs = min(args.epochs, 5)
        args.hidden_dim = min(args.hidden_dim, 8)
        args.patience = min(args.patience, 3)

    try:
        import numpy  # noqa: F401
        import torch  # noqa: F401
        import torch_geometric  # noqa: F401
    except ImportError as exc:
        logger.error(
            "Missing ML dependency (%s). Install requirements first:\n"
            "    pip install -r requirements.txt",
            exc,
        )
        return 1

    set_seeds(args.seed)

    try:
        logger.info("Loading graph from Neo4j...")
        snapshot = load_graph_snapshot()
        logger.info("Loaded graph: %d nodes, %d relationships", len(snapshot.nodes), len(snapshot.relationships))

        logger.info("Generating deterministic synthetic scenarios (seed=%d)...", args.seed)
        datasets = build_datasets(snapshot, seed=args.seed)
        counts = datasets.scenario_counts
        logger.info(
            "Scenarios: total=%d -> train=%d validation=%d test=%d",
            counts["total"], counts["train"], counts["validation"], counts["test"],
        )
    except RuntimeError as exc:
        logger.error("Cannot proceed: %s", exc)
        return 1

    in_channels = datasets.train[0].x.shape[1]
    logger.info("Input feature dimension: %d", in_channels)

    model, _state, best_epoch, early_stopped, train_loss, val_loss = run_training(datasets, in_channels, args)

    logger.info("")
    logger.info("Best epoch: %d%s", best_epoch, " (early stopped)" if early_stopped else "")
    logger.info("Best validation loss: %.4f", val_loss)

    test_metrics = evaluate(model, datasets.test)
    logger.info("")
    logger.info("Test MAE:  %s", test_metrics["mae"])
    logger.info("Test RMSE: %s", test_metrics["rmse"])
    logger.info("Test R2:   %s", test_metrics["r2"])
    logger.info("Test predictions evaluated: %d (across %d test scenarios)", test_metrics["n_predictions"], counts["test"])

    model_path, metadata_path = save_model_and_metadata(
        model, args, in_channels, counts, best_epoch, early_stopped, train_loss, val_loss, test_metrics,
    )

    logger.info("")
    logger.info("Model saved to:    %s", model_path)
    logger.info("Metadata saved to: %s", metadata_path)
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
