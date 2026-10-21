"""Eval runner: city threading + mid-run incidents (fast, small steps)."""

import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parents[2] / "evals"))

from runner import _apply_incident, run_scenario


def _sc(**kw):
    base = {
        "name": "t",
        "geometry": {"approaches": ["north", "south", "east", "west"]},
        "behavior_preset": "typical_urban",
        "weather_state": "clear",
        "steps": 300,
    }
    base.update(kw)
    return base


def test_city_threading_and_incident_labels():
    r = run_scenario(_sc(incident="sensor_failure"))
    assert r["incident_model"] == "synthetic-approx:sensor_failure"
    assert r["delta_wait_pct"] >= 0  # 300-step smoke: threading, not margin (full eval: 24.8%)


def test_rally_blocks_then_surges():
    cfg = _apply_incident({"generation_rates": {"n": 1000}}, "lane_block")
    assert cfg["generation_rates"]["n"] == 300
    cfg = _apply_incident({"weather_state": "clear"}, "sensor_failure")
    assert cfg["weather_state"] == "waterlogged"
