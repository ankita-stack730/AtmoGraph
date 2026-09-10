"""
Seed the Neo4j database with the mock (SYNTHETIC) supply-chain graph in
data/sample_supply_chain.json.

Safe to run repeatedly: every write uses MERGE on the node's `id`, so
re-running this script updates properties instead of creating duplicates.

Usage:
    cd backend
    python scripts/seed_neo4j.py            # seed (idempotent)
    python scripts/seed_neo4j.py --reset     # delete ALL nodes/relationships first

Requires NEO4J_URI / NEO4J_USERNAME / NEO4J_PASSWORD to be set (via .env).
"""
from __future__ import annotations

import argparse
import json
import logging
import sys
from pathlib import Path

# Allow running this script directly (`python scripts/seed_neo4j.py`)
sys.path.insert(0, str(Path(__file__).resolve().parent.parent))

from app.graph.neo4j_client import neo4j_client  # noqa: E402
from app.graph.queries import CONSTRAINT_QUERIES  # noqa: E402

logging.basicConfig(level=logging.INFO, format="%(levelname)s: %(message)s")
logger = logging.getLogger("atmograph.seed")

DATA_PATH = Path(__file__).resolve().parent.parent / "data" / "sample_supply_chain.json"

# Maps the JSON top-level key -> the Neo4j label to create for its entries.
LABEL_MAP = {
    "countries": "Country",
    "ports": "Port",
    "shipping_routes": "ShippingRoute",
    "suppliers": "Supplier",
    "manufacturers": "Manufacturer",
    "warehouses": "Warehouse",
    "products": "Product",
    "companies": "Company",
}

# Extra scalar properties (besides id/name) worth copying straight through
# for specific node collections.
EXTRA_PROPS = {
    "countries": [],
    "ports": ["country_id"],
    "shipping_routes": ["from_port_id", "to_port_id"],
    "suppliers": ["country_id"],
    "manufacturers": ["country_id"],
    "warehouses": ["country_id"],
    "products": [],
    "companies": ["country_id"],
}


def load_data() -> dict:
    with open(DATA_PATH, "r", encoding="utf-8") as f:
        return json.load(f)


def reset_database() -> None:
    logger.warning("Resetting database: deleting ALL nodes and relationships...")
    neo4j_client.run_query("MATCH (n) DETACH DELETE n")


def ensure_constraints() -> None:
    for query in CONSTRAINT_QUERIES:
        neo4j_client.run_query(query)
    logger.info("Uniqueness constraints ensured for all node labels.")


def seed_nodes(data: dict) -> None:
    for key, label in LABEL_MAP.items():
        items = data.get(key, [])
        for item in items:
            props = {"id": item["id"], "name": item["name"]}
            for extra_key in EXTRA_PROPS.get(key, []):
                if extra_key in item:
                    props[extra_key] = item[extra_key]
            cypher = f"MERGE (n:{label} {{id: $id}}) SET n += $props"
            neo4j_client.run_query(cypher, {"id": item["id"], "props": props})
        logger.info("Seeded %d %s node(s).", len(items), label)


def seed_relationships(data: dict) -> None:
    rels = data.get("relationships", {})
    total = 0

    for rel_type, edges in rels.items():
        for edge in edges:
            from_id = edge["from"]
            to_id = edge["to"]
            extra = {k: v for k, v in edge.items() if k not in ("from", "to")}
            cypher = (
                "MATCH (a {id: $from_id}), (b {id: $to_id}) "
                f"MERGE (a)-[r:{rel_type}]->(b) "
                "SET r += $extra"
            )
            neo4j_client.run_query(cypher, {"from_id": from_id, "to_id": to_id, "extra": extra})
            total += 1

    # Also connect suppliers/manufacturers/warehouses to their SHIPS_THROUGH ports
    # and route source/destination ports (derived from shipping_routes list).
    for route in data.get("shipping_routes", []):
        neo4j_client.run_query(
            "MATCH (p:Port {id: $from_port}), (r:ShippingRoute {id: $route_id}) "
            "MERGE (p)-[rel:SHIPS_THROUGH]->(r) SET rel += {}",
            {"from_port": route["from_port_id"], "route_id": route["id"]},
        )
        neo4j_client.run_query(
            "MATCH (r:ShippingRoute {id: $route_id}), (p:Port {id: $to_port}) "
            "MERGE (r)-[rel:SHIPS_THROUGH]->(p) SET rel += {}",
            {"route_id": route["id"], "to_port": route["to_port_id"]},
        )
        total += 2

    logger.info("Seeded %d relationship(s).", total)


def main() -> None:
    parser = argparse.ArgumentParser(description="Seed AtmoGraph's Neo4j database.")
    parser.add_argument("--reset", action="store_true", help="Delete all existing data first.")
    args = parser.parse_args()

    if not neo4j_client.verify_connectivity():
        logger.error(
            "Could not connect to Neo4j. Check NEO4J_URI / NEO4J_USERNAME / "
            "NEO4J_PASSWORD in your .env file and make sure Neo4j is running."
        )
        sys.exit(1)

    if args.reset:
        reset_database()

    ensure_constraints()
    data = load_data()
    seed_nodes(data)
    seed_relationships(data)

    logger.info("Seed complete.")
    neo4j_client.close()


if __name__ == "__main__":
    main()
