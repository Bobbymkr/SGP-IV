"""
Weather Model for Traffic Simulation
"""

import logging
import random
from dataclasses import dataclass
from enum import Enum
from typing import Dict, List, Tuple

logger = logging.getLogger(__name__)


class WeatherState(Enum):
    CLEAR = "clear"
    LIGHT_RAIN = "light_rain"
    HEAVY_MONSOON = "heavy_monsoon"
    WATERLOGGED = "waterlogged"


INDIA_WEATHER_SOURCES: Dict[WeatherState, List[str]] = {
    WeatherState.CLEAR: [
        "Dry conditions baseline; Indian urban free-flow speeds ~30-40 km/h (IIT/IIM city traffic studies)",
        "Clear-sky YOLO detection confidence near nominal in published Indian traffic datasets",
    ],
    WeatherState.LIGHT_RAIN: [
        "Indian urban free-flow speeds drop ~10-20% in light rain (road safety literature, CRRI studies)",
        "Moderate camera glare/wet-lens effects reduce vision detection confidence modestly",
        "Slight demand reduction as two-wheeler riders avoid trips in rain",
    ],
    WeatherState.HEAVY_MONSOON: [
        "Indian urban free-flow speeds drop ~20-30% in heavy rain; visibility/detection degradation well documented",
        "Heavy downpour cuts YOLO-style detection confidence substantially (rain streaks, spray, low contrast)",
        "Demand drops sharply during monsoon peaks; many commuters defer discretionary trips",
    ],
    WeatherState.WATERLOGGED: [
        "Waterlogging routinely submerges 1-2 lanes at low-lying junctions during Jun-Sep monsoon (Municipal flood reports: Mumbai, Chennai, Bengaluru, Delhi)",
        "Passable lane capacity roughly halves at flooded junctions; speeds crawl at wading depth",
        "Severe visibility/reflection artifacts degrade vehicle detection; only nearest lanes reliably sensed",
        "Braking decel severely limited on submerged pavement (hydroplaning risk)",
    ],
}


@dataclass(frozen=True)
class WeatherProfile:
    state: WeatherState
    speed_multiplier: float
    detection_confidence_factor: float
    usable_lane_fraction: float
    braking_decel_multiplier: float


WEATHER_PRESETS: Dict[str, WeatherProfile] = {
    "clear": WeatherProfile(
        state=WeatherState.CLEAR,
        speed_multiplier=1.0,
        detection_confidence_factor=1.0,
        usable_lane_fraction=1.0,
        braking_decel_multiplier=1.0,
    ),
    "light_rain": WeatherProfile(
        state=WeatherState.LIGHT_RAIN,
        speed_multiplier=0.8,
        detection_confidence_factor=0.85,
        usable_lane_fraction=1.0,
        braking_decel_multiplier=0.85,
    ),
    "heavy_monsoon": WeatherProfile(
        state=WeatherState.HEAVY_MONSOON,
        speed_multiplier=0.55,
        detection_confidence_factor=0.6,
        usable_lane_fraction=1.0,
        braking_decel_multiplier=0.7,
    ),
    "waterlogged": WeatherProfile(
        state=WeatherState.WATERLOGGED,
        speed_multiplier=0.35,
        detection_confidence_factor=0.5,
        usable_lane_fraction=0.5,
        braking_decel_multiplier=0.55,
    ),
}

_DEMAND_MULTIPLIER = {
    WeatherState.CLEAR: 1.0,
    WeatherState.LIGHT_RAIN: 0.9,
    WeatherState.HEAVY_MONSOON: 0.75,
    WeatherState.WATERLOGGED: 0.6,
}

_MONTH_TRANSITIONS: Dict[int, Dict[WeatherState, List[Tuple[float, WeatherState]]]] = {
    # month -> per-state [(probability, next_state), ...]
    m: {
        WeatherState.CLEAR: [
            (0.90, WeatherState.CLEAR),
            (0.08, WeatherState.LIGHT_RAIN),
            (0.02, WeatherState.HEAVY_MONSOON),
        ],
        WeatherState.LIGHT_RAIN: [
            (0.45, WeatherState.CLEAR),
            (0.50, WeatherState.LIGHT_RAIN),
            (0.05, WeatherState.HEAVY_MONSOON),
        ],
        WeatherState.HEAVY_MONSOON: [
            (0.20, WeatherState.CLEAR),
            (0.55, WeatherState.LIGHT_RAIN),
            (0.24, WeatherState.HEAVY_MONSOON),
            (0.01, WeatherState.WATERLOGGED),
        ],
        WeatherState.WATERLOGGED: [
            (0.05, WeatherState.CLEAR),
            (0.25, WeatherState.LIGHT_RAIN),
            (0.65, WeatherState.HEAVY_MONSOON),
            (0.05, WeatherState.WATERLOGGED),
        ],
    }
    for m in range(1, 6)
}
for m in range(10, 13):
    _MONTH_TRANSITIONS[m] = _MONTH_TRANSITIONS[1]

