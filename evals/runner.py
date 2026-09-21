"""Eval matrix runner: adaptive vs fixed-time baseline across scenario YAMLs."""

import json
import sys
import time
from concurrent.futures import ProcessPoolExecutor
from pathlib import Path

import yaml

REPO = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(REPO / "src"))

from adaptive_traffic.core.simulation.engine import create_intersection, create_simulation

RESULTS_DIR = REPO / "evals" / "results"


def _apply_incident(sim_config: dict, incident: str) -> dict:
    # ponytail: incidents approximated via existing knobs; dedicated IncidentEngine
    # when taxonomy grows beyond these two
    if incident == "sensor_failure":
        sim_config["weather_state"] = "waterlogged"
    elif incident == "lane_block":
        rates = sim_config.get("generation_rates") or {}
        first_key = next(iter(rates), None)
        if first_key is not None:
            rates[first_key] = int(rates[first_key] * 0.3)
    return sim_config


def run_scenario(scenario: dict) -> dict:
    name = scenario["name"]
    rows = {}
    for mode in (True, False):
        sim_config = {
            "seed": 42,
            "behavior_preset": scenario.get("behavior_preset", "typical_urban"),
            "weather_state": scenario.get("weather_state", "clear"),
            "adaptive_scheduling": mode,
        }
        if scenario.get("incident"):
            sim_config = _apply_incident(sim_config, scenario["incident"])
        sim = create_simulation(sim_config)
        geo = dict(scenario.get("geometry", {}))
        geo.setdefault("id", "eval-1")
        sim.add_intersection(create_intersection(geo))
        for _ in range(scenario.get("steps", 3000)):
            sim.step()
        stats = sim.get_network_stats()
        # Decision latency: sample refresh+decide on final state (Step 4 gate: p95 <10ms)
        ix = sim.intersections["eval-1"]
        lat = []
        for _ in range(200):
            t0 = time.perf_counter()
            sim._refresh_green_plan(ix)
            sim._next_phase(ix)
            lat.append((time.perf_counter() - t0) * 1000)
        lat.sort()
        rows["adaptive" if mode else "fixed"] = {
            "avg_waiting_time": round(stats["avg_waiting_time"], 2),
            "throughput_vph": round(stats["throughput"], 1),
            "queue_error": round(stats["queue_error"], 3),
            "completed": stats["total_completed"],
            "dec_p50_ms": round(lat[100], 3),
            "dec_p95_ms": round(lat[190], 3),
        }
    adaptive, fixed = rows["adaptive"], rows["fixed"]
    rows["delta_wait_pct"] = round(
        (fixed["avg_waiting_time"] - adaptive["avg_waiting_time"])
        / max(fixed["avg_waiting_time"], 1e-9) * 100, 2
    )
    return {
        "name": name,
        # Honesty label (Phase B): incidents are synthetic approximations via
        # existing sim knobs, not field events. See _apply_incident.
        "incident_model": f"synthetic-approx:{scenario['incident']}" if scenario.get("incident") else "none",
        **rows,
    }


def _load_scenarios() -> list:
    scenarios = []
    for path in sorted((REPO / "configs" / "evals").glob("*.yaml")):
        data = yaml.safe_load(path.read_text(encoding="utf-8"))
        scenarios.extend(data.get("scenarios", []))
    return scenarios


def main() -> int:
    scenarios = _load_scenarios()
    start = time.perf_counter()
    with ProcessPoolExecutor() as pool:
        results = list(pool.map(run_scenario, scenarios))
    wall = time.perf_counter() - start

    RESULTS_DIR.mkdir(parents=True, exist_ok=True)
    out = RESULTS_DIR / f"scorecard_{int(time.time())}.json"
    out.write_text(json.dumps({
        "wall_s": round(wall, 2),
        "notes": "incidents are synthetic approximations (sensor_failure->waterlogged, "
                 "lane_block->0.3x gen rate), not field events; queue_error is sim-internal",
        "results": results,
    }, indent=2), encoding="utf-8")

    prev_files = sorted(RESULTS_DIR.glob("scorecard_*.json"))
    prev = {}
    if len(prev_files) > 1:
        prev = {r["name"]: r for r in json.loads(prev_files[-2].read_text(encoding="utf-8"))["results"]}

    header = f"{'scenario':34} {'wait_adapt':>10} {'wait_fixed':>10} {'delta%':>8} {'qerr_a':>7} {'qerr_f':>7} {'dec95_a':>8}"
    print(header)
    print("-" * len(header))
    regressions = []
    lat_regressions = []
    for r in results:
        print(
            f"{r['name']:34} {r['adaptive']['avg_waiting_time']:>10.1f} "
            f"{r['fixed']['avg_waiting_time']:>10.1f} {r['delta_wait_pct']:>8.1f} "
            f"{r['adaptive']['queue_error']:>7.2f} {r['fixed']['queue_error']:>7.2f} "
            f"{r['adaptive']['dec_p95_ms']:>8.2f}"
        )
        if r["name"] in prev and r["adaptive"]["avg_waiting_time"] > prev[r["name"]]["adaptive"]["avg_waiting_time"] * 1.05:
            regressions.append(r["name"])
        if r["adaptive"]["dec_p95_ms"] > 10:
            lat_regressions.append(r["name"])

    print(f"\nwall: {wall:.1f}s | scorecard: {out.relative_to(REPO)}")
    if regressions:
        print(f"REGRESSION (>5% wait vs previous run): {regressions}")
    if lat_regressions:
        print(f"LATENCY REGRESSION (dec p95 >10ms): {lat_regressions}")
    if regressions or lat_regressions:
        return 1
    return 0


if __name__ == "__main__":
    sys.exit(main())
