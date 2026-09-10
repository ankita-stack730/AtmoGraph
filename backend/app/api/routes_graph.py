from fastapi import APIRouter, HTTPException

from app.graph import graph_service
from app.models.schemas import GraphNode, GraphSnapshot

router = APIRouter(prefix="/graph", tags=["graph"])


@router.get("", response_model=GraphSnapshot)
def get_graph():
    """Return the full supply-chain graph (nodes + relationships).

    NOTE: fine for MVP-sized demo data seeded by scripts/seed_neo4j.py.
    Would need pagination/filtering before this scales to thousands of nodes
    (see Section 13 of the spec).
    """
    return graph_service.get_full_graph()


@router.get("/node/{node_id}", response_model=GraphNode)
def get_node(node_id: str):
    node = graph_service.get_node_by_id(node_id)
    if node is None:
        raise HTTPException(status_code=404, detail=f"Node '{node_id}' not found")
    return node
