"""
Traffic Simulation Engine

Topology-generic microscopic simulation with India-specific driver-behavior
modeling, synthetic weather effects, demand-responsive N-way signal scheduling,
and true-vs-observed queue observability (detection degradation).
"""

import logging
import random
from dataclasses import dataclass, field
from typing import Optional

import numpy as np

from adaptive_traffic.config.city_profile import CityProfile
from adaptive_traffic.core.domain import Direction, VehicleType
from adaptive_traffic.core.monitoring import observe
from adaptive_traffic.core.simulation.behavior import BehaviorEngine, profile_for
from adaptive_traffic.core.simulation.weather import WeatherModel, WeatherState

logger = logging.getLogger(__name__)


@dataclass
class Vehicle:
    """Vehicle in simulation"""

    id: int
    vehicle_type: VehicleType
    direction: Direction
    lane: int
    position: float  # Distance from stop line (meters)
    speed: float  # m/s
    target_speed: float
    acceleration: float = 0.0
    waiting_time: float = 0.0
    route: list[Direction] = field(default_factory=list)
    current_target: Direction | None = None
    wrong_side: bool = False
    violating: bool = False
    violation_checked: bool = False
    encroachment_offset: float = 0.0


@dataclass
class Lane:
    """Lane in simulation"""

    direction: Direction
    lane_index: int
    length: float  # meters
    vehicles: list[Vehicle] = field(default_factory=list)
    stop_line: float = 0.0
    signal_state: str = "red"  # red, yellow, green


@dataclass
class Intersection:
    """Intersection with approaches, lanes, compatibility groups and signal control"""

    id: str
    lanes: dict[str, Lane]  # key: "direction_laneIndex"
    signal_timing: dict[str, float]  # phase name -> duration
    current_phase: str = ""
    phase_timer: float = 0.0
    approaches: list[Direction] = field(
        default_factory=lambda: [Direction.NORTH, Direction.SOUTH, Direction.EAST, Direction.WEST]
    )
    compatibility_groups: list[list[Direction]] = field(default_factory=list)
    phase_sequence: list[str] = field(default_factory=list)

    def __post_init__(self):
        if not self.compatibility_groups:
            self.compatibility_groups = _default_compatibility_groups(self.approaches)
        if not self.phase_sequence:
            seq = []
            for i in range(len(self.compatibility_groups)):
                seq.append(f"{i}_green")
                seq.append(f"{i}_yellow")
            self.phase_sequence = seq
        if self.current_phase not in self.phase_sequence:
            self.current_phase = self.phase_sequence[0]


def _default_compatibility_groups(approaches: list[Direction]) -> list[list[Direction]]:
    """Opposite directions may share green; everything else served separately."""
    pairs = [(Direction.NORTH, Direction.SOUTH), (Direction.EAST, Direction.WEST)]
    remaining = list(approaches)
    groups: list[list[Direction]] = []
    for a, b in pairs:
        shared = [d for d in (a, b) if d in remaining]
        for d in shared:
            remaining.remove(d)
        if shared:
            groups.append(shared)
    for d in remaining:
        groups.append([d])
    return groups


