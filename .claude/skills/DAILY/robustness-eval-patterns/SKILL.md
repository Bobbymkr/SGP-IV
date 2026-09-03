---
name: robustness-eval-patterns
description: "Project-specific patterns for T-REX style robustness testing and evaluation."
---

# Robustness Evaluation Patterns

Project-specific patterns for T-REX style robustness testing and evaluation.
Based on andngdtudk/T-REX, Traffic-Alpha robustness metrics, and academic evaluation suites.
**Adapted for Indian traffic systems - India-specific incident taxonomy.**

## Incident Taxonomy (T-REX + India-Specific)

| Incident Type | Description | Frequency | Severity |
|--------------|-------------|-----------|----------|
| `accident` | Vehicle collision blocks lanes | 10% of runs | CRITICAL |
| `lane_block` | Vehicle breaks down, blocks lane | 15% of runs | HIGH |
| `emergency` | Ambulance/police priority request | 5% of runs | HIGH |
| `rerouting` | GPS recalculates routes, distributes traffic | 20% of runs | MEDIUM |
| `sensor_failure` | YOLO detection drops 50% | 8% of runs | MEDIUM |
| `communication_loss` | NTCIP messages drop 100% | 3% of runs | HIGH |
| `dr_behavior` | Human drivers adapt (ICM rerouting) | 25% of runs | MEDIUM |
| `power_failure` | Controller loses power, fallback | 2% of runs | CRITICAL |

### India-Specific Incident Types (ADDED)

| Incident Type | Description | Frequency | Severity |
|--------------|-------------|-----------|----------|
| `autorickshaw_block` | Autorickshaw/taxi breakdown blocks 1-2 lanes | 12% of runs | HIGH |
| `cattle_on_road` | Cattle/animals on road (rural/peri-urban) | 5% of runs | CRITICAL |
| `religious_crowd` | Temple/mosque/church vicinity - high pedestrian/vehicle mix | 8% of runs | MEDIUM |
| `political_rally` | Protest/demonstration causing traffic disruption | 3% of runs | HIGH |
| `monsoon_flooding` | Waterlogging from seasonal rains - road submerged | 10% of runs (Jun-Sep) | CRITICAL |

**Augmented incident list** (original 8 + 5 India-specific):
```python
incidents = [
    "accident",           # stays - generic
    "lane_block",         # stays
    "sensor_failure",     # stays
    "emergency",          # stays
    "rerouting",          # stays
    "autorickshaw_block", # NEW - most common Indian breakdown
    "cattle_on_road",     # NEW - rural roads, especially NH highways
    "religious_crowd",    # NEW - temple/mosque/church vicinity
    "political_rally",    # NEW - protest/demonstration traffic
    "monsoon_flooding",   # NEW - waterlogging-induced closures (Jun-Sep)
]
```

## Robustness Test Wrapper - India Adaptations

