import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parent.parent))

import pytest
from fastapi.testclient import TestClient


@pytest.fixture
def client():
    """FastAPI TestClient. Import happens inside the fixture so tests that
    don't need the full app (e.g. pure unit tests) don't pay the import cost."""
    from app.main import app

    with TestClient(app) as c:
        yield c
