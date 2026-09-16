"""
Synthetic disruption scenario + node-level label generation for AtmoGraph's
GraphSAGE training pipeline.

============================================================================
HONESTY NOTICE (read before presenting any metric from this pipeline)
============================================================================
The AtmoGraph Neo4j graph is a small SYNTHETIC/DEMO supply-chain topology.
This project contains no real-world historical disruption dataset.

Every scenario and every label produced by this module is therefore a
CONTROLLED, DOCUMENTED SIMULATION over that synthetic topology -- not an
observed real-world outcome. A model trained on this data demonstrates the
GraphSAGE architecture and the end-to-end
    NLP -> Neo4j -> PyG -> GraphSAGE -> FastAPI -> React
pipeline. It is NOT a production forecasting model, and any metric computed
against these labels describes only how well the model fits this simulation.
============================================================================

LABEL RULE (deterministic, documented -- this is the single source of truth)
---------------------------------------------------------------------------
For a scenario (source_node_ids, disruption_type, severity) and node N:

    if N is a source node:
        label = clamp(0.90 + 0.10 * severity)

    elif N is unreachable from every source (different component):
        label = 0.02 * severity
        # deliberately small-but-nonzero so the model does not simply learn
        # "unreachable => exactly 0"

    else:
        decay       = HOP_DECAY_BASE ** hop_distance(N, nearest source)
        suscept     = TYPE_SUSCEPTIBILITY[disruption_type][node_type(N)]
        hub_bonus   = HUB_BONUS_WEIGHT * (degree(N) / max_degree(graph))
        label       = clamp(severity * decay * suscept + hub_bonus)

All labels are in [0, 1].

TARGET-LEAKAGE AVOIDANCE
---------------------------------------------------------------------------
app/ml/graph_data.py's 14-dim feature vector includes a `baseline_risk`
feature. That feature MUST NOT be fed the label. `baseline_risk_context()`
below fills it with the existing GRAPH_BASELINE hop-decay value -- a
function of hop distance ALONE (exactly what the deployed baseline engine
already reports, and what a human analyst would already see on the
Predictions page).

The label, by contrast, additionally depends on disruption_type x node_type
susceptibility and on node degree. So the label is NOT recoverable from any
single input feature: the model must actually learn the interaction between
node type, disruption type, topology position and severity. Hop distance and
baseline risk are graph-derived *context*, not the answer.

Neo4j is never written to by this module -- it only reads a GraphSnapshot.
"""

from __future__ import annotations

import random
from dataclasses import dataclass, field
from typing import TYPE_CHECKING, Dict, Iterable, List, Sequence, Set, Tuple

if TYPE_CHECKING:  # pragma: no cover - typing only, avoids a runtime pydantic import
    from app.models.schemas import GraphSnapshot


# ---------------------------------------------------------------------------
# Constants
# ---------------------------------------------------------------------------

SEED = 42

#: Hop-distance decay base used by the LABEL rule (distinct from the
#: GRAPH_BASELINE decay table in .env, which feeds the *feature*).
HOP_DECAY_BASE = 0.62

#: Weight of the "well-connected nodes suffer a bit more" term.
HUB_BONUS_WEIGHT = 0.05

#: Node types that can plausibly originate a supply-chain disruption.
ELIGIBLE_SOURCE_TYPES: Tuple[str, ...] = (
    "Port",
    "Supplier",
    "Manufacturer",
    "ShippingRoute",
)

#: Kept in sync with app/nlp/disruption_detector.py's DISRUPTION_KEYWORDS keys.
DISRUPTION_TYPES: Tuple[str, ...] = (
    "PORT_STRIKE",
    "CYBER_ATTACK",
    "WAR_CONFLICT",
    "NATURAL_DISASTER",
    "FACTORY_SHUTDOWN",
    "SUPPLIER_FAILURE",
    "SHIPPING_DELAY",
    "TRANSPORT_DISRUPTION",
)

