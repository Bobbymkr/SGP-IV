"""Signals API: lazy defaults, Surat-bounds validation, no-500 timing writes."""

from fastapi.testclient import TestClient

from adaptive_traffic.api.main import create_app
from adaptive_traffic.api.routes import signals as routes

client = TestClient(create_app())
BASE = "/api/v1/signals"


def setup_function(_):
    routes.signals_db.clear()


def test_unknown_signal_gets_live_default_not_404():
    r = client.get(f"{BASE}/demo-1")
    assert r.status_code == 200
    assert r.json()["signal_id"] == "demo-1"


def test_timing_write_returns_200_with_last_timing():
    r = client.post(
        f"{BASE}/demo-1/timing", json={"signal_id": "demo-1", "green_times": {"NS": 30, "EW": 25}}
    )
    assert r.status_code == 200, r.text
    body = r.json()
    assert body["last_timing"]["green_times"] == {"NS": 30.0, "EW": 25.0}
    assert body["updated_at"] is not None
    assert body["queues"] == {}  # queues stay vehicle counts


def test_out_of_bounds_green_rejected_422():
    r = client.post(f"{BASE}/demo-1/timing", json={"signal_id": "demo-1", "green_times": {"NS": 5}})
    assert r.status_code == 422
    r = client.post(
        f"{BASE}/demo-1/timing", json={"signal_id": "demo-1", "green_times": {"NS": 200}}
    )
    assert r.status_code == 422
    r = client.post(f"{BASE}/demo-1/timing", json={"signal_id": "demo-1", "green_times": {}})
    assert r.status_code == 422


def test_health_and_ntcip_timings_answer_on_fresh_box():
    assert client.get(f"{BASE}/demo-1/health").status_code == 200
    assert client.get(f"{BASE}/demo-1/ntcip/timing").status_code == 200
