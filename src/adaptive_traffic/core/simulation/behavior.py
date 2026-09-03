"""
Vehicle Behavior Profiles for Heterogeneous Traffic Simulation
"""

import logging
import random
from dataclasses import dataclass, replace
from typing import Optional

import numpy as np

try:
    from .engine import VehicleType
except ImportError:
    from adaptive_traffic.core.simulation.engine import VehicleType

logger = logging.getLogger(__name__)


@dataclass
class DisciplineProfile:
    """Behavioral discipline parameters for a vehicle class"""

    red_light_violation_prob: float
    stop_line_encroachment_mean_m: float
    stop_line_encroachment_std_m: float
    lane_drift_prob: float
    wrong_side_entry_prob: float
    speed_compliance_factor: float


DISCIPLINE_PRESETS = {
    "disciplined": DisciplineProfile(
        red_light_violation_prob=0.05,
        stop_line_encroachment_mean_m=0.1,
        stop_line_encroachment_std_m=0.2,
        lane_drift_prob=0.005,
        wrong_side_entry_prob=0.002,
        speed_compliance_factor=0.9,
    ),
    "typical_urban": DisciplineProfile(
        red_light_violation_prob=0.25,
        stop_line_encroachment_mean_m=0.8,
        stop_line_encroachment_std_m=0.5,
        lane_drift_prob=0.05,
        wrong_side_entry_prob=0.01,
        speed_compliance_factor=1.0,
    ),
    "aggressive_metro": DisciplineProfile(
        red_light_violation_prob=0.45,
        stop_line_encroachment_mean_m=1.5,
        stop_line_encroachment_std_m=0.8,
        lane_drift_prob=0.12,
        wrong_side_entry_prob=0.03,
        speed_compliance_factor=1.2,
    ),
}

INDIA_BEHAVIOR_SOURCES = {
    "red_light_violation_prob": (
        "Indian urban RLV studies commonly report 20-40% violations at signalized "
        "intersections (e.g., IIT Delhi / TRIPP observational studies); disciplined "
        "corridor enforcement drops to ~5%, congested metros reach ~45%."
    ),
    "stop_line_encroachment_mean_m": (
        "Field observations of Indian urban signals show stopped vehicles queueing "
        "~0-2 m past the marked stop line (mixed two-wheeler front-row filtering); "
        "mean ~0.8 m typical urban, ~1.5 m aggressive metro."
    ),
    "lane_drift_prob": (
        "Two-wheeler lateral filtering between lanes is near-ubiquitous in Indian "
        "heterogeneous traffic (NMT/lane-discipline studies); car drift rare (<1%), "
        "motorcycles an order of magnitude higher."
    ),
    "wrong_side_entry_prob": (
        "Wrong-side entry at urban Indian intersections observed in low single-digit "
        "percentages (road-safety audit reports); ~1% typical urban, up to ~3% in "
        "aggressive metro corridors."
    ),
    "speed_compliance_factor": (
        "Speed non-compliance on urban arterials commonly exceeds posted limits; "
        "aggressive metro riders average ~20% over free-flow target."
    ),
}


def profile_for(vehicle_type) -> DisciplineProfile:
    """Per-class adjusted copy of the typical_urban baseline"""
    base = DISCIPLINE_PRESETS["typical_urban"]
    name = getattr(vehicle_type, "value", str(vehicle_type)).lower()
    if name == "motorcycle":
        return replace(
            base,
            lane_drift_prob=min(base.lane_drift_prob * 10.0, 0.95),
            stop_line_encroachment_mean_m=base.stop_line_encroachment_mean_m + 0.6,
            red_light_violation_prob=min(base.red_light_violation_prob * 1.3, 0.95),
        )
    if name == "auto":
        return replace(
            base,
            lane_drift_prob=base.lane_drift_prob * 6.0,
            stop_line_encroachment_mean_m=base.stop_line_encroachment_mean_m + 0.3,
            speed_compliance_factor=base.speed_compliance_factor * 1.05,
        )
    if name == "bicycle":
        return replace(
            base,
            lane_drift_prob=base.lane_drift_prob * 4.0,
            red_light_violation_prob=base.red_light_violation_prob * 0.8,
        )
    if name in ("bus", "truck"):
        return replace(
            base,
            lane_drift_prob=base.lane_drift_prob * 0.2,
            red_light_violation_prob=base.red_light_violation_prob * 0.4,
            stop_line_encroachment_mean_m=max(0.0, base.stop_line_encroachment_mean_m - 0.3),
        )
    return replace(base)


