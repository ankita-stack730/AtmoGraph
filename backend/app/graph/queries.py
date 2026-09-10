"""
Cypher query strings, kept separate from the service layer so they're easy
to review/tune independently of Python logic.
"""

# All node labels we seed/support. Kept in one place so NLP matching and
# Cypher queries stay in sync.
NODE_LABELS = [
    "Supplier",
    "Manufacturer",
    "Warehouse",
    "Port",
    "ShippingRoute",
    "Product",
    "Company",
    "Country",
]

RELATIONSHIP_TYPES = [
    "SUPPLIES_TO",
    "MANUFACTURES",
    "SHIPS_THROUGH",
    "LOCATED_IN",
    "DEPENDS_ON",
    "CONNECTED_TO",
]

# --- Schema setup -----------------------------------------------------------

CONSTRAINT_QUERIES = [
    f"CREATE CONSTRAINT {label.lower()}_id_unique IF NOT EXISTS "
    f"FOR (n:{label}) REQUIRE n.id IS UNIQUE"
    for label in NODE_LABELS
]

# --- Read queries -------------------------------------------------------------

GET_FULL_GRAPH = """
MATCH (n)
OPTIONAL MATCH (n)-[r]->(m)
RETURN n, r, m
"""

GET_NODE_BY_ID = """
MATCH (n {id: $node_id})
RETURN n
LIMIT 1
"""

GET_NODE_NEIGHBORS = """
MATCH (n {id: $node_id})-[r]-(m)
RETURN n, r, m
"""

# Case-insensitive fuzzy match on node name — used to resolve NLP entities
# (e.g. "Rotterdam") to graph nodes.
FIND_NODES_BY_NAME = """
MATCH (n)
WHERE toLower(n.name) CONTAINS toLower($name)
RETURN n
LIMIT $limit
"""

# Multi-hop propagation from a set of source node ids, up to max_hops.
# Returns each reached node together with the shortest hop distance from
# ANY of the source nodes (APOC-free, pure Cypher variable-length path).
PROPAGATE_FROM_SOURCES = """
UNWIND $source_ids AS source_id
MATCH (source {id: source_id})
CALL {
    WITH source
    MATCH path = (source)-[*1..%(max_hops)s]-(target)
    WHERE target.id <> source.id
    RETURN target, min(length(path)) AS hop_distance
}
RETURN target.id AS node_id, target.name AS name, labels(target) AS labels,
       min(hop_distance) AS hop_distance
ORDER BY hop_distance ASC
"""


def propagate_query(max_hops: int) -> str:
    """Cypher does not allow parameterized relationship-hop ranges, so we
    interpolate the (server-side validated, integer-only) max_hops value."""
    safe_hops = max(1, min(int(max_hops), 10))
    return PROPAGATE_FROM_SOURCES % {"max_hops": safe_hops}