```python
import numpy as np
from typing import List, Dict, Any, Callable
import json
import time

class RobustnessTestConfig:
    """Configuration for robustness testing - India adapted"""
    def __init__(self,
                 incidents: List[str] = None,
                 num_runs: int = 30,
                 duration_seconds: int = 3600,  # 1 hour sim
                 sim_speed: float = 30.0,  # 30x realtime
                 output_dir: str = "tests/robustness/results",
                 monsoon_months=(6, 7, 8, 9)):  # June-September
        self.incidents = incidents or [
            "accident", "lane_block", "sensor_failure",
            "autorickshaw_block", "cattle_on_road"  # include India types
        ]
        self.num_runs = num_runs
        self.duration = duration_seconds
        self.speed = sim_speed
        self.output_dir = output_dir
        self.monsoon_months = monsoon_months

    def is_monsoon_season(self, current_month: int) -> bool:
        """Check if current simulation month is monsoon season"""
        return current_month in self.monsoon_months

class IncidentInjector:
    """Inject incidents into simulation at specified times - India adapted"""

    def __init__(self, sim, incident_configs: Dict[str, Dict],
                 monsoon_months=(6, 7, 8, 9)):
        self.incidents = incident_configs
        self.monsoon_months = monsoon_months
        self.active = False
        self.current_month = 6  # would be set from sim calendar

    def set_current_month(self, month: int):
        self.current_month = month

    def inject(self, sim, current_time: float):
        """Check and inject incidents at current simulation time"""
        if not self.active:
            return

        # Check monsoon season for flooding incident
        is_monsoon = self.is_monsoon_season(self.current_month)

        for incident_type, config in self.incidents.items():
            if current_time >= config["time"] and not getattr(self, f"_{incident_type}_active", False):
                # Skip monsoon flooding outside monsoon season (unless forced)
                if incident_type == "monsoon_flooding" and not is_monsoon:
                    # Option: still inject but with lower probability
                    pass  # or continue to skip

                self._apply_incident(sim, incident_type, config)
                setattr(self, f"_{incident_type}_active", True)

    def is_monsoon_season(self, month: int) -> bool:
        return month in self.monsoon_months

    def _apply_incident(self, sim, incident_type: str, config: Dict):
        """Apply specific incident to simulation - India adapted"""
        if incident_type == "accident":
            sim.block_lanes("east", n_lanes=2, duration=config["duration"])
            print(f"[INCIDENT] Accident blocks east lanes for {config['duration']}s")

        elif incident_type == "lane_block":
            sim.block_lane("south", lane_idx=0, duration=config["duration"])
            print(f"[INCIDENT] Lane block on south lane for {config['duration']}s")

        elif incident_type == "sensor_failure":
            sim.reduce_detection_confidence(severity=config.get("severity", 0.5))
            print(f"[INCIDENT] Sensor failure, confidence reduced by {config.get('severity', 0.5)*100:.0f}%")

        elif incident_type == "emergency":
            sim.trigger_emergency_priority(duration=config.get("duration", 60))
            print(f"[INCIDENT] Emergency priority request")

        elif incident_type == "rerouting":
            sim.simulate_rerouting(adaptation_factor=0.3)
            print(f"[INCIDENT] Rerouting activated")

        elif incident_type == "autorickshaw_block":
            # Autorickshaw is India's most common breakdown vehicle
            sim.block_lane("south", lane_idx=1, duration=config["duration"])
            # Autorickshaws often block inner lane; print notification
            print(f"[INCIDENT] Autorickshaw blocks inner lane for {config['duration']}s")

        elif incident_type == "cattle_on_road":
            # Cattle on road - common on Indian highways (NH 44, NH 19 etc.)
            sim.block_all_lanes("east", duration=config["duration"])
            print(f"[INCIDENT] Cattle on road blocks all east lanes for {config['duration']}s")

        elif incident_type == "religious_crowd":
            # Temple/mosque/church vicinity - high pedestrian density
            sim.reduce_speed_limit(30)  # Reduce to 30 km/h
            sim.increase_pedestrian_count(n_additional=50)
            print(f"[INCIDENT] Religious crowd - reduced speed, added pedestrians")

        elif incident_type == "political_rally":
            # Protest/demonstration - multi-intersection impact
            sim.block_intersection_approach("north", n_lanes=3, duration=config["duration"])
            print(f"[INCIDENT] Political rally blocks north approach for {config['duration']}s")

        elif incident_type == "monsoon_flooding":
            # Only during monsoon season (Jun-Sep)
            if self.is_monsoon_season(self.current_month):
                sim.flood_road("west", water_depth=config.get("water_depth", 0.5))
                sim.reduce_detection_confidence(severity=0.7)  # Heavy rain affects sensors
                print(f"[INCIDENT] Monsoon flooding - waterlogged west road, depth={config.get('water_depth', 0.5)}m")
            else:
                # Outside monsoon - still inject but as generic lane block
                sim.block_lanes("west", n_lanes=1, duration=config["duration"])
                print(f"[INCIDENT] Lane block (forced) on west for {config['duration']}s")

    def reset_incident(self, incident_type: str):
        """Reset incident state for re-testing"""
        if hasattr(self, f"_{incident_type}_active"):
            delattr(self, f"_{incident_type}_active")

class RobustnessEvaluator:
    """Run full robustness suite and generate India-adapted reports"""

    def __init__(self,
                 sim_config,
                 controller,
                 evaluator_config: RobustnessTestConfig):
        self.sim_config = sim_config
        self.controller = controller
        self.test_config = evaluator_config
        self.results = []

    def run_suite(self) -> Dict[str, Any]:
        """Run full robustness evaluation suite - India adapted"""
        print(f"Starting robustness evaluation: {self.test_config.num_runs} runs")
        print(f"Incidents: {self.test_config.incidents}")
        print(f"Duration per run: {self.test_config.duration // 3600}h "
              f"(@ {self.test_config.speed}x speed)")
        print("-" * 60)

        successful_runs = 0
        all_metrics = []

        for run_idx in range(self.test_config.num_runs):
            run_start = time.time()

            # Create fresh simulation + controller
            sim = self._create_simulation(run_idx)
            ctrl = self._create_controller(sim, run_idx)

            # Set monsoon month for this run (cycle through months)
            monsoon_month = (run_idx % 12) + 1  # cycle 1-12
            self._injector.set_current_month(monsoon_month)

            # Run simulation
            metrics = self._run_simulation(sim, ctrl, run_idx)

            # Post-process
            metrics["run_index"] = run_idx
            metrics["duration_sec"] = time.time() - run_start
            metrics["sim_speed"] = self.test_config.speed
            metrics["monsoon_month"] = monsoon_month

            self.results.append(metrics)
            successful_runs += 1

            # Progress
            if (run_idx + 1) % 10 == 0:
                print(f"  Completed {run_idx + 1}/{self.test_config.num_runs} runs")

        # Generate aggregate report - India adapted
        report = self._generate_report()
        return report

    def _run_simulation(self, sim, ctrl, run_idx: int) -> Dict:
        """Run single simulation with incident handling - India adapted"""
        metrics = {
            "total_wait": 0.0,
            "max_queue": 0.0,
            "throughput": 0.0,
            "incidents": [],
            "recovery_time": 0.0,
            "phase_stability": 0.0,
            "monsoon_month": self.test_config.is_monsoon_season(
                (run_idx % 12) + 1) if hasattr(self, '_injector') else False,
        }

        cycle_count = 0
        max_cycles = int(self.test_config.duration * self.test_config.speed)

        # Incident tracking - India augmented
        injector = IncidentInjector(sim,
            {"accident": {"time": 600, "duration": 300},
             "lane_block": {"time": 300, "duration": 180},
             "sensor_failure": {"time": 1200, "duration": 180},
             "autorickshaw_block": {"time": 480, "duration": 240},
             "cattle_on_road": {"time": 600, "duration": 300},
             "religious_crowd": {"time": 360, "duration": 120},
             "political_rally": {"time": 900, "duration": 360},
             "monsoon_flooding": {"time": 600, "duration": 480}})
        injector.set_current_month((run_idx % 12) + 1)

        while sim.running and cycle_count < max_cycles:
            current_time = sim.time / self.test_config.speed

            # Inject incidents (India adapted)
            injector.inject(sim, current_time)

            # Get state from simulation
            state = sim.get_state()  # {queues, occupancies, phase, etc.}

            # Controller action
            action = ctrl.act(state)

            # Step simulation
            sim.step(action)

            # Accumulate metrics
            metrics["total_wait"] += state.get("total_wait", 0)
            metrics["max_queue"] = max(metrics["max_queue"], state.get("max_queue", 0))
            metrics["throughput"] += state.get("throughput", 0)

            # Track incidents (India augmented)
            for itype in injector.incidents:
                if injector.incidents.get(itype, {}).get("active", False):
                    metrics["incidents"].append(itype)

            cycle_count += 1

        # Calculate final metrics
        if cycle_count > 0:
            metrics["avg_wait"] = metrics["total_wait"] / cycle_count
            metrics["throughput"] = metrics["throughput"] / cycle_count

        # Recovery time (time after last incident to return to baseline)
        metrics["recovery_time"] = injector.get_total_recovery_time()

        return metrics

    def _generate_report(self) -> Dict[str, Any]:
        """Generate aggregate robustness report - India adapted"""
        if not self.results:
            return {"error": "No results to analyze"}

        # Per-incident performance - India augmented
        incident_metrics = {}
        india_types = ["accident", "lane_block", "sensor_failure",
                      "autorickshaw_block", "cattle_on_road",
                      "religious_crowd", "political_rally", "monsoon_flooding"]

        for incident_type in india_types:
            # Filter runs where this incident occurred
            relevant = [r for r in self.results if incident_type in r.get("incidents", [])]

            if relevant:
                incident_metrics[incident_type] = {
                    "num_occurrences": len(relevant),
                    "avg_wait": np.mean([r["avg_wait"] for r in relevant]),
                    "max_wait": np.max([r["max_wait"] for r in relevant]),
                    "avg_throughput": np.mean([r["throughput"] for r in relevant]),
                    "recovery_time": np.mean([r["recovery_time"] for r in relevant]),
                    "success_rate": len([r for r in relevant if r["max_queue"] < 150]) / len(relevant),
                }

        # Overall metrics
        overall = {
            "total_runs": len(self.results),
            "successful_runs": sum(1 for r in self.results if r["max_queue"] < 150),
            "overall_avg_wait": np.mean([r["avg_wait"] for r in self.results]),
            "overall_max_queue": np.max([r["max_queue"] for r in self.results]),
            "overall_throughput": np.mean([r["throughput"] for r in self.results]),
        }

        # Incident impact (delta vs baseline) - India adapted
        baseline = self._get_baseline_metrics()
        incident_impact = {}
        for incident_type, metrics in incident_metrics.items():
            if "baseline" in baseline and baseline["baseline"]["avg_wait"] > 0:
                incident_impact[incident_type] = {
                    "wait_increase_pct": (
                        (metrics["avg_wait"] - baseline["baseline"]["avg_wait"]) /
                        baseline["baseline"]["avg_wait"] * 100
                    ),
                    "throughput_decrease_pct": (
                        (baseline["baseline"]["throughput"] - metrics["avg_throughput"]) /
                        baseline["baseline"]["throughput"] * 100
                    )
                }

        # Monsoon season analysis - India specific
        monsoon_analysis = {}
        monsoon_runs = [r for r in self.results if r.get("monsoon_month", False)]
        if monsoon_runs:
            monsoon_avg_wait = np.mean([r["avg_wait"] for r in monsoon_runs])
            non_monsoon_runs = [r for r in self.results if not r.get("monsoon_month", False)]
            if non_monsoon_runs:
                non_monsoon_avg_wait = np.mean([r["avg_wait"] for r in non_monsoon_runs])
                monsoon_analysis = {
                    "monsoon_avg_wait": monsoon_avg_wait,
                    "non_monsoon_avg_wait": non_monsoon_avg_wait,
                    "wait_increase_pct_monsoon": (
                        (monsoon_avg_wait - non_monsoon_avg_wait) /
                        non_monsoon_avg_wait * 100
                    ) if non_monsoon_avg_wait > 0 else 0
                }

        return {
            "overall": overall,
            "incident_metrics": incident_metrics,
            "incident_impact": incident_impact,
            "monsoon_analysis": monsoon_analysis,
            "per_run_results": self.results,
            "config": {
                "incidents_tested": self.test_config.incidents,
                "num_runs": self.test_config.num_runs,
                "duration_per_run_s": self.test_config.duration,
                "sim_speed": self.test_config.speed,
                "monsoon_months": self.test_config.monsoon_months
            }
        }

    def _get_baseline_metrics(self) -> Dict:
        """Get baseline (no-incident) metrics - unchanged"""
        no_incident = [r for r in self.results if not r.get("incidents")]
        if no_incident:
            return {
                "baseline": {
                    "avg_wait": np.mean([r["avg_wait"] for r in no_incident]),
                    "max_queue": np.min([r["max_queue"] for r in no_incident]),
                    "throughput": np.mean([r["throughput"] for r in no_incident]),
                }
            }
        return {}
```

