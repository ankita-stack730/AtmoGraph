"""
AtmoGraph backend entrypoint.

Run with:
    uvicorn app.main:app --reload
"""
import logging

from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware

from app.api import (
    routes_disruption,
    routes_graph,
    routes_health,
    routes_nlp,
    routes_prediction,
)
from app.config import get_settings
from app.graph.neo4j_client import neo4j_client

settings = get_settings()

logging.basicConfig(level=settings.log_level)
logger = logging.getLogger("atmograph.main")

app = FastAPI(
    title="AtmoGraph API",
    description="Supply Chain Ripple Effect Predictor — backend API (Phase 1-4).",
    version="0.1.0",
)

# Permissive CORS for local dev; tighten before any real deployment.
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

app.include_router(routes_health.router)
app.include_router(routes_graph.router)
app.include_router(routes_nlp.router)
app.include_router(routes_disruption.router)
app.include_router(routes_prediction.router)


@app.on_event("startup")
def on_startup():
    logger.info("Starting AtmoGraph API (env=%s)", settings.app_env)
    # Connect lazily/gracefully — don't crash the whole API if Neo4j is down;
    # /health will report it, and individual graph endpoints will error clearly.
    neo4j_client.connect()


@app.on_event("shutdown")
def on_shutdown():
    neo4j_client.close()


@app.get("/", tags=["health"])
def root():
    return {
        "service": "AtmoGraph API",
        "status": "running",
        "docs": "/docs",
    }