for m in range(6, 10):
    _MONTH_TRANSITIONS[m] = {
        WeatherState.CLEAR: [
            (0.60, WeatherState.CLEAR),
            (0.28, WeatherState.LIGHT_RAIN),
            (0.11, WeatherState.HEAVY_MONSOON),
            (0.01, WeatherState.WATERLOGGED),
        ],
        WeatherState.LIGHT_RAIN: [
            (0.25, WeatherState.CLEAR),
            (0.45, WeatherState.LIGHT_RAIN),
            (0.27, WeatherState.HEAVY_MONSOON),
            (0.03, WeatherState.WATERLOGGED),
        ],
        WeatherState.HEAVY_MONSOON: [
            (0.08, WeatherState.CLEAR),
            (0.32, WeatherState.LIGHT_RAIN),
            (0.52, WeatherState.HEAVY_MONSOON),
            (0.08, WeatherState.WATERLOGGED),
        ],
        WeatherState.WATERLOGGED: [
            (0.02, WeatherState.CLEAR),
            (0.15, WeatherState.LIGHT_RAIN),
            (0.63, WeatherState.HEAVY_MONSOON),
            (0.20, WeatherState.WATERLOGGED),
        ],
    }


class WeatherModel:
    """Stochastic weather model with India monsoon seasonality"""

    def __init__(self, initial_state: WeatherState = WeatherState.CLEAR):
        self._state = initial_state
        self._rng = random.Random()
        self._stochastic_enabled = False
        self._sim_time_s = 0.0

    def current(self) -> WeatherProfile:
        return WEATHER_PRESETS[self._state.value]

    def set_state(self, state: WeatherState):
        self._state = state
        logger.info("Weather state set to %s", state.value)

    def set_seed(self, seed: int):
        self._rng = random.Random(seed)
        self._stochastic_enabled = True

    def enable_stochastic(self, enabled: bool = True):
        self._stochastic_enabled = enabled

    def step(self, sim_time_s: float):
        self._sim_time_s += sim_time_s
        if not self._stochastic_enabled:
            return
        month = max(1, min(12, int((self._sim_time_s / 3600.0) % 8760 // 730) + 1))
        transitions = _MONTH_TRANSITIONS[month][self._state]
        r = self._rng.random()
        cumulative = 0.0
        for probability, next_state in transitions:
            cumulative += probability
            if r < cumulative:
                if next_state is not self._state:
                    logger.debug("Weather transition %s -> %s", self._state.value, next_state.value)
                self._state = next_state
                return

    def apply_to_generation_rate(self, base_veh_per_hour: float) -> float:
        return base_veh_per_hour * _DEMAND_MULTIPLIER[self._state]


if __name__ == "__main__":
    presets = [
        WEATHER_PRESETS["clear"],
        WEATHER_PRESETS["light_rain"],
        WEATHER_PRESETS["heavy_monsoon"],
        WEATHER_PRESETS["waterlogged"],
    ]

    speeds = [p.speed_multiplier for p in presets]
    dets = [p.detection_confidence_factor for p in presets]
    assert all(speeds[i] >= speeds[i + 1] for i in range(len(speeds) - 1))
    assert all(dets[i] >= dets[i + 1] for i in range(len(dets) - 1))

    m1 = WeatherModel(initial_state=WeatherState.CLEAR)
    m1.set_seed(42)
    m2 = WeatherModel(initial_state=WeatherState.CLEAR)
    m2.set_seed(42)
    for i in range(1000):
        m1.step(float(i * 3600))
        m2.step(float(i * 3600))
        assert m1.current().state == m2.current().state

    assert (
        abs(m1.apply_to_generation_rate(600.0) - 600.0 * _DEMAND_MULTIPLIER[m1.current().state])
        < 1e-9
    )

    dm = WeatherModel()
    assert dm.apply_to_generation_rate(100.0) == 100.0
    dm.set_state(WeatherState.LIGHT_RAIN)
    assert dm.apply_to_generation_rate(100.0) == 90.0
    dm.set_state(WeatherState.HEAVY_MONSOON)
    assert dm.apply_to_generation_rate(100.0) == 75.0
    dm.set_state(WeatherState.WATERLOGGED)
    assert dm.apply_to_generation_rate(100.0) == 60.0

    print("weather self-check passed")
