from fastapi import APIRouter

from app.graph.neo4j_client import neo4j_client

router = APIRouter(tags=["health"])


@router.get("/health")
def health():
    """Basic liveness + Neo4j connectivity check."""
    db_ok = neo4j_client.verify_connectivity()
    return {
        "status": "ok",
        "neo4j_connected": db_ok,
    }