#: Severity levels sampled per scenario.
SEVERITY_LEVELS: Tuple[float, ...] = (0.4, 0.55, 0.7, 0.85, 0.95)

#: Node types recognised by app/ml/graph_data.py (must stay consistent).
NODE_TYPES: Tuple[str, ...] = (
    "Supplier",
    "Manufacturer",
    "Warehouse",
    "Port",
    "ShippingRoute",
    "Product",
    "Company",
    "Country",
)

DEFAULT_SUSCEPTIBILITY = 0.45

#: How hard each disruption type hits each node type, 0-1.
#: HAND-AUTHORED DOMAIN SCAFFOLDING for the simulation -- not fitted to data.
TYPE_SUSCEPTIBILITY: Dict[str, Dict[str, float]] = {
    "PORT_STRIKE": {
        "Port": 1.00, "ShippingRoute": 0.90, "Warehouse": 0.70, "Manufacturer": 0.55,
        "Supplier": 0.50, "Country": 0.45, "Product": 0.40, "Company": 0.35,
    },
    "CYBER_ATTACK": {
        "Company": 0.85, "Manufacturer": 0.70, "Supplier": 0.60, "Warehouse": 0.55,
        "Port": 0.50, "ShippingRoute": 0.45, "Product": 0.40, "Country": 0.30,
    },
    "WAR_CONFLICT": {
        "Country": 0.90, "Port": 0.80, "ShippingRoute": 0.75, "Manufacturer": 0.60,
        "Supplier": 0.55, "Warehouse": 0.50, "Company": 0.45, "Product": 0.40,
    },
    "NATURAL_DISASTER": {
        "Port": 0.80, "Manufacturer": 0.75, "Warehouse": 0.75, "Supplier": 0.65,
        "Country": 0.60, "ShippingRoute": 0.60, "Product": 0.45, "Company": 0.40,
    },
    "FACTORY_SHUTDOWN": {
        "Manufacturer": 1.00, "Product": 0.80, "Company": 0.55, "Supplier": 0.55,
        "Warehouse": 0.50, "Country": 0.35, "Port": 0.25, "ShippingRoute": 0.20,
    },
    "SUPPLIER_FAILURE": {
        "Supplier": 1.00, "Manufacturer": 0.85, "Product": 0.60, "Company": 0.50,
        "Warehouse": 0.35, "Country": 0.30, "Port": 0.30, "ShippingRoute": 0.25,
    },
    "SHIPPING_DELAY": {
        "ShippingRoute": 1.00, "Port": 0.85, "Warehouse": 0.65, "Manufacturer": 0.50,
        "Supplier": 0.45, "Product": 0.40, "Country": 0.35, "Company": 0.30,
    },
    "TRANSPORT_DISRUPTION": {
        "ShippingRoute": 0.95, "Port": 0.75, "Warehouse": 0.60, "Manufacturer": 0.45,
        "Supplier": 0.40, "Product": 0.35, "Country": 0.30, "Company": 0.30,
    },
}

#: Fallback GRAPH_BASELINE decay table, mirroring the default
#: RISK_HOP_DECAY in .env. Used for the `baseline_risk` FEATURE only.
DEFAULT_BASELINE_DECAY: Tuple[float, ...] = (1.0, 0.8, 0.6, 0.4, 0.25, 0.15)


# ---------------------------------------------------------------------------
# Scenario definition
# ---------------------------------------------------------------------------

@dataclass(frozen=True)
class Scenario:
    """One synthetic disruption scenario.

    `source_node_ids` is always sorted so that a scenario's identity (and
    therefore the train/val/test split) is order-independent.
    """

    scenario_id: str
    source_node_ids: Tuple[str, ...]
    disruption_type: str
    severity: float

    def as_dict(self) -> dict:
        return {
            "scenario_id": self.scenario_id,
            "source_node_ids": list(self.source_node_ids),
            "disruption_type": self.disruption_type,
            "severity": self.severity,
        }