## Key Metrics - Add India Notes

```python
def compute_metrics(state: Dict, prev_state: Optional[Dict] = None) -> Dict:
    """Compute standard traffic control metrics from simulation state - India notes"""

    # Queue metrics - unchanged
    queues = state.get("queues", {})  # per-lane queue lengths (meters)
    total_queue = sum(queues.values()) if queues else 0
    avg_queue = total_queue / len(queues) if queues else 0
    max_queue = max(queues.values()) if queues else 0

    # Wait time metrics - unchanged
    total_wait = state.get("total_wait", 0)  # sum of all vehicle waits
    avg_wait_per_veh = total_wait / state.get("total_vehicles", 1)  # avoid div by 0

    # Throughput - unchanged
    throughput = state.get("throughput", 0)  # vehicles passed per second
    vehicles_total = state.get("vehicles_total", 0)  # total vehicles in system

    # Phase stability - unchanged
    phase = state.get("current_phase", 0)
    if prev_state:
        phase_change = abs(phase - prev_state.get("current_phase", phase))
        phase_stability = 1.0 / (1.0 + phase_change)  # 1 = stable, 0 = chaotic
    else:
        phase_stability = 1.0

    # Quality score - add India consideration for two-wheeler density
    # Lower wait + higher throughput + more stable = better
    queue_penalty = avg_queue / 100.0  # normalize by 100m scale
    throughput_bonus = min(throughput / 10.0, 1.0)  # normalize
    stability_bonus = phase_stability

    # Indian: two-wheelers have higher impact on queue metrics
    # (more vehicles per meter, faster acceleration/deceleration)
    quality_score = max(0, 1.0 - 0.4*queue_penalty + 0.3*throughput_bonus + 0.3*stability_bonus)
    quality_score = min(1.0, quality_score)  # clamp 0-1

    # Add India-specific flag for monsoon/flood impact
    india_context = {
        "high_two_wheeler_density": avg_queue > 50,  # heuristic threshold
        "queue_penalty_applied": queue_penalty
    }

    return {
        "total_queue_m": total_queue,
        "avg_queue_m": avg_queue,
        "max_queue_m": max_queue,
        "total_wait_veh-s": total_wait,
        "avg_wait_s_per_veh": avg_wait_per_veh,
        "throughput_veh_s": throughput,
        "vehicles_total": vehicles_total,
        "phase_stability": phase_stability,
        "quality_score": quality_score,
        "india_context": india_context
    }
```

