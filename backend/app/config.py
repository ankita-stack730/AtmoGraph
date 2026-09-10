"""
Central configuration for AtmoGraph backend.

All secrets/config come from environment variables (.env file locally).
Never hard-code credentials here.
"""
from functools import lru_cache
from typing import List

from pydantic_settings import BaseSettings, SettingsConfigDict


class Settings(BaseSettings):
    model_config = SettingsConfigDict(env_file=".env", env_file_encoding="utf-8", extra="ignore")

    # --- Neo4j ---
    neo4j_uri: str = "bolt://localhost:7687"
    neo4j_username: str = "neo4j"
    neo4j_password: str = "changeme"
    neo4j_database: str = "neo4j"

    # --- App ---
    app_env: str = "development"
    log_level: str = "INFO"

    # --- Risk propagation (BASELINE, see Section 8 of spec) ---
    risk_hop_decay: str = "1.0,0.8,0.6,0.4,0.25,0.15"
    risk_max_hops: int = 5

    @property
    def risk_hop_decay_list(self) -> List[float]:
        return [float(x.strip()) for x in self.risk_hop_decay.split(",") if x.strip()]


@lru_cache
def get_settings() -> Settings:
    """Cached settings singleton."""
    return Settings()