class TrafficSimulation:
    """Microscopic traffic simulation"""

    def __init__(self, config: dict, city_profile: Optional[CityProfile] = None):
        self.config = config
        self.city_profile = city_profile
        self.dt = config.get("time_step", 0.1)  # seconds
        self.simulation_time = 0.0
        self.max_time = config.get("max_time", 3600)  # seconds
        self.rng = random.Random(config.get("seed", 42))
        self.adaptive_scheduling = config.get("adaptive_scheduling", True)

        # Use city profile for behavior and weather if available
        behavior_preset = (
            city_profile.behavior_preset
            if city_profile
            else config.get("behavior_preset", "typical_urban")
        )
        weather_state = (
            city_profile.weather_profile if city_profile else config.get("weather_state", "clear")
        )

        self.behavior_engine = BehaviorEngine(behavior_preset, rng=self.rng)
        self.weather_model = WeatherModel(WeatherState(weather_state))

        # Vehicle properties by type - use city profile if available
        if city_profile:
            self.vehicle_properties = {
                VehicleType.CAR: {
                    "length": city_profile.vehicle_lengths.car,
                    "max_speed": 16.7,
                    "accel": 2.5,
                    "decel": 4.5,
                },
                VehicleType.BUS: {
                    "length": city_profile.vehicle_lengths.bus,
                    "max_speed": 13.9,
                    "accel": 1.5,
                    "decel": 3.5,
                },
                VehicleType.TRUCK: {
                    "length": city_profile.vehicle_lengths.truck,
                    "max_speed": 11.1,
                    "accel": 1.2,
                    "decel": 3.0,
                },
                VehicleType.MOTORCYCLE: {
                    "length": city_profile.vehicle_lengths.two_wheeler,
                    "max_speed": 22.2,
                    "accel": 3.5,
                    "decel": 5.0,
                },
                VehicleType.BICYCLE: {
                    "length": city_profile.vehicle_lengths.cycle,
                    "max_speed": 5.6,
                    "accel": 1.0,
                    "decel": 2.5,
                },
                VehicleType.AUTO: {
                    "length": city_profile.vehicle_lengths.autorickshaw,
                    "max_speed": 13.9,
                    "accel": 2.2,
                    "decel": 4.0,
                },
            }
            # Generation rates from vehicle mix
            mix = city_profile.vehicle_mix
            total_rate = config.get("total_generation_rate", 2000)
            self.generation_rates = {
                Direction.NORTH: total_rate * 0.25,
                Direction.SOUTH: total_rate * 0.25,
                Direction.EAST: total_rate * 0.25,
                Direction.WEST: total_rate * 0.25,
            }
        else:
            # Vehicle properties by type (defaults)
            self.vehicle_properties = {
                VehicleType.CAR: {"length": 4.5, "max_speed": 16.7, "accel": 2.5, "decel": 4.5},
                VehicleType.BUS: {"length": 12.0, "max_speed": 13.9, "accel": 1.5, "decel": 3.5},
                VehicleType.TRUCK: {"length": 10.0, "max_speed": 11.1, "accel": 1.2, "decel": 3.0},
                VehicleType.MOTORCYCLE: {
                    "length": 2.0,
                    "max_speed": 22.2,
                    "accel": 3.5,
                    "decel": 5.0,
                },
                VehicleType.BICYCLE: {"length": 1.8, "max_speed": 5.6, "accel": 1.0, "decel": 2.5},
                VehicleType.AUTO: {"length": 3.0, "max_speed": 13.9, "accel": 2.2, "decel": 4.0},
            }

            self._speed_compliance = {
                vt: profile_for(vt).speed_compliance_factor for vt in VehicleType
            }

            # Generation rates (vehicles/hour per approach)
            self.generation_rates = config.get(
                "generation_rates",
                {
                    Direction.NORTH: 600,
                    Direction.SOUTH: 600,
                    Direction.EAST: 400,
                    Direction.WEST: 400,
                },
            )

        self.intersections: dict[str, Intersection] = {}
        self.vehicles: list[Vehicle] = []
        self.vehicle_counter = 0
        self.vehicle_id_map: dict[int, Vehicle] = {}

        self._queue_error_sum = 0.0
        self._queue_error_n = 0

        # Step 2 event-trigger cache: last demands + preempt cadence per intersection
        self._demand_cache: dict[str, list[int]] = {}
        self._preempt_tick: dict[str, int] = {}
        # Starvation bound: greens since each group was last served
        self._wait_count: dict[str, list[int]] = {}

        # Statistics
        self.stats = {
            "total_generated": 0,
            "total_completed": 0,
            "total_waiting_time": 0.0,
            "total_travel_time": 0.0,
            "avg_speed": 0.0,
            "true_queue_length": 0,
            "observed_queue_length": 0,
            "queue_error": 0.0,
        }

    @property
    def behavior_preset(self) -> str:
        return self.behavior_engine.preset_name

    def add_intersection(self, intersection: Intersection):
        """Add intersection to simulation"""
        self.intersections[intersection.id] = intersection
        for lane in intersection.lanes.values():
            lane.vehicles = []
            lane.signal_state = "red"

    def step(self):
        """Advance simulation by one time step"""
        self.simulation_time += self.dt
        self.weather_model.step(self.simulation_time)
        self._update_signals()
        self._generate_vehicles()
        self._update_vehicles()
        self._remove_completed_vehicles()
        self._update_statistics()

    def _green_bounds(self) -> tuple[float, float]:
        """Min/max green seconds: city profile wins, else Indian defaults (7/50)."""
        bounds = self.city_profile.signal_bounds if self.city_profile else None
        if bounds is not None:
            return (float(bounds.min_green), float(bounds.max_green))
        return (7.0, 50.0)

    def _group_green_times(
        self, intersection: Intersection, demands: list[int]
    ) -> dict[int, float]:
        """Demand-following green durations per compatibility group.

        green = queued_vehicles * headway + startup lost time, clamped to
        green bounds. Unlike a fixed-budget proportional split (which holds
        cycles long under light demand and inflates waits), the cycle breathes:
        light demand -> short greens -> short reds for everyone. This is the
        discharge half of Webster's insight; headway 2.0s/veh is the Indian
        saturation value used across this codebase.
        """
        lo, hi = self._green_bounds()
        base = self.config.get("green_time", 30)
        headway = self.config.get("discharge_headway_s", 2.0)
        startup = self.config.get("startup_lost_s", 2.0)
        # Efficiency floor: chopping greens below ~3x yellow wastes the cycle
        # on lost time (measured: x4way_disciplined 6.5 -> 9.3 without it).
        floor = self.config.get("efficient_floor_s", 15.0)
        out = {}
        for i, d in enumerate(demands):
            if d <= 0:
                out[i] = float(base)
            else:
                out[i] = max(floor, max(lo, min(hi, d * headway + startup)))
        return out

    @observe("decide")
    def _refresh_green_plan(self, intersection: Intersection) -> list[int]:
        """Recompute demands + durations, cache the plan. Returns demands."""
        demands = [
            self._group_demand(intersection, g)
            for g in intersection.compatibility_groups
        ]
        if self.adaptive_scheduling:
            for idx, green in self._group_green_times(intersection, demands).items():
                intersection.signal_timing[f"{idx}_green"] = green
        self._demand_cache[intersection.id] = demands
        return demands

    def _maybe_preempt(self, intersection: Intersection) -> None:
        """Mid-phase early-cut check (event-driven, cached plan).

        Only fires on green phases past min-green: if another group's demand
        exceeds the current group's by >25%, cut to yellow now instead of
        serving a stale full green. Cheap int compare, ~1s sim cadence.
        """
        if not self.adaptive_scheduling:
            return
        phase = intersection.current_phase
        if not phase.endswith("_green"):
            return
        lo, _ = self._green_bounds()
        if intersection.phase_timer < lo:
            return
        # ~1s cadence: skip ticks inside the same whole second
        tick = int(intersection.phase_timer / 1.0)
        if self._preempt_tick.get(intersection.id) == tick:
            return
        self._preempt_tick[intersection.id] = tick
        cur_idx = int(phase.split("_", 1)[0])
        demands = [
            self._group_demand(intersection, g)
            for g in intersection.compatibility_groups
        ]
        self._demand_cache[intersection.id] = demands
        cur = demands[cur_idx]
        best_other = max(
            (d for i, d in enumerate(demands) if i != cur_idx), default=0
        )
        if best_other > cur and (best_other - cur) / max(cur, 1) > 0.25:
            intersection.current_phase = f"{cur_idx}_yellow"
            intersection.phase_timer = 0.0
            self._update_lane_signals(intersection)

    def _update_signals(self):
        """Update traffic signal states"""
        for intersection in self.intersections.values():
            intersection.phase_timer += self.dt
            phase_duration = intersection.signal_timing.get(intersection.current_phase, 30)
            if intersection.phase_timer >= phase_duration:
                intersection.current_phase = self._next_phase(intersection)
                intersection.phase_timer = 0.0
                if intersection.current_phase.endswith("_green"):
                    self._refresh_green_plan(intersection)
                self._update_lane_signals(intersection)
            else:
                self._maybe_preempt(intersection)

    def _group_demand(self, intersection: Intersection, group: list[Direction]) -> int:
        demand = 0
        for lane in intersection.lanes.values():
            if lane.direction in group:
                demand += sum(1 for v in lane.vehicles if v.speed < 1.0 and v.position < 50)
        return demand

    @observe("decide")
    def _next_phase(self, intersection: Intersection) -> str:
        """Pick next phase.

        Fixed mode: strict round-robin (untouched baseline).
        Adaptive mode: rotate, skipping zero-demand groups (D7 empty-skip),
        with Webster-proportional durations set by _refresh_green_plan.
        Rotation (not argmax) avoids starving small groups: a singleton's
        demand can never exceed a pair's sum, so greedy order + short greens
        spirals (x3way 6.0 -> 7.8); rotation + proportional durations gives
        the fairness of fixed timing with demand-sized greens.
        """
        current_idx = intersection.phase_sequence.index(intersection.current_phase)
        cur_group_idx = current_idx // 2
        n_groups = len(intersection.compatibility_groups)
        # Yellow always follows its green before switching groups
        if current_idx % 2 == 0:
            return f"{cur_group_idx}_yellow"
        if not self.adaptive_scheduling:
            next_group = (cur_group_idx + 1) % n_groups
            return f"{next_group}_green"
        demands = [self._group_demand(intersection, g) for g in intersection.compatibility_groups]
        waits = self._wait_count.setdefault(
            intersection.id, [0] * n_groups
        )
        # Starvation bound: a group with demand waiting a full rotation jumps
        # the queue (longest wait first). Otherwise argmax demand. Zero-demand
        # groups are never served (D7 empty-skip); all-zero stays put.
        forced = [i for i in range(n_groups) if demands[i] > 0 and waits[i] >= n_groups]
        if forced:
            best_idx = max(forced, key=lambda i: waits[i])
        else:
            best_idx, best_demand = -1, 0
            for i, d in enumerate(demands):
                if d > best_demand:
                    best_idx, best_demand = i, d
            if best_idx == -1:
                self._wait_count[intersection.id] = [0] * n_groups
                return f"{cur_group_idx}_green"  # nothing waiting: stay, reset debt
        for i in range(n_groups):
            waits[i] += 1
        waits[best_idx] = 0
        return f"{best_idx}_green"

    @observe("actuate")
    def _update_lane_signals(self, intersection: Intersection):
        """Update lane signal states based on current phase group"""
        idx = intersection.phase_sequence.index(intersection.current_phase)
        group_idx = idx // 2
        state = intersection.current_phase.split("_", 1)[1]
        active = set(intersection.compatibility_groups[group_idx])
        for lane in intersection.lanes.values():
            lane.signal_state = state if lane.direction in active else "red"

    def _generate_vehicles(self):
        """Generate new vehicles based on rates"""
        weather_profile = self.weather_model.current()
        for direction, base_rate in self.generation_rates.items():
            rate_per_hour = self.weather_model.apply_to_generation_rate(base_rate)
            rate_per_step = rate_per_hour * self.dt / 3600
            if self.rng.random() < rate_per_step:
                self._create_vehicle(direction)

    def _create_vehicle(self, direction: Direction):
        """Create a new vehicle"""
        vtype = self.rng.choices(list(VehicleType), weights=[0.55, 0.05, 0.08, 0.17, 0.10, 0.05])[0]

        props = self.vehicle_properties[vtype]

        for intersection in self.intersections.values():
            for lane_key, lane in intersection.lanes.items():
                if lane.direction == direction and lane.lane_index == 0:
                    entry_pos = lane.length
                    can_spawn = True
                    for veh in lane.vehicles:
                        if veh.position > entry_pos - props["length"] - 2:
                            can_spawn = False
                            break

                    if can_spawn:
                        anomaly = self.behavior_engine.sample_spawn_anomaly(vtype)
                        target_speed = (
                            props["max_speed"]
                            * self.weather_model.current().speed_multiplier
                            * self._speed_compliance[vtype]
                        )
                        vehicle = Vehicle(
                            id=self.vehicle_counter,
                            vehicle_type=vtype,
                            direction=direction,
                            lane=lane.lane_index,
                            position=entry_pos,
                            speed=0.0,
                            target_speed=target_speed,
                            current_target=direction,
                            wrong_side=(anomaly == "wrong_side"),
                        )

                        lane.vehicles.append(vehicle)
                        self.vehicles.append(vehicle)
                        self.vehicle_id_map[vehicle.id] = vehicle
                        self.vehicle_counter += 1
                        self.stats["total_generated"] += 1
                        return

    def _update_vehicles(self):
        """Update all vehicle positions and states"""
        for intersection in self.intersections.values():
            for lane_key, lane in intersection.lanes.items():
                self._update_lane_vehicles(lane, intersection)

    def _update_lane_vehicles(self, lane: Lane, intersection: Intersection):
        """Update vehicles in a single lane"""
        lane.vehicles.sort(key=lambda v: v.position)

        for i, vehicle in enumerate(lane.vehicles):
            props = self.vehicle_properties[vehicle.vehicle_type]

            if self.behavior_engine.maybe_lane_drift(vehicle.vehicle_type, self.rng):
                moved = self._try_lane_drift(vehicle, lane, intersection)
                if moved:
                    continue

            target_speed = self._calculate_target_speed(vehicle, lane, i, intersection)

            if vehicle.speed < target_speed:
                vehicle.acceleration = min(props["accel"], (target_speed - vehicle.speed) / self.dt)
            else:
                decel_cap = props["decel"] * self.weather_model.current().braking_decel_multiplier
                vehicle.acceleration = max(-decel_cap, (target_speed - vehicle.speed) / self.dt)

            vehicle.speed = max(0, vehicle.speed + vehicle.acceleration * self.dt)
            vehicle.position -= vehicle.speed * self.dt

            if vehicle.speed < 0.5:
                vehicle.waiting_time += self.dt
                self.stats["total_waiting_time"] += self.dt
                if (
                    lane.signal_state == "red"
                    and not vehicle.violating
                    and vehicle.position < 1.5
                    and vehicle.encroachment_offset == 0.0
                ):
                    offset = self.behavior_engine.encroachment_offset_m(
                        vehicle.vehicle_type, self.rng
                    )
                    if offset > 0:
                        # ponytail: offset recorded not applied — applying it would
                        # push position <= 0 and delete the vehicle; queue observer
                        # treats >1m offsets as inside camera dead zone instead
                        vehicle.encroachment_offset = min(offset, 2.5)

            if vehicle.position <= 0:
                # Vehicle will be removed in _remove_completed_vehicles
                vehicle.position = 0

    def _try_lane_drift(self, vehicle: Vehicle, lane: Lane, intersection: Intersection) -> bool:
        """Move vehicle into an adjacent lane of the same direction if space allows."""
        for new_idx in (vehicle.lane + 1, vehicle.lane - 1):
            target_key = f"{lane.direction.value}_{new_idx}"
            target_lane = intersection.lanes.get(target_key)
            if target_lane is None:
                continue
            gap_ok = all(abs(v.position - vehicle.position) > 6.0 for v in target_lane.vehicles)
            if gap_ok:
                lane.vehicles.remove(vehicle)
                target_lane.vehicles.append(vehicle)
                vehicle.lane = new_idx
                return True
        return False

    def _calculate_target_speed(
        self, vehicle: Vehicle, lane: Lane, index: int, intersection: Intersection
    ) -> float:
        """Calculate target speed for a vehicle"""
        props = self.vehicle_properties[vehicle.vehicle_type]
        max_speed = (
            props["max_speed"]
            * self.weather_model.current().speed_multiplier
            * self._speed_compliance[vehicle.vehicle_type]
        )

        if lane.signal_state == "red" and vehicle.position < 30:
            if not vehicle.violating:
                if not vehicle.violation_checked:
                    vehicle.violation_checked = True
                    if self.behavior_engine.maybe_violate_red(vehicle.vehicle_type, self.rng):
                        vehicle.violating = True
                        logger.debug("vehicle %s ran red light", vehicle.id)
                else:
                    return 0.0
            if not vehicle.violating:
                return 0.0

        elif lane.signal_state == "yellow" and vehicle.position < 20:
            return min(vehicle.speed, max_speed * 0.5)

        if index > 0:
            leader = lane.vehicles[index - 1]
            gap = leader.position - vehicle.position - props["length"]

            if gap < 10:
                return min(vehicle.speed, leader.speed * 0.9)
            elif gap < 20:
                return min(vehicle.speed, leader.speed * 1.1)

        return max_speed

    def _remove_completed_vehicles(self):
        """Remove vehicles that have passed through the intersection"""
        for intersection in self.intersections.values():
            for lane_key, lane in intersection.lanes.items():
                completed = [v for v in lane.vehicles if v.position <= 0]
                for v in completed:
                    lane.vehicles.remove(v)
                    self.vehicles.remove(v)
                    del self.vehicle_id_map[v.id]
                    self.stats["total_completed"] += 1

    def _waiting_vehicles(self) -> list[Vehicle]:
        return [v for v in self.vehicles if v.speed < 1.0 and v.position < 50]

    def _update_statistics(self):
        """Update simulation statistics including queue observability."""
        if self.vehicles:
            self.stats["avg_speed"] = np.mean([v.speed for v in self.vehicles])

        waiting = self._waiting_vehicles()
        detection_conf = self.weather_model.current().detection_confidence_factor
        observed = 0
        for v in waiting:
            if v.encroachment_offset > 1.0:
                # ponytail: hard cutoff models camera line-of-sight loss; replace
                # with per-camera geometry model if eval shows error curve too coarse
                continue
            if self.rng.random() < detection_conf:
                observed += 1

        self.stats["true_queue_length"] = len(waiting)
        self.stats["observed_queue_length"] = observed
        self._queue_error_sum += abs(len(waiting) - observed)
        self._queue_error_n += 1
        self.stats["queue_error"] = self._queue_error_sum / max(self._queue_error_n, 1)

    def get_intersection_state(self, intersection_id: str) -> dict:
        """Get current state of an intersection"""
        if intersection_id not in self.intersections:
            return {}

        intersection = self.intersections[intersection_id]

        queues_true: dict[str, int] = {}
        queues_observed: dict[str, int] = {}
        flows: dict[str, int] = {}
        detection_conf = self.weather_model.current().detection_confidence_factor

        for lane in intersection.lanes.values():
            direction = lane.direction.value
            waiting_true = [v for v in lane.vehicles if v.speed < 1.0 and v.position < 50]
            queues_true[direction] = queues_true.get(direction, 0) + len(waiting_true)
            observed = sum(
                1
                for v in waiting_true
                if v.encroachment_offset <= 1.0 and self.rng.random() < detection_conf
            )
            queues_observed[direction] = queues_observed.get(direction, 0) + observed
            moving = sum(1 for v in lane.vehicles if v.speed > 1.0 and v.position < 30)
            flows[direction] = flows.get(direction, 0) + moving * 3600

        idx = intersection.phase_sequence.index(intersection.current_phase)
        return {
            "queues": queues_true,
            "queues_observed": queues_observed,
            "flows": flows,
            "signal_phase": intersection.current_phase,
            "current_group_index": idx // 2,
            "active_approaches": [d.value for d in intersection.compatibility_groups[idx // 2]],
            "compatibility_groups": [
                [d.value for d in g] for g in intersection.compatibility_groups
            ],
            "phase_timer": intersection.phase_timer,
        }

    def get_network_stats(self) -> dict:
        """Get overall network statistics"""
        return {
            "simulation_time": self.simulation_time,
            "active_vehicles": len(self.vehicles),
            "total_generated": self.stats["total_generated"],
            "total_completed": self.stats["total_completed"],
            "avg_waiting_time": self.stats["total_waiting_time"]
            / max(self.stats["total_completed"], 1),
            "avg_speed": self.stats["avg_speed"],
            "throughput": self.stats["total_completed"]
            / max(self.simulation_time / 3600, 1 / 3600),
            "behavior_preset": self.behavior_engine.preset_name,
            "weather_state": self.weather_model.current().state.value,
            "adaptive_scheduling": self.adaptive_scheduling,
            "true_queue_length": self.stats["true_queue_length"],
            "observed_queue_length": self.stats["observed_queue_length"],
            "queue_error": self.stats["queue_error"],
        }


def create_intersection(config: dict, city_profile: Optional[CityProfile] = None) -> Intersection:
    """Factory function to create intersection"""
    approach_names = config.get("approaches", ["north", "south", "east", "west"])
    approaches = [Direction[a.upper()] for a in approach_names]

    # Use city profile for lanes per direction
    lanes_per_direction = (
        city_profile.lanes_per_approach if city_profile else config.get("lanes_per_direction", 2)
    )

    lanes = {}
    for direction in approaches:
        for lane_idx in range(lanes_per_direction):
            lane_key = f"{direction.value}_{lane_idx}"
            lanes[lane_key] = Lane(
                direction=direction,
                lane_index=lane_idx,
                length=config.get("lane_length", 200),
                stop_line=0.0,
            )

    raw_groups = config.get("compatibility_groups")
    if raw_groups is not None:
        compatibility_groups = [[Direction[d.upper()] for d in g] for g in raw_groups]
    elif "signal_timing" in config and any(
        k.startswith(("NS_", "EW_")) for k in config["signal_timing"]
    ):
        # legacy NS/EW config
        compatibility_groups = [
            [d for d in approaches if d in (Direction.NORTH, Direction.SOUTH)],
            [d for d in approaches if d in (Direction.EAST, Direction.WEST)],
        ]
        compatibility_groups = [g for g in compatibility_groups if g]
    else:
        compatibility_groups = _default_compatibility_groups(approaches)

    legacy_timing = config.get("signal_timing")
    if legacy_timing and not any(k.startswith(("NS_", "EW_")) for k in legacy_timing):
        signal_timing = dict(legacy_timing)
    else:
        signal_timing = {}
        green = config.get("green_time", 30)
        yellow = config.get("yellow_time", 5)
        for i in range(len(compatibility_groups)):
            signal_timing[f"{i}_green"] = green
            signal_timing[f"{i}_yellow"] = yellow

    return Intersection(
        id=config.get("id", "main"),
        lanes=lanes,
        signal_timing=signal_timing,
        approaches=approaches,
        compatibility_groups=compatibility_groups,
    )


def create_simulation(
    config: dict, city_profile: Optional[CityProfile] = None
) -> TrafficSimulation:
    """Factory function to create simulation"""
    return TrafficSimulation(config, city_profile)
