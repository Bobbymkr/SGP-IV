"""
City Profile Schema
Pydantic models for city-specific configuration
"""

from typing import Dict, List

from pydantic import BaseModel, Field


class VehicleLengths(BaseModel):
    """Vehicle lengths in meters per class"""

    car: float = 4.5
    bus: float = 12.0
    truck: float = 10.0
    two_wheeler: float = 2.0
    autorickshaw: float = 3.0
    cycle: float = 1.8
    tractor: float = 6.0
    bus_pedigree: float = 12.0


class VehicleMix(BaseModel):
    """Vehicle mix weights for spawning (must sum to 1.0)"""

    car: float = 0.55
    bus: float = 0.05
    truck: float = 0.08
    two_wheeler: float = 0.17
    autorickshaw: float = 0.10
    cycle: float = 0.03
    tractor: float = 0.01
    bus_pedigree: float = 0.01


class SignalBounds(BaseModel):
    """Signal timing bounds in seconds"""

    min_green: int = 10
    max_green: int = 60
    yellow: int = 5
    all_red: int = 2


class DetectorCalibration(BaseModel):
    """Detector calibration per approach (pixels to meters)"""

    north: float = 0.05
    south: float = 0.05
    east: float = 0.05
    west: float = 0.05


class IntersectionGeometry(BaseModel):
    """Intersection geometry for MAP generation"""

    approaches: List[str] = ["north", "south", "east", "west"]
    lanes_per_approach: int = 2
    lane_width: float = 3.5
    stop_line_positions: Dict[str, Dict[str, float]] = {}


class NTCIPConfig(BaseModel):
    """NTCIP controller configuration per intersection"""

    controller_ip: str = "127.0.0.1"
    stmp_port: int = 5000
    snmp_port: int = 161
    community: str = "public"
    phase_mapping: Dict[str, int] = {"north": 1, "south": 2, "east": 3, "west": 4}
    detector_mapping: Dict[str, str] = {"1": "north", "2": "south", "3": "east", "4": "west"}


class IncidentWeights(BaseModel):
    """Incident weights for robustness evaluation"""

    sensor_failure: float = 1.0
    lane_block: float = 1.5
    power_outage: float = 2.0
    weather_degradation: float = 1.0


class WeatherProfile(BaseModel):
    """Weather profile probabilities by month (1-12)"""

    clear: List[float] = Field(default_factory=lambda: [0.9] * 12)
    light_rain: List[float] = Field(default_factory=lambda: [0.1] * 12)
    heavy_monsoon: List[float] = Field(default_factory=lambda: [0.0] * 12)
    waterlogged: List[float] = Field(default_factory=lambda: [0.0] * 12)


class CityProfile(BaseModel):
    """Complete city profile configuration"""

    name: str
    lanes_per_approach: int = Field(default=3, ge=2, le=4)
    vehicle_mix: VehicleMix = Field(default_factory=VehicleMix)
    vehicle_lengths: VehicleLengths = Field(default_factory=VehicleLengths)
    signal_bounds: SignalBounds = Field(default_factory=SignalBounds)
    behavior_preset: str = Field(
        default="typical_urban", pattern="^(disciplined|typical_urban|aggressive_metro)$"
    )
    weather_profile: str = Field(
        default="clear", pattern="^(clear|light_rain|heavy_monsoon|waterlogged)$"
    )
    incident_weights: IncidentWeights = Field(default_factory=IncidentWeights)
    detector_calibration: DetectorCalibration = Field(default_factory=DetectorCalibration)
    ntcip_config: NTCIPConfig = Field(default_factory=NTCIPConfig)
    intersection_geometry: IntersectionGeometry = Field(default_factory=IntersectionGeometry)

    # Detection confidence thresholds per class (0-1)
    detection_thresholds: Dict[str, float] = Field(
        default_factory=lambda: {
            "car": 0.5,
            "bus": 0.45,
            "truck": 0.45,
            "two_wheeler": 0.4,
            "autorickshaw": 0.4,
            "cycle": 0.35,
            "tractor": 0.4,
            "bus_pedigree": 0.45,
        }
    )

    # Class mapping from model output to internal classes
    class_mapping: Dict[int, str] = Field(
        default_factory=lambda: {
            0: "car",
            1: "bus",
            2: "truck",
            3: "two_wheeler",
            4: "autorickshaw",
            5: "cycle",
            6: "tractor",
            7: "bus_pedigree",
        }
    )

    # Queue estimation parameters
    queue_estimation: Dict[str, float] = Field(
        default_factory=lambda: {
            "vehicle_length_buffer": 1.0,  # extra meters per vehicle
            "min_gap": 2.0,  # minimum gap between vehicles in queue
            "queue_zone_distance": 50.0,  # meters from stop line
        }
    )

    # Per-class discharge headways in seconds (trial-and-error calibrated per
    # city; missing keys fall back to policies.DEFAULT_HEADWAYS). Append-only:
    # never rename keys, the green policy reads them by name.
    discharge_headways: Dict[str, float] = Field(
        default_factory=lambda: {
            "two_wheeler": 1.0,
            "car": 2.0,
            "autorickshaw": 2.0,
            "cycle": 1.0,
            "tractor": 2.5,
            "bus": 3.2,
            "truck": 3.2,
            "bus_pedigree": 3.2,
        }
    )

    # Shared cycle budget in seconds for the dynamic demand-share cap.
    cycle_budget_s: float = 120.0

    class Config:
        extra = "allow"  # Allow additional city-specific fields


