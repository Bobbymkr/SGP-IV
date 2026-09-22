"""
Robustness Evaluation
Evaluates controller performance under various incidents and conditions using city profile weights
"""

import logging
from dataclasses import dataclass
from typing import Dict, List, Optional

from adaptive_traffic.config.city_profile import CityProfile
from adaptive_traffic.core.control.controllers import BaseController, TrafficState
from adaptive_traffic.core.simulation.engine import (
    TrafficSimulation,
    create_intersection,
    create_simulation,
)

logger = logging.getLogger(__name__)


@dataclass
class IncidentScenario:
    """Incident scenario for robustness testing"""

    name: str
    description: str
    weight: float
    apply_fn: callable  # Function to apply incident to simulation


@dataclass
class RobustnessResult:
    """Result of robustness evaluation"""

    scenario_name: str
    base_waiting_time: float
    incident_waiting_time: float
    degradation_pct: float
    weight: float
    weighted_score: float
    passed: bool  # degradation < threshold


class RobustnessEvaluator:
    """Evaluates controller robustness under incidents"""

    def __init__(self, city_profile: CityProfile, config: Optional[Dict] = None):
        self.profile = city_profile
        self.config = config or {}
        self.incident_weights = city_profile.incident_weights
        self.degradation_threshold = self.config.get(
            "degradation_threshold", 0.5
        )  # 50% max degradation

        # Define incident scenarios
        self.incidents = self._create_incident_scenarios()

    def _create_incident_scenarios(self) -> List[IncidentScenario]:
        """Create incident scenarios weighted by city profile"""
        return [
            IncidentScenario(
                name="sensor_failure",
                description="Detector failure - reduced detection confidence",
                weight=self.incident_weights.sensor_failure,
                apply_fn=self._apply_sensor_failure,
            ),
            IncidentScenario(
                name="lane_block",
                description="Lane blockage - reduced capacity",
                weight=self.incident_weights.lane_block,
                apply_fn=self._apply_lane_block,
            ),
            IncidentScenario(
                name="power_outage",
                description="Power outage - signal fallback to fixed-time",
                weight=self.incident_weights.power_outage,
                apply_fn=self._apply_power_outage,
            ),
            IncidentScenario(
                name="weather_degradation",
                description="Adverse weather - reduced speeds and detection",
                weight=self.incident_weights.weather_degradation,
                apply_fn=self._apply_weather_degradation,
            ),
        ]

    def _apply_sensor_failure(self, sim: TrafficSimulation):
        """Simulate sensor failure by reducing detection confidence"""
        sim.weather_model.current().detection_confidence_factor *= 0.3
        logger.info("Applied sensor failure: detection confidence reduced to 30%")

    def _apply_lane_block(self, sim: TrafficSimulation):
        """Simulate lane blockage by reducing generation rate on one approach"""
        # Block one lane on first approach
        for intersection in sim.intersections.values():
            for lane_key, lane in intersection.lanes.items():
                if lane.lane_index == 0 and lane.direction.value == "north":
                    lane.signal_state = "red"  # Permanently red = blocked
                    break
        logger.info("Applied lane block: northbound lane 0 blocked")

    def _apply_power_outage(self, sim: TrafficSimulation):
        """Simulate power outage - force fixed-time control"""
        sim.adaptive_scheduling = False
        logger.info("Applied power outage: forced fixed-time scheduling")

    def _apply_weather_degradation(self, sim: TrafficSimulation):
        """Simulate adverse weather"""
        sim.weather_model.set_state("heavy_monsoon")
        logger.info("Applied weather degradation: heavy monsoon")

    def evaluate(
        self,
        controller: BaseController,
        sim_config: Dict,
        steps: int = 3000,
    ) -> List[RobustnessResult]:
        """Run robustness evaluation for all incidents"""
        results = []

        # Run baseline (no incident)
        logger.info("Running baseline simulation...")
        base_sim = create_simulation(sim_config)
        for intersection_config in sim_config.get("intersections", []):
            base_sim.add_intersection(create_intersection(intersection_config))

        base_waiting = self._run_simulation_with_controller(base_sim, controller, steps)

        # Run each incident scenario
        for incident in self.incidents:
            logger.info(f"Running incident scenario: {incident.name}")

            incident_sim = create_simulation(sim_config)
            for intersection_config in sim_config.get("intersections", []):
                incident_sim.add_intersection(create_intersection(intersection_config))

            # Apply incident
            incident.apply_fn(incident_sim)

            # Run simulation with incident
            incident_waiting = self._run_simulation_with_controller(incident_sim, controller, steps)

            # Calculate degradation
            if base_waiting > 0:
                degradation = (incident_waiting - base_waiting) / base_waiting
            else:
                degradation = 0.0

            weighted_score = degradation * incident.weight
            passed = degradation < self.degradation_threshold

            result = RobustnessResult(
                scenario_name=incident.name,
                base_waiting_time=base_waiting,
                incident_waiting_time=incident_waiting,
                degradation_pct=degradation * 100,
                weight=incident.weight,
                weighted_score=weighted_score,
                passed=passed,
            )
            results.append(result)

            logger.info(
                f"  {incident.name}: base={base_waiting:.1f}s, "
                f"incident={incident_waiting:.1f}s, "
                f"degradation={degradation*100:.1f}%, "
                f"weighted={weighted_score:.3f}, "
                f"passed={passed}"
            )

        return results

    def _run_simulation_with_controller(
        self,
        sim: TrafficSimulation,
        controller: BaseController,
        steps: int,
    ) -> float:
        """Run simulation with controller and return average waiting time"""
        # Reset controller if it has state
        if hasattr(controller, "reset"):
            controller.reset()

        for _ in range(steps):
            # Get traffic state from simulation
            for intersection_id, intersection in sim.intersections.items():
                state_data = sim.get_intersection_state(intersection_id)

                traffic_state = TrafficState(
                    queue_lengths=state_data.get("queues", {}),
                    flow_rates=state_data.get("flows", {}),
                    occupancy={d: 0.5 for d in state_data.get("queues", {})},
                    phase=state_data.get("signal_phase", ""),
                    time_in_phase=state_data.get("phase_timer", 0),
                )

                # Compute timing
                timing = controller.compute_timing(traffic_state)

                # Apply timing to intersection
                for i, (phase_name, duration) in enumerate(timing.green_times.items()):
                    intersection.signal_timing[f"{i}_green"] = duration
                intersection.signal_timing[f"{intersection.current_phase}_yellow"] = (
                    timing.yellow_time
                )

            sim.step()

        return sim.stats["total_waiting_time"] / max(sim.stats["total_completed"], 1)

    def get_summary(self, results: List[RobustnessResult]) -> Dict:
        """Get summary statistics"""
        total_weighted = sum(r.weighted_score for r in results)
        all_passed = all(r.passed for r in results)
        max_degradation = max(r.degradation_pct for r in results) if results else 0

        return {
            "total_weighted_score": total_weighted,
            "all_passed": all_passed,
            "max_degradation_pct": max_degradation,
            "num_scenarios": len(results),
            "passed_scenarios": sum(1 for r in results if r.passed),
        }


def create_robustness_evaluator(
    city_profile: CityProfile, config: Optional[Dict] = None
) -> RobustnessEvaluator:
    """Factory function to create robustness evaluator"""
    return RobustnessEvaluator(city_profile, config)