class BehaviorEngine:
    """Applies behavioral anomalies to vehicles via a seeded rng"""

    def __init__(self, preset_name: str = "typical_urban", rng: Optional[random.Random] = None):
        if preset_name not in DISCIPLINE_PRESETS:
            raise ValueError(f"Unknown preset: {preset_name}")
        self.preset_name = preset_name
        self.base_profile = DISCIPLINE_PRESETS[preset_name]
        self.rng = rng if rng is not None else random.Random()

    def _profile(self, vehicle_type) -> DisciplineProfile:
        base = profile_for(vehicle_type)
        scale = self.base_profile.speed_compliance_factor
        # ponytail: single-knob preset scaling of the class-adjusted profile;
        # full per-parameter preset x class matrix only if calibration demands it
        return replace(
            base,
            red_light_violation_prob=np.clip(base.red_light_violation_prob * scale, 0.0, 0.95),
            stop_line_encroachment_mean_m=base.stop_line_encroachment_mean_m * scale,
            lane_drift_prob=np.clip(base.lane_drift_prob * scale, 0.0, 0.95),
            wrong_side_entry_prob=np.clip(base.wrong_side_entry_prob * scale, 0.0, 0.95),
        )

    def sample_spawn_anomaly(self, vehicle_type) -> Optional[str]:
        p = self._profile(vehicle_type)
        r = self.rng.random()
        if r < p.wrong_side_entry_prob:
            return "wrong_side"
        return None

    def maybe_violate_red(self, vehicle_type, rng: random.Random) -> bool:
        return rng.random() < self._profile(vehicle_type).red_light_violation_prob

    def encroachment_offset_m(self, vehicle_type, rng: random.Random) -> float:
        p = self._profile(vehicle_type)
        offset = rng.gauss(p.stop_line_encroachment_mean_m, p.stop_line_encroachment_std_m)
        return max(-0.5, offset)

    def maybe_lane_drift(self, vehicle_type, rng: random.Random) -> bool:
        return rng.random() < self._profile(vehicle_type).lane_drift_prob


if __name__ == "__main__":
    N = 10000
    for preset_name in ("disciplined", "typical_urban", "aggressive_metro"):
        engine = BehaviorEngine(preset_name=preset_name, rng=random.Random(42))
        rng = random.Random(43)
        expected = engine._profile(VehicleType.CAR).red_light_violation_prob
        rate = sum(engine.maybe_violate_red(VehicleType.CAR, rng) for _ in range(N)) / N
        assert abs(rate - expected) <= 0.05, f"{preset_name}: {rate} vs {expected}"

    eng = BehaviorEngine(preset_name="typical_urban", rng=random.Random(7))
    rng = random.Random(8)
    offsets = [eng.encroachment_offset_m(VehicleType.CAR, rng) for _ in range(N)]
    assert all(np.isfinite(o) and o >= -0.5 for o in offsets)

    moto = profile_for(VehicleType.MOTORCYCLE).lane_drift_prob
    bus = profile_for(VehicleType.BUS).lane_drift_prob
    assert moto > bus * 10, f"drift {moto} vs {bus}"
    assert BehaviorEngine(rng=random.Random(1)).sample_spawn_anomaly(VehicleType.CAR) in (
        None,
        "wrong_side",
    )

    print("behavior.py self-check passed")