# Tier 2 default profile (base for other cities)
TIER2_DEFAULT = CityProfile(
    name="tier2_default",
    lanes_per_approach=3,
    vehicle_mix=VehicleMix(
        car=0.55,
        bus=0.05,
        truck=0.08,
        two_wheeler=0.17,
        autorickshaw=0.10,
        cycle=0.03,
        tractor=0.01,
        bus_pedigree=0.01,
    ),
    vehicle_lengths=VehicleLengths(),
    signal_bounds=SignalBounds(min_green=10, max_green=60, yellow=5, all_red=2),
    behavior_preset="typical_urban",
    weather_profile="clear",
    incident_weights=IncidentWeights(),
    detector_calibration=DetectorCalibration(),
    ntcip_config=NTCIPConfig(),
    intersection_geometry=IntersectionGeometry(),
)

# Mumbai profile - extends tier2 with 4 lanes, aggressive metro
MUMBAI = CityProfile(
    name="mumbai",
    lanes_per_approach=4,
    vehicle_mix=VehicleMix(
        car=0.45,
        bus=0.08,
        truck=0.05,
        two_wheeler=0.25,
        autorickshaw=0.12,
        cycle=0.03,
        tractor=0.01,
        bus_pedigree=0.01,
    ),
    vehicle_lengths=VehicleLengths(),
    signal_bounds=SignalBounds(min_green=15, max_green=90, yellow=5, all_red=3),
    behavior_preset="aggressive_metro",
    weather_profile="heavy_monsoon",
    incident_weights=IncidentWeights(
        sensor_failure=1.2, lane_block=2.0, power_outage=2.5, weather_degradation=1.5
    ),
    detector_calibration=DetectorCalibration(north=0.045, south=0.045, east=0.05, west=0.05),
    ntcip_config=NTCIPConfig(),
    intersection_geometry=IntersectionGeometry(
        approaches=["north", "south", "east", "west"],
        lanes_per_approach=4,
        lane_width=3.2,
    ),
)

# Delhi profile - 4 lanes, typical urban
DELHI = CityProfile(
    name="delhi",
    lanes_per_approach=4,
    vehicle_mix=VehicleMix(
        car=0.50,
        bus=0.10,
        truck=0.07,
        two_wheeler=0.20,
        autorickshaw=0.08,
        cycle=0.03,
        tractor=0.01,
        bus_pedigree=0.01,
    ),
    vehicle_lengths=VehicleLengths(),
    signal_bounds=SignalBounds(min_green=15, max_green=80, yellow=5, all_red=2),
    behavior_preset="typical_urban",
    weather_profile="clear",
    incident_weights=IncidentWeights(
        sensor_failure=1.0, lane_block=1.5, power_outage=2.0, weather_degradation=1.0
    ),
    detector_calibration=DetectorCalibration(),
    ntcip_config=NTCIPConfig(),
    intersection_geometry=IntersectionGeometry(
        approaches=["north", "south", "east", "west"],
        lanes_per_approach=4,
        lane_width=3.5,
    ),
)

# Bangalore profile - 3 lanes, typical urban
BANGALORE = CityProfile(
    name="bangalore",
    lanes_per_approach=3,
    vehicle_mix=VehicleMix(
        car=0.55,
        bus=0.08,
        truck=0.05,
        two_wheeler=0.22,
        autorickshaw=0.07,
        cycle=0.02,
        tractor=0.005,
        bus_pedigree=0.005,
    ),
    vehicle_lengths=VehicleLengths(),
    signal_bounds=SignalBounds(min_green=10, max_green=70, yellow=5, all_red=2),
    behavior_preset="typical_urban",
    weather_profile="light_rain",
    incident_weights=IncidentWeights(
        sensor_failure=1.0, lane_block=1.3, power_outage=1.8, weather_degradation=1.2
    ),
    detector_calibration=DetectorCalibration(),
    ntcip_config=NTCIPConfig(),
    intersection_geometry=IntersectionGeometry(
        approaches=["north", "south", "east", "west"],
        lanes_per_approach=3,
        lane_width=3.5,
    ),
)

# All profiles registry
CITY_PROFILES = {
    "tier2_default": TIER2_DEFAULT,
    "mumbai": MUMBAI,
    "delhi": DELHI,
    "bangalore": BANGALORE,
}


def get_city_profile(name: str) -> CityProfile:
    """Get city profile by name"""
    profile = CITY_PROFILES.get(name.lower())
    if profile is None:
        raise ValueError(f"Unknown city profile: {name}. Available: {list(CITY_PROFILES.keys())}")
    return profile


def list_city_profiles() -> List[str]:
    """List available city profiles"""
    return list(CITY_PROFILES.keys())
