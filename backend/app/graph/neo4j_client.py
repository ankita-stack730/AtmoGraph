"""
Neo4j connection management.

Wraps the official neo4j Python driver behind a small client class so the
rest of the app never talks to the driver directly. Credentials always come
from environment variables via app.config.Settings — never hard-coded.
"""
from __future__ import annotations

import logging
from typing import Any, Dict, List, Optional

from neo4j import GraphDatabase, Driver
from neo4j.exceptions import ServiceUnavailable, AuthError

from app.config import get_settings

logger = logging.getLogger("atmograph.neo4j")


class Neo4jClient:
    """Thin wrapper around the neo4j driver with a simple run_query helper."""

    def __init__(self) -> None:
        self._driver: Optional[Driver] = None

    def connect(self) -> None:
        settings = get_settings()
        if self._driver is not None:
            return
        self._driver = GraphDatabase.driver(
            settings.neo4j_uri,
            auth=(settings.neo4j_username, settings.neo4j_password),
        )
        logger.info("Neo4j driver initialized for %s", settings.neo4j_uri)

    def close(self) -> None:
        if self._driver is not None:
            self._driver.close()
            self._driver = None
            logger.info("Neo4j driver closed")

    def verify_connectivity(self) -> bool:
        """Returns True if we can actually reach the database, False otherwise.

        Does not raise — callers (e.g. /health) should be able to report a
        clean 'db unreachable' status instead of crashing.
        """
        try:
            self.connect()
            self._driver.verify_connectivity()
            return True
        except (ServiceUnavailable, AuthError, Exception) as exc:  # noqa: BLE001
            logger.warning("Neo4j not reachable: %s", exc)
            return False

    def run_query(self, cypher: str, parameters: Optional[Dict[str, Any]] = None) -> List[Dict[str, Any]]:
        """Run a Cypher query and return a list of plain dicts."""
        settings = get_settings()
        self.connect()
        with self._driver.session(database=settings.neo4j_database) as session:
            result = session.run(cypher, parameters or {})
            return[dict(record) for record in result]


# Module-level singleton used across the app (FastAPI will manage its lifecycle
# via startup/shutdown events in main.py).
neo4j_client = Neo4jClient()
