"""Readiness honesty: registry+tier checks, no phantom database/redis claims."""

from fastapi.testclient import TestClient

from adaptive_traffic.api.main import create_app

client = TestClient(create_app())


def test_readiness_reports_registry_and_tier():
    r = client.get("/api/v1/health/ready")
    assert r.status_code == 200
    body = r.json()
    assert body["status"] in ("ready", "degraded")
    assert body["checks"]["models"] == "ok"  # registry shipped in repo
    assert body["checks"]["tier"] in ("low", "mid", "high")
    assert "database" not in body["checks"] and "redis" not in body["checks"]