@dataclass
class ScenarioSplit:
    """Scenario-level (never node-level) dataset split."""

    train: List[Scenario] = field(default_factory=list)
    validation: List[Scenario] = field(default_factory=list)
    test: List[Scenario] = field(default_factory=list)

    @property
    def sizes(self) -> Dict[str, int]:
        return {
            "train": len(self.train),
            "validation": len(self.validation),
            "test": len(self.test),
        }

    def all_scenarios(self) -> List[Scenario]:
        return [*self.train, *self.validation, *self.test]


# ---------------------------------------------------------------------------
# Graph helpers (pure python -- no torch, no Neo4j writes)
# ---------------------------------------------------------------------------

def node_type_of(labels: Sequence[str]) -> str:
    """First recognised AtmoGraph node type, matching graph_data._node_type."""
    for node_type in NODE_TYPES:
        if node_type in labels:
            return node_type
    return "Unknown"


def build_adjacency(snapshot: "GraphSnapshot") -> Dict[str, Set[str]]:
    """Undirected adjacency map.

    Ripple effects travel both downstream (a struck port delays the
    warehouses it feeds) and upstream (a dead factory strands its
    suppliers), and the deployed GRAPH_BASELINE Cypher already traverses
    undirected (`-[*1..n]-`). Neo4j's stored relationship directions are
    left completely untouched -- this is a read-only in-memory view.
    """
    adjacency: Dict[str, Set[str]] = {node.node_id: set() for node in snapshot.nodes}

    for relationship in snapshot.relationships:
        source = relationship.source
        target = relationship.target
        if source not in adjacency or target not in adjacency:
            continue  # skip dangling refs rather than crash on a partial snapshot
        adjacency[source].add(target)
        adjacency[target].add(source)

    return adjacency


def bfs_hop_distances(
    adjacency: Dict[str, Set[str]],
    source_node_ids: Iterable[str],
) -> Dict[str, int]:
    """Shortest hop distance from ANY source to every reachable node.

    Nodes in a different connected component are simply absent from the
    result (callers treat "absent" as unreachable).
    """
    distances: Dict[str, int] = {}
    frontier: List[str] = []

    for node_id in source_node_ids:
        if node_id in adjacency and node_id not in distances:
            distances[node_id] = 0
            frontier.append(node_id)

    while frontier:
        next_frontier: List[str] = []
        for node_id in frontier:
            for neighbour in adjacency[node_id]:
                if neighbour not in distances:
                    distances[neighbour] = distances[node_id] + 1
                    next_frontier.append(neighbour)
        frontier = next_frontier

    return distances


def degree_map(adjacency: Dict[str, Set[str]]) -> Dict[str, int]:
    return {node_id: len(neighbours) for node_id, neighbours in adjacency.items()}


def _clamp01(value: float) -> float:
    return max(0.0, min(1.0, value))


def susceptibility(disruption_type: str, node_type: str) -> float:
    return TYPE_SUSCEPTIBILITY.get(disruption_type, {}).get(node_type, DEFAULT_SUSCEPTIBILITY)


# ---------------------------------------------------------------------------
# Scenario generation
# ---------------------------------------------------------------------------

def eligible_source_nodes(snapshot: "GraphSnapshot") -> List[str]:
    """Candidate disruption origins, sorted by node_id for determinism.

    Sorting (rather than relying on Neo4j row order) is what makes scenario
    generation reproducible across database restarts and re-seeds.
    """
    return sorted(
        node.node_id
        for node in snapshot.nodes
        if node_type_of(node.labels) in ELIGIBLE_SOURCE_TYPES
    )


