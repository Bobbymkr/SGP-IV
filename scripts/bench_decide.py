"""Decide-path latency benchmark (Step 0 of fast-green plan).

Times the post-detection pipeline in isolation:
  synthetic detections -> estimate_from_detections -> TrafficState build
  -> engine demand + phase decision.
Record results in docs/BENCHMARKS.md. Budget: <10ms per decision (excl. detection).
"""

import argparse
import sys
import time
from pathlib import Path

import numpy as np

sys.path.insert(0, str(Path(__file__).resolve().parents[1] / "src"))

from adaptive_traffic.config.city_profile import get_city_profile  # noqa: E402
from adaptive_traffic.core.analytics.queue_estimator import QueueEstimator  # noqa: E402
from adaptive_traffic.core.control.controllers import TrafficState  # noqa: E402
from adaptive_traffic.core.domain import VehicleDetection  # noqa: E402
from adaptive_traffic.core.simulation.engine import (  # noqa: E402
    Intersection,
    create_intersection,
    create_simulation,
)


def synth_detections(n: int, seed: int = 7) -> list[VehicleDetection]:
    rng = np.random.default_rng(seed)
    dets = []
    for i in range(n):
        # bottom half of frame => inside queue zone for most boxes
        x1 = int(rng.integers(0, 560))
        y1 = int(rng.integers(240, 430))
        w, h = int(rng.integers(20, 80)), int(rng.integers(20, 60))
        dets.append(VehicleDetection(
            class_id=int(rng.integers(0, 6)),
            class_name="car",
            confidence=float(rng.uniform(0.4, 0.99)),
            bbox=(x1, y1, x1 + w, y1 + h),
            center=(x1 + w // 2, y1 + h // 2),
        ))
    return dets


def populate(intersection: Intersection, n_per_lane: int = 8) -> None:
    from adaptive_traffic.core.domain import VehicleType
    from adaptive_traffic.core.simulation.engine import Vehicle

    vid = 0
    for lane in intersection.lanes.values():
        for k in range(n_per_lane):
            lane.vehicles.append(Vehicle(
                id=vid, vehicle_type=VehicleType.CAR,
                direction=lane.direction, lane=lane.lane_index,
                position=5.0 + k * 7.0, speed=0.0, target_speed=0.0,
            ))
            vid += 1


def pct(times: list[float], q: float) -> float:
    s = sorted(times)
    return s[min(len(s) - 1, int(q * len(s)))] * 1000


def bench(fn, repeats: int = 200) -> tuple[float, float]:
    fn()  # warmup
    ts = []
    for _ in range(repeats):
        t0 = time.perf_counter()
        fn()
        ts.append(time.perf_counter() - t0)
    return sum(ts) / len(ts) * 1000, pct(ts, 0.95)


def main() -> int:
    p = argparse.ArgumentParser(description=__doc__)
    p.add_argument("--counts", default="50,150,300")
    p.add_argument("--repeats", type=int, default=200)
    args = p.parse_args()

    profile = get_city_profile("bangalore")
    estimator = QueueEstimator(profile)
    engine = create_simulation(config={"adaptive_scheduling": True},
                                 city_profile=profile)
    intersection = create_intersection(config={}, city_profile=profile)
    engine.add_intersection(intersection)
    populate(intersection)

    print(f"{'n_det':>6} {'estimate_ms':>12} {'+state_ms':>10} {'+decide_ms':>11} "
          f"{'total_p50':>10} {'total_p95':>10}")
    for n in (int(x) for x in args.counts.split(",")):
        dets = synth_detections(n)

        est_mean, _ = bench(
            lambda: estimator.estimate_from_detections(dets), args.repeats)

        def with_state():
            est = estimator.estimate_from_detections(dets)
            by_dir = {d: q.vehicle_count for d, q in est.by_direction.items()}
            return TrafficState(queue_lengths=by_dir, flow_rates={},
                                occupancy={}, phase="0_green", time_in_phase=5.0)

        state_mean, _ = bench(with_state, args.repeats)

        def decide():
            demands = [engine._group_demand(intersection, g)
                       for g in intersection.compatibility_groups]
            return engine._next_phase(intersection), demands

        dec_mean, _ = bench(decide, args.repeats)

        def total():
            est = estimator.estimate_from_detections(dets)
            by_dir = {d: q.vehicle_count for d, q in est.by_direction.items()}
            TrafficState(queue_lengths=by_dir, flow_rates={},
                         occupancy={}, phase="0_green", time_in_phase=5.0)
            engine._next_phase(intersection)

        tot_mean, tot_p95 = bench(total, args.repeats)
        print(f"{n:>6} {est_mean:>12.3f} {state_mean - est_mean:>10.3f} "
              f"{dec_mean:>11.3f} {tot_mean:>10.3f} {tot_p95:>10.3f}")
    return 0


if __name__ == "__main__":
    sys.exit(main())
