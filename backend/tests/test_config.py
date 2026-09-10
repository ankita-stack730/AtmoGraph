import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parent.parent))

from app.config import Settings


def test_risk_hop_decay_list_parses_csv():
    settings = Settings(risk_hop_decay="1.0,0.8,0.6,0.4")
    assert settings.risk_hop_decay_list == [1.0, 0.8, 0.6, 0.4]


def test_risk_hop_decay_list_strips_whitespace():
    settings = Settings(risk_hop_decay=" 1.0, 0.8 , 0.6")
    assert settings.risk_hop_decay_list == [1.0, 0.8, 0.6]


def test_default_settings_have_sane_neo4j_defaults():
    settings = Settings()
    assert settings.neo4j_uri.startswith("bolt://")
    assert settings.risk_max_hops >= 1