def generate_scenarios(
    snapshot: "GraphSnapshot",
    seed: int = SEED,
    scenarios_per_source: int = 3,
    multi_source_scenarios: int = 8,
) -> List[Scenario]:
    """Deterministically generate synthetic disruption scenarios.

    Same snapshot + same seed => byte-identical scenario list, every time.

    Single-source scenarios mirror the real demo flow ("Rotterdam port
    strike ..."); a handful of multi-source scenarios are added so the model
    also sees simultaneous disruptions.
    """
    if scenarios_per_source < 1:
        raise ValueError("scenarios_per_source must be >= 1")

    sources = eligible_source_nodes(snapshot)
    if not sources:
        return []

    rng = random.Random(seed)
    scenarios: List[Scenario] = []

    for node_id in sources:
        for index in range(scenarios_per_source):
            disruption_type = rng.choice(DISRUPTION_TYPES)
            severity = rng.choice(SEVERITY_LEVELS)
            scenarios.append(
                Scenario(
                    scenario_id=f"single__{node_id}__{disruption_type}__{index}",
                    source_node_ids=(node_id,),
                    disruption_type=disruption_type,
                    severity=severity,
                )
            )

    if len(sources) >= 2 and multi_source_scenarios > 0:
        for index in range(min(multi_source_scenarios, len(sources))):
            first = sources[index]
            second = sources[(index + 1) % len(sources)]
            if first == second:
                continue
            pair = tuple(sorted({first, second}))
            disruption_type = rng.choice(DISRUPTION_TYPES)
            severity = rng.choice(SEVERITY_LEVELS)
            scenarios.append(
                Scenario(
                    scenario_id=f"multi__{'_'.join(pair)}__{disruption_type}__{index}",
                    source_node_ids=pair,
                    disruption_type=disruption_type,
                    severity=severity,
                )
            )

    return scenarios


# ---------------------------------------------------------------------------
# Label generation (the documented simulation rule)
# ---------------------------------------------------------------------------

def compute_scenario_labels(
    snapshot: "GraphSnapshot",
    scenario: Scenario,
    adjacency: Dict[str, Set[str]] | None = None,
) -> Dict[str, float]:
    """Node-level ripple-risk labels in [0, 1] for one scenario.

    Implements exactly the LABEL RULE in this module's docstring. This is
    the ONLY place training targets are produced.
    """
    if adjacency is None:
        adjacency = build_adjacency(snapshot)

    hop_distances = bfs_hop_distances(adjacency, scenario.source_node_ids)
    degrees = degree_map(adjacency)
    max_degree = max(degrees.values(), default=0)
    sources = set(scenario.source_node_ids)
    severity = _clamp01(scenario.severity)

    labels: Dict[str, float] = {}

    for node in snapshot.nodes:
        node_id = node.node_id

        if node_id in sources:
            labels[node_id] = round(_clamp01(0.90 + 0.10 * severity), 6)
            continue

        if node_id not in hop_distances:
            labels[node_id] = round(_clamp01(0.02 * severity), 6)
            continue

        hop = hop_distances[node_id]
        decay = HOP_DECAY_BASE ** hop
        suscept = susceptibility(scenario.disruption_type, node_type_of(node.labels))
        hub_bonus = HUB_BONUS_WEIGHT * (degrees[node_id] / max_degree if max_degree else 0.0)

        labels[node_id] = round(_clamp01(severity * decay * suscept + hub_bonus), 6)

    return labels


def baseline_risk_context(
    snapshot: "GraphSnapshot",
    scenario: Scenario,
    adjacency: Dict[str, Set[str]] | None = None,
    decay_table: Sequence[float] | None = None,
) -> Dict[str, float]:
    """`baseline_risk` values for the FEATURE vector -- never the label.

    Reproduces the deployed GRAPH_BASELINE hop-decay risk, which depends on
    hop distance alone. See this module's TARGET-LEAKAGE AVOIDANCE section
    for why feeding this (and not the label) keeps the task learnable rather
    than trivial.
    """
    if adjacency is None:
        adjacency = build_adjacency(snapshot)
    if decay_table is None:
        decay_table = _load_baseline_decay()

    hop_distances = bfs_hop_distances(adjacency, scenario.source_node_ids)
    context: Dict[str, float] = {}

    for node in snapshot.nodes:
        hop = hop_distances.get(node.node_id)
        if hop is None:
            context[node.node_id] = 0.0
        else:
            index = min(hop, len(decay_table) - 1)
            context[node.node_id] = float(decay_table[index])

    return context