## Benchmark Networks (from T-REX) - Unchanged

The benchmark networks table and `get_benchmark_network` function remain unchanged from the original skill, as they're grid-size agnostic.

## Rules

- Test minimum 30 runs per incident type (for statistical significance)
- Each run: minimum 1 hour simulated time @ 30x speed = 2 minutes wall clock
- Metrics: total_wait, max_queue, throughput, quality_score, recovery_time
- **India addition**: Track monsoon season effects (months 6-9)
- Baseline: no-incident runs with same config for comparison
- Incident impact: % change vs baseline (wait increase, throughput decrease)
- Recovery time: seconds from incident end to quality_score > 95% of baseline
- **India addition**: Track autorickshaw_block, cattle_on_road, religious_crowd impacts separately
- Confidence intervals: 95% CI on all mean metrics (bootstrapping)
- Report format: JSON with overall, incident_metrics, incident_impact, monsoon_analysis sections
- Networks: grid4x4 (quick), cologne (medium), ingolstadt (large)
- Per-lane queues: north_0, north_1, south_0, south_1, east_0, east_1, west_0, west_1
- Phase states: Green/Yellow/Red per the 4-phase cycle
- Sensor failure: reduce YOLO conf threshold by 50% for duration
- Emergency priority: NTCIP REQUEST → grant extra green (up to +20s)
- Rerouting: distribute 30% of traffic to alternative routes
- Always log: sim_time, controller_type, network, incident_type, seed, monsoon_month
- Reproducibility: fix random seed per run (numpy.random.seed(42 + run_idx))
- India-specific: log `current_month` and `is_monsoon` for each run
