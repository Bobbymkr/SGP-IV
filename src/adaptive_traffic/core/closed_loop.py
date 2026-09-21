"""Estimate -> decide -> actuate bridge (Phase C lab slice).

The missing link the pipeline docstring called out: ``StagedPipeline`` ends at
an estimate, and the engine decides from sim-internal lane vehicles. This
module binds them — estimator output becomes lane demand, the engine picks a
phase, and the phase plan goes out as an NTCIP cycle config:

  frame -> StagedPipeline.process -> inject_estimate -> decide -> actuate

``run_frame`` is the one-call closed loop shared by the CI-sim script
(``scripts/run_closed_loop.py``) and the integration test. The future edge
runner calls the same function per drained frame.
"""

import itertools
import logging
from typing import Any, Optional

from adaptive_traffic.core.control.policies import (
    EmergencyEvent,
    ManualRegistry,
    resolve_priority,
)
from adaptive_traffic.core.ports.ntcip_port import (
    NTCIPCycleConfig,
    NTCIPPhaseTiming,
)

logger = logging.getLogger(__name__)

YELLOW_S = 5.0
ALL_RED_S = 2.0

_vid = itertools.count()


def _as_direction(name: str):
    from adaptive_traffic.core.simulation.engine import Direction

    try:
        return Direction[name.upper()]
    except KeyError:
        logger.warning(f"closed_loop: unknown direction {name!r}, skipping")
        return None