def _load_baseline_decay() -> Sequence[float]:
    """Read the real RISK_HOP_DECAY setting if importable, else fall back.

    Imported lazily so this module stays usable (and unit-testable) without
    pydantic-settings / a populated .env.
    """
    try:
        from app.config import get_settings

        decay = get_settings().risk_hop_decay_list
        if decay:
            return decay
    except Exception:  # noqa: BLE001 - config is optional for label generation
        pass
    return DEFAULT_BASELINE_DECAY


# ---------------------------------------------------------------------------
# Splitting
# ---------------------------------------------------------------------------

def split_scenarios(
    scenarios: Sequence[Scenario],
    seed: int = SEED,
    train_fraction: float = 0.70,
    validation_fraction: float = 0.15,
) -> ScenarioSplit:
    """Deterministic SCENARIO-level 70/15/15 split.

    Splitting by scenario (not by node) is essential: every scenario labels
    the whole graph, so a node-level split would put the same disruption in
    both train and test and leak the answer.

    Scenarios are sorted by scenario_id before shuffling so the split
    depends only on (scenario set, seed) -- not on generation order.
    """
    if not scenarios:
        return ScenarioSplit()

    ordered = sorted(scenarios, key=lambda s: s.scenario_id)
    rng = random.Random(seed)
    shuffled = list(ordered)
    rng.shuffle(shuffled)

    total = len(shuffled)
    n_train = int(round(total * train_fraction))
    n_validation = int(round(total * validation_fraction))

    # With very small scenario counts, rounding can starve val/test.
    # Guarantee a non-empty test split whenever there are >= 3 scenarios,
    # and a non-empty validation split whenever there are >= 2.
    if total >= 3:
        n_train = min(n_train, total - 2)
        n_train = max(n_train, 1)
        n_validation = max(n_validation, 1)
        n_validation = min(n_validation, total - n_train - 1)
    elif total == 2:
        n_train, n_validation = 1, 1
    else:
        n_train, n_validation = 1, 0

    return ScenarioSplit(
        train=shuffled[:n_train],
        validation=shuffled[n_train : n_train + n_validation],
        test=shuffled[n_train + n_validation :],
    )


# ---------------------------------------------------------------------------
# PyG example construction (imports torch lazily)
# ---------------------------------------------------------------------------

def build_scenario_example(snapshot: "GraphSnapshot", scenario: Scenario):
    """Build one training example: (Data with .y, node_id_to_index, index_to_node_id).

    Reuses app/ml/graph_data.build_graph_data so training and inference share
    one feature pipeline (14 features). `torch` / `graph_data` are imported
    here rather than at module import so scenario+label generation stays
    dependency-light.

    The label tensor is ordered to match the PyG node indices, so
    `data.y[i]` always corresponds to `index_to_node_id[i]`.
    """
    import torch

    from app.ml.graph_data import build_graph_data

    adjacency = build_adjacency(snapshot)

    data, node_id_to_index, index_to_node_id = build_graph_data(
        snapshot=snapshot,
        source_node_ids=list(scenario.source_node_ids),
        baseline_risk=baseline_risk_context(snapshot, scenario, adjacency),
        disruption_severity=scenario.severity,
    )

    labels = compute_scenario_labels(snapshot, scenario, adjacency)

    ordered = [labels[index_to_node_id[i]] for i in range(len(index_to_node_id))]
    data.y = torch.tensor(ordered, dtype=torch.float32)
    data.scenario_id = scenario.scenario_id

    return data, node_id_to_index, index_to_node_id


def build_scenario_dataset(snapshot: "GraphSnapshot", scenarios: Sequence[Scenario]) -> List:
    """Build a list of PyG Data objects (each with `.y`) for the scenarios."""
    return [build_scenario_example(snapshot, scenario)[0] for scenario in scenarios]
