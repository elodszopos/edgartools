"""Integration: /health through the real app (lifespan boot), plus the first golden."""

from edgar.__about__ import __version__ as edgartools_version
from fastapi.testclient import TestClient

from app.main import app


def test_health_ok_and_golden(golden):
    with TestClient(app) as client:
        response = client.get("/health")
    assert response.status_code == 200
    body = response.json()
    assert body == {"status": "ok", "edgartools_version": edgartools_version, "identity_set": True}
    golden("health", "ok", body)