def inject_estimate(sim, intersection_id: str, estimate) -> dict[str, int]:
    """Replace the sim's demand set with estimator output.

    Removes previously injected queued vehicles (speed < 1, position < 50 —
    exactly the ``_group_demand`` predicate) and adds one stopped vehicle per
    counted vehicle, spread round-robin over the direction's lanes. Vehicle
    types follow the estimate's per-class breakdown when present (so the
    weighted green policy sees the true mix); otherwise all-CAR (legacy).
    Returns per-direction injected counts. Unknown direction names are skipped.
    """
    from adaptive_traffic.core.domain import VehicleType
    from adaptive_traffic.core.simulation.engine import Vehicle

    # Estimator class key -> sim VehicleType (schema has no tractor/bus_pedigree
    # members; they discharge like their closest heavy class).
    _CLASS_VTYPE = {
        "car": VehicleType.CAR,
        "bus": VehicleType.BUS,
        "truck": VehicleType.TRUCK,
        "two_wheeler": VehicleType.MOTORCYCLE,
        "cycle": VehicleType.BICYCLE,
        "autorickshaw": VehicleType.AUTO,
        "tractor": VehicleType.TRUCK,
        "bus_pedigree": VehicleType.BUS,
    }

    ix = sim.intersections[intersection_id]
    for lane in ix.lanes.values():
        lane.vehicles = [v for v in lane.vehicles if not (v.speed < 1.0 and v.position < 50)]

    injected: dict[str, int] = {}
    lanes_by_dir: dict[str, list] = {}
    for lane in ix.lanes.values():
        lanes_by_dir.setdefault(lane.direction.value, []).append(lane)

    by_class = getattr(estimate, "by_class", None) or {}
    for name, queue in (estimate.by_direction or {}).items():
        direction = _as_direction(name)
        if direction is None:
            continue
        lanes = lanes_by_dir.get(direction.value)
        if not lanes:
            continue
        class_counts = by_class.get(name)
        if class_counts:
            typed: list = []
            for cls, n in class_counts.items():
                typed.extend([_CLASS_VTYPE.get(cls, VehicleType.CAR)] * int(n))
            # Pad/truncate to the direction total (defensive: class sums from
            # older estimates may disagree by rounding).
            while len(typed) < queue.vehicle_count:
                typed.append(VehicleType.CAR)
            typed = typed[: queue.vehicle_count]
        else:
            typed = [VehicleType.CAR] * queue.vehicle_count
        for k, vtype in enumerate(typed):
            lane = lanes[k % len(lanes)]
            lane.vehicles.append(
                Vehicle(
                    id=next(_vid),
                    vehicle_type=vtype,
                    direction=direction,
                    lane=lane.lane_index,
                    position=5.0 + (k // len(lanes)) * 7.0,
                    speed=0.0,
                    target_speed=0.0,
                )
            )
        injected[direction.value] = injected.get(direction.value, 0) + queue.vehicle_count
    return injected


def decide(
    sim,
    intersection_id: str,
    manual: Optional[ManualRegistry] = None,
    emergency: Optional[EmergencyEvent] = None,
) -> dict[str, Any]:
    """Refresh the green plan from current lane demand and pick next phase.

    Priority (operator rule): an ACTIVE manual protocol on this route owns the
    signal — EVP preempts there are suppressed; elsewhere EVP forces its
    group green; otherwise the adaptive plan runs. ``mode`` reports which fired.
    """
    ix = sim.intersections[intersection_id]
    n_groups = len(ix.compatibility_groups)
    verdict = resolve_priority(intersection_id, None, manual, emergency)
    if verdict == "manual":
        mode = "manual"
        demands = sim._refresh_green_plan(ix)
        phase = ix.current_phase  # human owns the signal: hold, don't rotate
    elif verdict == "evp" and emergency is not None:
        mode = "evp"
        demands = sim._refresh_green_plan(ix)
        # Force the emergency group green (via yellow when mid-green, per the
        # all-red-clearance invariant the engine already enforces on switch).
        if ix.current_phase == f"{emergency.group_idx}_green":
            phase = ix.current_phase
        else:
            phase = f"{emergency.group_idx}_green"
        ix.current_phase = phase
        ix.phase_timer = 0.0
        sim._update_lane_signals(ix)
    else:
        mode = "adaptive"
        demands, phase = sim.decide(ix)
        ix.current_phase = phase
        ix.phase_timer = 0.0
        sim._update_lane_signals(ix)
    return {
        "phase": phase,
        "demands": demands,
        "mode": mode,
        "greens": {i: float(ix.signal_timing.get(f"{i}_green", 30)) for i in range(n_groups)},
    }


def actuate(
    stmp, sim, intersection_id: str, yellow_s: float = YELLOW_S, all_red_s: float = ALL_RED_S
) -> tuple[bool, NTCIPCycleConfig]:
    """Translate the engine's group-green plan into an NTCIP cycle + SET it.

    Phase number = group index + 1; red fills the remainder of the cycle —
    the same math as ``PUT /signals/{id}/timing`` in the API layer.
    """
    ix = sim.intersections[intersection_id]
    n = len(ix.compatibility_groups)
    greens = [float(ix.signal_timing.get(f"{i}_green", 30)) for i in range(n)]
    yellows = [float(ix.signal_timing.get(f"{i}_yellow", yellow_s)) for i in range(n)]
    cycle = sum(g + y + all_red_s for g, y in zip(greens, yellows))
    cfg = NTCIPCycleConfig(
        cycle_length=cycle,
        offset=0.0,
        phases=[
            NTCIPPhaseTiming(
                phase_number=i + 1,
                green_time=g,
                yellow_time=y,
                red_time=cycle - g - y - all_red_s,
            )
            for i, (g, y) in enumerate(zip(greens, yellows))
        ],
    )
    return bool(stmp.set_phase_timing(cfg)), cfg


def run_frame(
    pipe,
    sim,
    intersection_id: str,
    stmp,
    frame: Any,
    manual: Optional[ManualRegistry] = None,
    emergency: Optional[EmergencyEvent] = None,
) -> dict[str, Any]:
    """One closed-loop iteration: detect -> estimate -> decide -> actuate."""
    stages = pipe.process(frame)
    raw = stages.detections
    dets = raw.detections if hasattr(raw, "detections") else raw
    injected = inject_estimate(sim, intersection_id, stages.estimate)
    plan = decide(sim, intersection_id, manual=manual, emergency=emergency)
    ok, cfg = actuate(stmp, sim, intersection_id)
    return {
        "detected": len(dets),
        "queued": stages.estimate.total_vehicles,
        "injected": injected,
        "phase": plan["phase"],
        "demands": plan["demands"],
        "mode": plan["mode"],
        "greens": plan["greens"],
        "cycle_length": cfg.cycle_length,
        "actuated": ok,
        "stage_ms": dict(stages.stage_ms),
    }


def create_loop(
    sim_config: Optional[dict] = None, intersection_config: Optional[dict] = None, city_profile=None
):
    """Fresh (sim, intersection_id) pair for loops: default 4-way, adaptive."""
    from adaptive_traffic.core.simulation.engine import create_intersection, create_simulation

    sim = create_simulation({"adaptive_scheduling": True, **(sim_config or {})}, city_profile)
    ix = create_intersection({"id": "loop-1", **(intersection_config or {})}, city_profile)
    sim.add_intersection(ix)
    return sim, ix.id
